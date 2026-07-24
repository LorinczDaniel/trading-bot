# If the goal is returns: what the measurements actually support

**Date:** 2026-07-24
**Context:** six tests produced no validated edge, and buy-and-hold was the only thing
with a positive Sharpe. Owner's stated goal is returns. So holding was measured properly,
including the parts that hurt.

## The caveat that has to come first

**Buy-and-hold "won" our tests because BTC went up 15x over the sample.** That is an
observation about one asset's past, not a strategy finding and not a forecast. Every
number below describes 2017–2026 for an asset in the strongest era of its existence.
Nothing here establishes that the next nine years resemble the last nine.

This matters more than usual because the numbers look encouraging, and encouraging
backward-looking numbers about a single asset are exactly the shape of the errors this
project spent all session learning to catch.

## 1. Holding periods: long has been forgiving, short has been a coin flip

BTC/USDT daily, 3,264 bars, every possible start date:

| horizon | windows | worst | 25th | median | 75th | best | % negative |
|---|---|---|---|---|---|---|---|
| 1 year | 2,899 | −83.1% | −19.4% | +42.9% | +123.7% | +1092.1% | **34.1%** |
| 2 years | 2,534 | −64.9% | +1.3% | +110.1% | +308.2% | +1478.2% | **24.5%** |
| 4 years | 1,803 | **+31.4%** | +160.8% | +244.9% | +455.5% | +1388.6% | **0.0%** |

Every four-year window was positive. **Do not read that as a law.** With 3,264 bars there
are only about two independent four-year periods in the sample; the 1,803 "windows"
overlap almost entirely, so that 0% is roughly two observations, not eighteen hundred.
It is consistent with a long uptrend and would be produced automatically by any asset that
rose over the period.

The honest reading of the table: **holding horizon dominated everything else.** At one
year a third of start dates lost money. At four years, in this sample, none did.

## 2. DCA versus lump sum: buys a better floor, costs the median

Fixed amount bought weekly, versus everything at the start:

| horizon | DCA median | lump median | DCA worst | lump worst | DCA % negative |
|---|---|---|---|---|---|
| 2 years | +64.0% | +109.8% | **−49.3%** | −65.1% | 23.5% |
| 4 years | +123.5% | +253.1% | **+34.8%** | +33.9% | 0.0% |

DCA is worse on average and better in the tail — the expected result for averaging into a
rising asset. At two years it cuts the worst case by ~16 percentage points and gives up
~46 points of median. Whether that trade is worth it is a risk-tolerance question, not a
measurement question.

## 3. Drawdown: the part that decides whether any of this is survivable

This is the most decision-relevant section and the one most easily skipped.

- Maximum drawdown over the full history: **−83.2%**
- Full-history Sharpe: **0.79**
- Days spent more than 20% below the prior peak: **2,339 (71.7% of all days)**
- More than 35% below: 1,987 (60.9%)
- More than 50% below: 1,303 (**39.9%**)
- More than 70% below: 312 (9.6%)
- Longest unbroken stretch below a prior peak: **1,073 days (2.9 years)**

Read those percentages again. Holding this asset meant being underwater by a fifth for
**more than seven days in ten**, and underwater by half for **two days in five**. The
"every four-year window was positive" result is only collectable by someone who sat
through that without selling.

**The binding constraint on this plan is not the strategy. It is position size** — small
enough that an 83% drawdown lasting three years is tolerable rather than forced-selling.
That is a personal question about capital and temperament, and it is not one a backtest
can answer.

## What this implies for the bot

Almost all of the strategy machinery is now surplus to the stated goal:

- `scan`, `walkforward`, the gates, the cost band, the cross-sectional engine — these were
  built to find an edge. They found that there is none to find. They remain valuable as an
  instrument and as a record, not as a live component.
- What a returns-focused bot needs is small and **already built and tested**: `LiveBroker`
  (real orders with precision and min-notional handling), `supervisor.py` (restart with
  crash-loop protection), `CsvTradeLog` + `report.py` (honest net P&L), `TelegramNotifier`,
  and `reconcile.py` (refuses to start on state drift).
- The missing piece is a scheduled-accumulation path: buy a fixed quote amount on a fixed
  schedule, log it, report it. That is a small addition to existing components rather than
  a new system.

## What is NOT established

- That BTC is the right asset. This was measured because it is what we have data for, not
  because it was compared against alternatives. **No equity index was benchmarked**, and on
  a risk-adjusted basis a broad index fund may well dominate — that comparison needs data
  this project does not have.
- That any of the historical distribution repeats.
- That accumulating a single volatile asset is appropriate for any particular person. It
  concentrates risk in one asset, in one custody arrangement, in one jurisdiction.

## Recommendation

If the goal is returns, the measured evidence supports **holding over long horizons and
sizing for an 83% drawdown**, not trading. The corresponding engineering task is to reduce
the bot to a scheduled accumulator with honest record-keeping, and to stop maintaining
strategy machinery that measured negative.

Before committing capital, the open comparison worth making is BTC against a broad equity
index on a risk-adjusted basis over the same period. That is the one question relevant to
this goal that the project has not measured and currently cannot.
