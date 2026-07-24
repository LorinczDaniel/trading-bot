import pandas as pd

from strategies.base import Strategy, Signal


class MACrossover(Strategy):
    """Moving-average crossover, optionally with a cost band.

    `band` widens the single crossing line into two: an entry must clear
    `slow * (1 + band)` and an exit must break `slow * (1 - band)`. A cross
    that only grazes the raw line costs a full round trip in fees to act on
    and predicts very little, and measured fee drag — not signal frequency —
    is what kills these configurations
    (`docs/research/2026-07-23-crypto-strategy-findings.md`).

    Defaults to 0.0, which reduces both lines back to `slow` and reproduces
    the unbanded behaviour exactly. That default is deliberate: every result
    recorded in the research docs was measured without a band, and a silent
    default would retroactively invalidate them.
    """

    def __init__(self, fast: int = 20, slow: int = 50, band: float = 0.0):
        if fast >= slow:
            raise ValueError("fast period must be < slow period")
        if band < 0:
            raise ValueError("band must not be negative")
        if band >= 1:
            # The lower line would sit at or below zero, so no price could ever
            # break it and a position could never be exited on signal.
            raise ValueError("band must be < 1")
        self.fast = fast
        self.slow = slow
        self.band = band

    @property
    def lookback(self) -> int:
        return self.slow + 1   # generate() reads the previous bar's averages too

    def generate(self, df: pd.DataFrame) -> Signal:
        if len(df) < self.slow + 1:
            return Signal("HOLD", reason="not enough data")
        fast = df["close"].rolling(self.fast).mean()
        slow = df["close"].rolling(self.slow).mean()
        prev_fast, prev_slow = fast.iloc[-2], slow.iloc[-2]
        curr_fast, curr_slow = fast.iloc[-1], slow.iloc[-1]

        # Both lines are tested for a CROSS, not merely for position: comparing
        # only the current bar would re-fire the same signal on every bar of a
        # sustained trend, which would raise churn rather than cut it.
        up, down = 1.0 + self.band, 1.0 - self.band
        if prev_fast <= prev_slow * up and curr_fast > curr_slow * up:
            return Signal("BUY", reason="fast crossed above slow")
        if prev_fast >= prev_slow * down and curr_fast < curr_slow * down:
            return Signal("SELL", reason="fast crossed below slow")
        if self.band and prev_fast <= prev_slow and curr_fast > curr_slow:
            return Signal("HOLD", reason="upward cross inside the cost band")
        if self.band and prev_fast >= prev_slow and curr_fast < curr_slow:
            return Signal("HOLD", reason="downward cross inside the cost band")
        return Signal("HOLD", reason="no cross")
