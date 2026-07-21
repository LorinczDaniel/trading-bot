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
