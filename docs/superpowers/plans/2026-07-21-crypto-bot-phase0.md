# Crypto Bot — Phase 0 Foundations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold a Python crypto trading bot that can fetch & cache historical candles, run one strategy (MA crossover) through an offline backtester with fees, and expose a broker-abstraction layer (ccxt, testnet-ready) — all covered by passing tests.

**Architecture:** Small, single-responsibility packages wired by a CLI. `config` loads settings; `data` fetches/caches OHLCV; `strategies` turn candles into BUY/SELL/HOLD signals; `backtest` replays a strategy over candles and computes metrics; `broker` hides the exchange behind an interface (`Broker` ABC + `CcxtBroker`). Phase 0 does **not** place live orders — the broker code exists and is unit-tested via delegation, but the runnable deliverable is the offline backtest.

**Tech Stack:** Python 3.12, ccxt, pandas, numpy, pyarrow (parquet cache), pydantic-settings, pytest. Indicators use plain pandas (`.rolling().mean()`) — NOT `pandas-ta` in Phase 0 (avoids the `pandas-ta` / NumPy 2.x `numpy.NaN` import breakage).

## Global Constraints

- **Runtime:** Python **3.12** inside WSL Ubuntu. All commands run from the project root `~/personal/trading_bot` with the venv active: prefix shell commands with `source .venv/bin/activate` (venv created in Task 1). When driving from the Windows side, wrap as `wsl -e bash -lc 'cd ~/personal/trading_bot && source .venv/bin/activate && <cmd>'`.
- **Broker abstraction:** Strategy, backtest, and data code MUST NOT import `ccxt` directly. Only `broker/ccxt_broker.py` and `cli.py` may import `ccxt`.
- **Testnet-first:** `CcxtBroker` defaults to `testnet=True` (`set_sandbox_mode(True)`). No live order is placed anywhere in Phase 0.
- **Secrets:** API keys load from `.env` only. `.env` is git-ignored from the first commit. `.env.example` documents the keys and states: trade-only permission, withdrawals disabled, IP-allowlisted.
- **Indicators:** plain pandas only in Phase 0 (no `pandas-ta` / `TA-Lib`).
- **Backtest realism:** the backtester models a per-trade `fee` (default `0.001`). Never assume zero cost by default.
- **Import style:** absolute imports from the project root (e.g. `from strategies.base import Signal`). Enabled by `pythonpath = ["."]` in `pyproject.toml`'s pytest config.
- **Commits:** one commit per task, conventional-commit style (`feat:`, `test:`, `chore:`).

---

## File Structure

```
trading_bot/
├─ pyproject.toml            # pytest config (pythonpath, testpaths)
├─ requirements.txt          # runtime deps
├─ requirements-dev.txt      # + pytest
├─ .gitignore
├─ .env.example
├─ config/
│  ├─ __init__.py
│  └─ settings.py            # Settings (pydantic-settings), load_settings()
├─ broker/
│  ├─ __init__.py
│  ├─ base.py                # Order dataclass, Broker ABC
│  └─ ccxt_broker.py         # CcxtBroker(Broker)
├─ data/
│  ├─ __init__.py
│  └─ provider.py            # MarketDataProvider (fetch + parquet cache)
├─ strategies/
│  ├─ __init__.py
│  ├─ base.py                # Signal dataclass, Strategy base
│  └─ ma_crossover.py        # MACrossover(Strategy)
├─ backtest/
│  ├─ __init__.py
│  ├─ metrics.py             # total_return, max_drawdown, sharpe_ratio
│  └─ engine.py              # run_backtest(), BacktestResult
├─ cli.py                    # `fetch` and `backtest` subcommands
├─ cache/                    # git-ignored candle cache (created at runtime)
└─ tests/
   ├─ test_config.py
   ├─ test_strategy_ma.py
   ├─ test_metrics.py
   ├─ test_engine.py
   ├─ test_provider.py
   ├─ test_broker.py
   └─ test_integration.py
```

---

### Task 1: Project scaffold, tooling & git

**Files:**
- Create: `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`, `.gitignore`, `.env.example`
- Create: `config/__init__.py`, `broker/__init__.py`, `data/__init__.py`, `strategies/__init__.py`, `backtest/__init__.py`, `tests/__init__.py`
- Create: `tests/test_sanity.py`

