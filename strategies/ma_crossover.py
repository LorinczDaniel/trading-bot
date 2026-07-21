import pandas as pd

from strategies.base import Strategy, Signal


class MACrossover(Strategy):
    def __init__(self, fast: int = 20, slow: int = 50):
        if fast >= slow:
            raise ValueError("fast period must be < slow period")
        self.fast = fast
        self.slow = slow

    def generate(self, df: pd.DataFrame) -> Signal:
        if len(df) < self.slow + 1:
            return Signal("HOLD", reason="not enough data")
        fast = df["close"].rolling(self.fast).mean()
        slow = df["close"].rolling(self.slow).mean()
        prev_fast, prev_slow = fast.iloc[-2], slow.iloc[-2]
        curr_fast, curr_slow = fast.iloc[-1], slow.iloc[-1]
        if prev_fast <= prev_slow and curr_fast > curr_slow:
            return Signal("BUY", reason="fast crossed above slow")
        if prev_fast >= prev_slow and curr_fast < curr_slow:
            return Signal("SELL", reason="fast crossed below slow")
        return Signal("HOLD", reason="no cross")
