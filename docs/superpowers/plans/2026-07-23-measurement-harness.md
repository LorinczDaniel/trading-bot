# Measurement Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the bot's backtest predict its live behaviour, on enough data to matter, and rank configurations with pre-committed fee-inclusive gates.

**Architecture:** Retire `backtest/engine.py` and route `backtest`, `walkforward`, and paper `run` through one simulation path (`Trader.run_replay` over `PaperBroker`), so backtest and live share one set of rules by construction. Add paginated, merging historical backfill so walk-forward has enough bars to be meaningful, and a bounded strategy lookback so the growing-slice replay does not go quadratic once data grows. On top of that, add a `scan` command that ranks configurations and names the reason for every rejection.

**Tech Stack:** Python 3.12, pandas 3.0, numpy 2.5, ccxt, pytest, parquet cache.

**Spec:** `docs/superpowers/specs/2026-07-23-measurement-harness-design.md`

## Global Constraints

- **ccxt import boundary:** only `broker/ccxt_broker.py` and `cli.py` may import `ccxt`. `data/provider.py` must stay ccxt-free — it receives an exchange object.
- **Backfill uses the public mainnet client.** `cmd_fetch` builds an unauthenticated exchange (`cli.py:30`); this must not change. Testnet OHLCV is sparse and partly synthetic.
- **No `pandas-ta`** — its `numpy.NaN` import breaks on numpy 2.x. Indicators are hand-rolled with pandas rolling windows.
- **Gate thresholds are fixed by the spec** and must be implemented exactly: `min trades = 20`, `max trades/day = 6`, `max fee drag = 0.30`, `min folds traded = 2`, `min_trades_fold = 5`, overfit when `avg_is > 0 and avg_oos < 0`. Do not tune these to make results look better.
- **The kill-switch is not a gate.** `scan` runs with `max_drawdown = 1.0` and `max_session_loss = 1.0` while keeping risk-based sizing and stops.
- **Backfill depth per timeframe:** 1h → ~1 year, 4h → ~2 years, 3m → ~30 days, 1m → ~7 days.
- **Running anything:** `wsl -e bash -lc 'cd ~/personal/trading_bot && source .venv/bin/activate && <cmd>'`
- **TDD:** every task writes a failing test first, watches it fail, then implements. Commit at the end of each task.

## File Structure

| File | Responsibility |
|---|---|
| `data/provider.py` (modify) | Paginated backfill + merge-not-overwrite cache writes |
| `strategies/base.py` (modify) | `Strategy.lookback` contract |
| `strategies/ma_crossover.py`, `rsi_reversion.py`, `trend_filter.py` (modify) | Per-strategy `lookback` |
| `trader.py` (modify) | `run_replay` returns per-bar equity; bounded window |
| `tradelog.py` (modify) | `MemoryTradeLog` in-memory sink |
| `backtest/simulate.py` (create) | The single simulation entry point + `BacktestResult` |
| `backtest/engine.py` (delete) | Replaced by `simulate.py` |
| `backtest/walkforward.py` (modify) | Runs on `simulate`; optimizer-level trade gate |
| `backtest/scan.py` (create) | Churn/cost metrics, gates, scan orchestration |
| `cli.py` (modify) | `fetch --days`, `backtest --kill-switch`, `scan` |

---

### Task 1: Paginated backfill

**Files:**
- Modify: `data/provider.py`
- Test: `tests/test_provider.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `timeframe_to_ms(timeframe: str) -> int` and `MarketDataProvider.backfill(symbol: str, timeframe: str = "1h", days: int = 365, page_limit: int = 1000, now_ms: int | None = None) -> pd.DataFrame`. The returned frame is timestamp-indexed, sorted, de-duplicated. `now_ms` exists purely so tests can pin the clock.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_provider.py`:

```python
from data.provider import MarketDataProvider, timeframe_to_ms

HOUR_MS = 3_600_000


def _bars(start_ms, count, step_ms=HOUR_MS):
    """Synthetic OHLCV rows: [ts, open, high, low, close, volume]."""
    return [[start_ms + i * step_ms, 100.0, 101.0, 99.0, 100.0 + i, 1.0]
            for i in range(count)]


class FakePagingExchange:
    """Serves bars from an in-memory list, honouring `since` and `limit`."""

    def __init__(self, bars):
        self.bars = bars
        self.since_calls = []

    def fetch_ohlcv(self, symbol, timeframe="1h", since=None, limit=1000):
        self.since_calls.append(since)
        page = [b for b in self.bars if since is None or b[0] >= since]
        return page[:limit]


def test_timeframe_to_ms_known_values():
    assert timeframe_to_ms("1m") == 60_000
    assert timeframe_to_ms("1h") == HOUR_MS
    assert timeframe_to_ms("4h") == 4 * HOUR_MS


def test_timeframe_to_ms_rejects_unknown():
    with pytest.raises(ValueError):
        timeframe_to_ms("7s")


def test_backfill_pages_past_the_limit(tmp_path):
    now = 3000 * HOUR_MS
    start = now - 2500 * HOUR_MS
    ex = FakePagingExchange(_bars(start, 2500))
    prov = MarketDataProvider(ex, cache_dir=str(tmp_path))

    df = prov.backfill("BTC/USDT", "1h", days=200, page_limit=1000, now_ms=now)

    assert len(df) == 2500                      # not capped at one page
    assert len(ex.since_calls) >= 3             # 2500 bars needs >= 3 pages
    assert df.index.is_monotonic_increasing
    assert not df.index.has_duplicates


def test_backfill_stops_when_exchange_makes_no_progress(tmp_path):
    """An exchange that ignores `since` must not loop forever."""
    now = 100 * HOUR_MS

    class StuckExchange:
        def __init__(self):
            self.calls = 0

        def fetch_ohlcv(self, symbol, timeframe="1h", since=None, limit=1000):
            self.calls += 1
            return _bars(0, 3)   # always the same three ancient bars

    ex = StuckExchange()
    prov = MarketDataProvider(ex, cache_dir=str(tmp_path))
    df = prov.backfill("BTC/USDT", "1h", days=5, page_limit=1000, now_ms=now)

    assert ex.calls <= 2         # detected no progress and gave up
    assert len(df) == 3


def test_backfill_on_empty_page_returns_what_it_has(tmp_path):
    class EmptyExchange:
        def fetch_ohlcv(self, symbol, timeframe="1h", since=None, limit=1000):
            return []

    prov = MarketDataProvider(EmptyExchange(), cache_dir=str(tmp_path))
    df = prov.backfill("BTC/USDT", "1h", days=5, now_ms=100 * HOUR_MS)
    assert df.empty
```

Add `import pytest` to the top of `tests/test_provider.py` if it is not already there.

- [ ] **Step 2: Run test to verify it fails**

Run: `wsl -e bash -lc 'cd ~/personal/trading_bot && source .venv/bin/activate && pytest tests/test_provider.py -v'`

Expected: FAIL with `ImportError: cannot import name 'timeframe_to_ms' from 'data.provider'`

- [ ] **Step 3: Write minimal implementation**

In `data/provider.py`, add `import time` at the top and insert after `OHLCV_COLUMNS`:

```python
_TIMEFRAME_MS = {
    "1m": 60_000, "3m": 180_000, "5m": 300_000, "15m": 900_000,
    "30m": 1_800_000, "1h": 3_600_000, "2h": 7_200_000, "4h": 14_400_000,
    "6h": 21_600_000, "12h": 43_200_000, "1d": 86_400_000,
}


def timeframe_to_ms(timeframe: str) -> int:
    """Bar duration in milliseconds — used to advance the backfill cursor."""
    try:
        return _TIMEFRAME_MS[timeframe]
    except KeyError:
        raise ValueError(
            f"unsupported timeframe: {timeframe!r} (known: {sorted(_TIMEFRAME_MS)})"
        ) from None
```

Then add this method to `MarketDataProvider`:

```python
    def backfill(self, symbol: str, timeframe: str = "1h", days: int = 365,
                 page_limit: int = 1000, now_ms: int | None = None) -> pd.DataFrame:
        """Page backwards-to-forwards through history, one exchange page at a time.

        A single `fetch_ohlcv` call is capped (1000 bars at Binance), so anything
        longer than that must be assembled from consecutive pages. The cursor
        advances past the last bar of each page; if it fails to advance the
        exchange is ignoring `since` and we stop rather than loop forever.
        """
        bar_ms = timeframe_to_ms(timeframe)
        now = now_ms if now_ms is not None else int(time.time() * 1000)
        cursor = now - days * 86_400_000
        rows: list = []

        while cursor < now:
            page = self.exchange.fetch_ohlcv(
                symbol, timeframe=timeframe, since=cursor, limit=page_limit
            )
            if not page:
                break
            rows.extend(page)
            next_cursor = page[-1][0] + bar_ms
            if next_cursor <= cursor:
                break          # exchange clamped `since`; no progress to be made
            cursor = next_cursor

        if not rows:
            return _to_dataframe([])
        df = _to_dataframe(rows)
        return df[~df.index.duplicated(keep="last")].sort_index()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `wsl -e bash -lc 'cd ~/personal/trading_bot && source .venv/bin/activate && pytest tests/test_provider.py -v'`

Expected: PASS, all tests in the file green.

- [ ] **Step 5: Commit**

```bash
wsl -e bash -lc 'cd ~/personal/trading_bot && git add data/provider.py tests/test_provider.py && git commit -m "feat: paginated OHLCV backfill with no-progress termination"'
```

---

### Task 2: Cache merges instead of overwriting

**Files:**
- Modify: `data/provider.py`
- Test: `tests/test_provider.py`

**Interfaces:**
- Consumes: `backfill` from Task 1.
- Produces: `MarketDataProvider._write_cache(symbol: str, timeframe: str, df: pd.DataFrame) -> pd.DataFrame`, used by both `fetch` and `backfill`. Returns the merged frame that was persisted.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_provider.py`:

