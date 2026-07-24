# Test 5: cross-sectional momentum — a large result that does not survive its controls

**Date:** 2026-07-24
**Claim under test:** the last untested lever. Rank coins against each other weekly, hold
the top K equal-weighted. The evidence floor found in
`2026-07-24-daily-bars-and-the-evidence-floor.md` says pooling across coins is the only
escape from "too slow to fee-survive, too slow to judge".

**Engine:** `backtest/cross_sectional.py`. Ranker receives history strictly *before* the
bar it trades on (pinned by a test that captures what the ranker is handed, not what it
returns). Coins with no price on the rebalance date are ineligible. Fees on both sides of
every change. Equity marked every bar.

## The headline, before controls

BTC/USDT daily, 29 screened symbols, 2022-06-16 → 2026-07-24, fee 0.001:

- 27 of 27 parameter combinations positive
- 21 of 27 beat buy-and-hold BTC
- median +290%, best +1400%, `momentum(28) top5 weekly` = **+573.76%** vs BTC +219%

That is the shape of a result that should be distrusted, so it was.

## Control 1 — is the universe just a basket of winners? **No.**

The panel is the top 30 coins by volume *today*. If ranking among known survivors were
the whole story, simply holding all of them equal-weighted would also beat BTC.

| | return |
|---|---|
| buy & hold BTC | +207.07% |
| **buy & hold the same 29 coins, equal weight** | **+91.20%** |

The universe *underperforms* BTC by a wide margin. "Winners' basket" is refuted.

## Control 2 — does any rotation work? **No.**

Random selection, top-5 weekly, 10 seeds: median **+59.48%**, range −54.15% to +190.39%.
Momentum's +573.76% sits far outside the random range. Rotation alone does not do it.

## Control 3 — is the accounting real? **Yes, exactly.**

Run on a BTC-only panel, buy once and hold, the engine returns **+207.07%** against a
manual calculation of **+207.07%**. No drift.

(One measurement note: the first equity point is recorded *after* the opening trade, so
`total_return` measures from a post-fee base and understates costs by one entry fee — the
same phase artifact already documented for `run_replay`. Worth ~0.1%, immaterial at these
magnitudes, but it flatters the strategy rather than the benchmark.)

## Control 4 — is it one lucky coin? **No.**

Most-held coin occupies 8.8% of position-slots; 24 of 29 coins are held at some point.
Leave-one-out on the five most-held:

| removed | return | change |
|---|---|---|
| DEXE | +355.74% | −218.03pp |
| RIF | +406.47% | −167.29pp |
| TRX | +529.91% | −43.85pp |
| ETH | +530.62% | −43.15pp |
| BNB | +537.15% | −36.62pp |

No single coin carries it; the result still beats BTC without either top contributor.

## Control 5 — the one that breaks it

Four controls passed. The fifth is the temporal split, and it is where the result comes
apart.

| window | momentum(28) k5 | hold BTC | vs BTC |
|---|---|---|---|
| full 2022-06 → | +573.76% | +207.07% | +366.70% |
| **half 1, 2022-06 → 2024-07** | **+103.09%** | **+196.16%** | **−93.07%** |
| half 2, 2024-07 → | +330.58% | +0.71% | +329.87% |
| last 1y, 2025-07 → | +27.72% | −43.62% | +71.34% |

**Momentum loses to BTC in the first half and only wins in the recent half.** That is the
exact signature of universe-selection bias: a coin that ran hard in 2025 is in today's
top-30 *because* it ran, so the recent window is where "top 30 by volume today" is most
contaminated.

Testing it directly — restrict the universe to the 16 coins that already had a full
history at 2022-06-16 (established names, not later additions):

| window | universe | momentum | hold same coins | edge over hold |
|---|---|---|---|---|
| full | all 29 | +573.76% | +91.20% | +482.56pp |
| full | **established 16** | **+282.33%** | +91.20% | +191.13pp |
| half 2 | all 29 | +330.58% | +46.13% | +284.45pp |
| half 2 | **established 16** | **+72.49%** | **+64.48%** | **+8.01pp** |
| last 1y | all 29 | +27.72% | −0.23% | +27.95pp |
| last 1y | **established 16** | +36.96% | +18.64% | +18.32pp |

**Roughly three-quarters of the apparent edge was recently-added coins.** And once the
benchmark is corrected from "hold BTC" to "hold the same universe" — which is the only
honest comparison for a strategy that picks from that universe — the residual edge in the
recent window is **+8 percentage points over two years**.

That is not an edge. That is noise around a universe that happened to outperform BTC.

## Reading

- The engine is correct, and the controls did their job. Four plausible explanations were
  eliminated and the fifth held.
- The correct benchmark is **hold-the-same-universe**, not hold-BTC. Against BTC the
  strategy looks spectacular largely because the 2024–26 window is one where BTC was flat
  and altcoins were not.
- What remains after removing recently-added coins is small, and it is measured on a
  universe that is *still* survivorship-biased: all 16 "established" coins are also
  still top-30 today, so coins that were large in 2022 and subsequently died are absent
  except the two forced in by hand.
- **No claim of edge.** The scan headline is unchanged.

## What would actually answer this

The blocking defect is the universe, not the strategy or the engine. To test properly:

1. Download a **much larger** set — several hundred symbols, chosen without reference to
   current volume, deliberately including coins that are now dead or illiquid.
2. Rebuild membership **point-in-time**: at each rebalance date, rank by trailing volume
   *as of that date* from the cached data, never by today's ranking.
3. Rerun. If the effect survives a point-in-time universe, it is worth taking seriously.

Step 2 is already specified in `2026-07-24-multi-coin-data-integrity.md` and the
`candidate_symbols` docstring; this test skipped it and the results show precisely the
distortion that was predicted there. The prediction was written before the test was run,
which is the one piece of good news in this document.

## Cost, for the record

Fee drag is no longer the binding constraint. At weekly rebalancing, turnover runs 23–86%
per rebalance and total fees over four years are ~$1,300–11,700 on a book that grew from
$10,000 — material, but never the difference between success and failure here. The
turnover thesis established at daily bars continues to hold: the cost problem is solved,
and what is left is the harder problem of whether there is anything to trade.
