# Risk + Regime Snapshot: One Portfolio, Three Stress Cases

This is a compact proof artifact for quant, risk, fintech, and hedge-fund-adjacent applications. It uses the local FastAPI app and seeded adjusted-close demo data, so the output is reproducible for code review but should not be treated as live investment analysis.

## Portfolio

Portfolio: `AI Barbell Portfolio`

Benchmark: `SPY`

Portfolio value: `$100,000`

Analysis start date: `2021-01-01`

| Symbol | Weight | Role |
|---|---:|---|
| `NVDA` | 20% | AI/growth concentration |
| `MSFT` | 20% | Large-cap technology |
| `JPM` | 15% | Financials exposure |
| `XOM` | 10% | Energy exposure |
| `GLD` | 10% | Gold proxy |
| `TLT` | 10% | Long-duration Treasury proxy |
| `CASH` | 15% | Liquidity sleeve |

Weight validation: `100.0%`

## Key Risk Metrics

| Metric | Value |
|---|---:|
| Annualized return | -6.57% |
| Annualized volatility | 12.04% |
| Sharpe ratio | -0.55 |
| Sortino ratio | -0.93 |
| Beta to `SPY` | 0.57 |
| Max drawdown | -45.73% |
| 95% one-day VaR | -1.28% |
| 95% one-day VaR dollars | `$1,277.92` |
| 95% expected shortfall | -1.54% |
| 95% expected shortfall dollars | `$1,544.32` |
| Tracking error | 10.53% |
| Information ratio | -0.39 |

## Concentration And Exposure

| Measure | Value |
|---|---:|
| Largest position | `NVDA`, 20% |
| Top five weight | 80% |
| HHI | 0.155 |
| Effective number of holdings | 6.45 |
| Number of holdings | 7 |

Largest exposures:

- Sector: Technology, 40%
- Asset class: Equity, 65%
- Factor: High Beta Growth, 20%; Quality Growth, 20%

## Historical Stress Cases

| Scenario | Portfolio return | Benchmark return | Worst drawdown | Main note |
|---|---:|---:|---:|---|
| COVID crash | -1.49% | -8.04% | -3.87% | Outperformed benchmark; JPM was weakest weighted holding. |
| 2022 rates shock | -27.40% | -12.39% | -29.92% | Underperformed benchmark; NVDA and TLT drove losses. |
| 2018 Q4 selloff | 3.47% | -5.28% | -3.43% | Outperformed benchmark; XOM was weakest weighted holding. |
| Regional banking stress | 4.21% | 3.71% | -2.00% | Slightly outperformed benchmark; JPM was weakest weighted holding. |

## Three Hypothetical Shocks

| Shock | Estimated portfolio return | Estimated dollar impact | Largest contributor |
|---|---:|---:|---|
| `QQQ -15%` | -10.39% | `-$10,387.50` | `NVDA` and `MSFT`, each -3.30% portfolio impact |
| `TLT -8%` | 0.24% | `$240.00` | Direct `TLT` loss partly offset by category sensitivity assumptions |
| `NVDA -25%` | -5.00% | `-$5,000.00` | Direct `NVDA` shock |

## Assumptions And Limits

- Uses deterministic seeded adjusted-close demo data, not live market data.
- VaR and expected shortfall are one-day historical estimates.
- Broad equity shocks use beta or simple category proxy assumptions.
- Commodity and rates proxy shocks use category sensitivities.
- Stress output is a sensitivity estimate, not a forecast or trading recommendation.

## Why This Is Useful In An Internship

This is the kind of tooling a junior quant, risk, fintech, or investment-ops intern can build and maintain: repeatable inputs, explicit assumptions, validation, stress cases, and a report that makes model output understandable to non-engineers.
