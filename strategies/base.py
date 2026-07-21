from dataclasses import dataclass

import pandas as pd


@dataclass
class Signal:
    action: str  # "BUY" | "SELL" | "HOLD"
    reason: str = ""


class Strategy:
    def generate(self, df: pd.DataFrame) -> Signal:
        raise NotImplementedError