**Interfaces:**
- Consumes: nothing (first task).
- Produces: a working venv with deps installed, `pytest` runnable from the project root, git initialized. Later tasks assume `pytest -q` works and packages are importable via `pythonpath = ["."]`.

- [ ] **Step 1: Create `requirements.txt`**

```
ccxt>=4.2
pandas>=2.0
numpy>=1.24
pyarrow>=14.0
pydantic>=2.5
pydantic-settings>=2.1
```

- [ ] **Step 2: Create `requirements-dev.txt`**

```
-r requirements.txt
pytest>=7.4
```

- [ ] **Step 3: Create `pyproject.toml`**

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
addopts = "-q"
```

- [ ] **Step 4: Create `.gitignore`**

```
.env
.venv/
__pycache__/
*.pyc
.pytest_cache/
cache/
```

- [ ] **Step 5: Create `.env.example`**

```
# Copy this file to .env and fill in your keys. NEVER commit .env.
# Create exchange API keys with TRADE-ONLY permission, WITHDRAWALS DISABLED,
# and IP-allowlisted to your machine/VPS.
EXCHANGE_ID=binance
EXCHANGE_API_KEY=
EXCHANGE_API_SECRET=
USE_TESTNET=true
```

- [ ] **Step 6: Create empty package markers**

Create these files, each containing a single blank line:
`config/__init__.py`, `broker/__init__.py`, `data/__init__.py`, `strategies/__init__.py`, `backtest/__init__.py`, `tests/__init__.py`

- [ ] **Step 7: Create the sanity test `tests/test_sanity.py`**

```python
def test_sanity():
    assert True
```

- [ ] **Step 8: Create venv and install deps**

Run:
```bash
cd ~/personal/trading_bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```
Expected: installs complete without error; `pip show ccxt` prints a version.

- [ ] **Step 9: Run the sanity test**

Run: `source .venv/bin/activate && pytest tests/test_sanity.py`
Expected: `1 passed`.

- [ ] **Step 10: Initialize git and commit**

```bash
cd ~/personal/trading_bot
git init
git add pyproject.toml requirements.txt requirements-dev.txt .gitignore .env.example \
        config/__init__.py broker/__init__.py data/__init__.py strategies/__init__.py \
        backtest/__init__.py tests/__init__.py tests/test_sanity.py docs/
git commit -m "chore: scaffold crypto bot project (Phase 0)"
```
Expected: commit succeeds. Confirm `.env` is NOT tracked: `git status --porcelain | grep -c '\.env$'` prints `0`.

---

### Task 2: Config / settings loader

**Files:**
- Create: `config/settings.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `Settings` (pydantic-settings model) with fields `exchange_id: str`, `exchange_api_key: str`, `exchange_api_secret: str`, `use_testnet: bool`; and `load_settings() -> Settings`. `cli.py` (Task 8) consumes `load_settings()`.

- [ ] **Step 1: Write the failing test `tests/test_config.py`**

```python
from config.settings import Settings


def test_defaults(monkeypatch, tmp_path):
    # Run in an empty dir so no real .env is read.
    monkeypatch.chdir(tmp_path)
    for var in ("EXCHANGE_ID", "EXCHANGE_API_KEY", "EXCHANGE_API_SECRET", "USE_TESTNET"):
        monkeypatch.delenv(var, raising=False)
    s = Settings()
    assert s.exchange_id == "binance"
    assert s.use_testnet is True
    assert s.exchange_api_key == ""


def test_from_env(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("EXCHANGE_ID", "kraken")
    monkeypatch.setenv("USE_TESTNET", "false")
    s = Settings()
    assert s.exchange_id == "kraken"
    assert s.use_testnet is False
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `source .venv/bin/activate && pytest tests/test_config.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'config.settings'`.

- [ ] **Step 3: Write `config/settings.py`**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    exchange_id: str = "binance"
    exchange_api_key: str = ""
    exchange_api_secret: str = ""
    use_testnet: bool = True


def load_settings() -> Settings:
    return Settings()
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `source .venv/bin/activate && pytest tests/test_config.py`
Expected: `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add config/settings.py tests/test_config.py
git commit -m "feat: add pydantic settings loader"
```

---

### Task 3: Strategy base + MA crossover

**Files:**
- Create: `strategies/base.py`, `strategies/ma_crossover.py`
- Test: `tests/test_strategy_ma.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `Signal` dataclass: `action: str` (`"BUY"|"SELL"|"HOLD"`), `reason: str = ""`.
  - `Strategy` base class with `generate(self, df: pd.DataFrame) -> Signal` (raises `NotImplementedError`).
  - `MACrossover(Strategy)` — `__init__(self, fast: int = 20, slow: int = 50)` (raises `ValueError` if `fast >= slow`); `generate(df)` reads the `close` column.
  - The backtest engine (Task 5) and CLI (Task 8) consume these.

