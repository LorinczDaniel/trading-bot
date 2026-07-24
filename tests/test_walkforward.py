import numpy as np
import pandas as pd
import pytest

from backtest.walkforward import walk_forward
from strategies.base import Strategy, Signal
from strategies.ma_crossover import MACrossover


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
    # min_trades_fold=1: with the default of 5, MACrossover(3, 8) makes too
    # few in-sample trades on these 24-bar folds to clear the gate, so every
    # fold fell back to `valid=False` and this only ever read the hardcoded
    # 0 literals from walk_forward's invalid-fold branch -- it would still
    # pass if the entire out-of-sample `simulate` call were deleted. Lowering
    # the gate lets real folds trade, and asserting nonzero counts (not just
    # `isinstance`) pins that the reported numbers came from actual trading.
    df = pd.DataFrame({"close": _prices(120)})
    results = walk_forward(df, lambda p: MACrossover(*p), [(3, 8)], n_splits=4, warmup=8,
                           min_trades_fold=1)
    assert all(r["valid"] for r in results)
    for r in results:
        assert isinstance(r["in_sample_trades"], int) and r["in_sample_trades"] > 0
        assert isinstance(r["oos_trades"], int)
    assert any(r["oos_trades"] > 0 for r in results)


def test_walk_forward_oos_return_equals_next_folds_in_sample_return():
    """Renamed from test_walk_forward_zero_trades_when_lookback_exceeds_fold.

    That test used TrendFilter(sma_period=100) on 24-bar folds, which never
    makes an in-sample trade either -- min_trades_fold=1 cannot fix that (0
    trades still fails a threshold of 1), so every fold stayed
    `valid=False` and the test only ever read the hardcoded 0 literals from
    walk_forward's invalid-fold branch; the real out-of-sample `simulate`
    call was never exercised.

    Swapped to MACrossover(3, 8) with a single-entry grid, which does trade.
    Fold k's OOS slice is exactly fold k+1's IS slice, and with only one
    grid candidate, that slice is always the "best" one -- so fold k's
    reported oos_return (from the OOS simulate call) must exactly equal
    fold k+1's independently-computed in_sample_return (from the IS
    optimization loop). A stub, a deleted OOS simulate() call, or an OOS
    calculation that silently reused in-sample numbers would break this
    equality, which two genuinely separate code paths currently satisfy.
    """
    df = pd.DataFrame({"close": _prices(120)})
    results = walk_forward(df, lambda p: MACrossover(*p), [(3, 8)], n_splits=4, warmup=8,
                           min_trades_fold=1)
    assert all(r["valid"] for r in results)
    assert all(r["oos_trades"] > 0 for r in results)
    for k in range(len(results) - 1):
        assert results[k]["oos_return"] == pytest.approx(results[k + 1]["in_sample_return"])


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


def test_walk_forward_pins_a_known_oos_outcome():
    """`oos_return` drives gate 5 of the scan (`unstable` since 2026-07-24,
    `overfit` before that) and decided one of the 16 rejections in the real
    scan -- but no test asserted a specific oos_return or a nonzero
    oos_trades count; test_walk_forward_structure
    only checks `isinstance(r["oos_return"], float)`, which a stubbed-out
    out-of-sample simulation would still satisfy.

    Pins an exact value from a fully scripted, deterministic strategy
    (EveryNBars) over a deterministic linear price series, so a regression
    that breaks, stubs, or zeroes out the out-of-sample simulate() call is
    caught. The expected value below was read from one real run of this
    exact setup, not hand-derived.
    """
    n = 200
    df = pd.DataFrame({"close": [100.0 + i for i in range(n)]})
    results = walk_forward(df, lambda p: EveryNBars(p), [5], n_splits=4, warmup=4,
                           min_trades_fold=1)

    r0 = results[0]
    assert r0["valid"]
    assert r0["oos_trades"] == 3
    assert r0["oos_trades"] > 0
    assert r0["oos_return"] == pytest.approx(0.02275111782674788)
