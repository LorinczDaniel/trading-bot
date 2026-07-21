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
):
    """Build a single Strategy instance from a name and parameters (for `backtest`)."""
    if name == "ma":
        return MACrossover(fast, slow)
    if name == "ma+trend":
        return TrendFilter(MACrossover(fast, slow), sma_period=trend_sma)
    if name == "rsi":
        return RSIReversion(rsi_period, rsi_low, rsi_high)
    if name == "rsi+trend":
        return TrendFilter(RSIReversion(rsi_period, rsi_low, rsi_high), sma_period=trend_sma)
    raise ValueError(f"unknown strategy: {name!r} (choose from {STRATEGY_NAMES})")


def walk_forward_grid(name: str, trend_sma: int = 200):
    """Return (param_grid, make_strategy) for walk-forward optimization of `name`.

    make_strategy(params) builds a Strategy from one grid entry; the grid shape
    differs per family (MA tunes fast/slow, RSI tunes period/low/high).
    """
    if name in ("ma", "ma+trend"):
        grid = [(f, s) for f in (5, 10, 20) for s in (30, 50, 100) if f < s]
        if name == "ma":
            return grid, lambda p: MACrossover(p[0], p[1])
        return grid, lambda p: TrendFilter(MACrossover(p[0], p[1]), sma_period=trend_sma)
    if name in ("rsi", "rsi+trend"):
        grid = [(period, low, 100 - low) for period in (7, 14, 21) for low in (20, 30)]
        if name == "rsi":
            return grid, lambda p: RSIReversion(p[0], p[1], p[2])
        return grid, lambda p: TrendFilter(RSIReversion(p[0], p[1], p[2]), sma_period=trend_sma)
    raise ValueError(f"unknown strategy: {name!r} (choose from {STRATEGY_NAMES})")
