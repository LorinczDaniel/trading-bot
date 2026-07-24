# Design — Trustworthy Measurement Harness

**Date:** 2026-07-23
**Status:** Approved, awaiting implementation plan
**Scope:** Sub-project A of the "measure then fix" strategy work. Sub-project B
(anti-churn mechanics) is deliberately excluded and depends on this landing first.

## Problem

The bot cannot currently be used to choose a configuration, for three
independent reasons.

**1. The backtester and the live trader disagree about position size.**
`backtest/engine.py:40` goes all-in (`qty = (cash * (1 - fee)) / price`), while
`trader.py:60` sizes by risk (`position_size(equity, price, stop,
risk_per_trade)`). With the default 1% risk and a 5% stop, the trader commits
~$2,000 of a $10,000 account — about 20% of what the backtest commits. The
backtest also has no stop-loss and no kill-switch. A backtest therefore does not
predict what the bot will do, so its ranking of configurations is not evidence.

**2. There is not enough data to measure.** Every cached dataset is 500 bars:
BTC 1h spans 21 days, BTC 3m spans 25 hours, BTC 1m spans 8 hours.
`data/provider.py:23-28` issues a single `fetch_ohlcv` call and overwrites the
cache, so history cannot accumulate past one exchange page (1000 bars at
Binance). With `--trend-sma 200` and `warmup 50`, a 500-bar set leaves ~250
usable bars; `walkforward --splits 4` then cuts that into 100-bar folds, which
is why folds report "0 trades".

**3. Fee churn is real but unmeasured.** The live 1m run
(`ledger/live_BTC-USDT_1m.csv`) took 5 fills in 13 minutes, paying ~$2 per fill
on a ~$2,000 position — a ~0.2% round-trip cost against 1m BTC moves smaller
than that. Every trade also lost money gross (-3.79, -2.13, -4.07), so this was
whipsaw, not fee drag alone. Nothing in the current output would have flagged
this before the run.

## Goals

- A single simulation code path shared by backtest, walk-forward, paper, and live.
- Enough historical data to make walk-forward validation meaningful.
- A scan that ranks configurations on fee-inclusive, overfitting-resistant
  criteria, and names the failure when a configuration is rejected.

## Non-goals

Cooldown / minimum-hold periods, signal-confirmation thresholds, fee-aware trade
gates, and per-strategy trailing-stop defaults are **sub-project B**. They are
built only after this harness can demonstrate whether they help.

---

## A1. Paginated backfill

**Module:** `data/provider.py`

Add `backfill(symbol, timeframe, days)`:

- Compute a start cursor `days` before now; loop
  `exchange.fetch_ohlcv(symbol, timeframe, since=cursor, limit=1000)`.
- Advance the cursor past the last returned bar each iteration. Terminate when a
  page is empty, when the cursor stops advancing, or when the cursor reaches now.
  The no-progress termination is what prevents an infinite loop against an
  exchange that clamps `since`.
- Respect `enableRateLimit`; no manual sleeps.

Change cache writes to **merge, never overwrite**: concatenate new bars with any
existing cached frame, drop duplicate timestamps (keep last), sort by index. A
short fetch must never shrink an existing cache.

`cli.py fetch` gains `--days N`. When present it backfills; when absent it keeps
today's single-page behaviour.

**Constraint:** backfill must use the **public mainnet** client. `cmd_fetch`
already constructs an unauthenticated exchange (`cli.py:30`) and this must not
change. Testnet OHLCV history is sparse and partly synthetic; routing backfill
through the authenticated testnet broker would corrupt every downstream
measurement.

**Backfill spans per timeframe.** Depth is chosen per timeframe, not uniformly —
a year of 1m bars is ~525,000 rows and would dominate scan runtime for no benefit,
because churn reveals itself within hours. Targets: **1h → ~1 year**, **4h → ~2
years**, **3m → ~30 days**, **1m → ~7 days**. The slow timeframes carry the
walk-forward validation; the fast ones only have to expose churn.

**Tests:** a fake exchange serving fixed pages asserts that the cursor advances,
that duplicates are dropped, that pre-existing cached rows survive a merge, and
that a no-progress response terminates the loop.

---

## A2. One simulation path

**New module:** `backtest/simulate.py`. **Deleted:** `backtest/engine.py`.

```
simulate(df, strategy, risk_config, cash, fee, warmup) -> BacktestResult
```

