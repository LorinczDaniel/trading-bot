import pytest

from strategies.factory import build_strategy, walk_forward_grid, STRATEGY_NAMES
from strategies.ma_crossover import MACrossover
from strategies.rsi_reversion import RSIReversion
from strategies.trend_filter import TrendFilter


def test_build_ma():
    s = build_strategy("ma", fast=5, slow=20)
    assert isinstance(s, MACrossover)
    assert s.fast == 5 and s.slow == 20


def test_build_ma_trend_wraps():
    s = build_strategy("ma+trend", fast=5, slow=20, trend_sma=100)
    assert isinstance(s, TrendFilter)
    assert isinstance(s.inner, MACrossover)
    assert s.sma_period == 100


def test_build_rsi():
    s = build_strategy("rsi", rsi_period=7, rsi_low=25, rsi_high=75)
    assert isinstance(s, RSIReversion)
    assert s.period == 7


def test_build_unknown_raises():
    with pytest.raises(ValueError):
        build_strategy("nope")


def test_walk_forward_grid_ma():
    grid, make = walk_forward_grid("ma")
    assert len(grid) > 0
    assert isinstance(make(grid[0]), MACrossover)


def test_walk_forward_grid_rsi_trend():
    grid, make = walk_forward_grid("rsi+trend")
    assert len(grid) > 0
    s = make(grid[0])
    assert isinstance(s, TrendFilter)
    assert isinstance(s.inner, RSIReversion)


def test_strategy_names_include_all_four():
    assert set(STRATEGY_NAMES) == {"ma", "ma+trend", "rsi", "rsi+trend"}


# --- cost band -------------------------------------------------------------


def test_build_strategy_passes_the_band_to_ma():
    assert build_strategy("ma", band=0.02).band == pytest.approx(0.02)


def test_build_strategy_passes_the_band_through_the_trend_wrapper():
    """`ma+trend` must band its inner crossover too, or the +trend variant
    silently measures a different mechanic than `ma` in the same scan."""
    s = build_strategy("ma+trend", band=0.02)
    assert s.inner.band == pytest.approx(0.02)


def test_walk_forward_grid_applies_the_band():
    """The grid's `make_strategy` builds the objects walk-forward actually
    simulates. If the band reached `build_strategy` but not here, a scan row's
    headline metrics and its fold metrics would describe different strategies
    — the exact defect 12e0e61 was written to remove."""
    _, make = walk_forward_grid("ma", band=0.02)
    assert make((20, 50)).band == pytest.approx(0.02)

    _, make_trend = walk_forward_grid("ma+trend", band=0.02)
    assert make_trend((20, 50)).inner.band == pytest.approx(0.02)


def test_the_band_defaults_to_zero_everywhere_in_the_factory():
    assert build_strategy("ma").band == 0.0
    assert build_strategy("ma+trend").inner.band == 0.0
    assert walk_forward_grid("ma")[1]((20, 50)).band == 0.0
    assert walk_forward_grid("ma+trend")[1]((20, 50)).inner.band == 0.0


def test_the_band_is_accepted_but_inert_for_rsi():
    """RSI's thresholds already encode their own entry/exit distance, so the
    MA cost band does not apply to it. The parameter is still accepted so
    callers (scan, CLI) can pass one band uniformly without special-casing
    the strategy name — it simply has no effect here."""
    s = build_strategy("rsi", band=0.02)
    assert isinstance(s, RSIReversion)
    assert not hasattr(s, "band")
