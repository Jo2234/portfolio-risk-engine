# Demo Portfolio Risk Report

This report is a portfolio-ready template for the current MVP. Replace bracketed values with the latest `/analyze` and `/stress` API outputs before presenting.

## 1. Portfolio Snapshot

Portfolio: AI Barbell Portfolio

Benchmark: `SPY`

Portfolio value: `$100,000`

Analysis window: `[start_date]` to `[end_date]`

| Symbol | Weight | Risk Role |
| --- | ---: | --- |
| `NVDA` | 20% | AI/growth concentration |
| `MSFT` | 20% | Large-cap technology |
| `JPM` | 15% | Financials and credit-cycle exposure |
| `XOM` | 10% | Energy and inflation sensitivity |
| `GLD` | 10% | Gold proxy and defensive commodity sleeve |
| `TLT` | 10% | Long-duration rates exposure |
| `CASH` | 15% | Liquidity and volatility dampener |

Weight validation: 100.0%

## 2. Executive Summary

The portfolio is intentionally barbelled between AI-oriented growth exposure and defensive sleeves in cash, gold, and long-duration Treasuries. The main risks to monitor are single-theme concentration in technology, sensitivity to broad equity drawdowns, and the possibility that long-duration bonds fail to hedge during inflationary or rates-led selloffs.

This report uses seeded adjusted-close demo data. The results demonstrate the analytics workflow and should not be read as live market risk estimates.

## 3. Key Metrics

| Metric | Value | Interpretation |
| --- | ---: | --- |
| Annualized return | `[annualized_return]` | CAGR over selected sample |
| Annualized volatility | `[annualized_volatility]` | Annualized daily return dispersion |
| Sharpe ratio | `[sharpe_ratio]` | Uses 0% risk-free rate in MVP |
| Sortino ratio | `[sortino_ratio]` | Uses downside volatility and 0% risk-free rate |
| Beta to benchmark | `[beta_to_benchmark]` | Sensitivity to `SPY` |
| Max drawdown | `[max_drawdown]` | Worst peak-to-trough loss in sample |
| 95% one-day VaR | `[var]` | Historical lower-tail threshold |
| 95% one-day VaR dollars | `[var_dollar]` | Loss amount if portfolio value is provided |
| 95% expected shortfall | `[expected_shortfall]` | Average loss beyond VaR |
| 95% expected shortfall dollars | `[expected_shortfall_dollar]` | Tail-loss amount if portfolio value is provided |
| Tracking error | `[tracking_error]` | Active risk versus `SPY` |
| Information ratio | `[information_ratio]` | Active return per unit of tracking error |

## 4. Concentration

| Measure | Value |
| --- | ---: |
| Largest single position | `[largest_single_position]` |
| Top five weight | `[top_5_weight]` |
| HHI | `[hhi]` |
| Effective number of holdings | `[effective_number_of_holdings]` |
| Number of holdings | `[number_of_holdings]` |

Concentration should be interpreted alongside correlation. A portfolio can appear diversified by holding count while still being dominated by one macro or factor exposure.

## 5. Exposures And Risk Contribution

| Exposure Type | Largest Bucket | Weight |
| --- | --- | ---: |
| Sector | `[largest_sector]` | `[largest_sector_weight]` |
| Asset class | `[largest_asset_class]` | `[largest_asset_class_weight]` |
| Factor | `[largest_factor]` | `[largest_factor_weight]` |

| Symbol | Weight | Risk Contribution |
| --- | ---: | ---: |
| `[symbol]` | `[weight]` | `[risk_contribution_pct]` |

## 6. Stress Scenarios

| Scenario | Portfolio Return | Benchmark Return | Worst Drawdown | Commentary |
| --- | ---: | ---: | ---: | --- |
| COVID crash | `[portfolio_return]` | `[benchmark_return]` | `[worst_drawdown]` | Fast equity liquidity shock |
| 2022 rates shock | `[portfolio_return]` | `[benchmark_return]` | `[worst_drawdown]` | Growth and duration pressure |
| 2018 Q4 selloff | `[portfolio_return]` | `[benchmark_return]` | `[worst_drawdown]` | Broad risk-off period |
| Regional banking stress | `[portfolio_return]` | `[benchmark_return]` | `[worst_drawdown]` | Financial-sector confidence shock |
| AI-led rally | `[portfolio_return]` | `[benchmark_return]` | `[worst_drawdown]` | Growth and AI upside scenario |

## 7. Hypothetical Shock

Scenario: `QQQ -15%`

| Field | Value |
| --- | ---: |
| Estimated portfolio return | `[estimated_portfolio_return]` |
| Estimated dollar impact | `[estimated_dollar_impact]` |
| Largest contributor | `[largest_contributor]` |

Assumptions:

- Direct shocks apply to matching symbols.
- Broad equity shocks use trailing beta estimates where history is available.
- Rates and commodity shocks use transparent category sensitivities.
- Results are sensitivity estimates, not forecasts.

## 8. Main Risks

Primary risks to call out:

- Technology concentration through `NVDA` and `MSFT`.
- Broad equity beta through growth-oriented holdings.
- Rates sensitivity through `TLT`.
- Scenario uncertainty because correlations can rise during stressed markets.
- Data limitation because the MVP uses seeded demo data.

## 9. Assumptions And Limitations

- Adjusted close is used for return calculation.
- Annualization uses 252 trading days.
- Sharpe ratio uses a 0% risk-free rate.
- `CASH` earns 0% in the MVP.
- VaR and expected shortfall are historical one-day measures.
- The app does not recommend trades or forecast precise future losses.
- Portfolios and reports are stored in memory in the current implementation.

## 10. Next Production Steps

- Replace seeded data with vendor-backed historical data ingestion.
- Add durable storage for portfolios, prices, and generated reports.
- Add manually verifiable fixture tests for every calculation.
- Export completed reports to Markdown and PDF.
- Add sector and factor exposure reports.
- Add calibrated factor-based stress testing.
