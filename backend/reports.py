from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def build_report_payload(portfolio: dict[str, Any], analysis: dict[str, Any]) -> dict[str, Any]:
    metrics = analysis["metrics"]
    scenarios = analysis["historical_scenarios"]
    worst_scenario = min(scenarios, key=lambda row: row["portfolio_return"]) if scenarios else None
    summary = deterministic_summary(portfolio, metrics, worst_scenario)
    return {
        "portfolio_id": portfolio["id"],
        "portfolio_name": portfolio["name"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "start_date": analysis["start_date"],
        "end_date": analysis["end_date"],
        "metrics": metrics,
        "performance_series": analysis["performance_series"],
        "drawdown_series": analysis["drawdown_series"],
        "rolling_returns": analysis["rolling_returns"],
        "correlation_matrix": analysis["correlation_matrix"],
        "exposures": analysis["exposures"],
        "concentration": analysis["concentration"],
        "risk_contributions": analysis["risk_contributions"],
        "scenarios": scenarios,
        "summary": summary,
        "warnings": analysis["warnings"],
        "assumptions": analysis["assumptions"],
        "export": {
            "format": "json",
            "title": f"Risk Report: {portfolio['name']}",
            "disclaimer": "Analytics are based on seeded demo data and are not investment advice.",
        },
    }


def deterministic_summary(
    portfolio: dict[str, Any],
    metrics: dict[str, Any],
    worst_scenario: dict[str, Any] | None,
) -> str:
    concentration = metrics["concentration"]
    exposures = metrics["exposures"]
    top_sector = exposures["sector"][0] if exposures["sector"] else {"name": "Unknown", "weight": 0.0}
    top_risk = metrics["risk_contributions"][0] if metrics["risk_contributions"] else {"symbol": "N/A", "risk_contribution_pct": 0.0}
    vol_ratio = (
        metrics["annualized_volatility"] / metrics["benchmark_annualized_volatility"]
        if metrics["benchmark_annualized_volatility"]
        else 0.0
    )
    risk_level = _risk_level(metrics["annualized_volatility"], metrics["max_drawdown"], concentration["hhi"])
    scenario_text = (
        f"The most damaging predefined scenario was {worst_scenario['scenario']} "
        f"at {worst_scenario['portfolio_return']:.1%}."
        if worst_scenario
        else "No historical scenario window was available."
    )
    return (
        f"{portfolio['name']} has a {risk_level} risk profile with annualized volatility of "
        f"{metrics['annualized_volatility']:.1%}, or {vol_ratio:.2f}x the benchmark. "
        f"The largest position is {concentration['largest_position_symbol']} at "
        f"{concentration['largest_single_position']:.1%}, while the largest sector exposure is "
        f"{top_sector['name']} at {top_sector['weight']:.1%}. "
        f"{top_risk['symbol']} is the largest estimated contributor to total variance. "
        f"Historical 95% one-day VaR is {metrics['value_at_risk']['95']['loss_pct']:.2%}, "
        f"with expected shortfall of {metrics['value_at_risk']['95']['expected_shortfall_loss_pct']:.2%}. "
        f"Maximum drawdown over the selected period was {metrics['max_drawdown']:.1%}. "
        f"{scenario_text} Assumptions: adjusted-close seeded demo data, 252 trading days, "
        "0% risk-free rate, and historical tail estimates; these figures are not forecasts."
    )


def _risk_level(volatility: float, max_drawdown: float, hhi: float) -> str:
    score = 0
    score += 2 if volatility >= 0.25 else 1 if volatility >= 0.15 else 0
    score += 2 if max_drawdown <= -0.30 else 1 if max_drawdown <= -0.18 else 0
    score += 1 if hhi >= 0.20 else 0
    if score >= 4:
        return "high"
    if score >= 2:
        return "moderate"
    return "lower"
