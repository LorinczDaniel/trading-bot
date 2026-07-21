import numpy as np
import pandas as pd


def total_return(equity: pd.Series) -> float:
    return float(equity.iloc[-1] / equity.iloc[0] - 1.0)


def max_drawdown(equity: pd.Series) -> float:
    running_max = equity.cummax()
    drawdown = equity / running_max - 1.0
    return float(drawdown.min())


def sharpe_ratio(equity: pd.Series, periods_per_year: int = 365) -> float:
    returns = equity.pct_change().dropna()
    if len(returns) == 0 or returns.std() == 0:
        return 0.0
    return float((returns.mean() / returns.std()) * np.sqrt(periods_per_year))


def buy_and_hold_return(close: pd.Series, fee: float = 0.001) -> float:
    """Return of buying at the first close and holding to the last.

    Models a single entry fee (you buy once and never sell), so it is a fair
    baseline for a fee-paying strategy to beat.
    """
    gross = close.iloc[-1] / close.iloc[0]
    return float(gross * (1 - fee) - 1.0)
