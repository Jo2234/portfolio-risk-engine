from __future__ import annotations

from math import sqrt

import numpy as np
import pandas as pd
import pytest

from backend.main import AnalyzeRequest, metrics, returns_for
from conftest import FIXTURE_RETURNS


START_DATE = "2024-01-01"
END_DATE = "2024-01-09"
TOL = 1e-6


def expected_portfolio_returns() -> np.ndarray:
    return np.array(FIXTURE_RETURNS["AAPL"]) * 0.6 + np.array(FIXTURE_RETURNS["MSFT"]) * 0.4


def expected_benchmark_returns() -> np.ndarray:
    return np.array(FIXTURE_RETURNS["SPY"])


def test_returns_for_uses_adjusted_close_percent_change_and_zero_cash(deterministic_prices):
    returns = returns_for(["AAPL", "MSFT", "CASH"], START_DATE, END_DATE)

    assert len(returns) == 6
    np.testing.assert_allclose(returns["AAPL"].to_numpy(), FIXTURE_RETURNS["AAPL"], rtol=TOL, atol=TOL)
    np.testing.assert_allclose(returns["MSFT"].to_numpy(), FIXTURE_RETURNS["MSFT"], rtol=TOL, atol=TOL)
    np.testing.assert_allclose(returns["CASH"].to_numpy(), FIXTURE_RETURNS["CASH"], rtol=TOL, atol=TOL)


def test_metrics_match_manual_return_and_risk_calculations(deterministic_prices):
    portfolio = {
        "benchmark_symbol": "SPY",
        "positions": [
            {"symbol": "AAPL", "weight": 0.6},
            {"symbol": "MSFT", "weight": 0.4},
        ],
    }
    request = AnalyzeRequest(start_date=START_DATE, end_date=END_DATE, var_confidence=0.95)

    result = metrics(portfolio, request)

    portfolio_returns = expected_portfolio_returns()
    benchmark_returns = expected_benchmark_returns()
    cumulative = np.cumprod(1 + portfolio_returns) - 1
    drawdown = np.cumprod(1 + portfolio_returns) / pd.Series(np.cumprod(1 + portfolio_returns)).cummax().to_numpy() - 1
    years = len(portfolio_returns) / 252
    annualized_return = (1 + cumulative[-1]) ** (1 / years) - 1
    annualized_volatility = pd.Series(portfolio_returns).std() * sqrt(252)
    var_95 = np.quantile(portfolio_returns, 0.05)
    expected_shortfall = portfolio_returns[portfolio_returns <= var_95].mean()
    beta = np.cov(portfolio_returns, benchmark_returns)[0, 1] / np.var(benchmark_returns)
    tracking_error = pd.Series(portfolio_returns - benchmark_returns).std() * sqrt(252)

    assert result["annualized_return"] == pytest.approx(annualized_return, rel=TOL, abs=TOL)
    assert result["annualized_volatility"] == pytest.approx(annualized_volatility, rel=TOL, abs=TOL)
    assert result["sharpe_ratio"] == pytest.approx(annualized_return / annualized_volatility, rel=TOL, abs=TOL)
    assert result["beta_to_benchmark"] == pytest.approx(beta, rel=TOL, abs=TOL)
    assert result["max_drawdown"] == pytest.approx(drawdown.min(), rel=TOL, abs=TOL)
    assert result["var"] == pytest.approx(var_95, rel=TOL, abs=TOL)
    assert result["expected_shortfall"] == pytest.approx(expected_shortfall, rel=TOL, abs=TOL)
    assert result["expected_shortfall"] <= result["var"] < 0
    assert result["tracking_error"] == pytest.approx(tracking_error, rel=TOL, abs=TOL)


def test_concentration_metrics_use_weights_directly(deterministic_prices):
    portfolio = {
        "benchmark_symbol": "SPY",
        "positions": [
            {"symbol": "AAPL", "weight": 0.6},
            {"symbol": "MSFT", "weight": 0.4},
        ],
    }

    concentration = metrics(
        portfolio,
        AnalyzeRequest(start_date=START_DATE, end_date=END_DATE, var_confidence=0.95),
    )["concentration"]

    assert concentration["largest_single_position"] == pytest.approx(0.6)
    assert concentration["top_5_weight"] == pytest.approx(1.0)
    assert concentration["hhi"] == pytest.approx(0.52)
    assert concentration["number_of_holdings"] == 2
    assert concentration["effective_number_of_holdings"] == pytest.approx(1 / 0.52)


def test_correlation_matrix_is_pairwise_asset_return_correlation(deterministic_prices):
    portfolio = {
        "benchmark_symbol": "SPY",
        "positions": [
            {"symbol": "AAPL", "weight": 0.6},
            {"symbol": "MSFT", "weight": 0.4},
        ],
    }

    correlation = metrics(
        portfolio,
        AnalyzeRequest(start_date=START_DATE, end_date=END_DATE, var_confidence=0.95),
    )["correlation_matrix"]

    expected_pairwise = np.corrcoef(FIXTURE_RETURNS["AAPL"], FIXTURE_RETURNS["MSFT"])[0, 1]
    assert correlation["AAPL"]["AAPL"] == 1.0
    assert correlation["MSFT"]["MSFT"] == 1.0
    assert correlation["AAPL"]["MSFT"] == pytest.approx(round(expected_pairwise, 4))
    assert correlation["MSFT"]["AAPL"] == pytest.approx(round(expected_pairwise, 4))


def test_var_confidence_changes_historical_lower_tail_quantile(deterministic_prices):
    portfolio = {
        "benchmark_symbol": "SPY",
        "positions": [
            {"symbol": "AAPL", "weight": 0.6},
            {"symbol": "MSFT", "weight": 0.4},
        ],
    }
    portfolio_returns = expected_portfolio_returns()

    var_95 = metrics(
        portfolio,
        AnalyzeRequest(start_date=START_DATE, end_date=END_DATE, var_confidence=0.95),
    )["var"]
    var_99 = metrics(
        portfolio,
        AnalyzeRequest(start_date=START_DATE, end_date=END_DATE, var_confidence=0.99),
    )["var"]

    assert var_95 == pytest.approx(np.quantile(portfolio_returns, 0.05), rel=TOL, abs=TOL)
    assert var_99 == pytest.approx(np.quantile(portfolio_returns, 0.01), rel=TOL, abs=TOL)
    assert var_99 <= var_95


def test_performance_and_drawdown_series_align_with_return_dates(deterministic_prices):
    portfolio = {
        "benchmark_symbol": "SPY",
        "positions": [
            {"symbol": "AAPL", "weight": 0.6},
            {"symbol": "MSFT", "weight": 0.4},
        ],
    }

    result = metrics(portfolio, AnalyzeRequest(start_date=START_DATE, end_date=END_DATE, var_confidence=0.95))

    portfolio_returns = expected_portfolio_returns()
    benchmark_returns = expected_benchmark_returns()
    expected_portfolio_cumulative = np.cumprod(1 + portfolio_returns) - 1
    expected_benchmark_cumulative = np.cumprod(1 + benchmark_returns) - 1

    assert len(result["performance_series"]) == 6
    assert len(result["drawdown_series"]) == 6
    assert result["performance_series"][0]["date"] == "2024-01-02"
    assert result["performance_series"][-1]["portfolio"] == pytest.approx(expected_portfolio_cumulative[-1])
    assert result["performance_series"][-1]["benchmark"] == pytest.approx(expected_benchmark_cumulative[-1])
    assert result["drawdown_series"][0]["drawdown"] == pytest.approx(0.0)
    assert result["drawdown_series"][-1]["drawdown"] <= 0
