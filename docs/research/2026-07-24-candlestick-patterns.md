# Test 12: candlestick patterns — real information, backwards, and worthless

**Date:** 2026-07-24
**Question:** do candle formations carry predictive information that could time momentum?

**Answer:** yes, genuinely — it is the first signal in this project to beat a proper random
control. It also works **opposite to how it is taught**, and the magnitude is too small to
be worth trading.

**Method:** seven classic patterns (bullish/bearish engulfing, hammer, shooting star, doji,
three white soldiers, three black crows) on 37 equity series and 127 crypto series.
Patterns computed only from bars up to *t*; forward returns from *t*'s close. Measured as
**excess over each asset's own unconditional base rate** — a pattern that "works" because
the asset drifts upward is not a signal.

## Result 1 — in equities the patterns are consistently inverted

Excess forward return at +5 days, and the share of assets agreeing with the pattern's
*traditional* direction:

| pattern | taught as | +5d excess | assets agreeing with the textbook |
|---|---|---|---|
| bearish engulfing | sell | **+0.188%** | **1 / 37 (2.7%)** |
| three black crows | sell | +0.221% | 6 / 37 (16.2%) |
| shooting star | sell | +0.113% | 6 / 37 (16.2%) |
| three white soldiers | buy | −0.129% | 5 / 37 (13.5%) |
| hammer | buy | −0.110% | 7 / 37 (18.9%) |
| bullish engulfing | buy | −0.114% | 9 / 37 (24.3%) |

Every single pattern points the wrong way, and the consistency is remarkable — after a
"bearish" engulfing, **36 of 37 equity series outperform their own base rate**. A random
signal would agree with the textbook about half the time.

The mechanism is unmysterious: bearish patterns mark short-term weakness, and equities
have a mild tendency to recover from it. The patterns identify dips, not tops.

## Result 2 — in crypto the effect was an outlier artifact

The first pass showed spectacular numbers: hammer +137.58% excess at 10 days, three white
soldiers +126.65% at 20 days. Those are not signals. Replacing the mean with the median:

| pattern | mean excess (+5d) | **median excess** |
|---|---|---|
| bullish engulfing | +6.895% | **−0.620%** |
| bearish engulfing | −4.517% | **+0.176%** |

The signs flip and the magnitudes collapse. A handful of coins going vertical dominated
every average. Breadth confirmed it independently — 41.7%, 52.0%, 55.1%, 51.6% agreement,
i.e. coin flips. **Crypto candles: nothing.**

## Result 3 — the signal is real, by the strictest test available

Trading SPY on bearish engulfing (enter next bar, hold five sessions), against **200 random
entry sets of identical count and holding period**:

| | Sharpe |
|---|---|
| bearish-engulfing entries | **0.615** |
| random entries, median | 0.287 |
| random entries, best of 200 | 0.604 |

**The pattern beat 200 of 200 random entry sets.** Nothing else in this project has done
that. Whatever candles are picking up, it is not noise.

## Result 4 — and it is still not worth trading

**Standalone it loses**, because being in cash 80% of the time forfeits more drift than the
timing gains: Sharpe below buy-and-hold in 9 of 10 assets, median −0.14.

So use it as an **overlay** — stay invested, tilt exposure around 100% on the signal:

| tilt | median Sharpe gain | assets positive |
|---|---|---|
| ±20% | **+0.006** | 6 / 10 |
| ±50% | **+0.003** | 6 / 10 |

Six of ten and a gain of three thousandths of a Sharpe point is indistinguishable from
nothing.

**Cost settles it.** SPY, ±50% tilt, against buy-and-hold's 0.644:

| cost per unit turnover | overlay Sharpe | vs hold |
|---|---|---|
| 0.00% | 0.725 | +0.081 |
| 0.05% | 0.683 | +0.039 |
| **0.10%** | 0.642 | **−0.002** |
| 0.20% | 0.558 | −0.086 |

**The entire edge is consumed by ten basis points of trading cost.** It exists only in a
frictionless world.

(The SPY temporal split is faintly encouraging — +0.004, +0.021, +0.092 across
1993–2005, 2005–2015, 2015–2026 — but on gains this small, and with 6/10 breadth, that is
not evidence of anything.)

## Reading

This is the cleanest example in the project of the distinction that matters:
**statistically real and economically worthless are different things.** The pattern beats
200/200 random controls and is still not tradeable, because the effect is roughly 0.19%
over five days and round-trip costs are of the same order.

Two things worth keeping:

1. **The patterns are inverted.** If anyone uses candles, the data says do the opposite of
   the textbook — bearish formations mark dips to buy, not tops to sell. That is a robust
   finding (36/37 assets), it just is not a profitable one.
2. **Crypto candle statistics are meaningless without medians.** Any mean taken across
   crypto assets is dominated by a few vertical moves. This applies to every future crypto
   cross-sectional statistic, not just candles.

## Answering the original question

"Changing momentum signals based on candle forms" — no. Candle forms do carry a small
amount of real information about the next few days in equities, in the reverse of the
conventional direction, and none at all in crypto once outliers are handled. The
information is an order of magnitude too small to overcome trading costs, so it cannot
usefully gate or modulate a momentum signal.
