import pandas as pd

from broker.paper_broker import PaperBroker
from risk.manager import RiskConfig, RiskManager, RiskState
from monitoring.notifier import Notifier
from strategies.base import Strategy, Signal
from trader import Trader


class Scripted(Strategy):
    def __init__(self, actions):
        self.actions = actions

    def generate(self, df):
        return Signal(self.actions.get(len(df) - 1, "HOLD"))


def _trader(trailing, notifier=None):
    broker = PaperBroker(cash=1000.0, fee=0.0)
    trader = Trader(
        "BTC/USDT", broker, Scripted({0: "BUY"}),
        RiskManager(RiskConfig(stop_loss_pct=0.10, trailing_stop=trailing)),
        RiskState(1000.0), notifier or Notifier(echo=False), fee=0.0,
    )
    return trader, broker


def test_trailing_stop_ratchets_up_and_never_down():
    trader, _ = _trader(trailing=True)
    trader.step(pd.DataFrame({"close": [100.0]}))                       # buy @100 -> stop 90
    assert round(trader.stop_price, 2) == 90.0
    trader.step(pd.DataFrame({"close": [100.0, 120.0]}))               # high 120 -> stop 108
    assert round(trader.stop_price, 2) == 108.0
    trader.step(pd.DataFrame({"close": [100.0, 120.0, 110.0]}))        # pullback -> stop holds
    assert round(trader.stop_price, 2) == 108.0


def test_trailing_stop_locks_gain_on_pullback():
    notifier = Notifier(echo=False)
    trader, broker = _trader(trailing=True, notifier=notifier)
    # run up to 130, then fall to 110 -> trailed stop (117) fires with a profit
    df = pd.DataFrame({"close": [100.0, 100.0, 100.0, 120.0, 130.0, 110.0]})
    trader.run_replay(df, warmup=0)
    assert broker.fetch_balance()["base"] == 0.0
    assert trader.state.realized_pnl > 0
    assert any("trailing-stop hit" in m for m in notifier.messages)


def test_without_trailing_the_fixed_stop_stays_put():
    # same path, fixed stop @90 is never touched -> still holding (exposed)
    trader, broker = _trader(trailing=False)
    df = pd.DataFrame({"close": [100.0, 100.0, 100.0, 120.0, 130.0, 110.0]})
    trader.run_replay(df, warmup=0)
    assert broker.fetch_balance()["base"] > 0.0
    assert round(trader.stop_price, 2) == 90.0  # never moved


def test_trailing_below_entry_still_labelled_plain_stop_loss():
    # price only falls -> trailing never lifts the stop above entry -> a normal stop-loss
    notifier = Notifier(echo=False)
    trader, broker = _trader(trailing=True, notifier=notifier)
    df = pd.DataFrame({"close": [100.0, 100.0, 88.0]})  # buy @100 (stop 90), drop to 88 -> stop
    trader.run_replay(df, warmup=0)
    assert broker.fetch_balance()["base"] == 0.0
    assert any("stop-loss hit" in m for m in notifier.messages)
    assert not any("trailing-stop hit" in m for m in notifier.messages)