It wires `PaperBroker`, `RiskManager`, `RiskState`, a silent `Notifier`, and an
in-memory `MemoryTradeLog`, drives `Trader.run_replay`, and returns the same
`BacktestResult` shape (`equity`, `trades`, `final_equity`) that
`backtest/metrics.py` and `backtest/walkforward.py` already consume. Both
`cmd_backtest` and `walk_forward` call it.

After this change, backtest / walk-forward / paper / live all run the same rules
through `Trader.step`. The divergence cannot silently return, because there is
only one implementation.

**Required change to `Trader.run_replay`.** It currently returns `None` and
discards per-bar equity (`trader.py:96-99`), but `max_drawdown` and
`sharpe_ratio` consume a per-bar `pd.Series` (`backtest/metrics.py:9-19`).
`CsvTradeLog` records equity only per fill, which cannot produce a drawdown
curve. `run_replay` must therefore collect `broker.equity(close_i)` for each bar
and return it as a `pd.Series` indexed by candle timestamp. Existing callers
that ignore the return value are unaffected.

**`MemoryTradeLog`** subclasses `TradeLog` and appends each recorded fill dict to
a list. This yields trade count, fee totals, and round-trip pairing for free, and
the rows are the same shape `report.summarize` already parses.

**Expected and intended consequence:** every previously reported backtest number
changes. Risk sizing trades a fraction of what all-in traded, and stops plus the
kill-switch now fire during replays. Prior headline returns are not comparable to
post-change ones. This is the correction, not a regression.

---

## A3. Bounded lookback

Both simulators pass a growing slice `df.iloc[:i+1]`, and every strategy
recomputes its rolling indicator across the entire slice while consuming only
`.iloc[-1]`. Cost is quadratic in bar count. At 500 bars this is invisible; after
A1 backfills to roughly 9,000 1h bars, multiplied by the parameter grid and the
walk-forward folds, a scan performs billions of strategy evaluations.

Fix: each `Strategy` exposes a `lookback` property —

| Strategy | `lookback` |
|---|---|
| `MACrossover` | `slow + 1` — `generate` reads the *previous* bar's averages (`ma_crossover.py:18`), so `slow` bars alone are one short |
| `RSIReversion` | `period + 1` — `close.diff()` consumes a bar |
| `TrendFilter` | `max(inner.lookback, sma_period)` |
| `Strategy` (base) | `200` — covers the default `--trend-sma`, so a strategy that forgets to override is still correct, only slower |

`run_replay` passes a bounded tail window of `lookback + 10` bars instead of the
full prefix. The 10-bar buffer absorbs the `diff()`/`clip()` operations that
consume one or two extra bars ahead of a rolling window. Because indicators read
only the last value of a rolling window, this leaves results unchanged.

**Test:** bounded and unbounded runs produce identical equity curves and trade
lists on a sample dataset. This is the test that makes the optimization safe.

---

## A4. Scan harness

**New module:** `backtest/scan.py`. **New subcommand:** `cli.py scan`.

For each (strategy × timeframe × parameter set): run `simulate` over the full
sample, and `walk_forward` for the in-sample/out-of-sample gap. Emit one row per
configuration:

`strategy, timeframe, bars, days, trades, trades/day, net return, edge vs buy &
hold, max drawdown, worst cumulative loss, fee drag, OOS gap, verdict`

`fee drag` is total fees divided by the absolute gross P&L — the fraction of the
strategy's activity consumed by costs. When gross P&L is exactly zero (no
round-trips completed), fee drag is reported as infinite and the configuration
fails the fee-drag gate; a run that paid fees and moved nothing is the worst
case, not an undefined one.

### Gates

These thresholds are fixed **now, before any results are seen**. Tuning them
after looking at output would turn "survives walk-forward" into post-hoc
rationalization, which is the exact failure the gate exists to prevent. Changing
a threshold later is allowed, but only as a deliberate, recorded amendment to
this spec.

| Gate | Threshold | Failure label |
|---|---|---|
| Sample size | `trades >= 20` | `too-few-trades` |
| Churn | `trades_per_day <= 6` | `churn` |
| Fee drag | `fees <= 30%` of gross P&L | `fee-drag` |

### The kill-switch is not a gate

An earlier draft gated on "the kill-switch never tripped". That is wrong, and the
reason matters enough to record.

`RiskState.realized_pnl` accumulates across a whole run and never resets
(`risk/manager.py:22-26`), and `RiskManager.approve` halts once
`−realized_pnl / starting_equity >= max_session_loss` (0.10 by default,
`manager.py:55-57`). That threshold is *session*-scoped and latching: once a run
crosses it, approval is denied for every remaining bar. Applied to a multi-year
historical sample, any configuration active enough to clear the 20-trade minimum
will eventually accumulate a 10% losing stretch — and then trade no more, even if
it would have recovered and finished up.

