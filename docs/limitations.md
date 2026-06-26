# Limitations

This project is a risk analytics demo. It should be presented as a transparent methodology prototype, not as an investment product.

## Data Limits

- The local application uses seeded demo data, not a live market-data vendor.
- Seeded returns are useful for repeatable demos and tests, but they do not reproduce exact historical prices.
- The current app does not persist imported market data.
- The current app does not reconcile dividends, splits, vendor corrections, symbol changes, or delistings beyond the adjusted-close assumption.

## Analytics Limits

- Historical VaR and expected shortfall depend entirely on the selected lookback window.
- VaR is not a worst-case loss estimate.
- Expected shortfall is more tail-aware than VaR, but it is still backward-looking.
- Beta and correlation are sample estimates and can change materially in stressed markets.
- Sharpe ratio uses a 0% risk-free rate in the MVP.
- Cash earns 0% in the MVP.
- The current implementation does not model transaction costs, taxes, liquidity, slippage, borrowing costs, or management fees.

## Stress-Test Limits

- Historical scenarios use seeded data and are scenario approximations.
- Hypothetical scenarios use direct shocks, trailing beta estimates, and category sensitivities, not a calibrated multi-factor risk model.
- Broad equity proxy shocks depend on trailing seeded returns when available, so the estimated beta is sample-dependent.
- Scenario results should be read as directional sensitivity estimates.

## Product Limits

- Portfolios and reports are stored in memory in the current build.
- Restarting the API clears created portfolios and generated reports.
- The static UI demonstrates the workflow but does not expose every API field.
- The API exposes richer analytics than the current static UI, including exposure, correlation, risk contribution, and full report payload fields.
- There is no authentication, authorization, audit log, or production data store.
- The app does not place trades or recommend securities.

## Production Upgrade Path

Before calling this production-grade, the project should add:

- Durable storage with portfolio, price, and report tables.
- Vendor-backed historical price ingestion with quality checks.
- Missing-data warnings and insufficient-history warnings.
- More complete tests for each formula using manually verifiable fixtures.
- Dollar VaR and expected shortfall in API responses.
- Factor exposure model and regression-based stress mapping.
- Sector and asset-class exposure reports.
- Report export to Markdown and PDF.
- Snapshot tests for generated reports.
- Authentication if used with non-public portfolios.
