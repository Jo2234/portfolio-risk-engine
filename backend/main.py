from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .analytics import analyze_portfolio, enrich_positions, returns_for as _returns_for, validate_positions
from .data import PRICES, SUPPORTED_SYMBOLS
from .reports import build_report_payload
from .schemas import AnalyzeRequest, PortfolioCreate, StressRequest
from .stress import run_historical_stress, run_hypothetical_stress


app = FastAPI(title="Portfolio Risk Engine", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

PORTFOLIOS: dict[str, dict[str, Any]] = {}
REPORTS: dict[str, dict[str, Any]] = {}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/symbols")
def symbols() -> dict[str, Any]:
    return {"symbols": SUPPORTED_SYMBOLS}


@app.post("/portfolios", status_code=201)
def create_portfolio(payload: PortfolioCreate) -> dict[str, Any]:
    benchmark_symbol = payload.benchmark_symbol.upper()
    raw_positions = [_model_dump(position) for position in payload.positions]
    try:
        validation = validate_positions(raw_positions, benchmark_symbol)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    now = datetime.now(timezone.utc).isoformat()
    portfolio_id = str(uuid4())
    portfolio = {
        "id": portfolio_id,
        "name": payload.name,
        "base_currency": payload.base_currency.upper(),
        "portfolio_value": payload.portfolio_value,
        "benchmark_symbol": benchmark_symbol,
        "positions": enrich_positions(raw_positions),
        "created_at": now,
        "updated_at": now,
    }
    PORTFOLIOS[portfolio_id] = portfolio
    return {"portfolio_id": portfolio_id, "validation": validation, **portfolio}


@app.post("/portfolios/{portfolio_id}/analyze")
def analyze(portfolio_id: str, req: AnalyzeRequest) -> dict[str, Any]:
    portfolio = _portfolio_or_404(portfolio_id)
    try:
        analysis = analyze_portfolio(
            portfolio=portfolio,
            start_date=req.start_date,
            end_date=req.end_date,
            selected_confidence=req.var_confidence,
            prices=PRICES,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    report = build_report_payload(portfolio, analysis)
    REPORTS[portfolio_id] = report
    return report


@app.post("/portfolios/{portfolio_id}/stress")
def stress(portfolio_id: str, req: StressRequest) -> dict[str, Any]:
    portfolio = _portfolio_or_404(portfolio_id)
    try:
        if req.scenario_type == "historical":
            return run_historical_stress(portfolio, PRICES)
        shocks = [_model_dump(shock) for shock in req.shocks]
        return run_hypothetical_stress(portfolio, shocks, PRICES)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/portfolios/{portfolio_id}/report")
def report(portfolio_id: str) -> dict[str, Any]:
    _portfolio_or_404(portfolio_id)
    if portfolio_id not in REPORTS:
        raise HTTPException(status_code=404, detail="No report available; run analyze first")
    return REPORTS[portfolio_id]


def _portfolio_or_404(portfolio_id: str) -> dict[str, Any]:
    if portfolio_id not in PORTFOLIOS:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return PORTFOLIOS[portfolio_id]


def _model_dump(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def returns_for(symbols: list[str], start: Any, end: Any):
    """Compatibility helper for calculation tests and notebooks."""
    returns, _ = _returns_for(
        symbols=symbols,
        start_date=_as_date(start),
        end_date=_as_date(end),
        prices=PRICES,
    )
    return returns


def metrics(portfolio: dict[str, Any], req: AnalyzeRequest) -> dict[str, Any]:
    """Compatibility helper returning the legacy flat metrics payload."""
    analysis = analyze_portfolio(
        portfolio=portfolio,
        start_date=_as_date(req.start_date),
        end_date=_as_date(req.end_date),
        selected_confidence=req.var_confidence,
        prices=PRICES,
    )
    return {
        **analysis["metrics"],
        "performance_series": analysis["performance_series"],
        "drawdown_series": analysis["drawdown_series"],
    }


def _as_date(value: Any):
    if hasattr(value, "date") and not isinstance(value, str):
        return value.date()
    if hasattr(value, "year") and hasattr(value, "month") and hasattr(value, "day") and not isinstance(value, str):
        return value
    from pandas import Timestamp

    return Timestamp(value).date()
