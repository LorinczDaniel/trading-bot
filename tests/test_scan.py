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


from backtest.scan import verdict, MIN_TRADES, MAX_TRADES_PER_DAY, MAX_FEE_DRAG


def _passing_row(**overrides):
    row = {"trades": 50, "trades_per_day": 0.5, "fee_drag": 0.05,
           "folds_traded": 3, "avg_is": 0.10, "avg_oos": 0.04}
    row.update(overrides)
    return row


def test_thresholds_match_the_spec():
    assert MIN_TRADES == 20
    assert MAX_TRADES_PER_DAY == 6.0
    assert MAX_FEE_DRAG == 0.30


def test_a_good_config_passes():
    assert verdict(_passing_row()) == ("PASS", "")


def test_too_few_trades_fails():
    assert verdict(_passing_row(trades=19)) == ("FAIL", "too-few-trades")


def test_churn_fails():
    assert verdict(_passing_row(trades_per_day=6.1)) == ("FAIL", "churn")


def test_fee_drag_fails():
    assert verdict(_passing_row(fee_drag=0.31)) == ("FAIL", "fee-drag")


def test_infinite_fee_drag_fails():
    assert verdict(_passing_row(fee_drag=float("inf"))) == ("FAIL", "fee-drag")


def test_insufficient_folds_fails():
    assert verdict(_passing_row(folds_traded=1)) == ("FAIL", "insufficient-folds")


def test_overfit_fails_when_profit_does_not_survive_out_of_sample():
    assert verdict(_passing_row(avg_is=0.20, avg_oos=-0.05)) == ("FAIL", "overfit")


def test_losing_in_sample_is_not_overfit():
    """Bad in both halves is honest failure, not curve-fitting."""
    assert verdict(_passing_row(avg_is=-0.10, avg_oos=-0.05)) == ("PASS", "")


def test_boundaries_are_inclusive_where_the_spec_says_so():
    assert verdict(_passing_row(trades=MIN_TRADES)) == ("PASS", "")
    assert verdict(_passing_row(trades_per_day=MAX_TRADES_PER_DAY)) == ("PASS", "")
    assert verdict(_passing_row(fee_drag=MAX_FEE_DRAG)) == ("PASS", "")
