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
           "folds_traded": 3, "folds_positive_oos": 3,
           "avg_is": 0.10, "avg_oos": 0.04,
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


def test_unstable_fails_when_a_minority_of_folds_survive_out_of_sample():
    """Gate 5, respecified 2026-07-24. The config that PASSed the old
    `overfit` rule -- `4h ma+trend`, 2 traded folds, one positive and one
    negative out-of-sample -- must now fail: an average carried by a single
    fold is not evidence of anything."""
    row = _passing_row(folds_traded=2, folds_positive_oos=1)
    assert verdict(row) == ("FAIL", "unstable")


def test_a_majority_of_positive_folds_passes():
    assert verdict(_passing_row(folds_traded=4, folds_positive_oos=3)) == ("PASS", "")


def test_a_tie_is_not_a_majority():
    """Half the folds positive is a coin flip, so it fails. Pins the rule as
    strictly-more-than-half rather than at-least-half."""
    row = _passing_row(folds_traded=4, folds_positive_oos=2)
    assert verdict(row) == ("FAIL", "unstable")


def test_stability_does_not_read_the_average_returns():
    """The gate must not regress to the old avg_is/avg_oos rule. This row is
    stable by fold count but would have FAILed `overfit` (avg_is > 0,
    avg_oos < 0) -- a positive average is no longer required, and a negative
    one is no longer disqualifying, because on a pinned grid those averages
    measure window drift, not curve-fitting. See
    docs/research/2026-07-24-overfit-gate-is-measuring-window-drift.md."""
    row = _passing_row(folds_traded=3, folds_positive_oos=2,
                       avg_is=0.20, avg_oos=-0.05)
    assert verdict(row) == ("PASS", "")


def test_losing_fails_when_an_otherwise_clean_config_makes_no_money():
    """Gate 6 (added 2026-07-23): net_return <= 0 fails even though every
    other gate is clear."""
    assert verdict(_passing_row(net_return=-0.01)) == ("FAIL", "losing")


def test_positive_net_return_still_passes():
    """A profitable, otherwise-clean config is unaffected by the new gate."""
    assert verdict(_passing_row(net_return=0.02)) == ("PASS", "")


def test_unstable_is_reported_before_losing():
    """A config that is both unstable and losing must report `unstable` — this
    pins gate 6 as strictly last, after gate 5, not before it."""
    row = _passing_row(folds_traded=2, folds_positive_oos=0, net_return=-0.01)
    assert verdict(row) == ("FAIL", "unstable")


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
            "oos_gap": 0.05, "folds_traded": 3, "folds_positive_oos": 2,
            "verdict": v, "reason": reason}


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


def test_format_table_shows_the_fold_counts_the_stability_gate_reads():
    """Gate 5 reads `folds_positive_oos` against `folds_traded`, so both must
    be visible on the row. Printing only the average returns would leave a
    `FAIL unstable` verdict unverifiable against its own table — the same
    reason avgIS/avgOOS were printed when the old gate read them."""
    row = _row("ma", "FAIL", "unstable")
    row["folds_traded"] = 2
    row["folds_positive_oos"] = 1

    out = format_table([row])
    header, body = out.splitlines()[0], out.splitlines()[2]

    assert "posOOS" in header
    # The count itself must appear under that column, not just the header.
    # `posOOS` is a 6-wide right-aligned field, so the header label starts
    # exactly where the body cell starts.
    col = header.index("posOOS")
    assert body[col:col + 6].strip() == "1"
    # And the neighbouring `folds` cell must still read 2 — proof the two
    # counts the gate compares are separately legible, not one merged column.
    fold_col = header.index("folds")
    assert body[fold_col:fold_col + 5].strip() == "2"


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


def test_scan_one_benchmarks_edge_over_the_traded_window_not_bar_zero():
    """`net_return` comes from the equity Series, which starts at bar
    `warmup`; the buy&hold baseline must be measured over that same window,
    not from bar 0, or `edge = net - hold` subtracts returns measured over
    different spans.

    Confines a huge, one-off price move to the warmup region (never seen
    again afterward), so the bar-0 baseline and the bar-`warmup` baseline
    diverge sharply. This would fail under the old
    `buy_and_hold_return(df["close"], fee=fee)` call, which baselined from
    bar 0.
    """
    import numpy as np
    from backtest.scan import scan_one
    from backtest.metrics import buy_and_hold_return

    warmup = 50
    n = 400
    # Warmup region: a violent, one-off run-up (100 -> ~1080).
    warmup_prices = [100.0 + i * 20.0 for i in range(warmup)]
    # Traded region: mild oscillation around the post-warmup level -- no
    # drift remotely comparable to the warmup move.
    rest_prices = [1080.0 + 10.0 * np.sin(i / 5.0) for i in range(n - warmup)]
    close = warmup_prices + rest_prices
    index = pd.date_range("2026-01-01", periods=n, freq="1h")
    df = pd.DataFrame({"close": close}, index=index)

    fee = 0.001
    row = scan_one(df, "BTC/USDT", "1h", "ma", warmup=warmup, splits=2, fee=fee)

    hold = row["net_return"] - row["edge"]
    expected_hold = buy_and_hold_return(df["close"].iloc[warmup:], fee=fee)
    bar_zero_hold = buy_and_hold_return(df["close"], fee=fee)

    assert hold == pytest.approx(expected_hold)
    # The two baselines must differ hugely -- proof this test would have
    # caught the old bar-0 baseline instead of silently agreeing with it.
    assert abs(expected_hold - bar_zero_hold) > 1.0