```python
def test_cache_merge_keeps_older_bars(tmp_path):
    """A short fetch must never shrink an existing cache."""
    now = 3000 * HOUR_MS
    old = FakePagingExchange(_bars(now - 10 * HOUR_MS, 10))
    prov = MarketDataProvider(old, cache_dir=str(tmp_path))
    prov.backfill("BTC/USDT", "1h", days=1, now_ms=now)

    # a later, shorter fetch covering only the last 3 bars
    recent = FakePagingExchange(_bars(now - 3 * HOUR_MS, 3))
    prov2 = MarketDataProvider(recent, cache_dir=str(tmp_path))
    prov2.backfill("BTC/USDT", "1h", days=1, now_ms=now)

    merged = prov2.load_cached("BTC/USDT", "1h")
    assert len(merged) == 10                     # nothing lost
    assert merged.index.is_monotonic_increasing
    assert not merged.index.has_duplicates


def test_cache_merge_adds_new_bars(tmp_path):
    now = 3000 * HOUR_MS
    first = FakePagingExchange(_bars(now - 10 * HOUR_MS, 5))
    MarketDataProvider(first, cache_dir=str(tmp_path)).backfill(
        "BTC/USDT", "1h", days=1, now_ms=now)

    second = FakePagingExchange(_bars(now - 6 * HOUR_MS, 6))  # 1 overlap + 5 new
    MarketDataProvider(second, cache_dir=str(tmp_path)).backfill(
        "BTC/USDT", "1h", days=1, now_ms=now)

    merged = MarketDataProvider(None, cache_dir=str(tmp_path)).load_cached("BTC/USDT", "1h")
    assert len(merged) == 10
```

- [ ] **Step 2: Run test to verify it fails**

Run: `wsl -e bash -lc 'cd ~/personal/trading_bot && source .venv/bin/activate && pytest tests/test_provider.py::test_cache_merge_keeps_older_bars -v'`

Expected: FAIL — `backfill` does not persist yet, so `load_cached` raises `FileNotFoundError`.

- [ ] **Step 3: Write minimal implementation**

In `data/provider.py`, add the `_write_cache` method and route both writers through it:

```python
    def _write_cache(self, symbol: str, timeframe: str, df: pd.DataFrame) -> pd.DataFrame:
        """Merge `df` into any existing cache and persist. Never shrinks the file:
        history accumulates across runs, so a short fetch cannot destroy a long
        backfill."""
        path = self._cache_path(symbol, timeframe)
        os.makedirs(self.cache_dir, exist_ok=True)
        if os.path.exists(path):
            df = pd.concat([pd.read_parquet(path), df])
        df = df[~df.index.duplicated(keep="last")].sort_index()
        df.to_parquet(path)
        return df
```

Replace the body of `fetch` (currently `data/provider.py:23-28`) with:

```python
    def fetch(self, symbol: str, timeframe: str = "1h", limit: int = 500) -> pd.DataFrame:
        raw = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        return self._write_cache(symbol, timeframe, _to_dataframe(raw))
```

And change the last two lines of `backfill` from returning the de-duplicated frame directly to persisting it:

```python
        if not rows:
            return _to_dataframe([])
        return self._write_cache(symbol, timeframe, _to_dataframe(rows))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `wsl -e bash -lc 'cd ~/personal/trading_bot && source .venv/bin/activate && pytest tests/test_provider.py -v'`

Expected: PASS. Task 1's `test_backfill_pages_past_the_limit` still passes because `_write_cache` returns the merged frame.

- [ ] **Step 5: Commit**

```bash
wsl -e bash -lc 'cd ~/personal/trading_bot && git add data/provider.py tests/test_provider.py && git commit -m "feat: cache writes merge instead of overwriting"'
```

---

### Task 3: `fetch --days` CLI wiring

**Files:**
- Modify: `cli.py:28-33` (`cmd_fetch`), `cli.py:290-294` (fetch parser)
- Test: manual smoke only (this task is argument plumbing over already-tested code)

**Interfaces:**
- Consumes: `MarketDataProvider.backfill` from Tasks 1-2.
- Produces: `fetch --days N` on the CLI.

- [ ] **Step 1: Replace `cmd_fetch`**

Replace `cli.py:28-33` with:

```python
def cmd_fetch(args):
    settings = load_settings()
    # Public mainnet client on purpose: testnet OHLCV history is sparse and
    # partly synthetic, and would poison every backtest built on it.
    exchange = getattr(ccxt, settings.exchange_id)({"enableRateLimit": True})
    prov = MarketDataProvider(exchange)
    if args.days:
        df = prov.backfill(args.symbol, args.timeframe, days=args.days)
        if df.empty:
            print(f"No candles returned for {args.symbol} {args.timeframe}.")
            return
        print(f"Backfilled {len(df)} candles for {args.symbol} {args.timeframe} "
              f"({df.index[0]} -> {df.index[-1]}); cached.")
        return
    df = prov.fetch(args.symbol, args.timeframe, args.limit)
    print(f"Fetched {len(df)} candles for {args.symbol} {args.timeframe}; cached.")
```

- [ ] **Step 2: Add the `--days` argument**

After `f.add_argument("--limit", type=int, default=500)` (`cli.py:293`) add:

```python
    f.add_argument("--days", type=int, default=None,
                   help="backfill this many days of history (paginated, merges into "
                        "the cache). Suggested depth: 1h=365, 4h=730, 3m=30, 1m=7")
```

- [ ] **Step 3: Verify the whole suite still passes**

Run: `wsl -e bash -lc 'cd ~/personal/trading_bot && source .venv/bin/activate && pytest'`

Expected: PASS, 109+ tests.

- [ ] **Step 4: Smoke-test the real backfill**

Run: `wsl -e bash -lc 'cd ~/personal/trading_bot && source .venv/bin/activate && python cli.py fetch --symbol BTC/USDT --timeframe 1h --days 365'`

Expected: a line reporting several thousand candles and a span of roughly a year. Record the actual span — the spec promises the achieved span, not a hoped-for one. If the exchange serves less, that is the honest number.

- [ ] **Step 5: Commit**

```bash
wsl -e bash -lc 'cd ~/personal/trading_bot && git add cli.py && git commit -m "feat: fetch --days backfills paginated history"'
```

---

### Task 4: `Strategy.lookback`

**Files:**
- Modify: `strategies/base.py`, `strategies/ma_crossover.py`, `strategies/rsi_reversion.py`, `strategies/trend_filter.py`
- Test: `tests/test_strategy_ma.py`, `tests/test_strategy_rsi.py`, `tests/test_trend_filter.py`

**Interfaces:**
- Consumes: nothing.
- Produces: every `Strategy` exposes `lookback: int` — the minimum number of trailing bars needed to produce a correct signal. Task 6 consumes it.

Note the exact values. `MACrossover.generate` reads `fast.iloc[-2]` (`strategies/ma_crossover.py:18`), so it needs `slow + 1` bars, not `slow`. `RSIReversion._rsi` calls `close.diff()`, which consumes one bar, so it needs `period + 1`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_strategy_ma.py`:

```python
def test_ma_lookback_covers_the_previous_bar():
    # generate() reads fast.iloc[-2], so slow bars alone are not enough
    assert MACrossover(fast=10, slow=30).lookback == 31
```

Append to `tests/test_strategy_rsi.py`:

```python
def test_rsi_lookback_accounts_for_diff():
    # _rsi() calls close.diff(), which consumes one bar
    assert RSIReversion(period=14).lookback == 15
```

Append to `tests/test_trend_filter.py`:

```python
from strategies.ma_crossover import MACrossover
from strategies.trend_filter import TrendFilter


def test_trend_filter_lookback_is_the_larger_requirement():
    assert TrendFilter(MACrossover(10, 30), sma_period=200).lookback == 200
    assert TrendFilter(MACrossover(10, 300), sma_period=200).lookback == 301


def test_base_strategy_has_a_safe_default_lookback():
    from strategies.base import Strategy
    assert Strategy().lookback >= 200
```

Ensure each test file imports the class it references.

- [ ] **Step 2: Run tests to verify they fail**

Run: `wsl -e bash -lc 'cd ~/personal/trading_bot && source .venv/bin/activate && pytest tests/test_strategy_ma.py tests/test_strategy_rsi.py tests/test_trend_filter.py -v'`

Expected: FAIL with `AttributeError: 'MACrossover' object has no attribute 'lookback'`

- [ ] **Step 3: Write the implementations**

`strategies/base.py` — replace the `Strategy` class:

```python
class Strategy:
    #: Minimum trailing bars needed for a correct signal. The replay loop uses
    #: this to pass a bounded window instead of the whole history. The default is
    #: deliberately generous (it covers the default --trend-sma of 200) so a
    #: strategy that forgets to override is merely slow, never wrong.
    lookback = 200

    def generate(self, df: pd.DataFrame) -> Signal:
        raise NotImplementedError
```

`strategies/ma_crossover.py` — add to `MACrossover`:

```python
    @property
    def lookback(self) -> int:
        return self.slow + 1   # generate() reads the previous bar's averages too
```

`strategies/rsi_reversion.py` — add to `RSIReversion`:

