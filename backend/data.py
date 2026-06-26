from __future__ import annotations

from datetime import date
from typing import Any

import numpy as np
import pandas as pd


SUPPORTED_SYMBOLS = [
    "AAPL",
    "MSFT",
    "NVDA",
    "JPM",
    "XOM",
    "UNH",
    "SPY",
    "QQQ",
    "IWM",
    "TLT",
    "GLD",
    "USO",
    "CPER",
    "CASH",
]

ASSET_METADATA: dict[str, dict[str, str]] = {
    "AAPL": {"sector": "Technology", "asset_class": "Equity", "factor": "Growth"},
    "MSFT": {"sector": "Technology", "asset_class": "Equity", "factor": "Quality Growth"},
    "NVDA": {"sector": "Technology", "asset_class": "Equity", "factor": "High Beta Growth"},
    "JPM": {"sector": "Financials", "asset_class": "Equity", "factor": "Value Cyclical"},
    "XOM": {"sector": "Energy", "asset_class": "Equity", "factor": "Commodity Cyclical"},
    "UNH": {"sector": "Health Care", "asset_class": "Equity", "factor": "Defensive Equity"},
    "SPY": {"sector": "Broad Equity", "asset_class": "ETF", "factor": "US Large Cap"},
    "QQQ": {"sector": "Technology", "asset_class": "ETF", "factor": "Growth"},
    "IWM": {"sector": "Small Cap", "asset_class": "ETF", "factor": "Small Cap"},
    "TLT": {"sector": "Rates", "asset_class": "ETF", "factor": "Duration"},
    "GLD": {"sector": "Commodity", "asset_class": "Commodity Proxy", "factor": "Gold"},
    "USO": {"sector": "Commodity", "asset_class": "Commodity Proxy", "factor": "Oil"},
    "CPER": {"sector": "Commodity", "asset_class": "Commodity Proxy", "factor": "Copper"},
    "CASH": {"sector": "Cash", "asset_class": "Cash", "factor": "Cash"},
}

HISTORICAL_SCENARIOS: dict[str, tuple[str, str]] = {
    "COVID crash": ("2020-02-18", "2020-03-31"),
    "2022 rates shock": ("2022-01-03", "2022-10-31"),
    "2018 Q4 selloff": ("2018-10-01", "2018-12-31"),
    "Regional banking stress": ("2023-03-01", "2023-03-31"),
}

UPSIDE_SCENARIOS: dict[str, tuple[str, str]] = {
    "AI-led rally": ("2023-01-03", "2023-07-31"),
}


def generate_demo_prices(end: date | None = None) -> pd.DataFrame:
    """Generate deterministic adjusted-close data with realistic common factors."""
    end_date = pd.Timestamp(end or date.today()).date()
    dates = pd.bdate_range("2017-01-03", end=end_date)
    rng = np.random.default_rng(1909)

    market = rng.normal(0.00032, 0.0095, len(dates))
    growth = 0.65 * market + rng.normal(0.00018, 0.010, len(dates))
    rates = -0.25 * market + rng.normal(0.00005, 0.0065, len(dates))
    energy = 0.45 * market + rng.normal(0.00008, 0.013, len(dates))
    defensive = 0.35 * market + rng.normal(0.00012, 0.0065, len(dates))
    gold = -0.10 * market + rng.normal(0.00009, 0.007, len(dates))
    small = 1.15 * market + rng.normal(0.00012, 0.010, len(dates))

    factor_returns = {
        "AAPL": 0.70 * growth + 0.45 * market + rng.normal(0.00006, 0.006, len(dates)),
        "MSFT": 0.62 * growth + 0.42 * market + rng.normal(0.00005, 0.005, len(dates)),
        "NVDA": 1.15 * growth + 0.40 * market + rng.normal(0.00012, 0.015, len(dates)),
        "JPM": 0.95 * market + rng.normal(0.00008, 0.008, len(dates)),
        "XOM": 0.40 * market + 0.80 * energy + rng.normal(0.00005, 0.006, len(dates)),
        "UNH": 0.25 * market + 0.90 * defensive + rng.normal(0.00006, 0.004, len(dates)),
        "SPY": market,
        "QQQ": 0.82 * growth + 0.45 * market + rng.normal(0.00005, 0.0045, len(dates)),
        "IWM": small,
        "TLT": rates,
        "GLD": gold,
        "USO": energy + rng.normal(-0.00004, 0.012, len(dates)),
        "CPER": 0.65 * energy + 0.50 * market + rng.normal(0.00003, 0.010, len(dates)),
    }

    shocks = _scenario_shocks(dates)
    rows: list[dict[str, Any]] = []
    for idx, symbol in enumerate(SUPPORTED_SYMBOLS):
        if symbol == "CASH":
            for day in dates:
                rows.append({"symbol": symbol, "date": day.date(), "adjusted_close": 1.0, "source": "cash"})
            continue

        returns = factor_returns[symbol].copy()
        for mask, symbol_shocks in shocks:
            returns[mask] += symbol_shocks.get(symbol, symbol_shocks.get("*", 0.0))

        returns = np.clip(returns, -0.18, 0.16)
        start_price = 75.0 + idx * 6.5
        prices = start_price * np.cumprod(1.0 + returns)
        for day, price in zip(dates, prices):
            rows.append(
                {
                    "symbol": symbol,
                    "date": day.date(),
                    "adjusted_close": float(max(price, 0.1)),
                    "source": "seeded-demo",
                }
            )
    return pd.DataFrame(rows)


def _scenario_shocks(dates: pd.DatetimeIndex) -> list[tuple[np.ndarray, dict[str, float]]]:
    return [
        (
            (dates >= "2018-10-01") & (dates <= "2018-12-31"),
            {"*": -0.0016, "TLT": 0.00025, "GLD": 0.0002, "USO": -0.0025, "NVDA": -0.0022, "QQQ": -0.0020},
        ),
        (
            (dates >= "2020-02-18") & (dates <= "2020-03-31"),
            {"*": -0.0048, "TLT": 0.0011, "GLD": 0.0006, "USO": -0.0090, "CASH": 0.0},
        ),
        (
            (dates >= "2022-01-03") & (dates <= "2022-10-31"),
            {"*": -0.0008, "QQQ": -0.0018, "NVDA": -0.0028, "AAPL": -0.0012, "MSFT": -0.0013, "TLT": -0.0019},
        ),
        (
            (dates >= "2023-03-01") & (dates <= "2023-03-31"),
            {"JPM": -0.0060, "IWM": -0.0025, "SPY": -0.0009, "TLT": 0.0010, "GLD": 0.0010},
        ),
        (
            (dates >= "2023-01-03") & (dates <= "2023-07-31"),
            {"NVDA": 0.0042, "MSFT": 0.0013, "AAPL": 0.0010, "QQQ": 0.0015, "SPY": 0.0007},
        ),
    ]


PRICES = generate_demo_prices()
