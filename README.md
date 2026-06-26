# Portfolio Risk Engine

A portfolio analytics and stress-testing demo for US equities, ETFs, commodity proxies, and cash. The project answers the practical analyst question:

> What am I exposed to, how much risk am I taking, what could hurt this portfolio, and how has it behaved in different market environments?

The current build is intentionally compact: a FastAPI service, seeded adjusted-close demo data, an in-memory portfolio/report store, and a static browser UI. It is designed to show risk methodology clearly rather than pretend to be a trading or forecasting platform.

## Quick Proof

- Calculates core portfolio metrics: return, volatility, Sharpe, Sortino, beta, drawdown, VaR, expected shortfall, tracking error, information ratio, concentration, exposure, risk contribution, and correlations.
- Includes historical stress windows for COVID, 2022 rates, 2018 Q4, March 2023 regional banking stress, and the 2023 AI-led rally.
- Supports hypothetical shocks for single assets, equity proxies, rates, oil, commodities, and cash sleeves.
- Persists a plain-English risk report generated from computed metrics; see [docs/reports/demo_portfolio_risk_report.md](docs/reports/demo_portfolio_risk_report.md).
- Tests cover API behavior, validation, report persistence, calculation fixtures, and stress output.

## What It Demonstrates

- Portfolio creation with ticker, weight, benchmark, and notional value inputs.
- Weight validation and supported-symbol validation.
- Return, volatility, Sharpe ratio, Sortino ratio, beta, drawdown, VaR, expected shortfall, tracking error, information ratio, concentration, exposure, risk contribution, and correlation metrics.
- Benchmark comparison against `SPY`.
- Historical stress windows for COVID, 2022 rates, 2018 Q4, March 2023 regional banking stress, and the 2023 AI-led rally.
- Hypothetical shock testing for single assets, broad equity proxies, rates, oil, and commodities.
- Plain-English risk commentary generated from computed metrics.

## Demo Portfolio

The default demo portfolio is an "AI Barbell Portfolio":

| Symbol | Weight | Role |
| --- | ---: | --- |
| `NVDA` | 20% | AI/growth equity concentration |
| `MSFT` | 20% | Large-cap technology |
| `JPM` | 15% | Financials exposure |
| `XOM` | 10% | Energy exposure |
| `GLD` | 10% | Gold proxy |
| `TLT` | 10% | Long-duration Treasury proxy |
| `CASH` | 15% | Zero-return cash sleeve in MVP |

This mix is useful in interviews because it contains concentrated growth exposure, cyclicals, a commodity hedge, a rates-sensitive bond proxy, and cash.

## Setup

Install the Python dependencies from the repository root if needed:

```bash
pip install -r requirements.txt
```

Start the API:

```bash
cd projects/portfolio-risk-engine
PYTHONPATH=. uvicorn backend.main:app --reload --port 8004
```

Serve the static UI in another terminal:

```bash
cd projects/portfolio-risk-engine
python3 -m http.server 5176 -d frontend
```

Open:

```text
http://localhost:5176
```

The browser UI expects the API at `http://localhost:8004`. To point it elsewhere, set `localStorage.apiBase` in the browser console.

## API Workflow

Create a portfolio:

```bash
curl -s -X POST http://localhost:8004/portfolios \
  -H "Content-Type: application/json" \
  -d '{
    "name": "AI Barbell Portfolio",
    "portfolio_value": 100000,
    "benchmark_symbol": "SPY",
    "positions": [
      { "symbol": "NVDA", "weight": 0.20 },
      { "symbol": "MSFT", "weight": 0.20 },
      { "symbol": "JPM", "weight": 0.15 },
      { "symbol": "XOM", "weight": 0.10 },
      { "symbol": "GLD", "weight": 0.10 },
      { "symbol": "TLT", "weight": 0.10 },
      { "symbol": "CASH", "weight": 0.15 }
    ]
  }'
```

Analyze the portfolio:

```bash
curl -s -X POST http://localhost:8004/portfolios/{portfolio_id}/analyze \
  -H "Content-Type: application/json" \
  -d '{ "start_date": "2021-01-01", "var_confidence": 0.95 }'
```

List supported symbols:

```bash
curl -s http://localhost:8004/symbols
```

Run a hypothetical QQQ shock:

```bash
curl -s -X POST http://localhost:8004/portfolios/{portfolio_id}/stress \
  -H "Content-Type: application/json" \
  -d '{ "shocks": [{ "target": "QQQ", "shock_pct": -0.15 }] }'
```

Fetch the latest generated report:

```bash
curl -s http://localhost:8004/portfolios/{portfolio_id}/report
```

## Key Assumptions

- The local demo uses seeded adjusted-close price data, not live market data.
- Returns are daily arithmetic returns from adjusted close.
- Annualization uses 252 trading days.
- The MVP Sharpe ratio uses a 0% risk-free rate.
- `CASH` has a 0% daily return.
- VaR and expected shortfall are historical one-day measures over the selected sample and include dollar values when portfolio value is provided.
- Hypothetical stress tests use direct shocks, trailing beta estimates where available, and category sensitivities for related holdings.
- Stress tests are sensitivity estimates, not forecasts.

See [docs/assumptions.md](docs/assumptions.md), [docs/formulas.md](docs/formulas.md), [docs/stress_scenarios.md](docs/stress_scenarios.md), and [docs/reports/demo_portfolio_risk_report.md](docs/reports/demo_portfolio_risk_report.md) for the audit trail and report template.

## Tests

```bash
cd projects/portfolio-risk-engine
PYTHONPATH=. pytest
```

The current test suite covers API behavior, validation, report persistence, calculation fixtures, and stress output. The testing notes in [docs/demo_workflow.md](docs/demo_workflow.md) describe the coverage story to present in a walkthrough.

## Limitations

This is a portfolio-ready demo, not an investment product. It does not trade, recommend securities, forecast future losses, model derivatives, or claim real-time data quality. Current results should be interpreted as a methodology walkthrough using deterministic demo data.