```python
    @property
    def lookback(self) -> int:
        return self.period + 1   # close.diff() consumes one bar
```

`strategies/trend_filter.py` — add to `TrendFilter`:

```python
    @property
    def lookback(self) -> int:
        return max(self.inner.lookback, self.sma_period)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `wsl -e bash -lc 'cd ~/personal/trading_bot && source .venv/bin/activate && pytest tests/test_strategy_ma.py tests/test_strategy_rsi.py tests/test_trend_filter.py -v'`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
wsl -e bash -lc 'cd ~/personal/trading_bot && git add strategies/ tests/test_strategy_ma.py tests/test_strategy_rsi.py tests/test_trend_filter.py && git commit -m "feat: strategies declare their lookback requirement"'
```

---

### Task 5: `run_replay` returns a per-bar equity curve

**Files:**
- Modify: `trader.py:96-99`
- Test: `tests/test_trader.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `Trader.run_replay(df: pd.DataFrame, warmup: int = 50) -> pd.Series` — equity after each replayed bar, indexed by that bar's timestamp. Tasks 8-13 depend on this; `backtest/metrics.py` consumes exactly this shape.

Why this is needed: `max_drawdown` and `sharpe_ratio` (`backtest/metrics.py:9-19`) require a per-bar series. `CsvTradeLog` records equity only per fill, which cannot produce a drawdown curve.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_trader.py`:

```python
def test_run_replay_returns_per_bar_equity():
    df = pd.DataFrame({"close": [100.0, 101.0, 102.0, 103.0]})
    broker = PaperBroker(cash=1000.0, fee=0.0)
    trader = Trader(
        "BTC/USDT", broker, HoldStrategy(), RiskManager(RiskConfig()),
        RiskState(1000.0), Notifier(echo=False), fee=0.0,
    )

    equity = trader.run_replay(df, warmup=1)

    assert isinstance(equity, pd.Series)
    assert len(equity) == 3                      # bars 1, 2, 3 — warmup skips bar 0
    assert list(equity.index) == [1, 2, 3]
    assert all(v == pytest.approx(1000.0) for v in equity)   # never traded
```

Add a `HoldStrategy` helper near the top of `tests/test_trader.py` if the file does not already define one:

```python
class HoldStrategy(Strategy):
    lookback = 1

    def generate(self, df):
        return Signal("HOLD")
```

Make sure `tests/test_trader.py` imports `pandas as pd`, `pytest`, `Strategy`, `Signal`, `PaperBroker`, `Trader`, `RiskManager`, `RiskConfig`, `RiskState`, and `Notifier`.

- [ ] **Step 2: Run test to verify it fails**

Run: `wsl -e bash -lc 'cd ~/personal/trading_bot && source .venv/bin/activate && pytest tests/test_trader.py::test_run_replay_returns_per_bar_equity -v'`

Expected: FAIL with `AssertionError` — `run_replay` currently returns `None`.

- [ ] **Step 3: Write the implementation**

Replace `run_replay` (`trader.py:96-99`) with:

```python
    def run_replay(self, df: pd.DataFrame, warmup: int = 50) -> pd.Series:
        """Drive the loop bar-by-bar over historical candles (a paper session).

        Returns equity after each replayed bar. The per-bar curve is what
        drawdown and Sharpe are computed from — the trade ledger only records
        equity at fills, which is too sparse to measure a drawdown.
        """
        equity, index = [], []
        for i in range(warmup, len(df)):
            self.step(df.iloc[: i + 1])
            equity.append(self.broker.equity(float(df["close"].iloc[i])))
            index.append(df.index[i])
        return pd.Series(equity, index=index, dtype="float64")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `wsl -e bash -lc 'cd ~/personal/trading_bot && source .venv/bin/activate && pytest tests/test_trader.py tests/test_integration.py -v'`

Expected: PASS. Existing callers ignore the return value, so nothing else changes.

- [ ] **Step 5: Commit**

```bash
wsl -e bash -lc 'cd ~/personal/trading_bot && git add trader.py tests/test_trader.py && git commit -m "feat: run_replay returns the per-bar equity curve"'
```

---

### Task 6: Bounded lookback window

**Files:**
- Modify: `trader.py` (`run_replay`)
- Test: `tests/test_trader.py`

**Interfaces:**
- Consumes: `Strategy.lookback` (Task 4), `run_replay` (Task 5).
- Produces: no signature change. `run_replay` internally slices a tail window of `strategy.lookback + 10` bars.

Why: the replay passes `df.iloc[:i+1]` and each strategy recomputes its rolling indicator over the whole slice while reading only `.iloc[-1]`. That is quadratic in bar count — invisible at 500 bars, ruinous at the ~9,000 bars Task 3 backfills.

The 10-bar buffer absorbs the `diff()`/`clip()` operations that consume a bar or two ahead of a rolling window.

- [ ] **Step 1: Write the failing test**

The critical property is that bounding changes nothing. Append to `tests/test_trader.py`:

```python
def _replay_unbounded(df, strategy, cash=10_000.0, fee=0.001, warmup=50):
    """Reference implementation: always passes the full prefix."""
    broker = PaperBroker(cash=cash, fee=fee)
    trader = Trader(
        "BTC/USDT", broker, strategy, RiskManager(RiskConfig()),
        RiskState(cash), Notifier(echo=False), fee=fee,
    )
    equity, index = [], []
    for i in range(warmup, len(df)):
        trader.step(df.iloc[: i + 1])
        equity.append(broker.equity(float(df["close"].iloc[i])))
        index.append(df.index[i])
    return pd.Series(equity, index=index, dtype="float64")


def test_bounded_window_matches_unbounded_replay():
    import numpy as np
    from strategies.ma_crossover import MACrossover

    # deterministic wave with enough swings to trigger repeated crossovers
    n = 600
    close = 100 + 10 * np.sin(np.arange(n) / 7.0) + np.arange(n) * 0.02
    df = pd.DataFrame({"close": close})

    expected = _replay_unbounded(df, MACrossover(10, 30))

    broker = PaperBroker(cash=10_000.0, fee=0.001)
    trader = Trader(
        "BTC/USDT", broker, MACrossover(10, 30), RiskManager(RiskConfig()),
        RiskState(10_000.0), Notifier(echo=False), fee=0.001,
    )
    actual = trader.run_replay(df, warmup=50)

    assert len(actual) == len(expected)
    assert actual.to_list() == pytest.approx(expected.to_list())
```

- [ ] **Step 2: Run test to verify it passes for the wrong reason, then fails**

Run: `wsl -e bash -lc 'cd ~/personal/trading_bot && source .venv/bin/activate && pytest tests/test_trader.py::test_bounded_window_matches_unbounded_replay -v'`

Expected: PASS — because `run_replay` is still unbounded, so it trivially equals the reference. This test is a *regression guard* for Step 3, not a red-then-green test. Proceed to Step 3 and confirm it still passes after the change; that is the signal that matters.

- [ ] **Step 3: Write the implementation**

Replace the loop in `run_replay`:

```python
    def run_replay(self, df: pd.DataFrame, warmup: int = 50) -> pd.Series:
        """Drive the loop bar-by-bar over historical candles (a paper session).

        Returns equity after each replayed bar. The per-bar curve is what
        drawdown and Sharpe are computed from — the trade ledger only records
        equity at fills, which is too sparse to measure a drawdown.

        Only the tail of the history is passed to the strategy. Indicators read
        the last value of a rolling window, so a window of `lookback + buffer`
        gives identical signals while keeping the replay linear in bar count
        instead of quadratic.
        """
        window = getattr(self.strategy, "lookback", 200) + 10
        equity, index = [], []
        for i in range(warmup, len(df)):
            start = max(0, i + 1 - window)
            self.step(df.iloc[start : i + 1])
            equity.append(self.broker.equity(float(df["close"].iloc[i])))
            index.append(df.index[i])
        return pd.Series(equity, index=index, dtype="float64")
```

- [ ] **Step 4: Run the full suite to verify nothing changed**

Run: `wsl -e bash -lc 'cd ~/personal/trading_bot && source .venv/bin/activate && pytest'`

Expected: PASS, including `test_bounded_window_matches_unbounded_replay`. If that test now fails, the buffer is too small or a strategy's `lookback` is understated — fix the `lookback`, do not enlarge the buffer to paper over it.

- [ ] **Step 5: Commit**

```bash
wsl -e bash -lc 'cd ~/personal/trading_bot && git add trader.py tests/test_trader.py && git commit -m "perf: bounded lookback window in run_replay (was quadratic in bar count)"'
```

---

### Task 7: `MemoryTradeLog`

**Files:**
- Modify: `tradelog.py`
- Test: `tests/test_tradelog.py`

**Interfaces:**
- Consumes: the existing `TradeLog` base (`tradelog.py:11-19`).
- Produces: `MemoryTradeLog()` with attribute `rows: list[dict]`. Task 8 reads `rows` to derive trade counts and fees without touching disk.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_tradelog.py`:

