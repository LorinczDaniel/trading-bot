import pandas as pd
import pytest

from data.binance_archive import (
    summarise_book_depth,
    summarise_metrics,
    BOOK_LEVELS,
)


def _depth_rows(ts, bid_depth, ask_depth):
    """One snapshot: five bid bands (negative pct) and five ask bands."""
    rows = []
    for lvl in range(1, 6):
        rows.append({"timestamp": ts, "percentage": -lvl,
                     "depth": bid_depth * lvl, "notional": bid_depth * lvl * 100})
        rows.append({"timestamp": ts, "percentage": lvl,
                     "depth": ask_depth * lvl, "notional": ask_depth * lvl * 100})
    return rows


# --- book depth ------------------------------------------------------------


def test_balanced_book_has_zero_imbalance():
    df = pd.DataFrame(_depth_rows("2026-01-01 00:00:00", 100.0, 100.0))
    out = summarise_book_depth(df)
    assert out["imbalance_1"].iloc[0] == pytest.approx(0.0)
    assert out["imbalance_5"].iloc[0] == pytest.approx(0.0)


def test_bid_heavy_book_is_positive_imbalance():
    """Sign convention: more bids than asks is POSITIVE, i.e. buying pressure.
    Getting this backwards would invert every downstream result silently."""
    df = pd.DataFrame(_depth_rows("2026-01-01 00:00:00", 300.0, 100.0))
    out = summarise_book_depth(df)
    assert out["imbalance_1"].iloc[0] == pytest.approx(0.5)


def test_ask_heavy_book_is_negative_imbalance():
    df = pd.DataFrame(_depth_rows("2026-01-01 00:00:00", 100.0, 300.0))
    assert summarise_book_depth(pd.DataFrame(df))["imbalance_1"].iloc[0] < 0


def test_snapshots_are_averaged_into_one_row_per_day():
    rows = (_depth_rows("2026-01-01 00:00:00", 300.0, 100.0)
            + _depth_rows("2026-01-01 12:00:00", 100.0, 300.0)
            + _depth_rows("2026-01-02 00:00:00", 200.0, 200.0))
    out = summarise_book_depth(pd.DataFrame(rows))
    assert len(out) == 2
    # Day 1 averages a bid-heavy and an ask-heavy snapshot -> roughly flat.
    assert out["imbalance_1"].iloc[0] == pytest.approx(0.0, abs=0.01)
    assert out["imbalance_1"].iloc[1] == pytest.approx(0.0)


def test_the_five_percent_band_aggregates_all_levels():
    """imbalance_5 must use the whole book out to 5%, not just the 5% band, or
    it measures a thin outer slice rather than total depth."""
    rows = [{"timestamp": "2026-01-01 00:00:00", "percentage": -1,
             "depth": 100.0, "notional": 1.0},
            {"timestamp": "2026-01-01 00:00:00", "percentage": -5,
             "depth": 900.0, "notional": 1.0},
            {"timestamp": "2026-01-01 00:00:00", "percentage": 1,
             "depth": 100.0, "notional": 1.0},
            {"timestamp": "2026-01-01 00:00:00", "percentage": 5,
             "depth": 100.0, "notional": 1.0}]
    out = summarise_book_depth(pd.DataFrame(rows))
    # bids 1000 vs asks 200 -> (1000-200)/1200
    assert out["imbalance_5"].iloc[0] == pytest.approx(800 / 1200)


def test_book_levels_are_the_documented_ones():
    assert BOOK_LEVELS == (1, 5)


def test_empty_depth_input_returns_empty_not_an_error():
    out = summarise_book_depth(pd.DataFrame(
        columns=["timestamp", "percentage", "depth", "notional"]))
    assert out.empty


# --- metrics ---------------------------------------------------------------


def _metric_rows(ts_list, oi, ratio):
    return pd.DataFrame({
        "create_time": ts_list,
        "symbol": ["BTCUSDT"] * len(ts_list),
        "sum_open_interest": [oi] * len(ts_list),
        "sum_open_interest_value": [oi * 1000.0] * len(ts_list),
        "count_toptrader_long_short_ratio": [ratio] * len(ts_list),
        "sum_toptrader_long_short_ratio": [ratio] * len(ts_list),
        "count_long_short_ratio": [ratio] * len(ts_list),
        "sum_taker_long_short_vol_ratio": [ratio] * len(ts_list),
    })


def test_metrics_collapse_to_one_row_per_day():
    df = _metric_rows(["2026-01-01 00:05:00", "2026-01-01 12:00:00",
                       "2026-01-02 00:05:00"], 100.0, 1.5)
    out = summarise_metrics(df)
    assert len(out) == 2
    assert out.index[0] == pd.Timestamp("2026-01-01")


def test_open_interest_uses_the_last_reading_of_the_day():
    """OI is a stock, not a flow. Averaging it across the day blurs the level a
    next-day signal would actually have seen at the close."""
    df = _metric_rows(["2026-01-01 00:05:00", "2026-01-01 23:55:00"], 100.0, 1.0)
    df.loc[1, "sum_open_interest"] = 250.0
    out = summarise_metrics(df)
    assert out["open_interest"].iloc[0] == 250.0


def test_ratios_are_averaged_over_the_day():
    df = _metric_rows(["2026-01-01 00:05:00", "2026-01-01 23:55:00"], 100.0, 1.0)
    df.loc[1, "sum_toptrader_long_short_ratio"] = 3.0
    out = summarise_metrics(df)
    assert out["toptrader_ls"].iloc[0] == pytest.approx(2.0)


def test_missing_columns_do_not_crash_the_summary():
    """Binance changed this schema over time; early files lack some columns."""
    df = pd.DataFrame({"create_time": ["2026-01-01 00:05:00"],
                       "sum_open_interest": [100.0]})
    out = summarise_metrics(df)
    assert len(out) == 1
    assert out["open_interest"].iloc[0] == 100.0