def test_scan_one_pins_walk_forward_to_the_default_params(monkeypatch):
    """Walk-forward inside `scan_one` must evaluate the SAME fixed params the
    headline metrics report -- not a grid re-optimized per fold -- or the
    `unstable`/`insufficient-folds` gates judge a different configuration than
    every other gate on the row.

    Captures the grid `scan_one` actually hands to `walk_forward` (not just
    the resulting `best_params`): a one-entry grid pinned to the factory
    default is the only thing that makes this deterministic. Checking
    `best_params` alone would be data-dependent -- a widened, multi-entry
    grid could still happen to pick the default on every fold for a given
    dataset and pass spuriously. Asserting the grid itself fails immediately,
    regardless of data, if the grid were ever widened back to multiple
    entries.
    """
    import numpy as np
    import backtest.scan as scan_mod
    from strategies.factory import default_params

    captured = {}
    real_walk_forward = scan_mod.walk_forward

    def spy(df, make_strategy, grid, **kwargs):
        captured["grid"] = grid
        folds = real_walk_forward(df, make_strategy, grid, **kwargs)
        captured["folds"] = folds
        return folds

    monkeypatch.setattr(scan_mod, "walk_forward", spy)

    n = 2000
    rng = np.random.default_rng(1)
    # Mild upward drift plus noise: enough crossovers for MA(20,50) to trade
    # repeatedly within each walk-forward fold.
    close = 100 + np.cumsum(rng.normal(0.05, 1.0, n))
    index = pd.date_range("2026-01-01", periods=n, freq="1h")
    df = pd.DataFrame({"close": close}, index=index)

    scan_mod.scan_one(df, "BTC/USDT", "1h", "ma", warmup=60, splits=3)

    assert captured["grid"] == [default_params("ma")]

    valid_folds = [f for f in captured["folds"] if f["valid"]]
    assert valid_folds, "expected at least one valid (traded) fold"
    for f in valid_folds:
        assert f["best_params"] == default_params("ma")


def test_scan_one_counts_only_traded_folds_that_were_positive_out_of_sample():
    """`folds_positive_oos` must count folds whose OOS return is strictly
    positive, among the traded folds only — an invalid or non-trading fold is
    absent evidence, not positive evidence.

    Drives `walk_forward` through a stub so the fold shape is exact and the
    assertion cannot drift with the price data: 4 folds, of which one is
    invalid, one traded at a loss, and two traded profitably.
    """
    import numpy as np
    import backtest.scan as scan_mod

    folds = [
        {"fold": 0, "valid": True, "best_params": (20, 50),
         "in_sample_return": 0.05, "in_sample_trades": 9,
         "oos_return": 0.03, "oos_trades": 5},
        {"fold": 1, "valid": False, "best_params": None,
         "in_sample_return": 0.0, "in_sample_trades": 0,
         "oos_return": 0.0, "oos_trades": 0},
        {"fold": 2, "valid": True, "best_params": (20, 50),
         "in_sample_return": 0.04, "in_sample_trades": 8,
         "oos_return": -0.02, "oos_trades": 6},
        {"fold": 3, "valid": True, "best_params": (20, 50),
         "in_sample_return": 0.01, "in_sample_trades": 7,
         "oos_return": 0.06, "oos_trades": 4},
    ]
    monkey = lambda *a, **k: folds
    original = scan_mod.walk_forward
    scan_mod.walk_forward = monkey
    try:
        n = 400
        rng = np.random.default_rng(2)
        close = 100 + np.cumsum(rng.normal(0.05, 1.0, n))
        index = pd.date_range("2026-01-01", periods=n, freq="1h")
        df = pd.DataFrame({"close": close}, index=index)
        row = scan_mod.scan_one(df, "BTC/USDT", "1h", "ma", warmup=60, splits=4)
    finally:
        scan_mod.walk_forward = original

    assert row["folds_traded"] == 3
    assert row["folds_positive_oos"] == 2


def test_scan_one_does_not_count_a_breakeven_fold_as_positive():
    """Pins `> 0`, not `>= 0`: a fold that ended exactly flat produced no
    out-of-sample profit and must not prop up the majority."""
    import numpy as np
    import backtest.scan as scan_mod

    folds = [
        {"fold": 0, "valid": True, "best_params": (20, 50),
         "in_sample_return": 0.05, "in_sample_trades": 9,
         "oos_return": 0.0, "oos_trades": 5},
        {"fold": 1, "valid": True, "best_params": (20, 50),
         "in_sample_return": 0.04, "in_sample_trades": 8,
         "oos_return": 0.03, "oos_trades": 6},
    ]
    original = scan_mod.walk_forward
    scan_mod.walk_forward = lambda *a, **k: folds
    try:
        n = 400
        rng = np.random.default_rng(3)
        close = 100 + np.cumsum(rng.normal(0.05, 1.0, n))
        index = pd.date_range("2026-01-01", periods=n, freq="1h")
        df = pd.DataFrame({"close": close}, index=index)
        row = scan_mod.scan_one(df, "BTC/USDT", "1h", "ma", warmup=60, splits=2)
    finally:
        scan_mod.walk_forward = original

    assert row["folds_traded"] == 2
    assert row["folds_positive_oos"] == 1


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