```python
from tradelog import MemoryTradeLog


def test_memory_tradelog_collects_rows():
    log = MemoryTradeLog()
    log.record_start(1000.0)
    log.record({"side": "buy", "price": 100.0, "fee": 0.1})
    log.record({"side": "sell", "price": 110.0, "fee": 0.11, "realized_pnl": 9.79})

    assert len(log.rows) == 3
    assert log.rows[0]["side"] == "start"
    assert log.rows[0]["equity_after"] == 1000.0
    assert log.rows[2]["realized_pnl"] == 9.79


def test_memory_tradelog_start_is_written_once():
    log = MemoryTradeLog()
    log.record_start(1000.0)
    log.record_start(9999.0)
    assert len(log.rows) == 1
    assert log.rows[0]["equity_after"] == 1000.0


def test_memory_tradelog_copies_the_row():
    """Recording must snapshot, so a caller mutating its dict cannot rewrite history."""
    log = MemoryTradeLog()
    row = {"side": "buy", "price": 100.0}
    log.record(row)
    row["price"] = 999.0
    assert log.rows[0]["price"] == 100.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `wsl -e bash -lc 'cd ~/personal/trading_bot && source .venv/bin/activate && pytest tests/test_tradelog.py -v'`

Expected: FAIL with `ImportError: cannot import name 'MemoryTradeLog' from 'tradelog'`

- [ ] **Step 3: Write the implementation**

Append to `tradelog.py`:

```python
class MemoryTradeLog(TradeLog):
    """In-memory sink for simulation. Backtests need trade counts and fee totals
    but must not touch the ledger directory — a scan runs thousands of sims."""

    def __init__(self):
        self.rows: list[dict] = []

    def record(self, trade: dict) -> None:
        self.rows.append(dict(trade))

    def record_start(self, equity: float, timestamp="") -> None:
        if self.rows:
            return
        self.record({"timestamp": timestamp, "side": "start", "equity_after": equity})
```

- [ ] **Step 4: Run test to verify it passes**

Run: `wsl -e bash -lc 'cd ~/personal/trading_bot && source .venv/bin/activate && pytest tests/test_tradelog.py -v'`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
wsl -e bash -lc 'cd ~/personal/trading_bot && git add tradelog.py tests/test_tradelog.py && git commit -m "feat: MemoryTradeLog in-memory sink for simulation"'
```

---

### Task 8: `simulate()` — the single simulation path

**Files:**
- Create: `backtest/simulate.py`
- Create: `tests/test_simulate.py`

**Interfaces:**
- Consumes: `MemoryTradeLog` (Task 7), `run_replay` returning a series (Tasks 5-6), `PaperBroker`, `Trader`, `RiskManager`/`RiskConfig`/`RiskState`, `Notifier`.
- Produces:
  - `scan_risk_config(risk_per_trade: float = 0.01, stop_loss_pct: float = 0.05) -> RiskConfig` — kill-switch thresholds disabled.
  - `live_risk_config(risk_per_trade: float = 0.01, stop_loss_pct: float = 0.05) -> RiskConfig` — production defaults.
  - `BacktestResult` dataclass: `equity: pd.Series`, `trades: list[dict]`, `final_equity: float`, `fills: list[dict]`.
  - `simulate(df, strategy, risk_config=None, cash=10_000.0, fee=0.001, warmup=50) -> BacktestResult`.

  `trades` entries are `{"entry": float, "exit": float, "pnl": float}` — the same shape `backtest/engine.py` produced, so `backtest/metrics.py` and `walkforward.py` keep working.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_simulate.py`:

```python
import pandas as pd
import pytest

from backtest.simulate import simulate, scan_risk_config, live_risk_config
from strategies.base import Strategy, Signal


class ScriptedStrategy(Strategy):
    """Emits a preset action at specific *index labels*.

    Keyed on the index label rather than len(df) because run_replay passes a
    bounded tail window — positional indices inside the window are not absolute
    bar numbers.
    """

    lookback = 1

    def __init__(self, actions):
        self.actions = actions

    def generate(self, df):
        return Signal(self.actions.get(df.index[-1], "HOLD"))


def test_risk_sized_buy_then_sell():
    # cash 1000, risk 1%, stop 5% -> risk $10 over a $5 stop distance = 2 units.
    # The old all-in engine would have bought 10 units; this is the divergence
    # the whole change exists to remove.
    df = pd.DataFrame({"close": [100.0, 100.0, 100.0, 110.0, 120.0]})
    res = simulate(df, ScriptedStrategy({2: "BUY", 4: "SELL"}),
                   cash=1000.0, fee=0.0, warmup=0)

    assert res.fills[0]["qty"] == pytest.approx(2.0)
    assert res.final_equity == pytest.approx(1040.0)
    assert len(res.trades) == 1
    assert res.trades[0] == pytest.approx({"entry": 100.0, "exit": 120.0, "pnl": 40.0})


def test_equity_curve_covers_every_replayed_bar():
    df = pd.DataFrame({"close": [100.0, 100.0, 100.0, 110.0, 120.0]})
    res = simulate(df, ScriptedStrategy({}), cash=1000.0, fee=0.0, warmup=0)
    assert len(res.equity) == 5
    assert res.equity.iloc[-1] == pytest.approx(1000.0)


def test_no_signals_preserves_cash():
    df = pd.DataFrame({"close": [100.0, 105.0, 110.0]})
    res = simulate(df, ScriptedStrategy({}), cash=500.0, fee=0.0, warmup=0)
    assert res.final_equity == pytest.approx(500.0)
    assert res.trades == []


def test_stop_loss_exits_the_position():
    # buy 2 @ 100 with a stop at 95; bar 3 prints 90 and the stop fires
    df = pd.DataFrame({"close": [100.0, 100.0, 100.0, 90.0]})
    res = simulate(df, ScriptedStrategy({2: "BUY"}), cash=1000.0, fee=0.0, warmup=0)

    assert len(res.trades) == 1
    assert res.trades[0]["pnl"] == pytest.approx(-20.0)
    assert res.fills[-1]["reason"] == "stop-loss hit"
    assert res.final_equity == pytest.approx(980.0)


def test_scan_config_disables_the_kill_switch_but_live_config_halts():
    """The kill-switch is a live-ops control, not a selection criterion.

    A single oversized losing trade puts realized P&L at -10% of starting
    capital. Under live thresholds that latches trading off for the rest of the
    run; under scan thresholds the bot keeps trading and the sample stays usable.
    """
    df = pd.DataFrame({"close": [100.0, 100.0, 100.0, 90.0, 90.0, 100.0]})
    actions = {2: "BUY", 5: "BUY"}

    halting = simulate(df, ScriptedStrategy(actions), cash=1000.0, fee=0.0, warmup=0,
                       risk_config=live_risk_config(risk_per_trade=0.5))
    scanning = simulate(df, ScriptedStrategy(actions), cash=1000.0, fee=0.0, warmup=0,
                        risk_config=scan_risk_config(risk_per_trade=0.5))

    assert len(halting.fills) == 2      # buy + stop-out, then blocked
    assert len(scanning.fills) == 3     # buy + stop-out + the second buy


def test_config_factories_have_the_specified_thresholds():
    scan = scan_risk_config()
    assert scan.max_drawdown == 1.0
    assert scan.max_session_loss == 1.0
    assert scan.risk_per_trade == 0.01      # sizing is unchanged
    assert scan.stop_loss_pct == 0.05       # stops are unchanged

    live = live_risk_config()
    assert live.max_drawdown == 0.20
    assert live.max_session_loss == 0.10
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `wsl -e bash -lc 'cd ~/personal/trading_bot && source .venv/bin/activate && pytest tests/test_simulate.py -v'`

Expected: FAIL with `ModuleNotFoundError: No module named 'backtest.simulate'`

- [ ] **Step 3: Write the implementation**

Create `backtest/simulate.py`:

