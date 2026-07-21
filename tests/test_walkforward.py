import pandas as pd

from backtest.walkforward import walk_forward
from strategies.ma_crossover import MACrossover


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