Used as a gate, this fails nearly every actively-trading configuration, and the
scan reports "nothing is worth soaking" as a finding when the truth is a
mis-scaled threshold. That is precisely the trap the gates exist to avoid.

The kill-switch is a live-operations control: halt and call a human. It is not a
config-selection criterion, and it cannot be both at these thresholds.

**Therefore:** `scan` passes `simulate` a risk config with the kill-switch
thresholds effectively disabled (`max_drawdown = 1.0`, `max_session_loss = 1.0`)
while keeping risk-based **sizing** and **stop-losses** — which are the parts that
actually diverged from the old all-in engine. The one-path property is unaffected:
the code path is identical, only a config value differs, and config is already a
parameter.

Drawdown and worst cumulative realized loss are reported as **ranking columns**,
not gates, so a config that would have tripped a live halt is visible rather than
erased. `backtest` and `walkforward` use the same scan config by default and gain
a `--kill-switch` flag for the separate, deliberate question "would this have
halted?".

This also removes a second-order distortion: with the halt live, a walk-forward
fold could latch off partway through, and its out-of-sample return would measure
"halted early" rather than true edge.
| Fold coverage | at least 2 walk-forward folds traded | `insufficient-folds` |
| Stability | fails unless a **majority** of traded folds were positive out-of-sample (`folds_positive_oos * 2 > folds_traded`) | `unstable` |
| Losing | fails when `net_return <= 0` | `losing` |

A configuration failing any gate is reported as FAIL with its label; it is not
silently dropped, because knowing *why* a configuration was rejected is the
output's main value. Survivors rank by **edge vs buy & hold, net of fees**,
descending.

### Amendment — 2026-07-23: `losing` gate added after the first real scan

The "Gates" section above states thresholds are fixed before any results are
seen, and that changing one afterward is post-hoc rationalization. This
amendment happens **after** the first real scan ran. The row was added to the
table above so the gate list stays a single source of truth, but its
provenance is disclosed here, not presented as if it had been part of the
original pre-committed set.

**What changed:** a sixth gate, `net_return > 0`, was added to `verdict`, by
owner decision. Failure label: `losing`. It is checked last, after `overfit`
— a configuration is reported by its most fundamental defect first (too few
trades, churn, cost, thin folds, curve-fitting), and only labelled `losing`
if it is otherwise sound and still fails to make money.

**Why this does not reopen the pre-commitment question:** the failure the
pre-commitment guards against is *loosening* a threshold once it is
inconvenient — moving a boundary so a configuration that would have failed
now passes. This is the opposite: a strict tightening. A tightening cannot
manufacture a passing configuration; it can only turn a PASS into a FAIL. The
mechanism the gates exist to prevent does not apply here.

**Why it was needed:** the first real scan surfaced `1h rsi+trend` — edge
`+43.51%`, `net_return -1.16%`. It "beat" buy-and-hold only because BTC fell
roughly 44% over the sample period, so it merely lost money more slowly than
holding did. Ranking survivors by `edge` alone would have crowned a
money-losing configuration as "best," and this scan's output feeds a decision
to run a bot with real money. A configuration that loses money is not
deployable however well it beat holding.

**Effect on the delivered result: none.** 0 of 16 configurations cleared the
original five gates, so none reaches the sixth. The 0/16 finding stands
unchanged; `losing` governs future scans, not this one.

### Amendment — 2026-07-24: gate 5 respecified from `overfit` to `unstable`

Gate 5 previously read `avg_is > 0 and avg_oos < 0` under the label `overfit`.
It has been replaced by a fold-stability rule: a configuration fails unless a
**majority of its traded folds were positive out-of-sample**. Label: `unstable`.
By owner decision, after the measurement recorded in
`docs/research/2026-07-24-overfit-gate-is-measuring-window-drift.md`.

**Why the old rule could not do its job.** The pin-params fix (`12e0e61`) made
`scan_one` hand `walk_forward` a **one-entry** grid, so every gate would judge
the same configuration the headline metrics were measured on. That was correct,
but it removed the thing the `overfit` label named: with a single grid entry the
optimizer selects nothing, so nothing is fitted and nothing can be over-fitted.
`avg_is` and `avg_oos` then compare one fixed strategy across two sets of
windows rather than a fitted choice against fresh data.

Worse, the folds overlap by construction (`backtest/walkforward.py:43-45`):
fold *k+1*'s in-sample slice **is** fold *k*'s out-of-sample slice. So on a
pinned row with all folds valid, the reported gap reduces exactly to

