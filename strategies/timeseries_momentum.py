import pandas as pd

from strategies.base import Strategy, Signal


class TimeSeriesMomentum(Strategy):
    """Long-only time-series momentum on a single asset.

    Hold the asset only while its trailing `window`-bar return sits in the top
    `1 - quantile` of that return's own recent history; otherwise stay flat.
    Once the condition fires, stay long for `hold` bars even if it stops firing.

    Published claim under test (see docs/research/2026-07-23-crypto-strategy-findings.md):
    a 28-bar window with a 5-bar hold on the crypto market portfolio produced an
    annualized Sharpe of 1.51 vs 0.85 for the market, net of 15bps per trade,
    while invested only ~48% of the time — the edge coming from sitting out
    drawdowns rather than from higher returns. The authors disclaim their own
    parameters as chosen in-sample with no holdout, which is precisely what a
    walk-forward run is for.

    The percentile is taken over a rolling `history` window rather than an
    expanding one, so the rule uses only information a trader would have had and
    the signal stays independent of how much older data happens to be prepended
    (the replay passes a bounded tail window).

    The `hold` window is what keeps this from churning: without it the position
    would be dropped the moment the return slipped out of the top third, which
    on noisy data means paying the round-trip cost repeatedly.
    """

    def __init__(self, window: int = 28, hold: int = 5,
                 quantile: float = 2.0 / 3.0, history: int = 365):
        if window < 1:
            raise ValueError("window must be >= 1")
        if hold < 1:
            raise ValueError("hold must be >= 1")
        if not (0.0 < quantile < 1.0):
            raise ValueError("require 0 < quantile < 1")
        if history < 2:
            raise ValueError("history must be >= 2")
        self.window = window
        self.hold = hold
        self.quantile = quantile
        self.history = history

    @property
    def lookback(self) -> int:
        # `history` samples of a `window`-bar return, evaluated across the last
        # `hold` bars, plus one bar to take the first return from.
        return self.window + self.history + self.hold + 1

    def generate(self, df: pd.DataFrame) -> Signal:
        if len(df) < self.lookback:
            return Signal("HOLD", reason="not enough data")

        close = df["close"]
        returns = close / close.shift(self.window) - 1.0
        # rank each return against its own trailing distribution, excluding
        # itself so the cut-off cannot be set by the value being tested
        cutoff = returns.shift(1).rolling(self.history).quantile(self.quantile)
        fired = returns >= cutoff

        recent = fired.iloc[-self.hold:]
        if recent.any():
            bars_ago = int(self.hold - 1 - recent.to_numpy().nonzero()[0][-1])
            latest = float(returns.iloc[-1])
            when = "now" if bars_ago == 0 else f"{bars_ago} bar(s) ago"
            return Signal(
                "BUY",
                reason=f"{self.window}-bar return {latest:+.2%} in top "
                       f"{1 - self.quantile:.0%} ({when})",
            )
        return Signal(
            "SELL",
            reason=f"{self.window}-bar return {float(returns.iloc[-1]):+.2%} "
                   f"below the top {1 - self.quantile:.0%} for {self.hold} bars",
        )
