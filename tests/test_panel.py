import pandas as pd
import pytest

from data.panel import (
    build_panel,
    find_redenominations,
    realized_volatility,
    MAX_BAR_RETURN,
    MIN_VOLATILITY,
    MIN_VOLATILITY_BARS,
)


def _series(prices, start="2026-01-01"):
    idx = pd.date_range(start, periods=len(prices), freq="1D")
    return pd.DataFrame({"close": prices}, index=idx)


# --- redenomination screen -------------------------------------------------
# See docs/research/2026-07-24-multi-coin-data-integrity.md: LUNA/USDT splices
# Terra Classic and Terra 2.0 on one ticker, producing a 177,400x "gain" in 18
# days. An unguarded cross-sectional ranking would buy that at maximum weight.


def test_a_clean_series_has_no_redenomination():
    df = _series([100.0, 102.0, 99.0, 105.0, 103.0])
    assert find_redenominations(df["close"]) == []


def test_the_luna_splice_is_detected():
    """The real shape, from Binance daily closes: collapse to 5e-05, then the
    reassigned ticker reopens at 8.87."""
    closes = [82.35, 30.29, 1.0769, 0.00032, 0.00005, 8.87, 4.8767]
    hits = find_redenominations(_series(closes)["close"])
    assert len(hits) == 1
    # Flagged on the bar where the impossible jump happens, not the collapse.
    assert hits[0] == pd.Timestamp("2026-01-06")


def test_an_ordinary_crash_is_not_flagged():
    """A coin that falls hard and stays down is real data, not a rename. It
    must survive the screen — losing coins are exactly what a survivorship-free
    universe exists to keep."""
    closes = [100.0, 60.0, 30.0, 12.0, 5.0, 4.0, 3.5]
    assert find_redenominations(_series(closes)["close"]) == []


def test_a_large_but_plausible_rally_is_not_flagged():
    """Crypto doubles. The screen must not fire on volatility, only on jumps
    no real asset produces in one bar."""
    closes = [1.0, 1.4, 2.0, 3.1, 2.8, 4.0]
    assert find_redenominations(_series(closes)["close"]) == []


def test_the_threshold_is_the_documented_one():
    assert MAX_BAR_RETURN == 20.0


def test_a_jump_just_over_the_threshold_is_flagged():
    closes = [1.0, 1.0, 21.5]
    assert len(find_redenominations(_series(closes)["close"])) == 1


def test_a_jump_just_under_the_threshold_is_not():
    closes = [1.0, 1.0, 19.5]
    assert find_redenominations(_series(closes)["close"]) == []


def test_zero_and_missing_prices_do_not_crash_the_screen():
    """Dead coins genuinely print zero or gap. The screen must survive them
    rather than raising or dividing by zero."""
    closes = [10.0, 0.0, 0.0, 5.0, float("nan"), 6.0]
    find_redenominations(_series(closes)["close"])   # must not raise


# --- stablecoin screen -----------------------------------------------------
# `USD1/USDT` reached the cache through the EXCLUDED_BASES name list and churned
# on noise around $1.00 (fee drag 1.14). New stablecoins keep being issued, so a
# denylist cannot hold — the same objection already accepted for redenominations.
# A stablecoin is identifiable by what it DOES.


def _peg(n=60):
    """A pegged token: tiny alternating wobble around 1.00."""
    return [1.0 + (0.001 if i % 2 else -0.001) for i in range(n)]


def _volatile(n=60):
    """A real coin: percent-scale moves, no drift assumption."""
    return [100.0 * (1.0 + 0.05 * ((i * 7 % 11) - 5) / 5.0) for i in range(n)]


def test_a_stablecoin_has_near_zero_volatility():
    assert realized_volatility(_series(_peg())["close"]) < MIN_VOLATILITY


def test_a_real_coin_clears_the_volatility_floor():
    assert realized_volatility(_series(_volatile())["close"]) > MIN_VOLATILITY


def test_a_stablecoin_is_dropped_from_the_panel():
    frames = {
        "BTC/USDT": _series(_volatile()),
        "USD1/USDT": _series(_peg()),
    }
    panel, dropped = build_panel(frames, return_dropped=True)
    assert list(panel.columns) == ["BTC/USDT"]
    assert "USD1/USDT" in dropped
    assert "stablecoin" in dropped["USD1/USDT"]


