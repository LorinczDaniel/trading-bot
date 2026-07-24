# Test 13: microstructure and positioning — IN PROGRESS, resumable

**Date:** 2026-07-24
**Status:** downloads incomplete. This records an early read and exactly how to finish.

## Why this exists

Two earlier docs recorded these branches as untestable:

- `2026-07-24-variance-risk-premium.md`: *"order book — no history via the API"*
- `2026-07-24-daily-bars-and-the-evidence-floor.md` era: *"open interest — Binance serves
  only ~30 days"*

**Both were wrong.** True of the REST API, false of Binance's free archive at
`data.binance.vision`, which was never checked. `data/binance_archive.py` now reads it.

## The early read — BTC positioning, 2030 days, 2021-01 → 2026-07

Significance threshold **±0.053**, fixed *before* seeing data, from a synthetic validation
that planted signals of known strength and measured the noise band over 30 random signals.

| signal | IC 1d | IC 5d | verdict |
|---|---|---|---|
| open interest, 5-day change | −0.025 | −0.040 | noise |
| **top-trader long/short (by size)** | −0.038 | **−0.073** | **clears** |
| **top-trader long/short (by count)** | −0.044 | **−0.078** | **clears** |
| all-accounts long/short | −0.035 | −0.055 | marginal |
| taker buy/sell volume | +0.010 | +0.003 | noise |

**The sign is negative and consistent**: when large accounts are more long, forward returns
are *lower*. Crowded positioning predicts weakness — a contrarian reading, and a documented
one.

This is the first predictive signal in thirteen tests to clear a pre-registered threshold.

## Why it is NOT yet a finding

1. **One asset.** Breadth across the other seven is the discriminating test, and it is what
   killed the crypto cross-sectional result.
2. **Multiple testing.** Five signals × two horizons = ten tests; roughly one would clear
   ±0.053 by chance. Three clearing is more than chance but not conclusive.
3. **No economic test.** Candlestick patterns beat 200/200 random controls and were still
   worthless after costs (`2026-07-24-candlestick-patterns.md`). An IC of −0.073 is small;
   it must survive a trading test against random timing with matched exposure.
4. **No temporal split.** 2021–2026 spans very different regimes.

## To resume

Downloads are **resumable** — cached days are skipped and progress flushes every 50 days,
so an interrupted run keeps nearly all its work.

```bash
# still needed: 7 more metrics symbols, 5 bookDepth symbols
python fetch_micro.py metrics BTCUSDT,ETHUSDT,SOLUSDT,XRPUSDT,DOGEUSDT,BNBUSDT,ADAUSDT,LINKUSDT 2021-01-01
python fetch_micro.py bookDepth BTCUSDT,ETHUSDT,SOLUSDT,XRPUSDT,DOGEUSDT 2023-01-01
```

Measured rates: metrics 0.30 s/file (16,240 files ≈ 82 min), bookDepth 1.09 s/file
(6,500 files ≈ 118 min). Run them in parallel.

Then the analysis, in this order — each step can kill the result:

1. **IC breadth** across all 8 symbols. Require the same sign in a clear majority.
2. **Temporal split.** Halve the sample; a signal in one half only is not a signal.
3. **Trading test** against 200 random entry sets with matched exposure, on Sharpe.
4. **Cost sensitivity.** The candle signal died at 10bps; find where this one dies.

Only if all four survive is it worth anything.

## Honest prior

Twelve tests, twelve negatives. The one real edge found (cash-and-carry basis) had already
been arbitraged away. An IC of −0.073 on one asset is more likely to be noise or to die in
step 3 than to be tradeable. But positioning data is genuinely different information from
the price transforms that failed, and this is the strongest pre-registered read yet, so it
deserves finishing.
