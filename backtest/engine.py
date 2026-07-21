from dataclasses import dataclass

import pandas as pd

from strategies.base import Strategy


@dataclass
class BacktestResult:
    equity: pd.Series
    trades: list
    final_equity: float


def run_backtest(
    df: pd.DataFrame,
    strategy: Strategy,
    initial_cash: float = 10_000.0,
    fee: float = 0.001,
    warmup: int = 50,
) -> BacktestResult:
    cash = initial_cash
    position = 0.0       # units of the asset held
    entry_price = 0.0
    equity_curve = []
    trades = []
    index = []

    for i in range(len(df)):
        price = float(df["close"].iloc[i])
        equity_curve.append(cash + position * price)
        index.append(df.index[i])

        if i < warmup:
            continue

        signal = strategy.generate(df.iloc[: i + 1])

        if signal.action == "BUY" and position == 0.0:
            qty = (cash * (1 - fee)) / price
            position = qty
            entry_price = price
            cash = 0.0
        elif signal.action == "SELL" and position > 0.0:
            proceeds = position * price * (1 - fee)
            trades.append(
                {"entry": entry_price, "exit": price, "pnl": proceeds - position * entry_price}
            )
            cash = proceeds
            position = 0.0
            entry_price = 0.0

    final_equity = cash + position * float(df["close"].iloc[-1])
    return BacktestResult(
        equity=pd.Series(equity_curve, index=index),
        trades=trades,
        final_equity=final_equity,
    )
