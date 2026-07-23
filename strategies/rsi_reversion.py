import pandas as pd

from strategies.base import Strategy, Signal


class RSIReversion(Strategy):
    """Mean-reversion: buy when RSI is oversold, sell when overbought."""

    def __init__(self, period: int = 14, low: float = 30.0, high: float = 70.0):
        if not (0 < low < high < 100):
            raise ValueError("require 0 < low < high < 100")
        self.period = period
        self.low = low
        self.high = high

    @property
    def lookback(self) -> int:
        return self.period + 1   # close.diff() consumes one bar

    def _rsi(self, close: pd.Series) -> float:
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(self.period).mean().iloc[-1]
        avg_loss = loss.rolling(self.period).mean().iloc[-1]
        if avg_loss == 0:
            return 100.0 if avg_gain > 0 else 50.0
        rs = avg_gain / avg_loss
        return 100.0 - 100.0 / (1.0 + rs)

    def generate(self, df: pd.DataFrame) -> Signal:
        if len(df) < self.period + 1:
            return Signal("HOLD", reason="not enough data")
        rsi = self._rsi(df["close"])
        if rsi < self.low:
            return Signal("BUY", reason=f"RSI {rsi:.0f} oversold")
        if rsi > self.high:
            return Signal("SELL", reason=f"RSI {rsi:.0f} overbought")
        return Signal("HOLD", reason=f"RSI {rsi:.0f} neutral")
