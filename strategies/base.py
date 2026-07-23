from dataclasses import dataclass

import pandas as pd


@dataclass
class Signal:
    action: str  # "BUY" | "SELL" | "HOLD"
    reason: str = ""


class Strategy:
    #: Minimum trailing bars needed for a correct signal. The replay loop uses
    #: this to pass a bounded window instead of the whole history. The default is
    #: deliberately generous (it covers the default --trend-sma of 200) so a
    #: strategy that forgets to override is merely slow, never wrong. This
    #: assumes a fixed trailing window (`.rolling`); a strategy built on a
    #: recursive accumulator (`ewm`, `expanding`) depends on full history and
    #: would produce different signals under a bounded window — special-case it.
    lookback = 200

    def generate(self, df: pd.DataFrame) -> Signal:
        raise NotImplementedError