- [ ] **Step 1: Write the failing test `tests/test_strategy_ma.py`**

```python
import pandas as pd
import pytest

from strategies.ma_crossover import MACrossover


def _df(prices):
    return pd.DataFrame({"close": prices})


def test_invalid_params_raise():
    with pytest.raises(ValueError):
        MACrossover(fast=5, slow=5)


def test_buy_on_upward_cross():
    # fast(2)=3.0 vs slow(3)=2.33 on last bar; equal on prev bar -> BUY
    sig = MACrossover(fast=2, slow=3).generate(_df([1, 1, 1, 1, 5]))
    assert sig.action == "BUY"


def test_sell_on_downward_cross():
    sig = MACrossover(fast=2, slow=3).generate(_df([5, 5, 5, 5, 1]))
    assert sig.action == "SELL"


def test_hold_when_no_cross():
    sig = MACrossover(fast=2, slow=3).generate(_df([1, 2, 3, 4, 5]))
    assert sig.action == "HOLD"


def test_hold_when_not_enough_data():
    sig = MACrossover(fast=2, slow=3).generate(_df([1, 2, 3]))
    assert sig.action == "HOLD"
    assert "not enough data" in sig.reason
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `source .venv/bin/activate && pytest tests/test_strategy_ma.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'strategies.ma_crossover'`.

- [ ] **Step 3: Write `strategies/base.py`**

```python
from dataclasses import dataclass

import pandas as pd


@dataclass
class Signal:
    action: str  # "BUY" | "SELL" | "HOLD"
    reason: str = ""


class Strategy:
    def generate(self, df: pd.DataFrame) -> Signal:
        raise NotImplementedError
```

- [ ] **Step 4: Write `strategies/ma_crossover.py`**

```python
import pandas as pd

from strategies.base import Strategy, Signal


class MACrossover(Strategy):
    def __init__(self, fast: int = 20, slow: int = 50):
        if fast >= slow:
            raise ValueError("fast period must be < slow period")
        self.fast = fast
        self.slow = slow

    def generate(self, df: pd.DataFrame) -> Signal:
        if len(df) < self.slow + 1:
            return Signal("HOLD", reason="not enough data")
        fast = df["close"].rolling(self.fast).mean()
        slow = df["close"].rolling(self.slow).mean()
        prev_fast, prev_slow = fast.iloc[-2], slow.iloc[-2]
        curr_fast, curr_slow = fast.iloc[-1], slow.iloc[-1]
        if prev_fast <= prev_slow and curr_fast > curr_slow:
            return Signal("BUY", reason="fast crossed above slow")
        if prev_fast >= prev_slow and curr_fast < curr_slow:
            return Signal("SELL", reason="fast crossed below slow")
        return Signal("HOLD", reason="no cross")
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `source .venv/bin/activate && pytest tests/test_strategy_ma.py`
Expected: `5 passed`.

- [ ] **Step 6: Commit**

```bash
git add strategies/base.py strategies/ma_crossover.py tests/test_strategy_ma.py
git commit -m "feat: add strategy base and MA crossover"
```

---

### Task 4: Backtest metrics

**Files:**
- Create: `backtest/metrics.py`
- Test: `tests/test_metrics.py`

**Interfaces:**
- Consumes: nothing.
- Produces (all take a `pd.Series` equity curve):
  - `total_return(equity) -> float`
  - `max_drawdown(equity) -> float` (negative or zero)
  - `sharpe_ratio(equity, periods_per_year: int = 365) -> float`
  - The CLI (Task 8) consumes these.

- [ ] **Step 1: Write the failing test `tests/test_metrics.py`**

