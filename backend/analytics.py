from __future__ import annotations

from datetime import date
from math import sqrt
from typing import Any

import numpy as np
import pandas as pd

from .data import ASSET_METADATA, HISTORICAL_SCENARIOS, PRICES, SUPPORTED_SYMBOLS

TRADING_DAYS = 252
WEIGHT_TOLERANCE = 1e-6


def validate_positions(positions: list[dict[str, Any]], benchmark_symbol: str = "SPY") -> dict[str, Any]:
    normalized = [_normalize_position(position) for position in positions]
    total = sum(position["weight"] for position in normalized)
    if abs(total - 1.0) > WEIGHT_TOLERANCE:
        raise ValueError(f"Weights must sum to 1.0; received {total:.6f}")

    unsupported = sorted({position["symbol"] for position in normalized if position["symbol"] not in SUPPORTED_SYMBOLS})
    if benchmark_symbol.upper() not in SUPPORTED_SYMBOLS:
        unsupported.append(benchmark_symbol.upper())
    if unsupported:
        raise ValueError(f"Unsupported symbols: {unsupported}")

    duplicates = sorted({symbol for symbol in [p["symbol"] for p in normalized] if [p["symbol"] for p in normalized].count(symbol) > 1})
    if duplicates:
        raise ValueError(f"Duplicate positions are not allowed: {duplicates}")

    return {
        "weight_total": round(total, 10),
        "supported": True,
    }