```python
"""The single simulation path.

Backtest, walk-forward, paper replay, and live trading all run the same rules
through `Trader.step`. This module wires a Trader to a PaperBroker over
historical candles; it deliberately does NOT reimplement sizing, stops, or
fills, because a second implementation is exactly how the old
backtest-vs-live divergence appeared.
"""

from dataclasses import dataclass

import pandas as pd

from broker.paper_broker import PaperBroker
from monitoring.notifier import Notifier
from risk.manager import RiskConfig, RiskManager, RiskState
from tradelog import MemoryTradeLog
from trader import Trader


def scan_risk_config(risk_per_trade: float = 0.01,
                     stop_loss_pct: float = 0.05) -> RiskConfig:
    """Risk config for measurement: sizing and stops intact, kill-switch off.

    RiskState.realized_pnl accumulates for a whole run and never resets, so the
    session-loss halt latches permanently once crossed. Over a multi-year sample
    any config that trades enough to be worth judging will cross it and then
    stop trading — which would make the kill-switch a near-universal reject
    rather than a measure of config quality. It belongs on the live bot.
    """
    return RiskConfig(
        risk_per_trade=risk_per_trade,
        stop_loss_pct=stop_loss_pct,
        max_drawdown=1.0,
        max_session_loss=1.0,
    )


def live_risk_config(risk_per_trade: float = 0.01,
                     stop_loss_pct: float = 0.05) -> RiskConfig:
    """Production thresholds — what the live bot actually runs with."""
    return RiskConfig(
        risk_per_trade=risk_per_trade,
        stop_loss_pct=stop_loss_pct,
        max_drawdown=0.20,
        max_session_loss=0.10,
    )


@dataclass
class BacktestResult:
    equity: pd.Series      # per-bar equity, indexed by candle timestamp
    trades: list           # round-trips: {"entry", "exit", "pnl"}
    final_equity: float
    fills: list            # raw ledger rows, one per buy/sell


def _round_trips(fills: list) -> list:
    """Pair each buy with the sell that closed it."""
    trades, entry = [], None
    for fill in fills:
        if fill["side"] == "buy":
            entry = fill
        elif fill["side"] == "sell" and entry is not None:
            trades.append({
                "entry": float(entry["price"]),
                "exit": float(fill["price"]),
                "pnl": float(fill["realized_pnl"]),
            })
            entry = None
    return trades


def simulate(df: pd.DataFrame, strategy, risk_config: RiskConfig | None = None,
             cash: float = 10_000.0, fee: float = 0.001,
             warmup: int = 50) -> BacktestResult:
    """Replay `strategy` over `df` through the real Trader and return the result."""
    config = risk_config if risk_config is not None else scan_risk_config()
    broker = PaperBroker(cash=cash, fee=fee)
    log = MemoryTradeLog()
    trader = Trader(
        "SIM", broker, strategy, RiskManager(config), RiskState(cash),
        Notifier(echo=False), fee=fee, tradelog=log,
    )
    equity = trader.run_replay(df, warmup=warmup)
    fills = [row for row in log.rows if row.get("side") in ("buy", "sell")]
    final = float(equity.iloc[-1]) if len(equity) else float(cash)
    return BacktestResult(
        equity=equity, trades=_round_trips(fills), final_equity=final, fills=fills,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `wsl -e bash -lc 'cd ~/personal/trading_bot && source .venv/bin/activate && pytest tests/test_simulate.py -v'`

Expected: PASS, all 6 tests.

- [ ] **Step 5: Commit**

```bash
wsl -e bash -lc 'cd ~/personal/trading_bot && git add backtest/simulate.py tests/test_simulate.py && git commit -m "feat: simulate() runs backtests through the real Trader"'
```

---

### Task 9: `backtest` command runs on `simulate`

**Files:**
- Modify: `cli.py:36-60` (`cmd_backtest`), `cli.py:10-11` (imports), `cli.py:296-301` (backtest parser)
- Test: run the command and compare against the old numbers

**Interfaces:**
- Consumes: `simulate`, `scan_risk_config`, `live_risk_config` (Task 8).
- Produces: `backtest` gains `--cash`, `--fee`, `--risk`, `--stop`, `--warmup`, `--kill-switch`.

Sizing now matters to the result, so the sizing knobs must be exposed — previously `backtest` had none because the engine went all-in regardless.

- [ ] **Step 1: Update the imports**

In `cli.py`, replace line 10:

```python
from backtest.engine import run_backtest
```

with:

```python
from backtest.simulate import simulate, scan_risk_config, live_risk_config
```

- [ ] **Step 2: Replace `cmd_backtest`**

Replace `cli.py:36-60` with:

```python
def cmd_backtest(args):
    prov = MarketDataProvider(exchange=None)
    df = prov.load_cached(args.symbol, args.timeframe)
    strategy = build_strategy(
        args.strategy,
        fast=args.fast,
        slow=args.slow,
        rsi_period=args.rsi_period,
        rsi_low=args.rsi_low,
        rsi_high=args.rsi_high,
        trend_sma=args.trend_sma,
    )
    make_config = live_risk_config if args.kill_switch else scan_risk_config
    config = make_config(risk_per_trade=args.risk, stop_loss_pct=args.stop)
    res = simulate(df, strategy, config, cash=args.cash, fee=args.fee, warmup=args.warmup)

    strat_ret = total_return(res.equity)
    hold_ret = buy_and_hold_return(df["close"])
    edge = strat_ret - hold_ret
    fees = sum(float(f.get("fee") or 0.0) for f in res.fills)
    print(f"Strategy:      {args.strategy}")
    print(f"Bars:          {len(res.equity)}")
    print(f"Final equity:  {res.final_equity:,.2f}   (started {args.cash:,.2f})")
    print(f"Total return:  {strat_ret:.2%}")
    print(f"Max drawdown:  {max_drawdown(res.equity):.2%}")
    print(f"Sharpe:        {sharpe_ratio(res.equity):.2f}")
    print(f"Round-trips:   {len(res.trades)}   (fills: {len(res.fills)})")
    print(f"Fees paid:     {fees:,.2f}")
    print(f"Buy & hold:    {hold_ret:.2%}")
    print(f"Edge vs hold:  {edge:+.2%}  ({'BEAT hold' if edge > 0 else 'LOST to hold'})")
    print(f"Kill-switch:   {'live thresholds' if args.kill_switch else 'disabled (measurement mode)'}")
```

- [ ] **Step 3: Add the new arguments**

Replace the backtest parser block (`cli.py:296-301`) with:

```python
    b = sub.add_parser("backtest", help="backtest a strategy on cached candles")
    b.add_argument("--symbol", default="BTC/USDT")
    b.add_argument("--timeframe", default="1h")
    _add_strategy_args(b)
    _add_param_args(b)
    b.add_argument("--cash", type=float, default=10_000.0)
    b.add_argument("--fee", type=float, default=0.001)
    b.add_argument("--risk", type=float, default=0.01, help="fraction of equity risked per trade")
    b.add_argument("--stop", type=float, default=0.05, help="stop-loss distance below entry")
    b.add_argument("--warmup", type=int, default=50)
    b.add_argument("--kill-switch", action="store_true",
                   help="apply the live drawdown/session-loss halts. Off by default: "
                        "they latch permanently over long samples and would truncate "
                        "the measurement rather than describe it.")
    b.set_defaults(func=cmd_backtest)
```

- [ ] **Step 4: Verify the command runs**

Run: `wsl -e bash -lc 'cd ~/personal/trading_bot && source .venv/bin/activate && python cli.py backtest --strategy ma --timeframe 1h'`

Expected: a report printing far fewer round-trips and a much smaller return than the pre-change engine did. **This is the intended correction, not a regression** — risk sizing trades ~20% of what all-in traded, and stops now fire. Old numbers are not comparable.

Then confirm the halting mode differs:

Run: `wsl -e bash -lc 'cd ~/personal/trading_bot && source .venv/bin/activate && python cli.py backtest --strategy ma --timeframe 1h --kill-switch'`

Expected: same or fewer round-trips than the previous run, and the footer reads `live thresholds`.

- [ ] **Step 5: Run the suite and commit**

Run: `wsl -e bash -lc 'cd ~/personal/trading_bot && source .venv/bin/activate && pytest'`

Expected: PASS except `tests/test_engine.py`, which still tests the old engine — Task 10 removes it.

```bash
wsl -e bash -lc 'cd ~/personal/trading_bot && git add cli.py && git commit -m "feat: backtest runs through simulate() with real risk sizing"'
```

---

### Task 10: Walk-forward on `simulate`, with an optimizer trade gate

**Files:**
- Modify: `backtest/walkforward.py`
- Delete: `backtest/engine.py`, `tests/test_engine.py`
- Test: `tests/test_walkforward.py`

**Interfaces:**
- Consumes: `simulate`, `scan_risk_config` (Task 8).
- Produces: `walk_forward(df, make_strategy, param_grid, n_splits=4, initial_cash=10_000.0, fee=0.001, warmup=50, risk_config=None, min_trades_fold=5) -> list[dict]`. Result dicts gain `"valid": bool`; `best_params` is `None` when no grid entry cleared the fold minimum.

Why the optimizer gate: `walkforward.py:42-44` picks best-in-sample parameters by return alone. With risk sizing, a barely-trading parameter set can post the best return on luck. Filtering at ranking time is too late — the curve-fit-by-inactivity entry has already been crowned and carried into the out-of-sample fold.

`min_trades_fold` is 5, not the sample-wide 20, because a fold is a fraction of the sample; 20 per fold would reject every fold on any realistic dataset. It filters inactivity, it does not claim significance.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_walkforward.py`:

```python
import pandas as pd
import numpy as np
import pytest

from backtest.walkforward import walk_forward
from strategies.base import Strategy, Signal


class EveryNBars(Strategy):
    """Alternates buy/sell every `n` bars — trade count is directly controllable."""

    lookback = 1

    def __init__(self, n):
        self.n = n
        self._long = False

    def generate(self, df):
        i = df.index[-1]
        if i % self.n:
            return Signal("HOLD")
        self._long = not self._long
        return Signal("BUY" if self._long else "SELL")


def test_optimizer_rejects_params_below_the_fold_trade_minimum():
    n = 1000
    df = pd.DataFrame({"close": 100 + 10 * np.sin(np.arange(n) / 11.0)})

    # n=400 trades ~ twice per fold; n=7 trades often. Only the active one is valid.
    grid = [400, 7]
    results = walk_forward(df, lambda p: EveryNBars(p), grid, n_splits=2,
                           warmup=10, min_trades_fold=5)

    for r in results:
        if r["valid"]:
            assert r["best_params"] == 7, "the near-inactive param set must be rejected"


def test_fold_with_no_valid_params_is_marked_invalid():
    n = 400
    df = pd.DataFrame({"close": 100 + 10 * np.sin(np.arange(n) / 11.0)})

    results = walk_forward(df, lambda p: EveryNBars(p), [300], n_splits=2,
                           warmup=10, min_trades_fold=5)

    assert all(not r["valid"] for r in results)
    assert all(r["best_params"] is None for r in results)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `wsl -e bash -lc 'cd ~/personal/trading_bot && source .venv/bin/activate && pytest tests/test_walkforward.py -v'`

Expected: FAIL with `KeyError: 'valid'`

- [ ] **Step 3: Write the implementation**

Replace the contents of `backtest/walkforward.py` below the docstring:

```python
import pandas as pd

from backtest.simulate import simulate, scan_risk_config
from backtest.metrics import total_return