```python
import pandas as pd
import pytest

from backtest.metrics import total_return, max_drawdown, sharpe_ratio


def test_total_return():
    assert total_return(pd.Series([100.0, 110.0])) == pytest.approx(0.10)


def test_max_drawdown():
    # peak 120 -> trough 60 => 60/120 - 1 = -0.5
    assert max_drawdown(pd.Series([100.0, 120.0, 60.0, 80.0])) == pytest.approx(-0.5)


def test_max_drawdown_monotonic_up_is_zero():
    assert max_drawdown(pd.Series([100.0, 110.0, 120.0])) == pytest.approx(0.0)


def test_sharpe_zero_when_flat():
    assert sharpe_ratio(pd.Series([100.0, 100.0, 100.0])) == 0.0
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `source .venv/bin/activate && pytest tests/test_metrics.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'backtest.metrics'`.

- [ ] **Step 3: Write `backtest/metrics.py`**

```python
import numpy as np
import pandas as pd


def total_return(equity: pd.Series) -> float:
    return float(equity.iloc[-1] / equity.iloc[0] - 1.0)


def max_drawdown(equity: pd.Series) -> float:
    running_max = equity.cummax()
    drawdown = equity / running_max - 1.0
    return float(drawdown.min())


def sharpe_ratio(equity: pd.Series, periods_per_year: int = 365) -> float:
    returns = equity.pct_change().dropna()
    if len(returns) == 0 or returns.std() == 0:
        return 0.0
    return float((returns.mean() / returns.std()) * np.sqrt(periods_per_year))
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `source .venv/bin/activate && pytest tests/test_metrics.py`
Expected: `4 passed`.

- [ ] **Step 5: Commit**

```bash
git add backtest/metrics.py tests/test_metrics.py
git commit -m "feat: add backtest performance metrics"
```

---

### Task 5: Backtest engine

**Files:**
- Create: `backtest/engine.py`
- Test: `tests/test_engine.py`

**Interfaces:**
- Consumes: `strategies.base.Strategy` / `Signal` (Task 3).
- Produces:
  - `BacktestResult` dataclass: `equity: pd.Series`, `trades: list[dict]`, `final_equity: float`. Each trade dict has keys `entry`, `exit`, `pnl`.
  - `run_backtest(df, strategy, initial_cash=10_000.0, fee=0.001, warmup=50) -> BacktestResult`. Long-flat model: on `BUY` while flat, invest all cash (minus fee) at the bar close; on `SELL` while long, sell all (minus fee). Equity is marked-to-market every bar. Signals during `warmup` bars are ignored.
  - The CLI (Task 8) and integration test (Task 8) consume `run_backtest`.

- [ ] **Step 1: Write the failing test `tests/test_engine.py`**

```python
import pandas as pd
import pytest

from backtest.engine import run_backtest
from strategies.base import Strategy, Signal


class ScriptedStrategy(Strategy):
    """Emits a preset action at specific bar indices, else HOLD."""

    def __init__(self, actions):
        self.actions = actions  # {bar_index: "BUY"|"SELL"}

    def generate(self, df):
        i = len(df) - 1
        return Signal(self.actions.get(i, "HOLD"))


def test_buy_then_sell_profit_no_fee():
    df = pd.DataFrame({"close": [100.0, 100.0, 100.0, 110.0, 120.0]})
    strat = ScriptedStrategy({2: "BUY", 4: "SELL"})
    res = run_backtest(df, strat, initial_cash=1000.0, fee=0.0, warmup=0)
    assert res.final_equity == pytest.approx(1200.0)
    assert len(res.trades) == 1
    assert res.trades[0]["pnl"] == pytest.approx(200.0)


def test_no_signals_preserves_cash():
    df = pd.DataFrame({"close": [100.0, 105.0, 110.0]})
    strat = ScriptedStrategy({})  # always HOLD
    res = run_backtest(df, strat, initial_cash=500.0, fee=0.0, warmup=0)
    assert res.final_equity == pytest.approx(500.0)
    assert res.trades == []


def test_fee_reduces_proceeds():
    df = pd.DataFrame({"close": [100.0, 100.0, 100.0]})
    strat = ScriptedStrategy({0: "BUY", 2: "SELL"})
    res = run_backtest(df, strat, initial_cash=1000.0, fee=0.01, warmup=0)
    # buy: qty = 1000*0.99/100 = 9.9 ; sell: 9.9*100*0.99 = 980.10
    assert res.final_equity == pytest.approx(980.10)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `source .venv/bin/activate && pytest tests/test_engine.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'backtest.engine'`.

- [ ] **Step 3: Write `backtest/engine.py`**

```python
from dataclasses import dataclass

