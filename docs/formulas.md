# Formula Notes

This document states the formulas used or expected by the MVP. Unless noted otherwise, returns are daily arithmetic returns and annualization uses 252 trading days.

## Asset Returns

Daily return for asset `i`:

```text
r_i,t = P_i,t / P_i,t-1 - 1
```

Where:

- `P_i,t` is the adjusted close for asset `i` on date `t`.
- `CASH` uses a flat price series, so its daily return is 0%.

## Portfolio Return

Daily portfolio return:

```text
r_p,t = sum(w_i * r_i,t)
```

Where:

- `w_i` is the portfolio weight for asset `i`.
- Weights are long-only in the MVP and must sum to 1.0.

## Cumulative Return

```text
C_t = product(1 + r_p,t) - 1
```

This is used for the performance series and drawdown base.

## Annualized Return

The current implementation uses CAGR over the selected sample:

```text
years = number_of_daily_returns / 252
annualized_return = (1 + cumulative_return_final) ^ (1 / years) - 1
```

This is sample-period dependent. Short windows can produce unstable annualized figures.

## Annualized Volatility

```text
annualized_volatility = std(r_p) * sqrt(252)
```

The MVP uses the daily sample standard deviation from pandas.

## Sharpe Ratio

```text
sharpe = annualized_return / annualized_volatility
```

MVP assumption:

```text
risk_free_rate = 0%
```

Production-ready version:

```text
sharpe = (annualized_return - risk_free_rate) / annualized_volatility
```

## Sortino Ratio

The MVP reports Sortino ratio with the same 0% risk-free-rate assumption:

```text
sortino = annualized_return / annualized_downside_volatility
```

Where downside volatility is the annualized standard deviation of negative daily portfolio returns.

## Beta To Benchmark

```text
beta = covariance(r_p, r_b) / variance(r_b)
```

Where:

- `r_p` is portfolio daily return.
- `r_b` is benchmark daily return.

Interpretation:

- `beta > 1`: historically more sensitive than the benchmark.
- `beta = 1`: similar benchmark sensitivity.
- `beta < 1`: lower benchmark sensitivity.
- Negative beta is possible if returns move opposite the benchmark in the sample.

## Drawdown

Wealth index:

```text
W_t = product(1 + r_p,t)
```

Drawdown:

```text
drawdown_t = W_t / max(W_0 ... W_t) - 1
```

Max drawdown:

```text
max_drawdown = min(drawdown_t)
```

Max drawdown is path-dependent. It measures the largest peak-to-trough loss within the selected period.

## Historical Value At Risk

For confidence level `c`:

```text
historical_var_c = quantile(r_p, 1 - c)
```

Examples:

- 95% one-day VaR uses the 5th percentile of daily returns.
- 99% one-day VaR uses the 1st percentile of daily returns.

The API returns VaR as a signed return. A value of `-0.021` means the 5th-percentile daily return was `-2.1%`.

Dollar version, when portfolio value is available:

```text
var_dollars = portfolio_value * historical_var_c
```

For user-facing loss language, display the absolute loss while preserving the signed calculation internally.

## Expected Shortfall

Expected shortfall, also called conditional VaR:

```text
expected_shortfall_c = average(r_p,t where r_p,t <= historical_var_c)
```

Interpretation:

- VaR estimates the loss threshold.
- Expected shortfall estimates the average loss after that threshold is breached.

The API returns expected shortfall as a signed return.

## Tracking Error

```text
tracking_error = std(r_p - r_b) * sqrt(252)
```

Tracking error measures active risk versus the benchmark.

## Information Ratio

```text
information_ratio = annualized_active_return / tracking_error
```

Where:

```text
annualized_active_return = annualized_return_p - annualized_return_b
```

## Concentration

Largest single position:

```text
max(w_i)
```

Top five weight:

```text
sum(five largest weights)
```

Herfindahl-Hirschman Index:

```text
HHI = sum(w_i ^ 2)
```

Effective number of holdings:

```text
effective_holdings = 1 / HHI
```

Interpretation:

- Higher HHI means more concentration.
- Effective holdings converts concentration into a more intuitive holding-count equivalent.

## Correlation

The correlation matrix is the pairwise Pearson correlation of daily asset returns:

```text
corr(i, j) = covariance(r_i, r_j) / (std(r_i) * std(r_j))
```

Correlation is sample-period dependent and can change sharply during stress periods.

## Exposure

The MVP sums position weights by metadata bucket:

```text
sector_exposure_s = sum(w_i where sector_i = s)
asset_class_exposure_a = sum(w_i where asset_class_i = a)
factor_exposure_f = sum(w_i where factor_i = f)
```

These are classification exposures, not regression-estimated factor loadings.

## Risk Contribution

The MVP estimates variance contribution using the annualized covariance matrix:

```text
portfolio_variance = w' * covariance_matrix * w
marginal_contribution = covariance_matrix * w
risk_contribution_i = w_i * marginal_contribution_i / portfolio_variance
```

This is a variance contribution estimate. It is useful for ranking risk drivers but depends on the selected sample covariance.

## Historical Scenario Return

For a scenario window from `a` to `b`:

```text
scenario_return = product(1 + r_p,t for t in [a, b]) - 1
```

Scenario drawdown uses the same drawdown formula, limited to the scenario window.

## Hypothetical Shock Impact

Direct asset shock:

```text
impact_i = w_i * shock_i
```

Portfolio shock impact:

```text
portfolio_impact = sum(impact_i)
```

Current broad equity proxy rule:

```text
applied_shock = shock * beta(symbol, target)
```

Where beta is estimated from trailing returns when available and clipped to the range `[-0.75, 2.5]`.

Fallback broad equity rules:

```text
if target == QQQ and factor contains Growth:
    fallback_beta = 1.10
elif asset_class in {Equity, ETF}:
    fallback_beta = 0.75
elif sector == Commodity:
    fallback_beta = 0.25
else:
    fallback_beta = 0.0
```

Rates, oil, gold, and copper shocks use simple category sensitivities. These are transparent scenario assumptions, not calibrated pricing models.
