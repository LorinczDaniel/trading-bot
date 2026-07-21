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