def walk_forward(
    df: pd.DataFrame,
    make_strategy,
    param_grid: list,
    n_splits: int = 4,
    initial_cash: float = 10_000.0,
    fee: float = 0.001,
    warmup: int = 50,
    risk_config=None,
    min_trades_fold: int = 5,
) -> list:
    """Walk-forward validation.

    Split the data into n_splits+1 contiguous folds. For each fold k, optimize
    the strategy parameters on fold k (in-sample) by picking the grid entry with
    the best in-sample return, then measure that choice on fold k+1 (out-of-sample).

    The gap between average in-sample and average out-of-sample return is the
    overfitting signal: a strategy that only looks good in-sample is curve-fit.

    Grid entries making fewer than `min_trades_fold` in-sample trades are
    rejected before "best" is chosen. Without that, risk sizing makes it possible
    for a near-inactive parameter set to win the fold on a single lucky trade —
    curve-fitting by inactivity, entering through the optimizer where the final
    ranking would never see it.

    `make_strategy(params)` must build a Strategy from one grid entry.
    """
    config = risk_config if risk_config is not None else scan_risk_config()
    n = len(df)
    fold = n // (n_splits + 1)
    if fold == 0:
        raise ValueError("not enough data for the requested number of splits")

    results = []
    for k in range(n_splits):
        is_slice = df.iloc[k * fold : (k + 1) * fold]
        oos_end = n if k == n_splits - 1 else (k + 2) * fold
        oos_slice = df.iloc[(k + 1) * fold : oos_end]

        best_params, best_is, best_is_trades = None, float("-inf"), 0
        for params in param_grid:
            r = simulate(is_slice, make_strategy(params), config,
                         initial_cash, fee, warmup)
            if len(r.trades) < min_trades_fold:
                continue                      # too inactive to be evidence
            ret = total_return(r.equity)
            if ret > best_is:
                best_is, best_params, best_is_trades = ret, params, len(r.trades)

        if best_params is None:
            results.append({
                "fold": k, "valid": False, "best_params": None,
                "in_sample_return": 0.0, "in_sample_trades": 0,
                "oos_return": 0.0, "oos_trades": 0,
            })
            continue

        oos = simulate(oos_slice, make_strategy(best_params), config,
                       initial_cash, fee, warmup)
        results.append({
            "fold": k,
            "valid": True,
            "best_params": best_params,
            "in_sample_return": best_is,
            "in_sample_trades": best_is_trades,
            "oos_return": total_return(oos.equity),
            "oos_trades": len(oos.trades),
        })
    return results
```

- [ ] **Step 4: Update `cmd_walkforward` for the new `valid` flag**

In `cli.py`, replace the loop and summary inside `cmd_walkforward` (`cli.py:70-91`) with:

```python
    for r in results:
        if not r["valid"]:
            print(f"fold {r['fold']}: no parameter set made enough trades to judge")
            continue
        oos = f"{r['oos_return']:+.2%}" if r["oos_trades"] > 0 else "n/a (0 trades)"
        print(
            f"fold {r['fold']}: best params {str(r['best_params']):>16}"
            f"  in-sample {r['in_sample_return']:+.2%} ({r['in_sample_trades']} tr)"
            f"  out-of-sample {oos}"
        )
    print("-" * 72)
    if traded:
        avg_is = sum(r["in_sample_return"] for r in traded) / len(traded)
        avg_oos = sum(r["oos_return"] for r in traded) / len(traded)
        print(f"AVG in-sample:      {avg_is:+.2%}   (over {len(traded)} folds that traded)")
        print(f"AVG out-of-sample:  {avg_oos:+.2%}")
        print(f"Overfitting gap:    {avg_is - avg_oos:+.2%}  (big gap => curve-fit, not real edge)")
    else:
        print("No fold produced any trades — nothing to measure.")
    if len(traded) < len(results):
        print(
            f"WARNING: {len(results) - len(traded)}/{len(results)} folds made 0 trades "
            f"or had no valid parameters.\n"
            f"         Fetch more data (fetch --days), use fewer --splits, "
            f"or a smaller --trend-sma."
        )
```

Also update the `traded` filter one line above (`cli.py:68`) to respect validity:

```python
    traded = [r for r in results if r["valid"] and r["oos_trades"] > 0]
```

- [ ] **Step 5: Delete the retired engine**

`backtest/engine.py` now has no importers — Task 9 moved `cli.py` off it and Step 3 moved `walkforward.py` off it. Confirm, then delete:

Run: `wsl -e bash -lc 'cd ~/personal/trading_bot && grep -rn "backtest.engine\|run_backtest" --include=*.py .'`

Expected: matches only in `backtest/engine.py` and `tests/test_engine.py`. If anything else matches, migrate it before deleting.

```bash
wsl -e bash -lc 'cd ~/personal/trading_bot && git rm backtest/engine.py tests/test_engine.py'
```

The coverage `tests/test_engine.py` provided (buy/sell round-trip, no-signal cash preservation, fee handling) is reproduced against the real trader in `tests/test_simulate.py` from Task 8.

- [ ] **Step 6: Run the full suite**

Run: `wsl -e bash -lc 'cd ~/personal/trading_bot && source .venv/bin/activate && pytest'`

Expected: PASS, no import errors.

- [ ] **Step 7: Commit**

```bash
wsl -e bash -lc 'cd ~/personal/trading_bot && git add -A backtest/ tests/ cli.py && git commit -m "feat: walk-forward on simulate() with an optimizer trade gate; retire engine.py"'
```

---

### Task 11: Scan metrics

**Files:**
- Create: `backtest/scan.py`
- Create: `tests/test_scan.py`

**Interfaces:**
- Consumes: `BacktestResult` (Task 8).
- Produces, all pure functions:
  - `total_fees(fills: list) -> float`
  - `fee_drag(fills: list, trades: list) -> float` — fees ÷ |gross P&L|; `inf` when gross P&L is zero.
  - `trades_per_day(n_trades: int, index: pd.Index) -> float`
  - `worst_cumulative_loss(trades: list, starting_cash: float) -> float` — deepest point of running realized P&L, as a positive fraction of starting capital.

Note on `pnl`: `Trader._sell` computes `qty*price*(1-fee) - qty*entry_price` (`trader.py:82`), which is net of the exit fee but blind to the entry fee. So gross P&L here is "gross of entry fees" — the same known caveat `report.py` documents. `fee_drag` is a ratio of costs to activity, and this does not distort it enough to matter.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_scan.py`:

```python
import pandas as pd
import pytest

from backtest.scan import total_fees, fee_drag, trades_per_day, worst_cumulative_loss


def test_total_fees_sums_and_tolerates_blanks():
    fills = [{"fee": 1.5}, {"fee": 2.0}, {"fee": ""}, {}]
    assert total_fees(fills) == pytest.approx(3.5)


def test_fee_drag_is_cost_over_activity():
    fills = [{"fee": 5.0}, {"fee": 5.0}]
    trades = [{"pnl": 50.0}]
    assert fee_drag(fills, trades) == pytest.approx(0.2)


def test_fee_drag_uses_absolute_gross_pnl():
    """A losing strategy still has measurable activity to compare fees against."""
    fills = [{"fee": 5.0}, {"fee": 5.0}]
    trades = [{"pnl": -50.0}]
    assert fee_drag(fills, trades) == pytest.approx(0.2)


def test_fee_drag_is_infinite_when_nothing_moved():
    """Paid fees, produced no P&L — the worst case, not an undefined one."""
    assert fee_drag([{"fee": 5.0}], []) == float("inf")
    assert fee_drag([{"fee": 5.0}], [{"pnl": 0.0}]) == float("inf")


def test_trades_per_day_over_a_timestamp_index():
    index = pd.to_datetime(["2026-01-01", "2026-01-11"])
    assert trades_per_day(20, index) == pytest.approx(2.0)


def test_trades_per_day_on_a_zero_span_index():
    index = pd.to_datetime(["2026-01-01", "2026-01-01"])
    assert trades_per_day(5, index) == float("inf")
    assert trades_per_day(0, index) == 0.0


def test_worst_cumulative_loss_finds_the_deepest_point():
    # running total: -100, -250, -50  -> deepest is -250 on 10_000 = 2.5%
    trades = [{"pnl": -100.0}, {"pnl": -150.0}, {"pnl": 200.0}]
    assert worst_cumulative_loss(trades, 10_000.0) == pytest.approx(0.025)


def test_worst_cumulative_loss_is_zero_when_never_negative():
    trades = [{"pnl": 100.0}, {"pnl": 50.0}]
    assert worst_cumulative_loss(trades, 10_000.0) == 0.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `wsl -e bash -lc 'cd ~/personal/trading_bot && source .venv/bin/activate && pytest tests/test_scan.py -v'`

Expected: FAIL with `ModuleNotFoundError: No module named 'backtest.scan'`

- [ ] **Step 3: Write the implementation**

Create `backtest/scan.py`:

```python
"""Cost and churn metrics, gates, and the configuration scan.

The scan exists to answer one question honestly: is any configuration worth
running unattended? Every rejection carries a named reason, because knowing why
a configuration failed is the output's main value.
"""

import pandas as pd


def total_fees(fills: list) -> float:
    """Sum the fee column, tolerating blank entries from ledger-shaped rows."""
    return sum(float(f.get("fee") or 0.0) for f in fills)


def fee_drag(fills: list, trades: list) -> float:
    """Fees as a fraction of gross P&L — the share of activity eaten by costs.

    Absolute gross P&L, so a losing strategy is still measured against how much
    it actually moved. Zero gross P&L means fees were paid for nothing, which is
    the worst possible case, so it reports infinity rather than dividing by zero.
    """
    gross = abs(sum(float(t["pnl"]) for t in trades))
    if gross == 0:
        return float("inf")
    return total_fees(fills) / gross


