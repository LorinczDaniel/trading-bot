# Test 10: equity rotation and the 200-day trend filter

**Date:** 2026-07-24
**Universe:** 31 ETFs — 11 SPDR sectors (from 1998), 15 asset classes, 5 factor funds.

**Why ETFs:** the survivorship blocker on stock selection is that delisted tickers are
unretrievable. Sector and asset-class ETFs sidestep it entirely — the SPDR sector funds
have traded since 1998, membership is fixed and public, and none have died. So
cross-sectional rotation is **honestly testable here**, unlike stock picking.

## 1. Sector rotation — dead

Momentum(126d) top-3, rebalanced monthly, against holding the 11 sectors equal-weight and
against random selection, judged on Sharpe:

| window | hold universe | momentum | beats random |
|---|---|---|---|
| 1999 → | 0.34 | 0.29 | 10/20 |
| 2013 → | 0.78 | 0.69 | 8/20 |
| half 2 | 0.79 | 0.65 | 9/20 |

Coin flips against random in every window, and below equal-weight hold in every window.
No edge.

## 2. Multi-asset rotation — worked, then stopped

| window | hold | momentum | beats random |
|---|---|---|---|
| 2007 → | 0.60 | **0.68** | **20/20** |
| 2016 → | 0.79 | 0.56 | 8/20 |

Beating 20 of 20 random seeds over 2007→ is a genuine signal. It does not survive into the
recent half — the same non-replication that killed crypto cross-sectional momentum.

## 3. The 200-day trend filter on SPY

This looked like the real thing: Sharpe improved in all three windows tested and drawdown
roughly halved. It is also the most data-mined rule in finance, so it got the full
treatment. Signal shifted one bar throughout, so it never acts on the price it trades at.

### It is entirely crash avoidance

The decisive test. Sharpe, buy-and-hold versus trend, in periods that **exclude** the
dot-com and GFC crashes:

| period | buy & hold | trend 200d | verdict |
|---|---|---|---|
| 1993–2000 | **1.32** | 1.12 | worse |
| 2003–2007 | **1.07** | 0.42 | much worse |
| 2009–2020 | **1.06** | 0.69 | worse |
| 2020–2026 | **1.17** | 0.91 | worse |

**In every single period that excludes a crash, buy-and-hold wins.** The full-history
Sharpe improvement (0.64 → 0.71) comes wholly from being out of the market during 2000–02
and 2008–09. There is no edge here; there is crash insurance with a premium.

### It does not generalise

200-day filter on each asset's full history, Sharpe gain versus buy-and-hold:

| positive | negative |
|---|---|
| EFA +0.11, DBC +0.11, SPY +0.06 | TLT −0.29, EEM −0.17, VNQ −0.17, MDY −0.13, IWM −0.10, GLD −0.06, QQQ −0.00 |

**Seven of ten negative.** SPY's +0.06 is the third-best result out of ten, which is what
selecting the famous case looks like.

### Parameters are knife-edge post-2010

From 2010, buy-and-hold Sharpe 0.85. Trend at 50d 0.61, 100d 0.82, 150d 0.81, **200d 0.88**,
250d 0.74, 300d 0.80. **Only the famous parameter beats holding, by 0.03.** Five of six fail.

### Costs bite fast

| cost per switch | Sharpe |
|---|---|
| 0.00% | 0.73 |
| 0.05% | 0.71 |
| 0.10% | 0.68 |
| 0.20% | 0.62 |
| 0.50% | 0.46 |

Buy-and-hold is 0.64. **Above roughly 0.15% per switch the filter is worse than doing
nothing** — before any tax consideration, and 215 switches in a taxable account is its own
problem.

### And it hurts in normal years

Underperformed buy-and-hold by more than 10% in 2007 (−10.1%), 2010 (−14.1%), 2011 (−11.3%)
and 2019 (−11.3%). Four separate years of double-digit underperformance is what holding
this actually feels like between crashes.

## The one thing that IS robust

Drawdown reduction, and it holds across every asset tested:

| | buy & hold | trend 200d |
|---|---|---|
| SPY | −55.2% | **−29.4%** |
| QQQ | −83.0% | **−58.9%** |
| IWM | −58.6% | **−28.9%** |
| EFA | −61.0% | **−28.8%** |
| VNQ | −73.1% | −52.6% |

Roughly halved, everywhere, with no exception.

**So the honest description is: not a strategy, a risk-management tool.** It costs return
(SPY 10.76% → 8.03%) and buys a much shallower worst case. Whether that trade is worth
taking is not a backtest question — it is the same question the returns document reached:

> the binding constraint is position size — small enough that a large drawdown is tolerable
> rather than forced-selling. That is a personal question about capital and temperament.

If someone would panic-sell at −55% but hold through −29%, the filter converts a strategy
they cannot execute into one they can, and the return it costs is the price of that. If
they would hold either way, it is a pure cost.

## Conclusion

Ten tests. No validated alpha in equities either — but the *reason* differs from crypto,
and that matters. In crypto the aggregate itself was a wealth destroyer (91.7% of coins
negative). In equities the aggregate is genuinely good: SPY at 15.04%/yr and Sharpe 0.84
over the same window BTC managed 0.79 with two and a half times the drawdown.

**The equity finding is not "nothing works." It is that the index is hard to beat, which
is a materially better place to end up.**
