"""Turn a trade ledger (see tradelog.py) into performance stats + an equity
curve. Pure functions over a DataFrame; the CLI does the file I/O."""

import pandas as pd

from backtest.metrics import max_drawdown


def summarize(trades: pd.DataFrame) -> dict:
    """Performance stats from a trade ledger.

    The HONEST headline is `net_pnl` = equity_end - equity_start, taken from the
    `equity_after` column (which reflects ALL fees). `realized_pnl` (summed from
    the per-trade pnl the trader records) is kept for the win/loss breakdown but
    is GROSS of entry fees — the trader's pnl formula omits the buy-side fee — so
    it reads slightly higher than net. Counts exclude the baseline 'start' row.
    """
    side = trades.get("side", pd.Series(dtype=object))
    fills = trades[side.isin(["buy", "sell"])] if len(trades) else trades
    fill_side = fills.get("side", pd.Series(dtype=object))
    sells = fills[fill_side == "sell"] if len(fills) else fills
    pnl = pd.to_numeric(sells.get("realized_pnl"), errors="coerce").dropna() \
        if len(sells) else pd.Series(dtype=float)
    wins, losses = pnl[pnl > 0], pnl[pnl < 0]
    fees = pd.to_numeric(fills.get("fee"), errors="coerce").fillna(0.0) \
        if len(fills) else pd.Series(dtype=float)
    equity = pd.to_numeric(trades.get("equity_after"), errors="coerce").dropna() \
        if len(trades) else pd.Series(dtype=float)

    gross_win = float(wins.sum())
    gross_loss = float(-losses.sum())  # a positive magnitude
    if gross_loss > 0:
        profit_factor = gross_win / gross_loss
    elif gross_win > 0:
        profit_factor = float("inf")  # winners, no losers
    else:
        profit_factor = 0.0

    equity_start = float(equity.iloc[0]) if len(equity) else 0.0
    equity_end = float(equity.iloc[-1]) if len(equity) else 0.0
    return {
        "fills": int(len(fills)),
        "buys": int((fill_side == "buy").sum()) if len(fills) else 0,
        "round_trips": int(len(pnl)),
        "net_pnl": equity_end - equity_start,
        "realized_pnl": float(pnl.sum()),
        "win_rate": float(len(wins) / len(pnl)) if len(pnl) else 0.0,
        "avg_win": float(wins.mean()) if len(wins) else 0.0,
        "avg_loss": float(losses.mean()) if len(losses) else 0.0,
        "profit_factor": profit_factor,
        "total_fees": float(fees.sum()),
        "equity_start": equity_start,
        "equity_end": equity_end,
        "equity_peak": float(equity.max()) if len(equity) else 0.0,
        "max_drawdown": max_drawdown(equity) if len(equity) >= 2 else 0.0,
        "return_pct": (equity_end / equity_start - 1.0) if equity_start else 0.0,
    }


def equity_curve(trades: pd.DataFrame) -> pd.DataFrame:
    """A tidy equity-after-each-trade table, ready to chart in a spreadsheet."""
    out = pd.DataFrame({
        "trade": range(1, len(trades) + 1),
        "equity_after": pd.to_numeric(trades.get("equity_after"), errors="coerce"),
    })
    if "timestamp" in trades:
        out.insert(1, "timestamp", trades["timestamp"].values)
    return out
