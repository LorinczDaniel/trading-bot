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
           "folds_traded": 3, "avg_is": 0.10, "avg_oos": 0.04,
           "net_return": 0.05}
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


def test_losing_fails_when_an_otherwise_clean_config_makes_no_money():
    """Gate 6 (added 2026-07-23): net_return <= 0 fails even though every
    other gate is clear."""
    assert verdict(_passing_row(net_return=-0.01)) == ("FAIL", "losing")


def test_positive_net_return_still_passes():
    """A profitable, otherwise-clean config is unaffected by the new gate."""
    assert verdict(_passing_row(net_return=0.02)) == ("PASS", "")


def test_overfit_is_reported_before_losing():
    """A config that is both overfit and losing must report `overfit` — this
    pins gate 6 as strictly last, after `overfit`, not before it."""
    row = _passing_row(avg_is=0.20, avg_oos=-0.05, net_return=-0.01)
    assert verdict(row) == ("FAIL", "overfit")


def test_breakeven_net_return_fails_the_losing_gate():
    """Pins the exact condition as `<= 0`, not `< 0`: breakeven is a fail."""
    assert verdict(_passing_row(net_return=0.0)) == ("FAIL", "losing")


def test_boundaries_are_inclusive_where_the_spec_says_so():
    assert verdict(_passing_row(trades=MIN_TRADES)) == ("PASS", "")
    assert verdict(_passing_row(trades_per_day=MAX_TRADES_PER_DAY)) == ("PASS", "")
    assert verdict(_passing_row(fee_drag=MAX_FEE_DRAG)) == ("PASS", "")


from backtest.scan import rank, format_table


def _row(strategy, v, reason="", edge=0.0):
    return {"symbol": "BTC/USDT", "timeframe": "1h", "strategy": strategy,
            "bars": 1000, "days": 41.7, "trades": 50, "trades_per_day": 1.2,
            "net_return": 0.05, "edge": edge, "max_drawdown": -0.08,
            "worst_loss": 0.03, "fee_drag": 0.1, "avg_is": 0.1, "avg_oos": 0.05,
            "oos_gap": 0.05, "folds_traded": 3, "verdict": v, "reason": reason}


def test_rank_puts_passing_configs_first_by_edge():
    rows = [_row("ma", "FAIL", "churn"),
            _row("rsi", "PASS", edge=0.01),
            _row("rsi+trend", "PASS", edge=0.09)]
    ranked = rank(rows)
    assert [r["strategy"] for r in ranked] == ["rsi+trend", "rsi", "ma"]


def test_rank_keeps_failures_rather_than_dropping_them():
    """Knowing why a config was rejected is the point of the output."""
    rows = [_row("ma", "FAIL", "churn"), _row("rsi", "FAIL", "fee-drag")]
    assert len(rank(rows)) == 2


def test_format_table_shows_the_failure_reason():
    out = format_table([_row("ma", "FAIL", "churn")])
    assert "churn" in out
    assert "ma" in out
    assert "BTC/USDT" in out


def test_format_table_stays_aligned_when_fee_drag_is_infinite():
    """fee_drag=inf is the documented worst case (fees paid, zero gross P&L).
    format(float("inf"), spec) pads correctly under a float spec; a row must
    not shift every later column by rendering a bare unpadded "inf" instead."""
    finite = _row("ma", "FAIL", "fee-drag")
    finite["fee_drag"] = 0.12
    infinite = _row("ma", "FAIL", "fee-drag")
    infinite["fee_drag"] = float("inf")

    out = format_table([finite, infinite])
    lines = out.splitlines()
    finite_line, infinite_line = lines[2], lines[3]

    # Only fee_drag differs between the two rows, so an aligned table must
    # produce two lines of identical length.
    assert len(infinite_line) == len(finite_line)
    # The inf cell must occupy its full 8-char column width (padded, like
    # Python's own float formatting), not collapse to a bare 3-char "inf"
    # that would shift every column after it.
    assert "     inf" in infinite_line
    # Everything after the feedrag column (avgIS onward) must land in the
    # same place on both lines — proof the shift didn't happen.
    assert infinite_line[infinite_line.index("     inf") + 8:] == \
        finite_line[finite_line.index("0.12") + 4:]


def test_scan_one_flags_a_churning_config():
    """Success criterion 3: the 1m config that churned in the live ledger must
    be rejected by a gate, not quietly ranked."""
    import numpy as np
    from backtest.scan import scan_one

    n = 3000
    # 1-minute bars of pure noise: crossovers fire constantly, nothing trends
    rng = np.random.default_rng(0)
    close = 65_000 + np.cumsum(rng.normal(0, 5, n))
    index = pd.date_range("2026-07-01", periods=n, freq="1min")
    df = pd.DataFrame({"close": close}, index=index)

    row = scan_one(df, "BTC/USDT", "1m", "ma", warmup=60, splits=2)

    assert row["verdict"] == "FAIL"
    assert row["reason"] == "churn"
