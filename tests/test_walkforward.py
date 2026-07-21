import pandas as pd

from backtest.walkforward import walk_forward
from strategies.ma_crossover import MACrossover
from strategies.trend_filter import TrendFilter


def _prices(n):
    # gentle drift + oscillation so crossovers actually occur
    return [100 + (i % 10) - (i % 7) + i * 0.1 for i in range(n)]


def test_walk_forward_structure():
    df = pd.DataFrame({"close": _prices(120)})
    grid = [(3, 8), (5, 15)]
    results = walk_forward(df, lambda p: MACrossover(*p), grid, n_splits=4, warmup=8)
    assert len(results) == 4
    for r in results:
        assert r["best_params"] in grid
        assert isinstance(r["in_sample_return"], float)
        assert isinstance(r["oos_return"], float)


def test_walk_forward_single_param_grid():
    df = pd.DataFrame({"close": _prices(100)})
    results = walk_forward(df, lambda p: MACrossover(*p), [(3, 8)], n_splits=3, warmup=8)
    assert all(r["best_params"] == (3, 8) for r in results)


def test_walk_forward_reports_trade_counts():
    df = pd.DataFrame({"close": _prices(120)})
    results = walk_forward(df, lambda p: MACrossover(*p), [(3, 8)], n_splits=4, warmup=8)
    for r in results:
        assert isinstance(r["in_sample_trades"], int)
        assert isinstance(r["oos_trades"], int)


def test_walk_forward_zero_trades_when_lookback_exceeds_fold():
    # fold = 120 // 5 = 24 bars, but the trend filter needs 100 -> never trades
    df = pd.DataFrame({"close": _prices(120)})
    make = lambda p: TrendFilter(MACrossover(3, 8), sma_period=100)  # noqa: E731
    results = walk_forward(df, make, [(3, 8)], n_splits=4, warmup=8)
    assert all(r["oos_trades"] == 0 for r in results)
