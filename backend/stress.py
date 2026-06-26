from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import numpy as np
import pandas as pd

from .analytics import historical_scenarios, returns_for
from .data import ASSET_METADATA, PRICES


def run_hypothetical_stress(
    portfolio: dict[str, Any],
    shocks: list[dict[str, Any]],
    prices: pd.DataFrame = PRICES,
    as_of: date | None = None,
) -> dict[str, Any]:
    weights = {position["symbol"]: float(position["weight"]) for position in portfolio["positions"]}
    if not shocks:
        raise ValueError("At least one shock is required for a hypothetical stress test")

    end = as_of or date.today()
    start = end - timedelta(days=365 * 3)
    returns, _ = returns_for(sorted(set(weights) | {"SPY", "QQQ", "TLT", "USO", "GLD"}), start, end, prices)
    contributors = []
    total = 0.0
    assumptions = [
        "Direct shocks are applied one-for-one to matching holdings.",
        "Broad market shocks use trailing beta estimates where return history is available.",
        "Commodity and rates proxy shocks use category sensitivities for related holdings.",
    ]

    for shock in shocks:
        target = str(shock["target"]).upper()
        shock_pct = float(shock["shock_pct"])
        for symbol, weight in weights.items():
            applied = _applied_shock(symbol, target, shock_pct, returns)
            impact = weight * applied
            if abs(impact) > 1e-12:
                contributors.append({"symbol": symbol, "applied_shock": float(applied), "portfolio_impact": float(impact)})
                total += impact
    return {
        "scenario_type": "hypothetical",
        "estimated_portfolio_return": float(total),
        "estimated_dollar_impact": _dollar_impact(portfolio.get("portfolio_value"), total),
        "contributors": sorted(contributors, key=lambda row: abs(row["portfolio_impact"]), reverse=True),
        "assumptions": assumptions
        + ["Broad equity shocks use a simple 0.65 beta proxy for equity-like holdings."],
        "limitations": ["Hypothetical shocks are approximations, not forecasts."],
    }


def run_historical_stress(portfolio: dict[str, Any], prices: pd.DataFrame = PRICES) -> dict[str, Any]:
    scenarios = historical_scenarios(portfolio, prices)
    worst = min(scenarios, key=lambda row: row["portfolio_return"]) if scenarios else None
    return {
        "scenario_type": "historical",
        "scenarios": scenarios,
        "worst_scenario": worst,
        "assumptions": ["Historical stress tests replay seeded adjusted-close returns for fixed windows."],
        "limitations": ["Past scenario returns may not resemble future stress events."],
    }


def _applied_shock(symbol: str, target: str, shock_pct: float, returns: pd.DataFrame) -> float:
    if symbol == "CASH":
        return 0.0
    if symbol == target:
        return shock_pct
    if target in {"SPY", "QQQ", "IWM"}:
        return shock_pct * _fallback_equity_beta(symbol, target)
    if target == "TLT":
        return shock_pct * _rates_sensitivity(symbol)
    if target == "USO":
        return shock_pct * _oil_sensitivity(symbol)
    if target in {"GLD", "CPER"}:
        return shock_pct * _commodity_sensitivity(symbol, target)
    return 0.0


def _beta(symbol: str, target: str, returns: pd.DataFrame) -> float:
    if symbol not in returns.columns or target not in returns.columns:
        return 0.0
    symbol_returns = returns[symbol]
    target_returns = returns[target]
    variance = float(np.var(target_returns, ddof=1)) if len(target_returns) > 1 else 0.0
    if variance <= 0:
        return 0.0
    beta = float(np.cov(symbol_returns, target_returns, ddof=1)[0, 1] / variance)
    return max(min(beta, 2.5), -0.75)


def _fallback_equity_beta(symbol: str, target: str) -> float:
    metadata = ASSET_METADATA[symbol]
    factor = metadata["factor"]
    asset_class = metadata["asset_class"]
    if target == "QQQ" and "Growth" in factor:
        return 1.10
    if asset_class in {"Equity", "ETF"}:
        return 0.65
    if metadata["sector"] == "Commodity":
        return 0.25
    return 0.0


def _rates_sensitivity(symbol: str) -> float:
    factor = ASSET_METADATA[symbol]["factor"]
    if factor == "Duration":
        return 1.0
    if "Growth" in factor:
        return -0.30
    if ASSET_METADATA[symbol]["asset_class"] == "Equity":
        return -0.12
    if symbol == "GLD":
        return 0.20
    return 0.0


def _oil_sensitivity(symbol: str) -> float:
    if symbol == "XOM":
        return 0.45
    if symbol == "CPER":
        return 0.20
    if ASSET_METADATA[symbol]["asset_class"] == "Equity":
        return -0.05
    return 0.0


def _commodity_sensitivity(symbol: str, target: str) -> float:
    if target == "GLD" and symbol == "TLT":
        return 0.10
    if ASSET_METADATA[symbol]["sector"] == "Commodity":
        return 0.30
    return 0.0


def _dollar_impact(value: float | None, return_impact: float) -> float | None:
    if value is None:
        return None
    return float(value) * float(return_impact)
