# Test 3: daily bars — the first PASS, and why it still isn't tradeable

**Date:** 2026-07-24
**Claim under test:** Tier 1 item 3 of `2026-07-23-crypto-strategy-findings.md`
("weekly rebalancing as a design constraint"): everything that survives costs in this
literature rebalances weekly, not hourly. The scan had never been run on daily bars —
only 1m, 3m, 1h and 4h — despite 3,263 daily bars sitting in the cache.

## Result 1 — `1d ma` clears every gate, the first configuration ever to do so

BTC/USDT daily, 3,263 bars, 2017-08-17 → 2026-07-23, pinned (20,50), fee 0.001:

| tf | strategy | trades | net | feedrag | avgIS | avgOOS | folds | posOOS | verdict |
|---|---|---|---|---|---|---|---|---|---|
| 1d | ma | 36 | +26.50% | **0.06** | +5.07% | **+5.73%** | 4 | 3 | **PASS** |
| 1d | rsi | 106 | −1.07% | 4.25 | −2.72% | −0.87% | 4 | 2 | FAIL fee-drag |
| 1d | rsi+trend | 28 | −1.68% | 0.94 | — | — | 0 | 0 | FAIL fee-drag |
| 1d | ma+trend | 15 | +16.73% | 0.04 | — | — | 0 | 0 | FAIL too-few-trades |

Per-fold, all four valid: OOS **+14.28%, −2.71%, +9.53%, +1.83%**.

Two things here are unlike anything the project has measured before:

1. **Fee drag collapses to 0.06** against a 0.30 ceiling. The progression across
   timeframes is now unambiguous — 1m/3m 1.5–14, 1h 0.78–6.4, 4h 0.21–0.75, **1d 0.04–0.06**.
   The literature's central claim, that *turnover* rather than fee level is the binding
   variable, is confirmed on our own data across four orders of timeframe.
2. **`avg_oos` (+5.73%) exceeds `avg_is` (+5.07%).** There is no overfitting signature at
   all, which is what one expects from parameters that were never fitted to this data.

## Result 2 — the recent-subsample test dissolves it

The research doc's methodology warning 4 says anomalies are regime-dependent and decaying,
that backtests spanning 2014–2022 systematically overstate forward edge, and that
**recent-subsample performance is the binding test**. Applying it:

| window | bars | trades | net | buy & hold | feedrag | folds | posOOS | verdict |
|---|---|---|---|---|---|---|---|---|
| full, 2017-08 → | 3263 | 36 | +26.50% | +1385.12% | 0.06 | 4 | 3 | **PASS** |
| last 6y, 2020-07 → | 2191 | 24 | +22.74% | +521.45% | 0.05 | 1 | 1 | FAIL insufficient-folds |
| last 4y, 2022-07 → | 1461 | 17 | +12.50% | +189.72% | 0.06 | 0 | 0 | FAIL too-few-trades |
| last 3y, 2023-07 → | 1096 | 12 | +11.41% | +151.10% | 0.05 | 0 | 0 | FAIL too-few-trades |
| last 2y, 2024-07 → | 730 | 8 | +1.04% | +11.62% | 0.26 | 0 | 0 | FAIL too-few-trades |

Note *how* it fails. Net return is **positive in every window** and fee drag stays at
0.05–0.06 throughout. Nothing breaks. What happens is that the evidence runs out: the
strategy makes **4.03 trades per year**, so no recent window contains enough of them to
judge.

**The PASS exists only because the window is nine years long.**

## Result 3 — the structural finding: an evidence floor

Those two results are not independent, and the tension between them is the real output of
this test.

- Cutting fee drag requires cutting turnover. `1d ma` gets drag to 0.06 by trading 4×/year.
- The `MIN_TRADES = 20` gate therefore needs **≥ 5.0 years** of daily data (20 ÷ 4.03).
- The same research doc says data older than roughly 2022 overstates forward edge, and
  that recent-subsample performance is the binding test.

**Those two constraints are close to incompatible on a single asset.** Any daily-bar
configuration slow enough to survive fees is too slow to accumulate a statistically
judgeable number of trades inside the window where the evidence is still trustworthy. The
scan is not being unfair — it is correctly reporting that a 4-trades-per-year strategy
cannot be validated on 2 years of data.

This is a floor imposed by arithmetic, not by our thresholds. Lowering `MIN_TRADES` would
not fix it; it would only relabel an unjudgeable configuration as judged.

**This is the strongest argument yet for the multi-coin cross-sectional design**, and it
arrives from our own measurements rather than from the literature. A cross-sectional
strategy over N coins rebalancing weekly gets N × 52 position-decisions per year while
keeping each individual holding period long. It buys statistical power *without* buying
turnover. That is precisely why every cost-surviving strategy in the harvested literature
is cross-sectional, and we have now derived the reason independently.

## Result 4 — it loses enormously to buy and hold, in every window

+26.50% against +1385.12% over the full sample. +1.04% against +11.62% over the last two
years. It underperforms holding BTC in all five windows.

Part of this is exposure, not skill: the Trader risk-sizes to roughly 20% of equity while
buy-and-hold is 100% invested, and `1d ma` is out of the market much of the time. Scaling
naively for that does not come close to closing a 50× gap.

It bears repeating that **the gates never required beating buy and hold** — `edge` is the
ranking metric among survivors, not a gate, and the owner added `net > 0` in the
2026-07-23 amendment precisely because ranking on `edge` alone would crown a money-loser.
So `1d ma` passing while losing to hold is the gate set behaving as specified, not a
defect. But no one should read "PASS" as "worth trading in place of holding BTC."

## Result 5 — maker/limit orders are ruled out on our venue

The 2026-07-23 doc closes by listing what it did not establish, including: *"Current
Binance fee tiers, maker/taker rates, and VIP thresholds were not confirmed against live
documentation."* Confirmed now, from the exchange itself via `ccxt.load_markets()`:

```
binance SPOT    BTC/USDT   maker 0.0010   taker 0.0010    <- no differential
binance FUTURES BTC/USDT   maker 0.0002   taker 0.0005
```

**On Binance spot there is no maker discount at all.** Recommended next step #3 of the
2026-07-23 doc ("switch the broker to maker/limit orders"), and the maker conclusion drawn
from methodology finding 5 (liquidity is what prices the crypto cross-section), both
assumed a differential that does not exist on the product we trade. Resting limit orders
on spot would buy zero fee saving and add fill risk.

The differential exists only on futures — so "go maker" actually means "go derivatives",
which brings leverage, funding rates and liquidation risk. That is a risk decision, not a
cost optimisation, and it should not be filed under fee reduction.

## Reading

- Daily bars confirm the turnover thesis decisively; the fee problem is solved at 1d.
- Solving it exposes the next binding constraint, which is **evidence, not cost**.
- `1d ma` is not tradeable: unjudgeable on recent data, and far behind holding BTC.
- Scan headline across all tested configurations is now **1 of 20** — and that one PASS
  does not survive the recent-subsample test the research doc calls binding.

## Next

The multi-coin cross-sectional universe, for the reason derived in Result 3 rather than
because a paper recommended it. Before building it, the load-bearing claim behind it
(CTREND: 3.87%/week gross, 2.90%/week net at 30/40bps) is still **unverified** — it is one
of the 90+ claims that never got an adversarial pass, and it is large enough to warrant
skepticism on principle. Verify that claim before committing to the architecture change.
