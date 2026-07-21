import pandas as pd

from strategies.base import Strategy, Signal
from strategies.trend_filter import TrendFilter


class StubStrategy(Strategy):
    def __init__(self, action):
        self.action = action

    def generate(self, df):
        return Signal(self.action)


def _df(prices):
    return pd.DataFrame({"close": prices})


def test_buy_allowed_in_uptrend():
    # last price 5 >= SMA(3)=(3+4+5)/3=4 -> uptrend -> BUY passes
    strat = TrendFilter(StubStrategy("BUY"), sma_period=3)
    assert strat.generate(_df([1, 2, 3, 4, 5])).action == "BUY"


def test_buy_suppressed_in_downtrend():
    # last price 1 < SMA(3)=(3+2+1)/3=2 -> downtrend -> BUY becomes HOLD
    strat = TrendFilter(StubStrategy("BUY"), sma_period=3)
    assert strat.generate(_df([5, 4, 3, 2, 1])).action == "HOLD"


def test_sell_passes_through_regardless():
    strat = TrendFilter(StubStrategy("SELL"), sma_period=3)
    assert strat.generate(_df([5, 4, 3, 2, 1])).action == "SELL"


def test_hold_passes_through():
    strat = TrendFilter(StubStrategy("HOLD"), sma_period=3)
    assert strat.generate(_df([1, 2, 3, 4, 5])).action == "HOLD"


def test_buy_suppressed_when_not_enough_data():
    strat = TrendFilter(StubStrategy("BUY"), sma_period=200)
    assert strat.generate(_df([1, 2, 3])).action == "HOLD"
