# Reporting Guide

The risk report should be clear enough for a portfolio analyst and transparent enough for an interviewer to audit.

Use [reports/demo_portfolio_risk_report.md](reports/demo_portfolio_risk_report.md) as the MVP report template.

## Report Structure

Recommended sections:

1. Portfolio snapshot.
2. Performance and benchmark comparison.
3. Risk metrics.
4. Concentration and exposure.
5. Correlation.
6. Historical stress scenarios.
7. Hypothetical shock results.
8. Plain-English risk commentary.
9. Assumptions and limitations.

## Portfolio Snapshot

Include:

- Portfolio name.
- Analysis date range.
- Benchmark.
- Portfolio value, if provided.
- Holdings and weights.
- Weight validation result.

Example:

```text
The AI Barbell Portfolio is a seven-position, long-only portfolio benchmarked to SPY. Weights sum to 100.0%, with the largest position in NVDA at 20.0%.
```

## Risk Metrics

Show both values and interpretation:

| Metric | Include | Interpretation |
| --- | --- | --- |
| Annualized return | Percent | CAGR over selected sample |
| Annualized volatility | Percent | Annualized standard deviation of daily returns |
| Sharpe ratio | Number | Return per unit of volatility, using disclosed risk-free rate |
| Sortino ratio | Number | Return per unit of downside volatility |
| Beta | Number | Sensitivity to benchmark daily returns |
| Max drawdown | Percent | Worst peak-to-trough decline |
| VaR | Percent and dollars when available | Historical one-day lower-tail threshold |
| Expected shortfall | Percent and dollars when available | Average loss beyond VaR threshold |
| Tracking error | Percent | Active risk versus benchmark |
| Information ratio | Number | Active return per unit of active risk |

## Concentration

Include:

- Sector exposure.
- Asset-class exposure.
- Factor exposure.
- Largest single position.
- Top five weight.
- HHI.
- Effective number of holdings.
- Number of holdings.

Suggested language:

```text
Concentration risk is mainly driven by the top technology positions. HHI and effective holdings translate that concentration into a single audit-friendly measure.
```

## Stress Results

For each stress scenario, include:

- Scenario name.
- Portfolio return or estimated impact.
- Benchmark return where available.
- Worst drawdown where available.
- Largest contributors.
- Assumptions used.
- Limitations.

Avoid vague language such as "safe" or "protected." Prefer direct, qualified language:

```text
In this seeded scenario, the portfolio lost less than the benchmark because cash and GLD reduced equity exposure. This does not guarantee similar behavior in future selloffs.
```

## Plain-English Commentary Rules

The commentary should:

- Be generated from computed metrics.
- Name the largest risk drivers.
- Mention benchmark-relative volatility.
- Mention largest sector exposure and largest estimated risk contributor.
- Explain VaR and expected shortfall without overstating precision.
- Include the most damaging historical stress result when available.
- Disclose key assumptions.

The commentary should not:

- Recommend buying or selling securities.
- Claim future loss prediction.
- Introduce numbers not present in the metrics payload.
- Hide limitations behind generic AI prose.

## Export Readiness Checklist

Before exporting a report to Markdown or PDF:

- Confirm weights sum to 100%.
- Confirm benchmark data exists for the selected date range.
- Confirm every number in the summary appears in the metrics or scenario payload.
- Label whether data is seeded demo data or vendor-sourced market data.
- Include risk-free rate assumption.
- Include VaR confidence level.
- Include analysis start and end dates.
- Include scenario assumptions.
- Include a non-advice disclaimer.
