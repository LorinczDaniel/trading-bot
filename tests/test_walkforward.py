import numpy as np
import pandas as pd
import pytest

from backtest.walkforward import walk_forward
from strategies.base import Strategy, Signal
from strategies.ma_crossover import MACrossover
from strategies.trend_filter import TrendFilter


def _prices(n):
    # gentle drift + oscillation so crossovers actually occur
    return [100 + (i % 10) - (i % 7) + i * 0.1 for i in range(n)]


def test_walk_forward_structure():
    # min_trades_fold=1: these short synthetic folds (~24 bars) rarely clear the
    # default gate of 5 in-sample trades. This test checks fold plumbing and
    # best_params selection, not the trade-count gate (see the two gate tests
    # below), so it relaxes the minimum rather than going vacuous under `if valid`.
    df = pd.DataFrame({"close": _prices(120)})
    grid = [(3, 8), (5, 15)]
    results = walk_forward(df, lambda p: MACrossover(*p), grid, n_splits=4, warmup=8,
                           min_trades_fold=1)
    assert len(results) == 4
    for r in results:
        assert r["valid"]
        assert r["best_params"] in grid
        assert isinstance(r["in_sample_return"], float)
        assert isinstance(r["oos_return"], float)


def test_walk_forward_single_param_grid():
    # Same relaxation as above, and for the same reason.
    df = pd.DataFrame({"close": _prices(100)})
    results = walk_forward(df, lambda p: MACrossover(*p), [(3, 8)], n_splits=3, warmup=8,
                           min_trades_fold=1)
    assert all(r["valid"] for r in results)
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


class EveryNBars(Strategy):
    """Alternates buy/sell every `n` bars — trade count is directly controllable."""

    lookback = 1

    def __init__(self, n):
        self.n = n
        self._long = False

    def generate(self, df):
        i = df.index[-1]
        if i % self.n:
            return Signal("HOLD")
        self._long = not self._long
        return Signal("BUY" if self._long else "SELL")


def test_optimizer_rejects_params_below_the_fold_trade_minimum():
    n = 1000
    df = pd.DataFrame({"close": 100 + 10 * np.sin(np.arange(n) / 11.0)})

    # n=400 trades ~ twice per fold; n=7 trades often. Only the active one is valid.
    grid = [400, 7]
    results = walk_forward(df, lambda p: EveryNBars(p), grid, n_splits=2,
                           warmup=10, min_trades_fold=5)

    for r in results:
        if r["valid"]:
            assert r["best_params"] == 7, "the near-inactive param set must be rejected"


def test_fold_with_no_valid_params_is_marked_invalid():
    n = 400
    df = pd.DataFrame({"close": 100 + 10 * np.sin(np.arange(n) / 11.0)})

    results = walk_forward(df, lambda p: EveryNBars(p), [300], n_splits=2,
                           warmup=10, min_trades_fold=5)

    assert all(not r["valid"] for r in results)
    assert all(r["best_params"] is None for r in results)
