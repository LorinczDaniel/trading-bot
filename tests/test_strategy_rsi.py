import pandas as pd
import pytest

from strategies.rsi_reversion import RSIReversion


def _df(prices):
    return pd.DataFrame({"close": prices})


def test_invalid_thresholds_raise():
    with pytest.raises(ValueError):
        RSIReversion(low=70, high=30)


def test_buy_when_oversold():
    # strictly falling -> RSI 0 -> oversold -> BUY
    sig = RSIReversion(period=14).generate(_df(list(range(40, 10, -1))))
    assert sig.action == "BUY"


def test_sell_when_overbought():
    # strictly rising -> RSI 100 -> overbought -> SELL
    sig = RSIReversion(period=14).generate(_df(list(range(10, 40))))
    assert sig.action == "SELL"


def test_hold_when_neutral():
    # oscillating up/down -> RSI ~50 -> HOLD
    sig = RSIReversion(period=14).generate(_df([100, 101] * 10))
    assert sig.action == "HOLD"


def test_hold_when_not_enough_data():
    sig = RSIReversion(period=14).generate(_df([1, 2, 3, 4, 5]))
    assert sig.action == "HOLD"
    assert "not enough data" in sig.reason
