# Verification: the CTREND claim, checked against the paper

**Date:** 2026-07-24
**Why:** CTREND is the load-bearing claim behind the proposed multi-coin architecture
change, and it was one of the 90+ claims in `2026-07-23-crypto-strategy-findings.md` that
never received an adversarial pass. Verified before committing to the build.

**Source:** Fieberg, Liedtke, Poddig, Walker & Zaremba, "A Trend Factor for the Cross
Section of Cryptocurrency Returns", *Journal of Financial and Quantitative Analysis*,
doi:10.1017/S0022109024000747. Full text read directly.

Provenance is better than assumed: this is a peer-reviewed JFQA paper, not a working
paper or preprint.

## Claims that hold

| Our recorded claim | Paper | Verdict |
|---|---|---|
| 3.87%/week gross, t=5.19, Sharpe 1.94 | Table 3, H−L row | **confirmed exactly** |
| net 2.90%/wk at 30/40bps, 2.35% at 50/60bps | Table 9 | **confirmed** (t=3.89 and t=3.16) |
| breakeven cost 1.41%/trade | Table 9 BETC | **confirmed** (BETC-5% = 0.88%) |
| 68% weekly turnover | p.32 | **confirmed** |
| top-100 / largest coins still work | 50% biggest 3.84%, 10% biggest 2.51%, 50% most liquid 4.36% | **confirmed** |
| 28 technical indicators, elastic net, weekly rebalance | Section III | **confirmed** |
| not a micro-cap artifact | "the CTREND effect originates mainly from the biggest and most liquid cryptocurrencies" | **confirmed** |

Also confirmed: robustness across 55,296 research designs, significance in both bull
(4.49%) and bear (3.25%) markets, and returns that survive holding periods up to 4 weeks.

## Claim that was WRONG, in our favour

Our Tier-2 entry recorded this catch:

> "**Catch:** it is long-short, and the crypto short leg is where these strategies die.
> A long-only version captures a fraction."

**The first half is right and the second half is wrong.** Table 3's quintile
decomposition:

| Rank | Avg weekly | t-stat | Sharpe | αCCAPM | αLTW | βCMKT |
|---|---|---|---|---|---|---|
| L (lowest CTREND) | **0.12%** | (0.16) | 0.06 | −1.70 | −1.51 | 0.98 |
| 2 | 0.93% | (1.32) | 0.49 | −0.82 | −0.82 | 0.94 |
| 3 | 1.12% | (1.79) | 0.67 | −0.56 | −0.99 | 0.91 |
| 4 | 2.72% | (3.59) | 1.34 | 0.67 | 0.19 | 1.10 |
| H (highest CTREND) | **3.98%** | (4.80) | 1.80 | **2.11** (3.49) | 1.10 (1.94) | 1.01 |
| H−L | 3.87% | (5.19) | 1.94 | 3.80 | 2.62 | 0.03 |

The long leg alone earns **3.98% per week — more than the 3.87% long-short spread.** The
short leg earns 0.12% with a t-statistic of 0.16, i.e. nothing distinguishable from zero;
shorting it actually *subtracts* from the raw return.

This matters a great deal to us. Our own research independently ruled out any short leg
("short-only momentum lost money at 20 of 21 parameter pairs with ZERO costs"). We
recorded that as a reason CTREND would only partly transfer. It isn't — **in raw-return
terms a long-only CTREND captures the entire effect**, and the constraint we already
imposed on ourselves costs essentially nothing.

## The honest counterweight: the long leg is not market-neutral

The H−L spread has `βCMKT = 0.03` — genuinely market-neutral. The long leg does not:
`βCMKT = 1.01`. A long-only CTREND is a fully market-exposed crypto position, so a large
part of its 3.98%/week is simply the crypto market's return, which is available by
holding BTC.

What is left after controlling for that:

- **α vs CCAPM: 2.11%/week, t = 3.49** — significant.
- **α vs the LTW 3-factor model: 1.10%/week, t = 1.94** — *not* significant at the 5%
  level.

So the incremental edge of a long-only CTREND over a market-and-momentum-exposed
benchmark is around 1.1%/week and does not clear conventional significance. The top
quintile also has `βCMOM = 0.52` and an average prior-3-week return of **+62.74%** — it is
buying strong recent winners, and is substantially a momentum portfolio.

**The right way to state it:** long-only CTREND keeps the whole raw return, but a good
part of that is beta we could obtain far more cheaply. The market-neutral part of the
effect is exactly the part that requires the short leg we cannot run.

## Two further caveats that bear on using this

1. **The sample ends May 2022 — four years stale.** Apr 2015 to May 2022, 423 weekly
   observations, 3,244 unique coins, minimum $1M market cap. The authors themselves note
   "an inevitable decline in profitability over time is visible," though the recent half
   still yields 3.26%/week. Our own methodology warning (anomalies decay; recent
   subsamples are the binding test) applies with full force to a result that stops before
   the 2022 crash, the 2023–24 recovery, and the spot-ETF era.
2. **Their cost assumption is more conservative than our actual cost.** They assume 30bps
   for the long leg; Binance spot taker is 10bps. On costs we are three times better off
   than the paper's base case — and the BETC of 1.41% is 14x our fee. Cost is genuinely
   not the obstacle here, which is consistent with everything our own scan measured.

## What this changes

- The multi-coin direction survives verification and is **strengthened**: the leg we can
  actually trade is the leg that carries the raw return.
- But the expected prize should be stated honestly as **a market-exposed long portfolio
  with roughly 1–2%/week of alpha of contested significance**, not "3.87% per week".
- The design target is therefore a long-only, weekly-rebalanced, cross-sectional ranking
  over the largest/most liquid Binance spot pairs — which is also the subsample where the
  paper's effect is strongest and where our fee advantage applies.

## What remains unverified

- Whether any of this survives 2022–2026. Nothing in the paper covers it, and we cannot
  check without a multi-coin dataset — which is the first thing the build would produce.
  That makes the data layer worth building *even if the strategy is later rejected*: it is
  the instrument for answering the question.
- Whether a 28-indicator elastic-net forecast is reproducible at our scale, or whether a
  much simpler cross-sectional rank (the paper shows individual indicators work too,
  though weaker) captures enough of it.