import pandas as pd

from strategies.base import Strategy


@dataclass
class BacktestResult:
    equity: pd.Series
    trades: list
    final_equity: float


def run_backtest(
    df: pd.DataFrame,
    strategy: Strategy,
    initial_cash: float = 10_000.0,
    fee: float = 0.001,
    warmup: int = 50,
) -> BacktestResult:
    cash = initial_cash
    position = 0.0       # units of the asset held
    entry_price = 0.0
    equity_curve = []
    trades = []
    index = []

    for i in range(len(df)):
        price = float(df["close"].iloc[i])
        equity_curve.append(cash + position * price)
        index.append(df.index[i])

        if i < warmup:
            continue

        signal = strategy.generate(df.iloc[: i + 1])

        if signal.action == "BUY" and position == 0.0:
            qty = (cash * (1 - fee)) / price
            position = qty
            entry_price = price
            cash = 0.0
        elif signal.action == "SELL" and position > 0.0:
            proceeds = position * price * (1 - fee)
            trades.append(
                {"entry": entry_price, "exit": price, "pnl": proceeds - position * entry_price}
            )
            cash = proceeds
            position = 0.0
            entry_price = 0.0

    final_equity = cash + position * float(df["close"].iloc[-1])
    return BacktestResult(
        equity=pd.Series(equity_curve, index=index),
        trades=trades,
        final_equity=final_equity,
    )
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `source .venv/bin/activate && pytest tests/test_engine.py`
Expected: `3 passed`.

- [ ] **Step 5: Commit**

```bash
git add backtest/engine.py tests/test_engine.py
git commit -m "feat: add long-flat backtest engine"
```

---

### Task 6: Market data provider (fetch + cache)

**Files:**
- Create: `data/provider.py`
- Test: `tests/test_provider.py`

**Interfaces:**
- Consumes: an injected `exchange` object exposing `fetch_ohlcv(symbol, timeframe, limit) -> list[list]` (rows `[ts_ms, open, high, low, close, volume]`). In production this is a `ccxt` exchange; in tests it is a fake. Provider does NOT import ccxt.
- Produces:
  - `MarketDataProvider(exchange, cache_dir="cache")`.
  - `.fetch(symbol, timeframe="1h", limit=500) -> pd.DataFrame` — returns a DataFrame indexed by a `ts` datetime with columns `["open","high","low","close","volume"]`, and writes a parquet cache file.
  - `.load_cached(symbol, timeframe="1h") -> pd.DataFrame` — reads the cache; raises `FileNotFoundError` if absent.
  - The CLI (Task 8) and integration test consume these.

- [ ] **Step 1: Write the failing test `tests/test_provider.py`**

```python
import pandas as pd
import pytest

from data.provider import MarketDataProvider


class FakeExchange:
    def fetch_ohlcv(self, symbol, timeframe="1h", limit=500):
        return [
            [1609459200000, 1.0, 2.0, 0.5, 1.5, 100.0],
            [1609462800000, 1.5, 2.5, 1.0, 2.0, 120.0],
        ]


def test_fetch_shapes_and_caches(tmp_path):
    prov = MarketDataProvider(FakeExchange(), cache_dir=str(tmp_path))
    df = prov.fetch("BTC/USDT", "1h", limit=2)
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]
    assert df.index.name == "ts"
    assert len(df) == 2
    assert df["close"].iloc[-1] == 2.0


def test_load_cached_roundtrip(tmp_path):
    prov = MarketDataProvider(FakeExchange(), cache_dir=str(tmp_path))
    prov.fetch("BTC/USDT", "1h", limit=2)
    df2 = prov.load_cached("BTC/USDT", "1h")
    assert len(df2) == 2
    assert df2["close"].iloc[-1] == 2.0


def test_load_cached_missing_raises(tmp_path):
    prov = MarketDataProvider(FakeExchange(), cache_dir=str(tmp_path))
    with pytest.raises(FileNotFoundError):
        prov.load_cached("ETH/USDT", "1h")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `source .venv/bin/activate && pytest tests/test_provider.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'data.provider'`.

- [ ] **Step 3: Write `data/provider.py`**

```python
import os

