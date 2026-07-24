from strategies.ma_crossover import MACrossover
from strategies.rsi_reversion import RSIReversion
from strategies.trend_filter import TrendFilter

STRATEGY_NAMES = ["ma", "ma+trend", "rsi", "rsi+trend"]


def build_strategy(
    name: str,
    fast: int = 20,
    slow: int = 50,
    rsi_period: int = 14,
    rsi_low: float = 30.0,
    rsi_high: float = 70.0,
    trend_sma: int = 200,
    band: float = 0.0,
):
    """Build a single Strategy instance from a name and parameters (for `backtest`).

    `band` is the MA cost band (see `MACrossover`). It is accepted for every
    name so callers can pass one band uniformly without special-casing the
    strategy, but it only applies to the MA families — RSI's low/high
    thresholds already encode their own entry and exit distance.
    """
    if name == "ma":
        return MACrossover(fast, slow, band=band)
    if name == "ma+trend":
        return TrendFilter(MACrossover(fast, slow, band=band), sma_period=trend_sma)
    if name == "rsi":
        return RSIReversion(rsi_period, rsi_low, rsi_high)
    if name == "rsi+trend":
        return TrendFilter(RSIReversion(rsi_period, rsi_low, rsi_high), sma_period=trend_sma)
    raise ValueError(f"unknown strategy: {name!r} (choose from {STRATEGY_NAMES})")


def default_params(name: str):
    """Return `build_strategy`'s default parameter tuple for `name`, shaped to
    match what `walk_forward_grid`'s `make_strategy` expects for that family.

    This is the single source of truth `scan_one` pins walk-forward to, so that
    every gate on a scan row judges the same fixed configuration the headline
    metrics (built via `build_strategy` with its own defaults) were measured
    on. Mirrors `build_strategy`'s signature defaults by hand rather than via
    `inspect.signature` (matching this module's existing style, e.g.
    `walk_forward_grid`'s hardcoded grids) — if those defaults ever change,
    this function must change with them:
      - ma / ma+trend  -> (fast=20, slow=50)
      - rsi / rsi+trend -> (rsi_period=14, rsi_low=30.0, rsi_high=70.0)
    """
    if name in ("ma", "ma+trend"):
        return (20, 50)
    if name in ("rsi", "rsi+trend"):
        return (14, 30.0, 70.0)
    raise ValueError(f"unknown strategy: {name!r} (choose from {STRATEGY_NAMES})")


def walk_forward_grid(name: str, trend_sma: int = 200, band: float = 0.0):
    """Return (param_grid, make_strategy) for walk-forward optimization of `name`.

    make_strategy(params) builds a Strategy from one grid entry; the grid shape
    differs per family (MA tunes fast/slow, RSI tunes period/low/high).

    `band` rides in the closure alongside `trend_sma` rather than joining the
    grid: it is a fixed property of the configuration under test, not a
    dimension to optimize over. `scan_one` must pass the same value here as it
    passes to `build_strategy`, or a scan row's headline metrics and its fold
    metrics would describe different strategies.
    """
    if name in ("ma", "ma+trend"):
        grid = [(f, s) for f in (5, 10, 20) for s in (30, 50, 100) if f < s]
        if name == "ma":
            return grid, lambda p: MACrossover(p[0], p[1], band=band)
        return grid, lambda p: TrendFilter(MACrossover(p[0], p[1], band=band),
                                           sma_period=trend_sma)
    if name in ("rsi", "rsi+trend"):
        grid = [(period, low, 100 - low) for period in (7, 14, 21) for low in (20, 30)]
        if name == "rsi":
            return grid, lambda p: RSIReversion(p[0], p[1], p[2])
        return grid, lambda p: TrendFilter(RSIReversion(p[0], p[1], p[2]), sma_period=trend_sma)
    raise ValueError(f"unknown strategy: {name!r} (choose from {STRATEGY_NAMES})")
