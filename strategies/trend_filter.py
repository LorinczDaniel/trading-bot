import pandas as pd

from strategies.base import Strategy, Signal


class TrendFilter(Strategy):
    """Regime filter: wraps another strategy and only allows BUY signals when
    price is at or above a long-period SMA (i.e. in an uptrend). SELL and HOLD
    pass through unchanged. This cuts whipsaw losses from buying into downtrends.
    """

    def __init__(self, inner: Strategy, sma_period: int = 200):
        self.inner = inner
        self.sma_period = sma_period

    def generate(self, df: pd.DataFrame) -> Signal:
        signal = self.inner.generate(df)
        if signal.action != "BUY":
            return signal
        if len(df) < self.sma_period:
            return Signal("HOLD", reason="trend filter: not enough data")
        sma = df["close"].rolling(self.sma_period).mean().iloc[-1]
        price = df["close"].iloc[-1]
        if price >= sma:
            return signal
        return Signal("HOLD", reason="trend filter: price below SMA, buy suppressed")
