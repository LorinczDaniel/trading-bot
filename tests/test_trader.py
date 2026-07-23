import pandas as pd
import pytest

from broker.paper_broker import PaperBroker
from risk.manager import RiskConfig, RiskManager, RiskState
from monitoring.notifier import Notifier
from strategies.base import Strategy, Signal
from trader import Trader


class Scripted(Strategy):
    def __init__(self, actions):
        self.actions = actions  # {bar_index: action}

    def generate(self, df):
        return Signal(self.actions.get(len(df) - 1, "HOLD"))


class HoldStrategy(Strategy):
    lookback = 1

    def generate(self, df):
        return Signal("HOLD")


def _make(cash=1000.0, fee=0.0, config=None):
    broker = PaperBroker(cash=cash, fee=fee)
    risk = RiskManager(config or RiskConfig(stop_loss_pct=0.05))
    state = RiskState(cash)
    notifier = Notifier(echo=False)
    return broker, risk, state, notifier


def test_buy_then_sell_makes_profit():
    broker, risk, state, notifier = _make()
    trader = Trader("BTC/USDT", broker, Scripted({2: "BUY", 4: "SELL"}), risk, state, notifier, fee=0.0)
    df = pd.DataFrame({"close": [100.0, 100.0, 100.0, 110.0, 120.0]})
    trader.run_replay(df, warmup=0)
    assert broker.fetch_balance()["base"] == 0.0
    assert broker.equity(120.0) > 1000.0
    assert state.realized_pnl > 0.0


def test_stop_loss_exits_position():
    broker, risk, state, notifier = _make(config=RiskConfig(stop_loss_pct=0.05))
    trader = Trader("BTC/USDT", broker, Scripted({2: "BUY"}), risk, state, notifier, fee=0.0)
    # buy at 100 (stop 95), then price falls to 90 -> stop-loss fires
    df = pd.DataFrame({"close": [100.0, 100.0, 100.0, 90.0, 90.0]})
    trader.run_replay(df, warmup=0)
    assert broker.fetch_balance()["base"] == 0.0
    assert state.realized_pnl < 0.0
    assert any("stop-loss" in m.lower() for m in notifier.messages)


def test_kill_switch_blocks_buy():
    broker, risk, state, notifier = _make(config=RiskConfig(max_positions=0))
    trader = Trader("BTC/USDT", broker, Scripted({2: "BUY", 4: "SELL"}), risk, state, notifier, fee=0.0)
    df = pd.DataFrame({"close": [100.0, 100.0, 100.0, 110.0, 120.0]})
    trader.run_replay(df, warmup=0)
    assert broker.fetch_balance()["base"] == 0.0  # never entered
    assert any("blocked" in m.lower() for m in notifier.messages)


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


def test_run_replay_discriminates_sampling_order_pricing_and_index():
    """Regression for a review finding: test_run_replay_returns_per_bar_equity
    above uses HoldStrategy, which never opens a position. With base == 0,
    PaperBroker.equity(price) == quote regardless of price/timing/index, so
    that test passes identically even if run_replay (1) sampled equity BEFORE
    self.step() instead of after, (2) priced off df["close"].iloc[i - 1]
    instead of iloc[i], or (3) built the index positionally instead of from
    df.index[i]. This test closes that gap.

    A strategy that BUYs on the very first replayed bar, against a close
    series that changes on every bar, makes each subsequent equity value
    depend on both the exact price sampled and exactly when it is sampled
    relative to the trade. A real DatetimeIndex (via pd.date_range) means a
    positional index substitute can never accidentally coincide with the
    real one, unlike the default RangeIndex used elsewhere in this file.

    Price choice: strictly RISING after entry (rather than disabling
    trailing_stop). RiskConfig's default trailing_stop=True stays live and
    non-triggering throughout, which is closer to how run_replay is actually
    exercised than turning the feature off would be.

    Fee choice: a NONZERO broker fee (0.01), deliberately diverging from the
    "fee=0.0 for clean arithmetic" suggestion. This is forced, not stylistic:
    for a market order filled and valued at the same price P, equity(P) is
    exactly conserved when fee == 0 (quote and base just swap in equal
    value), so sampling equity before vs. after self.step() is mathematically
    indistinguishable at fee=0 on any bar, including the entry bar. A nonzero
    fee makes the buy strictly reduce equity(P) by qty*P*fee, giving mutation
    (1) something observable to fail on.
    """
    # close[0], close[1] are warmup bars, never priced or signalled on directly,
    # but deliberately distinct from close[2] so mutation (2) — pricing off the
    # previous bar — is caught even on the very first replayed bar.
    close = [90.0, 95.0, 100.0, 105.0, 110.0, 120.0]
    df = pd.DataFrame(
        {"close": close},
        index=pd.date_range("2024-01-01", periods=len(close), freq="D"),
    )
    cash, fee, warmup = 1000.0, 0.01, 2
    risk_per_trade, stop_loss_pct = 0.01, 0.05  # RiskConfig defaults, restated
    # explicitly so the expectation below doesn't read them back off the
    # object under test.

    broker, risk, state, notifier = _make(cash=cash, fee=fee)
    trader = Trader(
        "BTC/USDT", broker, Scripted({warmup: "BUY"}), risk, state, notifier, fee=0.0,
    )

    equity = trader.run_replay(df, warmup=warmup)

    # Independently computed expectation (mirrors, but does not call, the
    # position_size/place_order logic under test).
    entry_price = close[warmup]
    stop = entry_price * (1 - stop_loss_pct)
    qty = (cash * risk_per_trade) / (entry_price - stop)          # = 2.0
    remaining_cash = cash - qty * entry_price * (1 + fee)         # broker fee
    expected = [qty * c + remaining_cash for c in close[warmup:]]

    assert list(equity.index) == list(df.index[warmup:])
    assert equity.tolist() == pytest.approx(expected)
    # Sanity: rising prices mean the trailing stop never fires, so the
    # position opened on the entry bar is still fully open at the end.
    assert broker.fetch_balance()["base"] == pytest.approx(qty)


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
