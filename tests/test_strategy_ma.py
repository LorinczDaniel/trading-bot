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
