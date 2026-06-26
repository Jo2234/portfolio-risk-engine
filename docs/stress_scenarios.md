# Stress Scenarios

Stress tests answer: "What could hurt this portfolio, and through which positions?" They are sensitivity tools, not predictions.

## Historical Scenarios

Historical scenarios replay the portfolio over a named date window using the available price series. Each output should include portfolio return, benchmark return, worst drawdown, key contributors where available, and a short interpretation.

| Scenario | Window | Intended Risk Lens |
| --- | --- | --- |
| COVID crash | 2020-02-18 to 2020-03-31 | Fast cross-asset liquidity shock and equity drawdown |
| 2022 rates shock | 2022-01-03 to 2022-10-31 | Growth equity and long-duration bond pressure |
| 2018 Q4 selloff | 2018-10-01 to 2018-12-31 | Broad equity risk-off period |
| Regional banking stress | 2023-03-01 to 2023-03-31 | Financial-sector and confidence shock |
| AI-led rally | 2023-01-03 to 2023-07-31 | Upside scenario for AI and growth-heavy allocations |

The current seeded local data starts in 2017, so each predefined scenario has local demo coverage. If a future scenario window has no seeded data, the API should return a no-data scenario row instead of inventing a result.

## Hypothetical Scenarios

Hypothetical shocks apply a user-specified percentage move to a target. The current API supports arbitrary target symbols, with special treatment for broad equity proxies.

Examples:

| Scenario | Input | Interpretation |
| --- | --- | --- |
| Nasdaq drawdown | `QQQ -15%` | Tests AI/growth and technology sensitivity |
| S&P 500 selloff | `SPY -10%` | Tests broad equity beta |
| Rates proxy shock | `TLT -8%` | Tests duration exposure |
| Oil shock | `USO +20%` or `USO -20%` | Tests energy and commodity sensitivity |
| Gold shock | `GLD +10%` or `GLD -10%` | Tests defensive commodity sleeve |
| Single-name event | `NVDA -25%` | Tests concentration in a specific holding |

## Current Shock Mechanics

Direct match:

```text
if holding_symbol == shock_target:
    applied_shock = shock_pct
```

Broad equity proxy:

```text
if shock_target in {"SPY", "QQQ", "IWM"}:
    applied_shock = shock_pct * trailing_beta
```

When trailing beta is unavailable, the engine falls back to explainable category assumptions:

- `QQQ` shocks apply higher fallback beta to growth-factor holdings.
- Equity and ETF holdings receive a broad equity fallback beta.
- Commodity-sector holdings receive lower equity fallback beta.

Rates, oil, gold, and copper proxy shocks use category sensitivities for related holdings.

Portfolio impact:

```text
portfolio_impact = sum(weight * applied_shock)
```

Dollar impact:

```text
dollar_impact = portfolio_value * portfolio_impact
```

## Example Interpretation

For the demo portfolio, a `QQQ -15%` shock should primarily affect growth-oriented holdings through trailing beta or growth fallback assumptions. The output is useful because it identifies which holdings drive the estimated portfolio loss, not because it claims the shock map is a full factor model.

## What A Complete Report Should Say

Each stress result should include:

- Estimated portfolio return impact.
- Estimated dollar impact when portfolio value is provided.
- Largest contributors to gain or loss.
- Shock assumptions.
- Whether the shock was directly applied or proxy-applied.
- Why the result is approximate.

## Known Stress-Test Limits

- The current MVP does not model changing correlations during crises.
- It does not model volatility expansion, liquidity gaps, or intraday moves.
- It estimates broad market shock beta from seeded trailing returns where available, but it does not run a full multi-factor regression.
- It does not model options convexity, credit spreads, or yield-curve moves directly.
- It uses simple category sensitivities for rates and commodity proxies.
