import pandas as pd
import pytest

from backtest.metrics import (
    total_return,
    max_drawdown,
    sharpe_ratio,
    buy_and_hold_return,
)


def test_total_return():
    assert total_return(pd.Series([100.0, 110.0])) == pytest.approx(0.10)


def test_max_drawdown():
    # peak 120 -> trough 60 => 60/120 - 1 = -0.5
    assert max_drawdown(pd.Series([100.0, 120.0, 60.0, 80.0])) == pytest.approx(-0.5)


def test_max_drawdown_monotonic_up_is_zero():
    assert max_drawdown(pd.Series([100.0, 110.0, 120.0])) == pytest.approx(0.0)


def test_sharpe_zero_when_flat():
    assert sharpe_ratio(pd.Series([100.0, 100.0, 100.0])) == 0.0


def test_buy_and_hold_no_fee():
    # 100 -> 120 is +20%
    assert buy_and_hold_return(pd.Series([100.0, 110.0, 120.0]), fee=0.0) == pytest.approx(0.20)


def test_buy_and_hold_with_entry_fee():
    # 1.20 * (1 - 0.01) - 1 = 0.188
    assert buy_and_hold_return(pd.Series([100.0, 120.0]), fee=0.01) == pytest.approx(0.188)