import pandas as pd

OHLCV_COLUMNS = ["ts", "open", "high", "low", "close", "volume"]


def _to_dataframe(raw: list) -> pd.DataFrame:
    df = pd.DataFrame(raw, columns=OHLCV_COLUMNS)
    df["ts"] = pd.to_datetime(df["ts"], unit="ms")
    return df.set_index("ts")


class MarketDataProvider:
    def __init__(self, exchange, cache_dir: str = "cache"):
        self.exchange = exchange
        self.cache_dir = cache_dir

    def _cache_path(self, symbol: str, timeframe: str) -> str:
        safe = symbol.replace("/", "-")
        return os.path.join(self.cache_dir, f"{safe}_{timeframe}.parquet")

    def fetch(self, symbol: str, timeframe: str = "1h", limit: int = 500) -> pd.DataFrame:
        raw = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = _to_dataframe(raw)
        os.makedirs(self.cache_dir, exist_ok=True)
        df.to_parquet(self._cache_path(symbol, timeframe))
        return df

    def load_cached(self, symbol: str, timeframe: str = "1h") -> pd.DataFrame:
        path = self._cache_path(symbol, timeframe)
        if not os.path.exists(path):
            raise FileNotFoundError(f"No cached data at {path}")
        return pd.read_parquet(path)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `source .venv/bin/activate && pytest tests/test_provider.py`
Expected: `3 passed`.

- [ ] **Step 5: Commit**

```bash
git add data/provider.py tests/test_provider.py
git commit -m "feat: add market data provider with parquet cache"
```

---

### Task 7: Broker abstraction + ccxt broker

**Files:**
- Create: `broker/base.py`, `broker/ccxt_broker.py`
- Test: `tests/test_broker.py`

**Interfaces:**
- Consumes: `ccxt` (only here and in `cli.py`).
- Produces:
  - `Order` dataclass: `symbol: str`, `side: str`, `qty: float`, `type: str = "market"`, `price: float | None = None`, `client_id: str | None = None`.
  - `Broker` ABC: abstract methods `fetch_ohlcv`, `fetch_balance`, `place_order`, `cancel_order`, `fetch_open_orders`.
  - `CcxtBroker(Broker)` — `__init__(exchange_id, api_key="", api_secret="", testnet=True)` builds a ccxt exchange (with `enableRateLimit=True`) and calls `set_sandbox_mode(True)` when `testnet`. `place_order` maps `Order.client_id` → ccxt `params["clientOrderId"]`.

- [ ] **Step 1: Write the failing test `tests/test_broker.py`**

```python
from broker.base import Order
from broker.ccxt_broker import CcxtBroker


class FakeCcxt:
    def __init__(self):
        self.calls = []

    def create_order(self, **kwargs):
        self.calls.append(("create_order", kwargs))
        return {"id": "1"}

    def fetch_ohlcv(self, symbol, timeframe="1h", limit=500):
        self.calls.append(("fetch_ohlcv", symbol, timeframe, limit))
        return []


def test_order_defaults():
    o = Order(symbol="BTC/USDT", side="buy", qty=0.1)
    assert o.type == "market"
    assert o.price is None
    assert o.client_id is None


def test_place_order_maps_client_id():
    broker = CcxtBroker("binance", testnet=True)  # offline construction
    broker.exchange = FakeCcxt()                   # swap in a recorder
    broker.place_order(Order(symbol="BTC/USDT", side="buy", qty=0.1, client_id="bot-abc"))
    name, kwargs = broker.exchange.calls[0]
    assert name == "create_order"
    assert kwargs["side"] == "buy"
    assert kwargs["amount"] == 0.1
    assert kwargs["params"]["clientOrderId"] == "bot-abc"


def test_fetch_ohlcv_delegates():
    broker = CcxtBroker("binance", testnet=True)
    broker.exchange = FakeCcxt()
    broker.fetch_ohlcv("ETH/USDT", "4h", 10)
    assert broker.exchange.calls[0] == ("fetch_ohlcv", "ETH/USDT", "4h", 10)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `source .venv/bin/activate && pytest tests/test_broker.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'broker.ccxt_broker'`.

- [ ] **Step 3: Write `broker/base.py`**

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Order:
    symbol: str
    side: str            # "buy" | "sell"
    qty: float
    type: str = "market"
    price: float | None = None
    client_id: str | None = None


class Broker(ABC):
    @abstractmethod
    def fetch_ohlcv(self, symbol, timeframe="1h", limit=500): ...

    @abstractmethod
    def fetch_balance(self) -> dict: ...

    @abstractmethod
    def place_order(self, order: Order) -> dict: ...

    @abstractmethod
    def cancel_order(self, order_id: str, symbol: str) -> dict: ...

    @abstractmethod
    def fetch_open_orders(self, symbol=None) -> list: ...
```

