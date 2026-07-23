"""Cost and churn metrics, gates, and the configuration scan.

The scan exists to answer one question honestly: is any configuration worth
running unattended? Every rejection carries a named reason, because knowing why
a configuration failed is the output's main value.
"""

import pandas as pd


def total_fees(fills: list) -> float:
    """Sum the fee column, tolerating blank entries from ledger-shaped rows."""
    return sum(float(f.get("fee") or 0.0) for f in fills)


def fee_drag(fills: list, trades: list) -> float:
    """Fees as a fraction of gross P&L — the share of activity eaten by costs.

    Absolute gross P&L, so a losing strategy is still measured against how much
    it actually moved. Zero gross P&L means fees were paid for nothing, which is
    the worst possible case, so it reports infinity rather than dividing by zero.

    Gross P&L here is GROSS OF ENTRY FEES: `Trader._sell` computes
    `qty*price*(1-fee) - qty*entry_price`, net of the exit fee but blind to the
    entry fee (same known caveat `report.py` documents). This does not distort
    fee_drag enough to matter, because fee_drag is a ratio of cost to activity,
    not a claim about true net P&L.
    """
    gross = abs(sum(float(t["pnl"]) for t in trades))
    if gross == 0:
        return float("inf")
    return total_fees(fills) / gross


def trades_per_day(n_trades: int, index) -> float:
    """Trade frequency. A swing bot trading many times a day is churning."""
    if len(index) < 2:
        return float("inf") if n_trades else 0.0
    span = pd.Timestamp(index[-1]) - pd.Timestamp(index[0])
    days = span.total_seconds() / 86_400.0
    if days <= 0:
        return float("inf") if n_trades else 0.0
    return n_trades / days


def worst_cumulative_loss(trades: list, starting_cash: float) -> float:
    """Deepest point of the running realized-P&L total, as a fraction of start.

    Reported rather than gated: it is what the live kill-switch would have
    reacted to, so it belongs in front of the user, not in a pass/fail rule.
    """
    running, worst = 0.0, 0.0
    for t in trades:
        running += float(t["pnl"])
        worst = min(worst, running)
    return abs(worst) / starting_cash if starting_cash else 0.0
