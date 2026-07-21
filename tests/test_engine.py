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