```
oos_gap = (first_window_return - last_window_return) / n_splits
```

verified to seven digits against BTC/USDT 4h. That is window drift, not
curve-fitting. A gate label must not claim a property it cannot measure.

**Why a fold-count rule instead.** For a pinned configuration — which is what a
soak test actually runs — the answerable question is temporal stability: did
this one fixed setup make money out-of-sample in more windows than it lost in?
The count survives the overlap problem, because each fold's out-of-sample
window is judged on its own rather than averaged against its neighbours. Ties
fail: half the folds positive is a coin flip, not evidence. Only folds that
actually traded are counted; an invalid or non-trading fold is absent evidence,
not positive evidence.

**Effect on the delivered result: it changes it, from 1/16 to 0/16.** This is
the first amendment that does. `4h ma+trend` — the single configuration that
passed after the pin-params fix — has 2 traded folds, one positive
(`+1.29%`) and one negative (`−0.99%`) out-of-sample, on **4 out-of-sample
trades in total**. Its `avg_oos` of `+0.15%` was the average of those two
numbers. Under the stability rule it fails, and no configuration passes.

**Why this does not reopen the pre-commitment question.** Same reasoning as the
`losing` amendment, and it applies with more force here: this is a strict
tightening, so it can only turn a PASS into a FAIL. The pre-commitment exists to
stop a threshold being *loosened* until something passes. Nothing here makes a
failing configuration pass; the change removes the project's only passing
result. That direction is the evidence that the gates are being read honestly
rather than negotiated with.

**What is deliberately not changed.** `cli.py walkforward` still re-optimizes
over the full grid. "Does selecting parameters on this strategy family hold up
out-of-sample?" is a real and separate question, and that command remains the
place it is answered. `avg_is`/`avg_oos` remain as reported columns — they no
longer gate anything, and the scan's docstrings now state that they measure
window drift on a pinned row.

### Optimizer gate

`walk_forward` currently selects best-in-sample parameters by return alone
(`backtest/walkforward.py:42-44`). Once simulation routes through the Trader,
risk sizing and the kill-switch make it possible for a degenerate,
barely-trading parameter set to post the best in-sample return. The minimum-trade
gate must therefore also apply **inside the optimizer**: grid entries with fewer
than `min_trades_fold = 5` in-sample trades are rejected before "best" is chosen.
If no entry qualifies, the fold reports no valid parameters rather than crowning
a near-inactive winner.

The fold minimum is 5 rather than the sample-wide 20 because a fold is a fraction
of the sample; requiring 20 per fold would reject every fold on any realistic
dataset. It is a filter against inactivity, not a claim of significance.

Without this, curve-fitting-by-inactivity enters through the optimizer and the
final ranking never sees it.

---

## A5. Testing

Test-driven, matching the existing suite's conventions. All tests use
deterministic synthetic price series and a fake exchange; none touch the network.

- Backfill: cursor advance, duplicate removal, merge preserving old rows,
  no-progress termination.
- Bounded lookback: identical results to the unbounded path.
- `simulate`: reproduces known `Trader` behaviour on a hand-built scenario,
  including a stop-loss exit and a kill-switch halt.
- Each gate: fires on a row crafted to violate exactly that gate, and does not
  fire on a row that satisfies it.
- Optimizer gate: a grid where the highest-return entry is below the trade
  minimum results in that entry being rejected.
- Scan: survivors ordered by edge, failures labelled.

---

## Risks

- **Scan runtime.** Bounded lookback mitigates the quadratic cost, but a wide
  grid across several timeframes may still take minutes. Mitigation: keep the
  grid small, print elapsed time per configuration.
- **Invalidated history.** All previously reported backtest numbers become
  incomparable. Intended, but it means no prior result can be cited after this
  lands.
- **Backfill depth.** Bounded by what the exchange actually serves and by rate
  limits. The implementation reports the span it achieved; no target span is
  promised in advance.
- **Gates may reject everything.** It is a real possible outcome that no
  configuration passes. That is a finding — it means no tested configuration is
  worth soaking — not a bug to be fixed by loosening thresholds.

## Success criteria

1. `fetch --days N` accumulates history across repeated runs without data loss.
2. `backtest`, `walkforward`, and paper `run` produce results from one shared
   code path.
3. `scan` prints a ranked table where every rejected configuration carries a
   named failure reason, and the 1m MA-crossover configuration that churned in
   the live ledger is rejected by the churn or fee-drag gate.
