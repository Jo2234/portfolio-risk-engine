# Assumptions

This document is the audit trail for how the portfolio risk engine currently interprets data, weights, risk, and stress results.

## Data

- The local demo uses seeded adjusted-close price data generated inside the application.
- Seeded data exists so the project can run without API keys, market-data subscriptions, or internet access.
- Adjusted close is treated as the price input because it better approximates total-return behavior than raw close when splits and distributions matter.
- The seeded series intentionally embeds recognizable market regimes, including the 2018 Q4 selloff, 2020 COVID crash, 2022 rates shock, March 2023 regional banking stress, and a 2023 AI-led rally window.
- Results should not be compared to live market data tick-for-tick. They demonstrate methodology, workflow, and API structure.

## Asset Universe

Supported symbols in the MVP:

- Equities: `AAPL`, `MSFT`, `NVDA`, `JPM`, `XOM`, `UNH`
- Equity ETFs: `SPY`, `QQQ`, `IWM`
- Rates proxy: `TLT`
- Commodity proxies: `GLD`, `USO`, `CPER`
- Cash: `CASH`

The MVP assumes all positions are long-only. Weights must be non-negative and must sum to 1.0 within a tolerance of `1e-6`.

## Cash

- `CASH` is represented as a stable price series with 0% daily return.
- The MVP does not apply interest income or a Treasury bill curve.
- A production version should support a configurable cash return or a 3-month Treasury bill proxy.

## Portfolio Value

- Portfolio value is optional for percentage-only analysis.
- When provided, it is used to express VaR, expected shortfall, and stress impacts in dollar terms.
- The current API returns percentage and dollar versions for hypothetical stress, VaR, and expected shortfall when portfolio value is provided.

## Return Window

- User-selected `start_date` and `end_date` define the analysis period.
- Daily returns are aligned by trading date after pivoting price history by symbol.
- Missing adjusted-close observations are surfaced as warnings, and remaining missing return values are filled with 0 for local demo stability.
- Windows with fewer than 30 trading days are flagged because risk estimates become unstable.

## Benchmark

- `SPY` is the default benchmark.
- Beta, tracking error, benchmark-relative performance, and historical scenario comparisons are calculated against the selected benchmark symbol.
- Benchmark quality matters: using `SPY` for a commodity-heavy or rates-heavy portfolio can explain broad equity sensitivity but not all relevant risk.

## Risk-Free Rate

- The MVP uses a 0% risk-free rate for Sharpe ratio.
- This must be disclosed anywhere Sharpe ratio is shown.
- A production version should allow a Treasury bill rate or a user-specified risk-free rate.

## Stress Testing

- Historical scenarios replay seeded returns over named windows and report best/worst holdings plus weighted contributors.
- Hypothetical scenarios apply direct shocks to matching assets.
- Broad `SPY`, `QQQ`, and `IWM` shocks use trailing beta estimates when return history is available, with fallback beta assumptions for related equity-like holdings.
- Rates, oil, gold, and copper shocks use category sensitivities for related holdings.
- Stress results are approximations, not forecasts or capital-at-risk guarantees.

## Risk Commentary

- The plain-English summary is deterministic and generated from computed metrics.
- It should not introduce numbers that are not present in the metrics payload.
- It includes volatility versus benchmark, largest position, largest sector exposure, largest risk contributor, 95% VaR, expected shortfall, max drawdown, and the most damaging predefined scenario.
- If an LLM-generated summary is added later, all numeric claims should be validated against computed values before display.