def trades_per_day(n_trades: int, index) -> float:
    """Trade frequency. A swing bot trading many times a day is churning."""
    if len(index) < 2:
        return float("inf") if n_trades else 0.0
    span = pd.Timestamp(index[-1]) - pd.Timestamp(index[0])
    days = span.total_seconds() / 86_400.0
    if days <= 0:
        return float("inf") if n_trades else 0.0
    return n_trades / days


def worst_cumulative_loss(trades: list, starting_cash: float) -> float:
    """Deepest point of the running realized-P&L total, as a fraction of start.

    Reported rather than gated: it is what the live kill-switch would have
    reacted to, so it belongs in front of the user, not in a pass/fail rule.
    """
    running, worst = 0.0, 0.0
    for t in trades:
        running += float(t["pnl"])
        worst = min(worst, running)
    return abs(worst) / starting_cash if starting_cash else 0.0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `wsl -e bash -lc 'cd ~/personal/trading_bot && source .venv/bin/activate && pytest tests/test_scan.py -v'`

Expected: PASS, all 8 tests.

- [ ] **Step 5: Commit**

```bash
wsl -e bash -lc 'cd ~/personal/trading_bot && git add backtest/scan.py tests/test_scan.py && git commit -m "feat: scan cost and churn metrics"'
```

---

### Task 12: Gates and verdicts

**Files:**
- Modify: `backtest/scan.py`
- Test: `tests/test_scan.py`

**Interfaces:**
- Consumes: metric functions from Task 11.
- Produces: module constants `MIN_TRADES = 20`, `MAX_TRADES_PER_DAY = 6.0`, `MAX_FEE_DRAG = 0.30`, `MIN_FOLDS_TRADED = 2`; and `verdict(row: dict) -> tuple[str, str]` returning `("PASS", "")` or `("FAIL", "<label>")`.

`row` must carry: `trades`, `trades_per_day`, `fee_drag`, `folds_traded`, `avg_is`, `avg_oos`.

These thresholds come from the spec and were fixed before any results were seen. Changing one to make a configuration pass is the precise failure the gates exist to prevent — if a threshold is wrong, amend the spec deliberately and say so.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_scan.py`:

```python
from backtest.scan import verdict, MIN_TRADES, MAX_TRADES_PER_DAY, MAX_FEE_DRAG


def _passing_row(**overrides):
    row = {"trades": 50, "trades_per_day": 0.5, "fee_drag": 0.05,
           "folds_traded": 3, "avg_is": 0.10, "avg_oos": 0.04}
    row.update(overrides)
    return row


def test_thresholds_match_the_spec():
    assert MIN_TRADES == 20
    assert MAX_TRADES_PER_DAY == 6.0
    assert MAX_FEE_DRAG == 0.30


def test_a_good_config_passes():
    assert verdict(_passing_row()) == ("PASS", "")


def test_too_few_trades_fails():
    assert verdict(_passing_row(trades=19)) == ("FAIL", "too-few-trades")


def test_churn_fails():
    assert verdict(_passing_row(trades_per_day=6.1)) == ("FAIL", "churn")


def test_fee_drag_fails():
    assert verdict(_passing_row(fee_drag=0.31)) == ("FAIL", "fee-drag")


def test_infinite_fee_drag_fails():
    assert verdict(_passing_row(fee_drag=float("inf"))) == ("FAIL", "fee-drag")


def test_insufficient_folds_fails():
    assert verdict(_passing_row(folds_traded=1)) == ("FAIL", "insufficient-folds")


def test_overfit_fails_when_profit_does_not_survive_out_of_sample():
    assert verdict(_passing_row(avg_is=0.20, avg_oos=-0.05)) == ("FAIL", "overfit")


def test_losing_in_sample_is_not_overfit():
    """Bad in both halves is honest failure, not curve-fitting."""
    assert verdict(_passing_row(avg_is=-0.10, avg_oos=-0.05)) == ("PASS", "")


def test_boundaries_are_inclusive_where_the_spec_says_so():
    assert verdict(_passing_row(trades=MIN_TRADES)) == ("PASS", "")
    assert verdict(_passing_row(trades_per_day=MAX_TRADES_PER_DAY)) == ("PASS", "")
    assert verdict(_passing_row(fee_drag=MAX_FEE_DRAG)) == ("PASS", "")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `wsl -e bash -lc 'cd ~/personal/trading_bot && source .venv/bin/activate && pytest tests/test_scan.py -v'`

Expected: FAIL with `ImportError: cannot import name 'verdict' from 'backtest.scan'`

- [ ] **Step 3: Write the implementation**

Append to `backtest/scan.py`:

```python
# Gate thresholds. Fixed by the design spec before any results were seen; tuning
# them after looking at output turns "survives walk-forward" into post-hoc
# rationalization, which is the exact failure the gates exist to prevent.
MIN_TRADES = 20              # below this, results are noise
MAX_TRADES_PER_DAY = 6.0     # above this, a swing bot is churning
MAX_FEE_DRAG = 0.30          # costs must not eat a third of the activity
MIN_FOLDS_TRADED = 2         # walk-forward needs at least two folds to say anything


def verdict(row: dict) -> tuple[str, str]:
    """Apply the gates in order and return ("PASS", "") or ("FAIL", label).

    Order matters only for which label a multiply-failing config reports; the
    cheapest, most fundamental objection is checked first.
    """
    if row["trades"] < MIN_TRADES:
        return "FAIL", "too-few-trades"
    if row["trades_per_day"] > MAX_TRADES_PER_DAY:
        return "FAIL", "churn"
    if row["fee_drag"] > MAX_FEE_DRAG:
        return "FAIL", "fee-drag"
    if row["folds_traded"] < MIN_FOLDS_TRADED:
        return "FAIL", "insufficient-folds"
    if row["avg_is"] > 0 and row["avg_oos"] < 0:
        return "FAIL", "overfit"
    return "PASS", ""
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `wsl -e bash -lc 'cd ~/personal/trading_bot && source .venv/bin/activate && pytest tests/test_scan.py -v'`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
wsl -e bash -lc 'cd ~/personal/trading_bot && git add backtest/scan.py tests/test_scan.py && git commit -m "feat: scan gates with spec-fixed thresholds"'
```

---

### Task 13: Scan orchestration and CLI

**Files:**
- Modify: `backtest/scan.py`, `cli.py`
- Test: `tests/test_scan.py`

**Interfaces:**
- Consumes: `simulate`, `scan_risk_config` (Task 8); `walk_forward` (Task 10); metrics and `verdict` (Tasks 11-12); `build_strategy`, `walk_forward_grid` (`strategies/factory.py`).
- Produces:
  - `scan_one(df, symbol, timeframe, strategy_name, *, cash=10_000.0, fee=0.001, warmup=50, risk_per_trade=0.01, stop_loss_pct=0.05, splits=4, trend_sma=200) -> dict`
  - `rank(rows: list[dict]) -> list[dict]` — PASS rows first, sorted by `edge` descending; FAIL rows after, sorted by label.
  - `format_table(rows: list[dict]) -> str`
  - `cli.py scan` subcommand.

Row keys: `symbol, timeframe, strategy, bars, days, trades, trades_per_day, net_return, edge, max_drawdown, worst_loss, fee_drag, avg_is, avg_oos, oos_gap, folds_traded, verdict, reason`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_scan.py`:

```python
from backtest.scan import rank, format_table


def _row(strategy, v, reason="", edge=0.0):
    return {"symbol": "BTC/USDT", "timeframe": "1h", "strategy": strategy,
            "bars": 1000, "days": 41.7, "trades": 50, "trades_per_day": 1.2,
            "net_return": 0.05, "edge": edge, "max_drawdown": -0.08,
            "worst_loss": 0.03, "fee_drag": 0.1, "avg_is": 0.1, "avg_oos": 0.05,
            "oos_gap": 0.05, "folds_traded": 3, "verdict": v, "reason": reason}


def test_rank_puts_passing_configs_first_by_edge():
    rows = [_row("ma", "FAIL", "churn"),
            _row("rsi", "PASS", edge=0.01),
            _row("rsi+trend", "PASS", edge=0.09)]
    ranked = rank(rows)
    assert [r["strategy"] for r in ranked] == ["rsi+trend", "rsi", "ma"]


def test_rank_keeps_failures_rather_than_dropping_them():
    """Knowing why a config was rejected is the point of the output."""
    rows = [_row("ma", "FAIL", "churn"), _row("rsi", "FAIL", "fee-drag")]
    assert len(rank(rows)) == 2


def test_format_table_shows_the_failure_reason():
    out = format_table([_row("ma", "FAIL", "churn")])
    assert "churn" in out
    assert "ma" in out
    assert "BTC/USDT" in out


def test_scan_one_flags_a_churning_config():
    """Success criterion 3: the 1m config that churned in the live ledger must
    be rejected by a gate, not quietly ranked."""
    import numpy as np
    from backtest.scan import scan_one

    n = 3000
    # 1-minute bars of pure noise: crossovers fire constantly, nothing trends
    rng = np.random.default_rng(0)
    close = 65_000 + np.cumsum(rng.normal(0, 5, n))
    index = pd.date_range("2026-07-01", periods=n, freq="1min")
    df = pd.DataFrame({"close": close}, index=index)

    row = scan_one(df, "BTC/USDT", "1m", "ma", warmup=60, splits=2)

    assert row["verdict"] == "FAIL"
    assert row["reason"] in ("churn", "fee-drag", "too-few-trades", "insufficient-folds")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `wsl -e bash -lc 'cd ~/personal/trading_bot && source .venv/bin/activate && pytest tests/test_scan.py -v'`

