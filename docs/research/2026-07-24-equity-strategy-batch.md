# Test 11: five more equity families, and why risk parity stopped working

**Date:** 2026-07-24
All signals shifted one bar, costs charged, judged on Sharpe against buy-and-hold with
sub-periods.

## Summary

| family | verdict |
|---|---|
| short-term reversal | **dead** — worse than holding at every horizon |
| factor ETFs | **dead** — all five below SPY on Sharpe |
| dual momentum | marginal (+0.04 at 126d, −0.08 at 252d) |
| volatility targeting | real but modest, and crash-driven |
| **risk parity / diversification** | **largest gain in the project — and its mechanism has broken** |

## Dead on arrival

**Short-term reversal.** Buying SPY after down days, the documented equity effect that is
the *opposite* of the momentum that failed. Sharpe: −0.46 (1 down day), −0.24 (2), −0.07
(3) versus buy-and-hold, and worse still post-2010. Whatever reversal existed is gone.

**Factor ETFs**, common window 2013–2026, Sharpe versus SPY's 0.85: MTUM 0.83, QUAL 0.83,
USMV 0.79, VLUE 0.74, SIZE 0.72. **All five below the index.** MTUM earned more (15.81% vs
13.92%) but with proportionally more risk. Thirteen years of paying for factor exposure
that did not deliver risk-adjusted improvement.

**Volatility targeting** improves Sharpe by +0.08 to +0.11 over the full history but only
+0.02 to +0.04 post-2010, with two of four settings negative. Same signature as the trend
filter: the gain is concentrated in crashes.

## Risk parity: the biggest result, and the most fragile

Inverse-volatility weighting across SPY/TLT/GLD, 60-day lookback:

| | annualized | Sharpe | max DD |
|---|---|---|---|
| 100% SPY | 10.81% | 0.64 | −55.2% |
| 60/40 SPY/TLT | 8.57% | 0.80 | −29.9% |
| 50/30/20 SPY/TLT/GLD | 9.41% | 0.93 | −24.6% |
| **risk parity** | 9.13% | **1.03** | **−21.8%** |

Sharpe 1.03 against 0.64 is the largest improvement anything has produced in this project,
and unlike the trend filter it is **parameter-robust** — 0.97/1.01/1.01/0.96 across 20, 60,
120 and 252-day lookbacks, and it survives cost up to ~0.2% per rebalance.

### But the gain is one regime, and the mechanism has since broken

| period | SPY Sharpe | RP Sharpe | gain |
|---|---|---|---|
| 2004–2012 (bond bull) | 0.31 | 1.26 | **+0.96** |
| 2013–2021 (low rates) | 1.00 | 0.96 | **−0.04** |
| 2022–2026 (rate shock) | 0.71 | 0.80 | +0.09 |
| **2022 alone** | −0.74 | **−1.13** | **−0.40** |

The headline gain is almost entirely 2004–2012, when equities went nowhere and bonds
rallied. Through 2013–2021 there was no benefit at all. **In 2022 — the year diversification
was supposed to earn its keep — risk parity was worse than holding SPY.**

### And here is *why*, which is the useful part

Correlation of daily returns with SPY:

| pair | full sample | pre-2022 | **2022+** |
|---|---|---|---|
| SPY–TLT | −0.30 | **−0.41** | **+0.10** |
| SPY–GLD | +0.07 | +0.04 | +0.15 |

**The stock–bond correlation flipped sign.** Risk parity works by combining assets that
move oppositely; when inflation drove both down together, the diversification it depends on
simply was not there. This is not a statistical fluke to be explained away — it is the
mechanism failing, visibly, in the data.

Splitting the pair confirms it. Post-2022: **SPY+GLD reaches Sharpe 1.25** while
**SPY+TLT collapses to 0.27**. Bonds stopped diversifying; gold kept doing it.

(Resist the obvious conclusion. "Use gold instead of bonds" is picking the asset that
worked over four years after seeing the answer — precisely the error that produced a +573%
crypto result. It is a hypothesis, not a finding.)

## What survives

**Diversification is real but not free, and not constant.** It reduced drawdown in every
period tested — −21.9% against SPY's −55.2% over the full sample, and still −20.6% against
−24.5% in the recent one. That part held even when the Sharpe gain did not.

That matters because of what the returns document established: the binding constraint on
actually collecting equity returns is **surviving the drawdown**, not finding alpha. A
portfolio that halves the worst case is worth something even when it adds no risk-adjusted
return — for the same reason the trend filter was worth something.

## Where eleven tests leave equities

Nothing beats the index on risk-adjusted terms through *timing*. What does help is
**structural**: diversify across genuinely uncorrelated assets, and size positions so the
drawdown is survivable. Both reduce the worst case; neither is alpha, and neither depends
on predicting anything.

That is a duller answer than "found a strategy," and it is the one the evidence supports.
The single most useful number in this document is the correlation table — because it says
the classic 60/40 diversification premium is materially weaker now than the backtests that
sell it, and it says so with a mechanism rather than a hunch.