- [ ] **Step 4: Write `broker/ccxt_broker.py`**

```python
import ccxt

from broker.base import Broker, Order


class CcxtBroker(Broker):
    def __init__(self, exchange_id: str, api_key: str = "", api_secret: str = "", testnet: bool = True):
        exchange_class = getattr(ccxt, exchange_id)
        self.exchange = exchange_class(
            {"apiKey": api_key, "secret": api_secret, "enableRateLimit": True}
        )
        if testnet:
            self.exchange.set_sandbox_mode(True)

    def fetch_ohlcv(self, symbol, timeframe="1h", limit=500):
        return self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    def fetch_balance(self) -> dict:
        return self.exchange.fetch_balance()

    def place_order(self, order: Order) -> dict:
        params = {}
        if order.client_id:
            params["clientOrderId"] = order.client_id
        return self.exchange.create_order(
            symbol=order.symbol,
            type=order.type,
            side=order.side,
            amount=order.qty,
            price=order.price,
            params=params,
        )

    def cancel_order(self, order_id: str, symbol: str) -> dict:
        return self.exchange.cancel_order(order_id, symbol)

    def fetch_open_orders(self, symbol=None) -> list:
        return self.exchange.fetch_open_orders(symbol)
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `source .venv/bin/activate && pytest tests/test_broker.py`
Expected: `3 passed`.

- [ ] **Step 6: Commit**

```bash
git add broker/base.py broker/ccxt_broker.py tests/test_broker.py
git commit -m "feat: add broker abstraction and ccxt broker"
```

---

### Task 8: CLI wiring + end-to-end integration test

**Files:**
- Create: `cli.py`
- Test: `tests/test_integration.py`

**Interfaces:**
- Consumes: `config.settings.load_settings` (Task 2), `data.provider.MarketDataProvider` (Task 6), `strategies.ma_crossover.MACrossover` (Task 3), `backtest.engine.run_backtest` (Task 5), `backtest.metrics.*` (Task 4), and `ccxt` (for the live `fetch` command).
- Produces: `cli.py` with argparse subcommands `fetch` and `backtest`, plus module-level `cmd_fetch(args)` and `cmd_backtest(args)` and `build_parser()` for testability.

- [ ] **Step 1: Write the failing integration test `tests/test_integration.py`**

```python
import pandas as pd

from data.provider import MarketDataProvider
from strategies.ma_crossover import MACrossover
from backtest.engine import run_backtest
from backtest.metrics import total_return, max_drawdown


class FakeExchange:
    def fetch_ohlcv(self, symbol, timeframe="1h", limit=500):
        # Deterministic V-shape: down then up, 60 bars so warmup(50) is satisfied.
        prices = [100 - i for i in range(30)] + [70 + i for i in range(30)]
        base_ts = 1609459200000
        return [[base_ts + i * 3600000, p, p, p, float(p), 1.0] for i, p in enumerate(prices)]


def test_fetch_then_backtest_end_to_end(tmp_path):
    prov = MarketDataProvider(FakeExchange(), cache_dir=str(tmp_path))
    prov.fetch("BTC/USDT", "1h", limit=60)
    df = prov.load_cached("BTC/USDT", "1h")

    res = run_backtest(df, MACrossover(fast=5, slow=10), initial_cash=1000.0, fee=0.001, warmup=10)

    assert isinstance(res.equity, pd.Series)
    assert len(res.equity) == 60
    assert res.final_equity > 0
    # metrics compute without error
    assert isinstance(total_return(res.equity), float)
    assert max_drawdown(res.equity) <= 0.0
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `source .venv/bin/activate && pytest tests/test_integration.py`
Expected: The imports resolve (Tasks 3–6 exist), but if you run before writing `cli.py` this test still passes on its own — that's fine; it validates the wiring. If it fails, it's a real integration bug to fix before proceeding.