def test_a_depegged_stablecoin_is_NOT_caught_by_the_volatility_screen():
    """Documents a real limit rather than asserting a capability.

    UST held its peg for months and then collapsed to near zero. Measured over
    the full series the collapse dominates, so realized volatility clears the
    floor and the screen lets it through.

    That is the defensible behaviour: after the break it IS a real (dying)
    asset whose price moves are genuine, and a survivorship-free universe is
    supposed to keep coins that died. The name-based `EXCLUDED_BASES` list in
    data/universe.py still covers the known algorithmic stables; this screen is
    the structural backstop for the ones nobody listed, not a replacement.
    """
    closes = _peg(50) + [0.35, 0.09, 0.02, 0.01, 0.008]
    assert realized_volatility(_series(closes)["close"]) > MIN_VOLATILITY


def test_volatility_ignores_gaps_rather_than_propagating_nan():
    closes = _volatile()
    closes[5] = float("nan")
    closes[17] = float("nan")
    vol = realized_volatility(_series(closes)["close"])
    assert vol > 0 and vol != float("inf")


def test_a_series_too_short_to_measure_is_not_called_a_stablecoin():
    """Absence of evidence must not silently exclude a coin — that would be a
    fresh survivorship hole in the screen meant to prevent one. A few bars of
    quiet drift look exactly like a peg."""
    assert realized_volatility(_series(_peg(10))["close"]) == float("inf")


def test_the_short_series_guard_is_the_documented_length():
    assert MIN_VOLATILITY_BARS == 30
    assert realized_volatility(_series(_peg(29))["close"]) == float("inf")
    assert realized_volatility(_series(_peg(31))["close"]) < MIN_VOLATILITY


# --- panel assembly --------------------------------------------------------


def test_build_panel_aligns_symbols_on_a_shared_index():
    frames = {
        "BTC/USDT": _series([100.0, 101.0, 102.0]),
        "ETH/USDT": _series([10.0, 11.0, 12.0]),
    }
    panel = build_panel(frames)
    assert list(panel.columns) == ["BTC/USDT", "ETH/USDT"]
    assert len(panel) == 3
    assert panel.loc[panel.index[1], "ETH/USDT"] == 11.0


def test_coins_listed_later_are_nan_before_they_existed_not_filled():
    """A late listing must read NaN before its first bar, never a
    back-filled price. Back-filling would let the strategy hold a coin before
    it could be bought — look-ahead of the most direct kind."""
    frames = {
        "BTC/USDT": _series([100.0, 101.0, 102.0, 103.0]),
        "NEW/USDT": _series([5.0, 6.0], start="2026-01-03"),
    }
    panel = build_panel(frames)
    assert len(panel) == 4
    assert pd.isna(panel.loc[pd.Timestamp("2026-01-01"), "NEW/USDT"])
    assert pd.isna(panel.loc[pd.Timestamp("2026-01-02"), "NEW/USDT"])
    assert panel.loc[pd.Timestamp("2026-01-03"), "NEW/USDT"] == 5.0


def test_a_dead_coin_stays_nan_after_it_dies():
    """The mirror case: a delisted coin must not carry its last price forward.
    Holding a dead coin at a stale price invents a position that could not be
    exited."""
    frames = {
        "BTC/USDT": _series([100.0, 101.0, 102.0, 103.0]),
        "DEAD/USDT": _series([5.0, 4.0]),
    }
    panel = build_panel(frames)
    assert panel.loc[pd.Timestamp("2026-01-02"), "DEAD/USDT"] == 4.0
    assert pd.isna(panel.loc[pd.Timestamp("2026-01-03"), "DEAD/USDT"])
    assert pd.isna(panel.loc[pd.Timestamp("2026-01-04"), "DEAD/USDT"])


def test_build_panel_drops_a_spliced_symbol_and_reports_it():
    """A symbol carrying a redenomination is excluded from the panel by
    default, and the caller is told which and why — silently dropping data is
    as bad as silently keeping bad data."""
    frames = {
        "BTC/USDT": _series([100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0]),
        "LUNA/USDT": _series([82.35, 30.29, 1.0769, 0.00032, 0.00005, 8.87, 4.8767]),
    }
    panel, dropped = build_panel(frames, return_dropped=True)
    assert list(panel.columns) == ["BTC/USDT"]
    assert "LUNA/USDT" in dropped


def test_screening_can_be_disabled_deliberately():
    """The screen must be defeatable for inspection, but only on purpose."""
    frames = {
        "LUNA/USDT": _series([82.35, 30.29, 1.0769, 0.00032, 0.00005, 8.87, 4.8767]),
    }
    panel = build_panel(frames, screen=False)
    assert "LUNA/USDT" in panel.columns


def test_an_empty_panel_is_an_empty_frame_not_a_crash():
    panel = build_panel({})
    assert panel.empty


def test_panel_index_is_sorted():
    frames = {
        "A/USDT": _series([1.0, 2.0], start="2026-01-05"),
        "B/USDT": _series([3.0, 4.0], start="2026-01-01"),
    }
    panel = build_panel(frames)
    assert panel.index.is_monotonic_increasing
