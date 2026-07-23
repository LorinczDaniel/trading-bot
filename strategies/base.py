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
    #: strategy that forgets to override is merely slow, never wrong.
    lookback = 200

    def generate(self, df: pd.DataFrame) -> Signal:
        raise NotImplementedError
