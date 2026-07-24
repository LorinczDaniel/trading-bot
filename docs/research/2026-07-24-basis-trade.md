# Test 7: cash-and-carry basis — a real edge, measured, and largely competed away

**Date:** 2026-07-24
**Mechanism:** long spot, short perpetual, same quantity. Delta-neutral, so price moves
cancel exactly and what remains is the funding stream shorts collect from longs. **A cash
flow, not a forecast** — a different mechanism class from the six predictive tests that
failed.

**Data:** real Binance funding history, 5 assets, 6,495–7,528 eight-hourly periods each,
2019-09 → 2026-07. Not simulated, not assumed.

## The result: this one actually works

Constant target leverage, rebalanced on a 10% band, spot taker 0.10% and futures taker
0.05% charged on entry and every rebalance:

| asset | leverage | margin | annualized | Sharpe | max DD |
|---|---|---|---|---|---|
| BTC | 3x | cross | **+8.89%** | 9.96 | −1.2% |
| ETH | 3x | cross | +10.11% | 8.95 | −1.4% |
| XRP | 3x | cross | +10.56% | 7.19 | −2.1% |
| DOGE | 3x | cross | +9.11% | 6.52 | −2.1% |
| SOL | 3x | cross | −1.13% | −0.12 | −30.3% |

**Equal-weight portfolio of all five: +7.14% annualized, Sharpe 3.95, max drawdown −6.6%
over 5.9 years.**

Compare against the only other positive thing found all session — holding BTC: Sharpe
0.79, max drawdown −83.2%. On risk-adjusted terms this is not close.

**This is the low-volatility, positive-Sharpe profile that leverage is actually for**, and
the leverage document predicted exactly that: drag scales with σ², and a delta-neutral
position has almost none.

## Cross-margin is not optional

| asset | 3x isolated | 3x cross |
|---|---|---|
| BTC | −2.05% (**liquidated 2020-10-27**) | +8.89% |
| ETH | −2.78% (**liquidated 2021-01-03**) | +10.11% |
| XRP | −3.42% (**liquidated 2020-11-21**) | +10.56% |
| DOGE | −4.11% (**liquidated 2020-11-24**) | +9.11% |

With isolated margin, a price *rise* liquidates the short while the offsetting spot gain
sits in a different account and cannot rescue it. Every asset died. This confirms the
harvested research's caveat — that legs which are not cross-margined get liquidated — and
locates it precisely: the trade requires a unified/portfolio-margin account, or it is not
merely worse, it is fatal.

## Two bugs found in my own simulation, both flattering

Recorded because either would have produced a better-looking and wrong answer.

1. **The legs were not actually hedged.** The first version matched *notionals* rather
   than *quantities*. The spot leg held fixed units while a fixed-notional perp is
   implicitly rebalanced, so the legs stopped offsetting the instant the price moved and
   the "delta-neutral" position carried real directional exposure. Symptom: drawdowns
   beyond −100%, which is impossible for equity.
2. **Leverage grew without bound.** With fixed units, notional tracks the price while
   capital stays flat, so across BTC's ~10x rise the effective leverage silently became
   ~10x and the yield compounded on exposure no margin system would permit. It reported
   +20.76% annualized and Sharpe 8.43 for BTC. With constant-leverage rebalancing (and its
   fees) the same configuration gives **+8.89%**.

## The binding test: it is decaying, hard

Funding by year, annualized:

| asset | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|
| BTC | 17.19% | 30.61% | 4.16% | 7.87% | 11.92% | 5.13% | **1.76%** |
| ETH | 27.41% | 37.54% | 0.79% | 8.26% | 12.96% | 4.93% | **0.88%** |
| XRP | 24.59% | 48.14% | 0.01% | 8.20% | 14.19% | 3.53% | **−1.73%** |

Trailing windows:

| asset | full history | last 12 months | last 3 months |
|---|---|---|---|
| BTC | 11.67% | 3.43% | **3.35%** |
| ETH | 14.01% | 2.57% | **2.23%** |
| DOGE | 12.54% | 2.98% | **3.44%** |
| XRP | 14.87% | 0.61% | **−0.95%** |
| SOL | 0.10% | −1.49% | **−0.76%** |

And the cause the research predicted is confirmed on our own data. Pre versus post the
January 2024 spot-ETF launch:

| asset | pre | post | change |
|---|---|---|---|
| BTC | 14.45% | 6.92% | **−7.53pp** |
| ETH | 18.29% | 7.05% | **−11.24pp** |
| XRP | 20.22% | 6.40% | **−13.82pp** |

## What that leaves today

At the current BTC rate of ~3.35%, yield on capital at 3x is `3.35% × 0.75 ≈ 2.5%` before
rebalancing fees.

**For roughly 2.5% a year you would be taking:**

- **Exchange counterparty risk.** This is the dominant risk and it is entirely absent from
  the Sharpe. FTX destroyed people running precisely this trade. A Sharpe of 9.96 describes
  a smooth accrual; it says nothing about the venue holding both legs failing.
- **Auto-deleveraging**, where the exchange force-closes profitable shorts in extreme moves.
- **Liquidation on rebalance lag**, since the band is only checked daily here.
- **Funding regime risk** — SOL shows the rate can sit negative for years, and XRP has gone
  negative in the last three months.

**Sharpe is the wrong risk measure for this trade.** Its risks are tail-shaped and
structural, not volatility-shaped, so the headline number systematically understates them.
That is the single most important sentence in this document.

## Conclusion

The mechanism is real and was genuinely good: ~7–10% annualized, market-neutral, Sharpe
around 4 at portfolio level, max drawdown under 7%, on real funding data over nearly six
years. It is the first thing this project has found that beats holding on risk-adjusted
terms, and it is the first result that survived its own controls rather than dying to them.

**It has also been arbitraged down to roughly a quarter of its historical rate**, and the
decay is causal and identified rather than mysterious — spot ETFs gave institutions a
cheaper way to hold long exposure, so fewer of them pay up on perps.

The honest position: this was a real edge that we can measure and would have been worth
trading in 2021–2024. At today's rate the return no longer obviously compensates the
counterparty risk, and the relevant comparison is not BTC — it is the risk-free rate.
**If short-term government paper yields more than ~2.5%, this trade currently has negative
excess return.** That comparison should be made against live yields before any capital
moves.

## If it were to be pursued

The bot cannot do this today: spot-only `LiveBroker`, no futures API, no margin management,
no ADL handling, and `reconcile.py` assumes an unlevered single-leg book. The build is a
two-legged position manager with rebalancing — real work, and worth it only if the funding
rate recovers or a venue with a persistently higher rate is found.

The cheap next measurement, if this stays interesting: the same funding history from other
venues (Bybit, OKX, Hyperliquid). Rates differ across venues, and the research noted
cross-venue *spreads* were where the remaining dispersion lived.