def enrich_positions(positions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched = []
    for position in positions:
        normalized = _normalize_position(position)
        metadata = ASSET_METADATA[normalized["symbol"]]
        legacy_asset_class = "cash" if normalized["symbol"] == "CASH" else "market"
        enriched.append(
            {
                **normalized,
                "sector": metadata["sector"],
                "asset_class": legacy_asset_class,
                "risk_asset_class": metadata["asset_class"],
                "factor": metadata["factor"],
            }
        )
    return enriched


def analyze_portfolio(
    portfolio: dict[str, Any],
    start_date: date,
    end_date: date,
    selected_confidence: float = 0.95,
    prices: pd.DataFrame = PRICES,
) -> dict[str, Any]:
    if start_date >= end_date:
        raise ValueError("start_date must be before end_date")

    weights = {position["symbol"]: float(position["weight"]) for position in portfolio["positions"]}
    benchmark_symbol = portfolio.get("benchmark_symbol", "SPY").upper()
    requested_symbols = sorted(set(weights) | {benchmark_symbol})
    returns, warnings = returns_for(requested_symbols, start_date, end_date, prices)
    if returns.empty:
        raise ValueError("No price history is available for the requested date range")

    for symbol in requested_symbols:
        if symbol not in returns.columns:
            returns[symbol] = 0.0

    asset_returns = returns[list(weights.keys())]
    portfolio_returns = asset_returns.mul(pd.Series(weights)).sum(axis=1)
    benchmark_returns = returns[benchmark_symbol]

    metrics = _risk_return_metrics(
        portfolio_returns=portfolio_returns,
        benchmark_returns=benchmark_returns,
        selected_confidence=selected_confidence,
        portfolio_value=portfolio.get("portfolio_value"),
    )
    concentration = concentration_metrics(weights)
    exposures = exposure_metrics(portfolio["positions"])
    correlation = correlation_metrics(asset_returns, benchmark_returns)
    risk_contributions = risk_contribution(asset_returns, weights)

    metrics["concentration"] = concentration
    metrics["exposures"] = exposures
    metrics["correlation"] = correlation
    metrics["correlation_matrix"] = correlation["matrix"]
    metrics["risk_contributions"] = risk_contributions

    cumulative = (1.0 + portfolio_returns).cumprod() - 1.0
    benchmark_cumulative = (1.0 + benchmark_returns).cumprod() - 1.0
    drawdowns = drawdown_series(portfolio_returns)
    rolling_21 = rolling_return_series(portfolio_returns, 21)
    rolling_63 = rolling_return_series(portfolio_returns, 63)

    return {
        "start_date": str(start_date),
        "end_date": str(end_date),
        "metrics": metrics,
        "performance_series": _paired_series(cumulative, benchmark_cumulative, "portfolio", "benchmark"),
        "drawdown_series": [{"date": str(index), "drawdown": float(value)} for index, value in drawdowns.items()],
        "rolling_returns": {
            "21_day": [{"date": str(index), "return": float(value)} for index, value in rolling_21.dropna().items()],
            "63_day": [{"date": str(index), "return": float(value)} for index, value in rolling_63.dropna().items()],
        },
        "correlation_matrix": correlation["matrix"],
        "exposures": exposures,
        "concentration": concentration,
        "risk_contributions": risk_contributions,
        "historical_scenarios": historical_scenarios(portfolio, prices),
        "warnings": warnings,
        "assumptions": [
            "Adjusted close prices use deterministic seeded demo data for local development.",
            "Cash earns a 0% daily return.",
            "Risk-free rate is 0% for Sharpe and Sortino calculations.",
            "VaR and expected shortfall are historical one-day estimates, not forecasts.",
        ],
    }


def returns_for(
    symbols: list[str],
    start_date: date,
    end_date: date,
    prices: pd.DataFrame = PRICES,
) -> tuple[pd.DataFrame, list[str]]:
    normalized = sorted({symbol.upper() for symbol in symbols})
    df = prices[prices["symbol"].isin(normalized)].copy()
    df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
    warnings: list[str] = []
    if df.empty:
        return pd.DataFrame(), ["No adjusted-close rows found for the requested date range."]

    pivot = df.pivot(index="date", columns="symbol", values="adjusted_close").sort_index()
    for symbol in normalized:
        if symbol not in pivot.columns:
            warnings.append(f"{symbol} has no price history in the requested window.")
            pivot[symbol] = np.nan

    if len(pivot.index) < 30:
        warnings.append("Requested window has fewer than 30 trading days; risk estimates may be unstable.")

    missing_ratio = pivot.isna().mean()
    for symbol, ratio in missing_ratio.items():
        if ratio > 0:
            warnings.append(f"{symbol} is missing {ratio:.1%} of adjusted-close observations.")

    returns = pivot.pct_change(fill_method=None).dropna(how="all")
    returns["CASH"] = 0.0 if "CASH" in normalized else returns.get("CASH", pd.Series(index=returns.index, dtype=float))
    returns = returns.reindex(columns=normalized)
    returns = returns.fillna(0.0)
    return returns, warnings


def historical_scenarios(portfolio: dict[str, Any], prices: pd.DataFrame = PRICES) -> list[dict[str, Any]]:
    rows = []
    for name, (start_text, end_text) in HISTORICAL_SCENARIOS.items():
        start = pd.Timestamp(start_text).date()
        end = pd.Timestamp(end_text).date()
        rows.append(_scenario_result(name, portfolio, start, end, prices))
    return rows


def concentration_metrics(weights: dict[str, float]) -> dict[str, Any]:
    sorted_weights = sorted(weights.items(), key=lambda item: item[1], reverse=True)
    hhi = sum(weight * weight for weight in weights.values())
    return {
        "largest_single_position": float(sorted_weights[0][1]),
        "largest_position_symbol": sorted_weights[0][0],
        "top_5_weight": float(sum(weight for _, weight in sorted_weights[:5])),
        "hhi": float(hhi),
        "number_of_holdings": len(weights),
        "effective_number_of_holdings": float(1.0 / hhi) if hhi else 0.0,
        "top_positions": [{"symbol": symbol, "weight": float(weight)} for symbol, weight in sorted_weights[:5]],
    }


def exposure_metrics(positions: list[dict[str, Any]]) -> dict[str, Any]:
    sectors: dict[str, float] = {}
    asset_classes: dict[str, float] = {}
    factors: dict[str, float] = {}
    for position in positions:
        weight = float(position["weight"])
        sector = position.get("sector") or ASSET_METADATA[position["symbol"]]["sector"]
        asset_class = position.get("risk_asset_class") or ASSET_METADATA[position["symbol"]]["asset_class"]
        factor = position.get("factor") or ASSET_METADATA[position["symbol"]]["factor"]
        sectors[sector] = sectors.get(sector, 0.0) + weight
        asset_classes[asset_class] = asset_classes.get(asset_class, 0.0) + weight
        factors[factor] = factors.get(factor, 0.0) + weight

    return {
        "sector": _sorted_exposure(sectors),
        "asset_class": _sorted_exposure(asset_classes),
        "factor": _sorted_exposure(factors),
    }


def correlation_metrics(asset_returns: pd.DataFrame, benchmark_returns: pd.Series) -> dict[str, Any]:
    matrix = asset_returns.corr().replace([np.inf, -np.inf], np.nan).fillna(0.0)
    matrix_payload = {
        row: {column: float(round(value, 4)) for column, value in values.items()}
        for row, values in matrix.to_dict(orient="index").items()
    }
    pairwise = matrix.where(~np.eye(len(matrix), dtype=bool)).stack()
    rolling = asset_returns.apply(lambda column: column.rolling(63).corr(benchmark_returns)).tail(260)
    return {
        "matrix": matrix_payload,
        "average_pairwise_correlation": float(pairwise.mean()) if not pairwise.empty else 0.0,
        "rolling_63d_to_benchmark": [
            {"date": str(index), **{symbol: _clean_float(value) for symbol, value in values.items()}}
            for index, values in rolling.fillna(0.0).iterrows()
        ],
    }


def risk_contribution(asset_returns: pd.DataFrame, weights: dict[str, float]) -> list[dict[str, Any]]:
    ordered_symbols = list(weights.keys())
    covariance = asset_returns[ordered_symbols].cov() * TRADING_DAYS
    weight_vector = np.array([weights[symbol] for symbol in ordered_symbols])
    portfolio_variance = float(weight_vector.T @ covariance.to_numpy() @ weight_vector)
    if portfolio_variance <= 0:
        return [{"symbol": symbol, "weight": float(weights[symbol]), "risk_contribution_pct": 0.0} for symbol in ordered_symbols]

    marginal = covariance.to_numpy() @ weight_vector
    contributions = weight_vector * marginal / portfolio_variance
    rows = [
        {
            "symbol": symbol,
            "weight": float(weights[symbol]),
            "risk_contribution_pct": float(contribution),
            "annualized_volatility": float(asset_returns[symbol].std() * sqrt(TRADING_DAYS)),
        }
        for symbol, contribution in zip(ordered_symbols, contributions)
    ]
    return sorted(rows, key=lambda row: abs(row["risk_contribution_pct"]), reverse=True)


def drawdown_series(returns: pd.Series) -> pd.Series:
    wealth = (1.0 + returns).cumprod()
    return wealth / wealth.cummax() - 1.0


def rolling_return_series(returns: pd.Series, window: int) -> pd.Series:
    return (1.0 + returns).rolling(window).apply(np.prod, raw=True) - 1.0


def _risk_return_metrics(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
    selected_confidence: float,
    portfolio_value: float | None,
) -> dict[str, Any]:
    cumulative_return = float((1.0 + portfolio_returns).prod() - 1.0)
    benchmark_cumulative_return = float((1.0 + benchmark_returns).prod() - 1.0)
    years = max(len(portfolio_returns) / TRADING_DAYS, 1.0 / TRADING_DAYS)
    annualized_return = float((1.0 + cumulative_return) ** (1.0 / years) - 1.0)
    benchmark_annualized_return = float((1.0 + benchmark_cumulative_return) ** (1.0 / years) - 1.0)
    annualized_volatility = float(portfolio_returns.std() * sqrt(TRADING_DAYS))
    benchmark_annualized_volatility = float(benchmark_returns.std() * sqrt(TRADING_DAYS))
    downside = portfolio_returns[portfolio_returns < 0]
    downside_volatility = float(downside.std() * sqrt(TRADING_DAYS)) if len(downside) > 1 else 0.0
    tracking_error = float((portfolio_returns - benchmark_returns).std() * sqrt(TRADING_DAYS))
    active_return = annualized_return - benchmark_annualized_return
    benchmark_variance = float(np.var(benchmark_returns)) if len(benchmark_returns) > 1 else 0.0
    beta = (
        float(np.cov(portfolio_returns, benchmark_returns, ddof=1)[0, 1] / benchmark_variance)
        if benchmark_variance
        else 0.0
    )

    value_at_risk = {
        "95": _tail_metric(portfolio_returns, 0.95, portfolio_value),
        "99": _tail_metric(portfolio_returns, 0.99, portfolio_value),
    }
    selected_key = str(int(round(selected_confidence * 100)))
    selected_tail = value_at_risk.get(selected_key) or _tail_metric(portfolio_returns, selected_confidence, portfolio_value)
    max_drawdown = float(drawdown_series(portfolio_returns).min())
    benchmark_max_drawdown = float(drawdown_series(benchmark_returns).min())

    return {
        "daily_observations": int(len(portfolio_returns)),
        "cumulative_return": cumulative_return,
        "annualized_return": annualized_return,
        "benchmark_cumulative_return": benchmark_cumulative_return,
        "benchmark_annualized_return": benchmark_annualized_return,
        "benchmark_relative_return": cumulative_return - benchmark_cumulative_return,
        "annualized_volatility": annualized_volatility,
        "benchmark_annualized_volatility": benchmark_annualized_volatility,
        "sharpe_ratio": annualized_return / annualized_volatility if annualized_volatility else 0.0,
        "sortino_ratio": annualized_return / downside_volatility if downside_volatility else 0.0,
        "beta_to_benchmark": beta,
        "max_drawdown": max_drawdown,
        "benchmark_max_drawdown": benchmark_max_drawdown,
        "tracking_error": tracking_error,
        "information_ratio": active_return / tracking_error if tracking_error else 0.0,
        "value_at_risk": value_at_risk,
        "var": selected_tail["return"],
        "var_loss_pct": selected_tail["loss_pct"],
        "var_dollar": selected_tail["dollar"],
        "expected_shortfall": selected_tail["expected_shortfall_return"],
        "expected_shortfall_loss_pct": selected_tail["expected_shortfall_loss_pct"],
        "expected_shortfall_dollar": selected_tail["expected_shortfall_dollar"],
    }


def _tail_metric(returns: pd.Series, confidence: float, portfolio_value: float | None) -> dict[str, Any]:
    threshold = float(np.quantile(returns, 1.0 - confidence))
    tail = returns[returns <= threshold]
    expected_shortfall = float(tail.mean()) if not tail.empty else threshold
    value = float(portfolio_value or 0.0)
    return {
        "confidence": confidence,
        "return": threshold,
        "loss_pct": max(-threshold, 0.0),
        "dollar": max(-threshold, 0.0) * value if value else None,
        "expected_shortfall_return": expected_shortfall,
        "expected_shortfall_loss_pct": max(-expected_shortfall, 0.0),
        "expected_shortfall_dollar": max(-expected_shortfall, 0.0) * value if value else None,
    }


def _scenario_result(
    name: str,
    portfolio: dict[str, Any],
    start_date: date,
    end_date: date,
    prices: pd.DataFrame,
) -> dict[str, Any]:
    weights = {position["symbol"]: float(position["weight"]) for position in portfolio["positions"]}
    benchmark_symbol = portfolio.get("benchmark_symbol", "SPY")
    returns, warnings = returns_for(list(weights) + [benchmark_symbol], start_date, end_date, prices)
    if returns.empty:
        return {
            "scenario": name,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "portfolio_return": 0.0,
            "benchmark_return": 0.0,
            "worst_drawdown": 0.0,
            "best_holding": None,
            "worst_holding": None,
            "commentary": "No seeded data is available for this scenario window.",
            "warnings": warnings,
        }

    asset_returns = returns[list(weights)]
    portfolio_returns = asset_returns.mul(pd.Series(weights)).sum(axis=1)
    holding_returns = {symbol: float((1.0 + asset_returns[symbol]).prod() - 1.0) for symbol in weights}
    best_symbol = max(holding_returns, key=holding_returns.get)
    worst_symbol = min(holding_returns, key=holding_returns.get)
    portfolio_return = float((1.0 + portfolio_returns).prod() - 1.0)
    benchmark_return = float((1.0 + returns[benchmark_symbol]).prod() - 1.0)
    contributors = [
        {
            "symbol": symbol,
            "holding_return": holding_return,
            "weighted_contribution": float(weights[symbol] * holding_return),
        }
        for symbol, holding_return in holding_returns.items()
    ]
    return {
        "scenario": name,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "portfolio_return": portfolio_return,
        "benchmark_return": benchmark_return,
        "worst_drawdown": float(drawdown_series(portfolio_returns).min()),
        "best_holding": {"symbol": best_symbol, "return": holding_returns[best_symbol]},
        "worst_holding": {"symbol": worst_symbol, "return": holding_returns[worst_symbol]},
        "contributors": sorted(contributors, key=lambda row: row["weighted_contribution"]),
        "commentary": _historical_commentary(name, portfolio_return, benchmark_return, worst_symbol),
        "warnings": warnings,
    }


def _historical_commentary(name: str, portfolio_return: float, benchmark_return: float, worst_symbol: str) -> str:
    relative = "outperformed" if portfolio_return > benchmark_return else "underperformed"
    return (
        f"During {name}, the portfolio {relative} the benchmark by "
        f"{portfolio_return - benchmark_return:.1%}; {worst_symbol} was the weakest weighted holding."
    )


def _normalize_position(position: dict[str, Any]) -> dict[str, Any]:
    return {"symbol": str(position["symbol"]).upper(), "weight": float(position["weight"])}


def _sorted_exposure(values: dict[str, float]) -> list[dict[str, Any]]:
    return [
        {"name": name, "weight": float(weight)}
        for name, weight in sorted(values.items(), key=lambda item: item[1], reverse=True)
    ]


def _paired_series(left: pd.Series, right: pd.Series, left_name: str, right_name: str) -> list[dict[str, Any]]:
    aligned = pd.concat([left.rename(left_name), right.rename(right_name)], axis=1).fillna(0.0).tail(520)
    return [
        {"date": str(index), left_name: float(row[left_name]), right_name: float(row[right_name])}
        for index, row in aligned.iterrows()
    ]


def _clean_float(value: Any) -> float:
    if value is None or pd.isna(value) or np.isinf(value):
        return 0.0
    return float(value)
