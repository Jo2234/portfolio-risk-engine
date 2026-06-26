from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


FIXTURE_DATES = pd.bdate_range("2024-01-01", periods=7)
FIXTURE_RETURNS = {
    "AAPL": [0.10, -0.05, 0.02, -0.08, 0.04, -0.01],
    "MSFT": [0.00, 0.02, -0.01, 0.03, -0.02, 0.01],
    "SPY": [0.05, -0.02, 0.01, -0.04, 0.02, 0.00],
    "CASH": [0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
}


def prices_from_returns(symbol: str, returns: list[float], start_price: float = 100.0) -> list[dict[str, object]]:
    prices = [start_price]
    for daily_return in returns:
        prices.append(prices[-1] * (1 + daily_return))
    return [
        {
            "symbol": symbol,
            "date": date.date(),
            "adjusted_close": price,
            "source": "pytest-fixture",
        }
        for date, price in zip(FIXTURE_DATES, prices)
    ]


@pytest.fixture(autouse=True)
def clear_app_state():
    from backend import main

    main.PORTFOLIOS.clear()
    main.REPORTS.clear()
    yield
    main.PORTFOLIOS.clear()
    main.REPORTS.clear()


@pytest.fixture
def client() -> TestClient:
    from backend.main import app

    return TestClient(app)


@pytest.fixture
def deterministic_prices(monkeypatch):
    from backend import main

    rows = []
    for symbol, returns in FIXTURE_RETURNS.items():
        rows.extend(prices_from_returns(symbol, returns))
    prices = pd.DataFrame(rows)
    monkeypatch.setattr(main, "PRICES", prices)
    return prices


@pytest.fixture
def two_asset_portfolio_payload() -> dict[str, object]:
    return {
        "name": "Two Asset Fixture Portfolio",
        "portfolio_value": 100000,
        "benchmark_symbol": "SPY",
        "positions": [
            {"symbol": "AAPL", "weight": 0.6},
            {"symbol": "MSFT", "weight": 0.4},
        ],
    }
