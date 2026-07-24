import pandas as pd
import pytest

from data.pit import members_at, build_volume_panel, MIN_HISTORY_BARS


def _idx(n, start="2026-01-01"):
    return pd.date_range(start, periods=n, freq="1D")


def _frame(closes, volumes):
    return pd.DataFrame({"close": closes, "volume": volumes}, index=_idx(len(closes)))


# --- volume panel ----------------------------------------------------------


def test_build_volume_panel_uses_quote_volume_not_base_volume():
    """Ranking on base volume would rank a coin priced at $0.0001 above one
    priced at $50,000 purely because more units change hands. Liquidity is a
    money quantity, so the panel must carry price * volume."""
    frames = {"A/USDT": _frame([2.0, 2.0], [100.0, 100.0])}
    vol = build_volume_panel(frames)
    assert vol.loc[vol.index[0], "A/USDT"] == pytest.approx(200.0)


def test_volume_panel_is_nan_where_a_coin_has_no_bar():
    frames = {
        "A/USDT": _frame([1.0, 1.0, 1.0], [10.0, 10.0, 10.0]),
        "B/USDT": pd.DataFrame({"close": [1.0], "volume": [10.0]},
                               index=_idx(1, "2026-01-03")),
    }
    vol = build_volume_panel(frames)
    assert pd.isna(vol.loc[pd.Timestamp("2026-01-01"), "B/USDT"])


# --- point-in-time membership ---------------------------------------------


def test_membership_ranks_by_trailing_volume_at_that_date():
    n = 120
    vol = pd.DataFrame({
        "BIG/USDT": [1000.0] * n,
        "SMALL/USDT": [1.0] * n,
    }, index=_idx(n))
    members = members_at(vol, vol.index[100], top_n=1, lookback=30)
    assert members == ["BIG/USDT"]


def test_membership_changes_as_volume_changes():
    """The whole point: a coin that was liquid in 2023 and dead in 2025 must be
    a member in 2023 and not in 2025."""
    n = 200
    early_big = [1000.0] * 100 + [1.0] * 100
    late_big = [1.0] * 100 + [1000.0] * 100
    vol = pd.DataFrame({"EARLY/USDT": early_big, "LATE/USDT": late_big},
                       index=_idx(n))
    assert members_at(vol, vol.index[90], top_n=1, lookback=30) == ["EARLY/USDT"]
    assert members_at(vol, vol.index[190], top_n=1, lookback=30) == ["LATE/USDT"]


def test_membership_never_reads_the_future():
    """The decisive property. A coin with zero volume up to date t and enormous
    volume after must NOT be a member at t."""
    n = 200
    vol = pd.DataFrame({
        "STEADY/USDT": [10.0] * n,
        "LATER/USDT": [0.0] * 100 + [1_000_000.0] * 100,
    }, index=_idx(n))
    members = members_at(vol, vol.index[99], top_n=1, lookback=30)
    assert members == ["STEADY/USDT"]


def test_a_coin_without_enough_history_is_not_a_member():
    """A two-week-old listing has no trailing record to rank on, and admitting
    it lets a brand-new coin displace an established one on a few noisy days."""
    n = 120
    vol = pd.DataFrame({
        "OLD/USDT": [10.0] * n,
        "NEW/USDT": [float("nan")] * (n - 5) + [1_000_000.0] * 5,
    }, index=_idx(n))
    members = members_at(vol, vol.index[-1], top_n=5, lookback=30)
    assert "NEW/USDT" not in members
    assert "OLD/USDT" in members


def test_the_history_requirement_is_the_documented_one():
    assert MIN_HISTORY_BARS == 90


def test_a_coin_with_no_volume_at_all_is_excluded():
    n = 120
    vol = pd.DataFrame({"A/USDT": [10.0] * n, "ZERO/USDT": [0.0] * n}, index=_idx(n))
    assert members_at(vol, vol.index[-1], top_n=5, lookback=30) == ["A/USDT"]


def test_membership_is_capped_at_top_n():
    n = 120
    vol = pd.DataFrame({f"C{i}/USDT": [float(i + 1)] * n for i in range(10)},
                       index=_idx(n))
    assert len(members_at(vol, vol.index[-1], top_n=3, lookback=30)) == 3


def test_membership_before_any_history_exists_is_empty():
    n = 120
    vol = pd.DataFrame({"A/USDT": [10.0] * n}, index=_idx(n))
    assert members_at(vol, vol.index[5], top_n=5, lookback=30) == []


def test_membership_is_ordered_most_liquid_first():
    n = 120
    vol = pd.DataFrame({
        "MID/USDT": [50.0] * n,
        "TOP/USDT": [500.0] * n,
        "LOW/USDT": [5.0] * n,
    }, index=_idx(n))
    assert members_at(vol, vol.index[-1], top_n=3, lookback=30) == [
        "TOP/USDT", "MID/USDT", "LOW/USDT"]
