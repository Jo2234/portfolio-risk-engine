# Demo Workflow

This workflow is designed for a portfolio, recruiter, or interview walkthrough. It emphasizes what the engine calculates, what assumptions it uses, and where the MVP intentionally stops.

## 1. Start The App

Terminal 1:

```bash
cd projects/portfolio-risk-engine
PYTHONPATH=. uvicorn backend.main:app --reload --port 8004
```

Terminal 2:

```bash
cd projects/portfolio-risk-engine
python3 -m http.server 5176 -d frontend
```

Open:

```text
http://localhost:5176
```

## 2. Open With The Analyst Question

Frame the project in one sentence:

```text
This engine explains what a portfolio is exposed to, how much risk it is taking, what could hurt it, and how it behaved across stress regimes.
```

Then call out the deliberate constraint:

```text
The current demo uses seeded adjusted-close data so the analytics workflow is repeatable without market-data credentials.
```

## 3. Analyze The Demo Portfolio

Use the UI button:

```text
Analyze Demo Portfolio
```

Expected outputs to discuss:

- Annualized return.
- Annualized volatility.
- Sharpe ratio with 0% risk-free rate.
- Max drawdown.
- Historical VaR.
- Expected shortfall.
- Sector, asset-class, and factor exposures.
- Risk contribution estimates.
- Plain-English risk summary.

The strongest talking point is not the exact number. It is that every displayed metric has a disclosed formula and assumption.

## 4. Explain The Risk Summary

The summary is deterministic and based on computed metrics. It should explain:

- Whether volatility is elevated.
- Which position is largest.
- Which sector exposure is largest.
- Which holding contributes most to estimated variance.
- What the one-day VaR and expected shortfall imply.
- Which predefined historical scenario was most damaging.
- That the figures come from seeded adjusted-close demo data.

Good interview framing:

```text
I intentionally kept the commentary tied to computed values. If I later add an LLM, I would validate every number against the metrics payload before showing it.
```

## 5. Run A Hypothetical Shock

Use the UI button:

```text
Run QQQ Shock
```

Or call the API:

```bash
curl -s -X POST http://localhost:8004/portfolios/{portfolio_id}/stress \
  -H "Content-Type: application/json" \
  -d '{ "shocks": [{ "target": "QQQ", "shock_pct": -0.15 }] }'
```

Discuss:

- Estimated portfolio return impact.
- Dollar impact on the notional portfolio value.
- Which holdings contributed most.
- Why broad equity proxy mapping is approximate.
- Why trailing beta and category sensitivity assumptions are useful but not a complete factor model.

## 6. Review Historical Scenarios

Historical scenarios are included in the `/analyze` response:

- COVID crash.
- 2022 rates shock.
- 2018 Q4 selloff.
- Regional banking stress.
- AI-led rally.

For each scenario, discuss portfolio return, benchmark return, and worst drawdown. If a scenario has no seeded data, the engine should say so plainly rather than inventing precision.

## 7. Show The API Contract

The three core endpoints are:

```text
GET /symbols
POST /portfolios
POST /portfolios/{portfolio_id}/analyze
POST /portfolios/{portfolio_id}/stress
```

The report endpoint returns the latest generated report:

```text
GET /portfolios/{portfolio_id}/report
```

This makes the project easy to extend into a full frontend, scheduled report generator, or persistent analytics service.

## 8. Testing Story

Run:

```bash
cd projects/portfolio-risk-engine
PYTHONPATH=. pytest
```

Current tests should cover:

- Weight validation.
- Analysis response shape.
- Stress contributors.
- Daily return calculation.
- Portfolio return calculation.
- CAGR annualized return.
- Annualized volatility.
- Sharpe ratio.
- Max drawdown.
- Historical VaR.
- Expected shortfall.
- Beta.
- Correlation matrix.
- Hypothetical stress impact.
- Report persistence and summary generation.

Use fixture data where expected results can be calculated by hand. For floating-point comparisons, use relative tolerance `1e-6` unless a formula requires looser tolerance.

## 9. Strong Close

Close the walkthrough with the limitation and upgrade path:

```text
This is not an investment recommendation engine. It is a transparent risk analytics prototype. The next production steps are live data ingestion, durable storage, stronger missing-data checks, broader formula tests, and exportable reports.
```
