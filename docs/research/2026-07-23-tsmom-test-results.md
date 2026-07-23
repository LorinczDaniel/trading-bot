# Test 1: long-only time-series momentum on BTC — results

**Date:** 2026-07-23
**Claim under test:** buying the market only when the trailing 28-day return sits in the top third of its own history, holding 5 days, produced an annualized Sharpe of **1.51 vs 0.85** for the market, net of 15 bps per trade, while invested only **48%** of the time — the outperformance coming from avoiding drawdowns rather than from higher returns.

Source paper's own disclaimer: the (28, 5) pair was chosen by scanning all combinations from 1–56 days on the **same full sample** used to report performance, with no holdout. The authors call it a "best-case scenario" with data-snooping bias. Adjudicating that is exactly what this harness is for.

## Setup

- `strategies/timeseries_momentum.py` — `TimeSeriesMomentum(window, hold, quantile=2/3, history=365)`
- Data: BTC/USDT daily, **3,263 bars, 2017-08-17 → 2026-07-23** (Binance inception to now)
- Traded window after warmup: 2,863 bars, 2018-09-21 → 2026-07-23 — includes the 2018 bear, the 2021 bull, the 2022 crash, and the 2023–26 recovery
- Fee 0.1% (Binance taker, worse than the paper's 15 bps), risk sizing on, kill-switch disabled for measurement
- Percentile taken over a **rolling** 365-bar window, not expanding, so the rule uses only information available at the time

Market baseline over the same bars: return **+860.9%**, Sharpe **0.78**, max drawdown **−76.6%**.

## Result 1 — the Sharpe claim partially replicates

| window | hold | Sharpe | vs market | time in market | trades |
|---|---|---|---|---|---|
| 14 | 5 | 0.95 | +0.17 | 51% | 157 |
| 14 | 10 | 0.68 | −0.10 | 61% | 176 |
| 14 | 20 | 0.90 | +0.12 | 77% | 192 |
| 28 | 5 | **0.91** | **+0.13** | **46%** | 131 |
| 28 | 10 | 1.02 | +0.24 | 54% | 130 |
| 28 | 20 | 0.85 | +0.07 | 64% | 149 |
| 56 | 5 | **1.07** | **+0.29** | 40% | 109 |
| 56 | 10 | 1.01 | +0.23 | 45% | 109 |
| 56 | 20 | 0.91 | +0.13 | 52% | 117 |

**8 of 9 parameter pairs beat the market on Sharpe.** That breadth matters more than any single number — it matches the paper's "nearly all lookback/holding pairs beat the market after costs," and robustness across a parameter grid is much harder to fake than one tuned pair.

**But the magnitude does not replicate.** The paper's headline is 1.51; our best is **1.07**, and the paper's specific (28, 5) gives **0.91**. The market baseline replicates almost exactly (0.78 here vs 0.85 there), so we are measuring the same thing — the strategy's edge is simply smaller on this sample.

**"Invested ~48% of the time" replicates precisely:** (28, 5) is in the market **46%** of the time. The mechanism behaves as described.

## Result 2 — parameter selection does NOT survive walk-forward

This is the decisive test, and it fails.

| fold | best in-sample params | in-sample | out-of-sample |
|---|---|---|---|
| 0 | (56, 10) | +20.24% (5 tr) | **+41.75%** (14 tr) |
| 1 | (14, 20) | +50.85% (15 tr) | **−8.38%** (21 tr) |
| 2 | (28, 5) | −1.32% (9 tr) | **−2.69%** (11 tr) |
| 3 | (14, 5) | +4.45% (14 tr) | **−2.54%** (10 tr) |

Average in-sample **+18.55%**, average out-of-sample **+7.03%**, overfitting gap **+11.52%**.

Two things kill confidence:

1. **The winning parameters change every single fold** — (56,10), (14,20), (28,5), (14,5). There is no stable optimum to select.
2. **Only 1 of 4 folds is positive out-of-sample.** The positive average is carried entirely by fold 0's +41.75%; strip it and the strategy loses in every remaining fold.

Note our `overfit` gate would **not** flag this, because it fires only when `avg_is > 0 AND avg_oos < 0`, and avg_oos here is +7.03%. That is a gate limitation worth recording: a strategy can pass on a single lucky fold. A stricter rule — e.g. requiring a majority of folds positive OOS — would have caught it.

## Reading

The honest conclusion is split:

- **The mechanism has something.** Being long only in strong trends beat market Sharpe across 8 of 9 parameterisations and cut time-in-market to 40–77%. That breadth is the credible part.
- **Optimising its parameters is worthless.** Picking the best-in-sample pair is a coin flip out-of-sample. If this is ever used, it should run a **fixed, non-optimised** parameter — mid-range, chosen a priori — never a walk-forward-selected one.
- **It does not clear the bar to trade.** One positive fold out of four is not evidence.

## Caveats

- Returns are **not** comparable to buy-and-hold here: the Trader risk-sizes to ~20% exposure while buy-and-hold is 100% invested. Only **Sharpe** (scale-invariant) is a fair comparison, which is why the tables report it. For the same reason the strategy's low max drawdown is flattered by sizing and is not directly comparable to the market's −76.6%.
- Single asset (BTC), not the crypto market portfolio the paper used.
- Fee is 10 bps vs the paper's 15 bps, so costs are *not* the reason for the shortfall.
- A first walk-forward attempt returned "no parameter set cleared the fold minimum" on 1,825 bars — that was a **harness misconfiguration**, not a finding: `warmup=400` exceeded the ~365-bar fold length, so no bars were replayed. Fixed by extending the daily cache to 3,263 bars.

## Next

Per the research priority list, the remaining untested items are the **cost-aware no-trade band** (cheapest, and it addresses signal-to-trade conversion rather than predictability) and **maker/limit orders** (changes the sign of a cost rather than its size).
