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