> Note: this integration test intentionally does not import `cli.py` (which needs network for `fetch`). `cli.py` is verified by the manual smoke in Step 5.

- [ ] **Step 3: Write `cli.py`**

```python
import argparse

import ccxt

from config.settings import load_settings
from data.provider import MarketDataProvider
from strategies.ma_crossover import MACrossover
from backtest.engine import run_backtest
from backtest.metrics import total_return, max_drawdown, sharpe_ratio


def cmd_fetch(args):
    settings = load_settings()
    exchange = getattr(ccxt, settings.exchange_id)({"enableRateLimit": True})
    prov = MarketDataProvider(exchange)
    df = prov.fetch(args.symbol, args.timeframe, args.limit)
    print(f"Fetched {len(df)} candles for {args.symbol} {args.timeframe}; cached.")


def cmd_backtest(args):
    prov = MarketDataProvider(exchange=None)
    df = prov.load_cached(args.symbol, args.timeframe)
    res = run_backtest(df, MACrossover(fast=args.fast, slow=args.slow))
    print(f"Bars:          {len(res.equity)}")
    print(f"Final equity:  {res.final_equity:,.2f}")
    print(f"Total return:  {total_return(res.equity):.2%}")
    print(f"Max drawdown:  {max_drawdown(res.equity):.2%}")
    print(f"Sharpe:        {sharpe_ratio(res.equity):.2f}")
    print(f"Trades:        {len(res.trades)}")


def build_parser():
    p = argparse.ArgumentParser(prog="trading-bot")
    sub = p.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch", help="fetch & cache candles from the exchange")
    f.add_argument("--symbol", default="BTC/USDT")
    f.add_argument("--timeframe", default="1h")
    f.add_argument("--limit", type=int, default=500)
    f.set_defaults(func=cmd_fetch)

    b = sub.add_parser("backtest", help="run MA-crossover backtest on cached candles")
    b.add_argument("--symbol", default="BTC/USDT")
    b.add_argument("--timeframe", default="1h")
    b.add_argument("--fast", type=int, default=20)
    b.add_argument("--slow", type=int, default=50)
    b.set_defaults(func=cmd_backtest)

    return p


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the full test suite**

Run: `source .venv/bin/activate && pytest`
Expected: all tests pass (sanity + config + strategy + metrics + engine + provider + broker + integration).

- [ ] **Step 5: Manual smoke test against the live exchange (public data, no keys needed)**

Run:
```bash
source .venv/bin/activate
python cli.py fetch --symbol BTC/USDT --timeframe 1h --limit 300
python cli.py backtest --symbol BTC/USDT --timeframe 1h --fast 20 --slow 50
```
Expected: `fetch` prints "Fetched 300 candles ..."; `backtest` prints a metrics block (Final equity, Total return, Max drawdown, Sharpe, Trades). Exact numbers depend on live market data.

> If `fetch` fails with a geo/exchange error, set `EXCHANGE_ID=kraken` in `.env` and retry — public OHLCV works without API keys on most exchanges.

- [ ] **Step 6: Commit**

```bash
git add cli.py tests/test_integration.py
git commit -m "feat: add CLI (fetch/backtest) and end-to-end integration test"
```

---

## Definition of Done (Phase 0)

- `pytest` is green across all 8 test files.
- `python cli.py fetch` caches real candles; `python cli.py backtest` prints metrics.
- `.env` is git-ignored and never committed; `.env.example` documents key hygiene.
- Broker abstraction is in place (`Broker` ABC + `CcxtBroker`, testnet default) — no live orders placed.
- The codebase matches the file structure above, ready for Phase 1 (more strategies, walk-forward) and Phase 2 (risk manager + kill-switch, live testnet trading loop).

## Self-Review Notes

- **Spec coverage:** data layer (Task 6), strategy engine (Tasks 3), backtest (Tasks 4–5), broker abstraction (Task 7), config/secrets (Tasks 1–2), CLI/wiring (Task 8). Risk manager, monitoring/alerts, and the live trading loop are explicitly deferred to Phase 2 per the blueprint roadmap — not gaps.
- **Type consistency:** `Signal.action`/`reason`, `Order` fields, `BacktestResult.equity/trades/final_equity`, and metric signatures are used identically across tasks.
- **No placeholders:** every code and test step contains complete, runnable code.