Expected: FAIL with `ImportError: cannot import name 'rank' from 'backtest.scan'`

- [ ] **Step 3: Write the implementation**

Append to `backtest/scan.py`. Add these imports at the top of the file, below `import pandas as pd`:

```python
from backtest.metrics import total_return, max_drawdown, buy_and_hold_return
from backtest.simulate import simulate, scan_risk_config
from backtest.walkforward import walk_forward
from strategies.factory import build_strategy, walk_forward_grid
```

Then append:

```python
def scan_one(df, symbol: str, timeframe: str, strategy_name: str, *,
             cash: float = 10_000.0, fee: float = 0.001, warmup: int = 50,
             risk_per_trade: float = 0.01, stop_loss_pct: float = 0.05,
             splits: int = 4, trend_sma: int = 200) -> dict:
    """Measure one (strategy, timeframe) configuration and return its scan row."""
    config = scan_risk_config(risk_per_trade=risk_per_trade, stop_loss_pct=stop_loss_pct)
    strategy = build_strategy(strategy_name, trend_sma=trend_sma)
    res = simulate(df, strategy, config, cash=cash, fee=fee, warmup=warmup)

    net = total_return(res.equity) if len(res.equity) else 0.0
    hold = buy_and_hold_return(df["close"], fee=fee)

    try:
        grid, make_strategy = walk_forward_grid(strategy_name, trend_sma=trend_sma)
        folds = walk_forward(df, make_strategy, grid, n_splits=splits,
                             initial_cash=cash, fee=fee, warmup=warmup,
                             risk_config=config)
    except ValueError:
        folds = []          # not enough data to split at all
    traded = [f for f in folds if f["valid"] and f["oos_trades"] > 0]
    avg_is = sum(f["in_sample_return"] for f in traded) / len(traded) if traded else 0.0
    avg_oos = sum(f["oos_return"] for f in traded) / len(traded) if traded else 0.0

    span_days = 0.0
    if len(df.index) >= 2:
        span_days = (pd.Timestamp(df.index[-1]) - pd.Timestamp(df.index[0])).total_seconds() / 86_400.0

    row = {
        "symbol": symbol,
        "timeframe": timeframe,
        "strategy": strategy_name,
        "bars": len(df),
        "days": span_days,
        "trades": len(res.trades),
        "trades_per_day": trades_per_day(len(res.trades), df.index),
        "net_return": net,
        "edge": net - hold,
        "max_drawdown": max_drawdown(res.equity) if len(res.equity) else 0.0,
        "worst_loss": worst_cumulative_loss(res.trades, cash),
        "fee_drag": fee_drag(res.fills, res.trades),
        "avg_is": avg_is,
        "avg_oos": avg_oos,
        "oos_gap": avg_is - avg_oos,
        "folds_traded": len(traded),
    }
    row["verdict"], row["reason"] = verdict(row)
    return row


def rank(rows: list) -> list:
    """Passing configurations first, best edge first. Failures follow, grouped by
    reason — they are kept, never dropped: a named rejection is information."""
    passing = sorted([r for r in rows if r["verdict"] == "PASS"],
                     key=lambda r: r["edge"], reverse=True)
    failing = sorted([r for r in rows if r["verdict"] != "PASS"],
                     key=lambda r: (r["reason"], r["strategy"], r["timeframe"]))
    return passing + failing


def _fmt(value: float, spec: str) -> str:
    if value == float("inf"):
        return "inf"
    return format(value, spec)


def format_table(rows: list) -> str:
    header = (f"{'symbol':<10} {'tf':>4} {'strategy':<10} {'bars':>6} {'days':>6} "
              f"{'trades':>6} {'tr/day':>7} {'net':>8} {'edge':>8} {'maxDD':>7} "
              f"{'worst':>7} {'feedrag':>8} {'oosgap':>8} {'folds':>5}  verdict")
    lines = [header, "-" * len(header)]
    for r in rows:
        tag = r["verdict"] if r["verdict"] == "PASS" else f"FAIL {r['reason']}"
        lines.append(
            f"{r['symbol']:<10} {r['timeframe']:>4} {r['strategy']:<10} "
            f"{r['bars']:>6} {r['days']:>6.1f} {r['trades']:>6} "
            f"{_fmt(r['trades_per_day'], '>7.2f')} {r['net_return']:>7.2%} "
            f"{r['edge']:>+7.2%} {r['max_drawdown']:>6.1%} {r['worst_loss']:>6.1%} "
            f"{_fmt(r['fee_drag'], '>8.2f')} {r['oos_gap']:>+7.2%} "
            f"{r['folds_traded']:>5}  {tag}"
        )
    return "\n".join(lines)
```

- [ ] **Step 4: Add the `scan` CLI command**

In `cli.py`, add the import near the other backtest imports:

```python
from backtest.scan import scan_one, rank, format_table
```

Add the command function after `cmd_walkforward`:

```python
def cmd_scan(args):
    import time

    prov = MarketDataProvider(exchange=None)
    timeframes = [t.strip() for t in args.timeframes.split(",") if t.strip()]
    strategies = [s.strip() for s in args.strategies.split(",") if s.strip()]

    rows, skipped = [], []
    for tf in timeframes:
        try:
            df = prov.load_cached(args.symbol, tf)
        except FileNotFoundError:
            skipped.append(f"{tf} (no cached data — run: fetch --timeframe {tf} --days N)")
            continue
        for name in strategies:
            started = time.time()
            row = scan_one(df, args.symbol, tf, name, cash=args.cash, fee=args.fee,
                           warmup=args.warmup, risk_per_trade=args.risk,
                           stop_loss_pct=args.stop, splits=args.splits,
                           trend_sma=args.trend_sma)
            rows.append(row)
            print(f"  scanned {name} {tf} in {time.time() - started:.1f}s", flush=True)

    if not rows:
        raise SystemExit("Nothing to scan. " + "; ".join(skipped))

    print()
    print(format_table(rank(rows)))
    print()
    passing = [r for r in rows if r["verdict"] == "PASS"]
    if passing:
        best = max(passing, key=lambda r: r["edge"])
        print(f"{len(passing)}/{len(rows)} configurations passed. "
              f"Best by edge: {best['strategy']} on {best['timeframe']} "
              f"({best['edge']:+.2%} vs buy & hold).")
    else:
        print(f"0/{len(rows)} configurations passed. That is a finding, not a bug: "
              f"no tested configuration is worth soaking. Do not loosen the "
              f"thresholds to manufacture a winner.")
    for note in skipped:
        print(f"SKIPPED {note}")
```

Register the parser inside `build_parser`, after the walkforward block:

```python
    sc = sub.add_parser("scan", help="rank strategy/timeframe configurations against the gates")
    sc.add_argument("--symbol", default="BTC/USDT")
    sc.add_argument("--timeframes", default="1h,4h",
                    help="comma-separated, e.g. 1h,4h,3m,1m (needs cached data for each)")
    sc.add_argument("--strategies", default=",".join(STRATEGY_NAMES),
                    help="comma-separated subset of " + ",".join(STRATEGY_NAMES))
    sc.add_argument("--trend-sma", type=int, default=200)
    sc.add_argument("--splits", type=int, default=4)
    sc.add_argument("--cash", type=float, default=10_000.0)
    sc.add_argument("--fee", type=float, default=0.001)
    sc.add_argument("--risk", type=float, default=0.01)
    sc.add_argument("--stop", type=float, default=0.05)
    sc.add_argument("--warmup", type=int, default=50)
    sc.set_defaults(func=cmd_scan)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `wsl -e bash -lc 'cd ~/personal/trading_bot && source .venv/bin/activate && pytest tests/test_scan.py -v'`

Expected: PASS

- [ ] **Step 6: Run the full suite**

Run: `wsl -e bash -lc 'cd ~/personal/trading_bot && source .venv/bin/activate && pytest'`

Expected: PASS.

- [ ] **Step 7: Run a real scan**

First backfill the depths the spec calls for:

```bash
wsl -e bash -lc 'cd ~/personal/trading_bot && source .venv/bin/activate && \
  python cli.py fetch --timeframe 1h --days 365 && \
  python cli.py fetch --timeframe 4h --days 730 && \
  python cli.py fetch --timeframe 3m --days 30 && \
  python cli.py fetch --timeframe 1m --days 7'
```

Then scan:

```bash
wsl -e bash -lc 'cd ~/personal/trading_bot && source .venv/bin/activate && \
  python cli.py scan --timeframes 1h,4h,3m,1m'
```

Expected: a ranked table. **Verify success criterion 3** — the `ma` row on `1m` must read `FAIL churn` or `FAIL fee-drag`. If it passes, a gate is mis-wired; investigate rather than adjusting the threshold.

If the scan is slow, note the per-config timings printed in Step 4 and report them — the spec lists runtime as a known risk.

- [ ] **Step 8: Commit**

```bash
wsl -e bash -lc 'cd ~/personal/trading_bot && git add backtest/scan.py cli.py tests/test_scan.py && git commit -m "feat: scan command ranks configurations against the gates"'
```

---

## Completion checklist

- [ ] `fetch --days N` accumulates history across repeated runs without losing bars (spec success criterion 1)
- [ ] `backtest`, `walkforward`, and paper `run` all execute through `Trader.step`; `backtest/engine.py` is deleted (criterion 2)
- [ ] `scan` prints a ranked table where every rejected configuration carries a named reason, and the 1m MA-crossover configuration is rejected by the churn or fee-drag gate (criterion 3)
- [ ] Full suite green
- [ ] Record the achieved backfill span per timeframe — the spec promises the real number, not a target
