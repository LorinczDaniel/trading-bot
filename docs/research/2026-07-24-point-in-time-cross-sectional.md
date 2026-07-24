# Test 6: cross-sectional momentum, properly controlled — a definitive negative

**Date:** 2026-07-24
**What changed from Test 5:** every defect it identified in itself, fixed.

| | Test 5 | Test 6 |
|---|---|---|
| universe | top 30 by volume **today** | **full population**, 642 symbols |
| delisted coins | 2, forced in by hand | all of them, ~190 |
| membership | static, chosen at the end | **point-in-time**, trailing volume at each date |
| benchmark | hold BTC | **hold-same-universe** and **random selection** |
| metric | total return | **Sharpe** (return is a volatility tilt) |

## Headline

**It does not work, and the earlier positive result was entirely universe bias.**

The same strategy that returned **+573.76%** on the biased universe returns **−99.71%**
on a point-in-time one.

| | return | Sharpe |
|---|---|---|
| buy & hold BTC | **+34.26%** | **+0.38** |
| hold the PIT universe (top 50, equal weight) | −96.29% | −0.30 |
| random top-5 weekly (median of 20 seeds) | −98.38% | −0.37 |
| momentum(28) top-5 weekly | **−99.71%** | **−0.38** |

Momentum beats random on Sharpe in **9 of 20 seeds** — a coin flip. Across a parameter
grid, **1 of 12** settings beat random and **0 of 12** beat holding the universe.

## Why the sanity check mattered

An equal-weight basket losing 96% while BTC gained 34% is extreme enough to be a bug
signature, so it was verified two ways before being believed.

**A real bug was found first.** The rebalance interleaved trims and top-ups, so an
underweight position was capped by whatever cash happened to be free at that instant and
the cash a later trim released was never deployed — the book drifted off equal weight and
accumulated idle cash. Fixed by two passes, trims before top-ups, pinned by a test.

It changed the result by 0.07pp (−96.22% → −96.29%). The loss was not the bug.

**Then the number was reproduced without the engine.** Compounding the equal-weighted mean
of member returns week by week in plain pandas gives **−96.00%**, against the engine's
−96.29%; the difference is fees. The engine is not manufacturing the loss.

## The finding underneath the finding

Per-coin total return over each coin's own history, 492 symbols with more than 400 bars:

| percentile | total return |
|---|---|
| worst | −100.0% (QUICK) |
| 25th | −97.5% |
| **median** | **−91.7%** |
| 75th | −74.7% |
| best | +3997.5% (SOL) |

**91.7% of coins have negative total returns.** The median altcoin lost 92% of its value.

That is the whole explanation. A cross-sectional strategy picks from this distribution;
equal-weighting it loses 96%; picking five by any rule loses 97–100%. There is no ranking
signal to find because the population is overwhelmingly negative-sum, and weekly
rebalancing into it compounds the damage by repeatedly buying back into decliners.

**Ranking by trailing volume is itself adverse selection.** High volume marks the coin
currently being promoted. The universe churns 13.4% per week, so a liquidity-ranked
portfolio continuously rotates into whatever is hottest — which is the worst available
selection rule from this distribution.

## The one result that does not replicate

Half 1 (2021-01 → 2023-10) shows momentum beating random on Sharpe in **20 of 20 seeds**,
+0.40 Sharpe over random. Half 2 shows **3 of 20** and −0.31.

A signal present in one half and absent — reversed, in fact — in the other is not an edge.
Reporting only the first half would have produced a compelling and false result, which is
exactly what the temporal split exists to prevent.

## What survives

- **Buy and hold BTC beat every configuration tested**, on both return and Sharpe, and it
  is the only strategy in this document with a positive Sharpe.
- The measurement apparatus works. It caught a real accounting bug, an independent
  verification confirmed the headline, and the metric correction (Sharpe over raw return)
  changed how a result would have been read.
- The CTREND claim verified in `2026-07-24-ctrend-claim-verified.md` — 3.87%/week over
  2015–2022 across 3,244 coins — **does not reproduce** on a tradeable Binance spot
  universe over 2021–2026. That is not a refutation of the paper: different era, different
  universe, and their long leg was β≈1.01 to a market that was rising. It is a statement
  that the effect is not available to us, here, now.

## Residual limitation, stated plainly

The universe is Binance-serviceable symbols. Coins hard-purged from the API are absent, so
a survivorship floor remains — but it works *against* the result reported here: including
the fully-purged coins would make the universe's return worse, not better. The negative is
therefore conservative.

## Conclusion

The prediction branch is closed. Across six tests — 16 single-asset configurations, daily
bars, time-series momentum, a cost band, biased cross-sectional, and now point-in-time
cross-sectional — nothing has produced a validated edge, and the one candidate that
cleared every gate (`1d ma`) did so only because BTC has nine years of history.

The instrument is trustworthy. The conclusion it keeps returning is that classical
technical prediction on retail-accessible crypto does not have an edge worth trading,
and that the median altcoin is a wealth-destroying asset that no ranking rule redeems.
