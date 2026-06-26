from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class Position(BaseModel):
    symbol: str
    weight: float = Field(ge=0, le=1)


class PortfolioCreate(BaseModel):
    name: str
    portfolio_value: float | None = Field(default=100000, gt=0)
    benchmark_symbol: str = "SPY"
    base_currency: str = "USD"
    positions: list[Position]


class AnalyzeRequest(BaseModel):
    start_date: date = date(2021, 1, 1)
    end_date: date = Field(default_factory=date.today)
    var_confidence: float = Field(default=0.95, ge=0.8, le=0.999)


class Shock(BaseModel):
    target: str
    shock_pct: float


class StressRequest(BaseModel):
    scenario_type: Literal["hypothetical", "historical"] = "hypothetical"
    shocks: list[Shock] = Field(default_factory=list)
    start_date: date | None = None
    end_date: date | None = None

