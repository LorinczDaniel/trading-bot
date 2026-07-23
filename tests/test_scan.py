import pandas as pd
import pytest

from backtest.scan import total_fees, fee_drag, trades_per_day, worst_cumulative_loss


def test_total_fees_sums_and_tolerates_blanks():
    fills = [{"fee": 1.5}, {"fee": 2.0}, {"fee": ""}, {}]
    assert total_fees(fills) == pytest.approx(3.5)


def test_fee_drag_is_cost_over_activity():
    fills = [{"fee": 5.0}, {"fee": 5.0}]
    trades = [{"pnl": 50.0}]
    assert fee_drag(fills, trades) == pytest.approx(0.2)


def test_fee_drag_uses_absolute_gross_pnl():
    """A losing strategy still has measurable activity to compare fees against."""
    fills = [{"fee": 5.0}, {"fee": 5.0}]
    trades = [{"pnl": -50.0}]
    assert fee_drag(fills, trades) == pytest.approx(0.2)


def test_fee_drag_is_infinite_when_nothing_moved():
    """Paid fees, produced no P&L — the worst case, not an undefined one."""
    assert fee_drag([{"fee": 5.0}], []) == float("inf")
    assert fee_drag([{"fee": 5.0}], [{"pnl": 0.0}]) == float("inf")


def test_trades_per_day_over_a_timestamp_index():
    index = pd.to_datetime(["2026-01-01", "2026-01-11"])
    assert trades_per_day(20, index) == pytest.approx(2.0)


def test_trades_per_day_on_a_zero_span_index():
    index = pd.to_datetime(["2026-01-01", "2026-01-01"])
    assert trades_per_day(5, index) == float("inf")
    assert trades_per_day(0, index) == 0.0


def test_worst_cumulative_loss_finds_the_deepest_point():
    # running total: -100, -250, -50  -> deepest is -250 on 10_000 = 2.5%
    trades = [{"pnl": -100.0}, {"pnl": -150.0}, {"pnl": 200.0}]
    assert worst_cumulative_loss(trades, 10_000.0) == pytest.approx(0.025)


def test_worst_cumulative_loss_is_zero_when_never_negative():
    trades = [{"pnl": 100.0}, {"pnl": 50.0}]
    assert worst_cumulative_loss(trades, 10_000.0) == 0.0
