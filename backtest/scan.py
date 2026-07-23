"""Cost and churn metrics, gates, and the configuration scan.

The scan exists to answer one question honestly: is any configuration worth
running unattended? Every rejection carries a named reason, because knowing why
a configuration failed is the output's main value.
"""

import pandas as pd

from backtest.metrics import total_return, max_drawdown, buy_and_hold_return
from backtest.simulate import simulate, scan_risk_config
from backtest.walkforward import walk_forward
from strategies.factory import build_strategy, default_params, walk_forward_grid


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


# Gate thresholds. Fixed by the design spec before any results were seen; tuning
# them after looking at output turns "survives walk-forward" into post-hoc
# rationalization, which is the exact failure the gates exist to prevent.
MIN_TRADES = 20              # below this, results are noise
MAX_TRADES_PER_DAY = 6.0     # above this, a swing bot is churning
MAX_FEE_DRAG = 0.30          # costs must not eat a third of the activity
MIN_FOLDS_TRADED = 2         # walk-forward needs at least two folds to say anything


def verdict(row: dict) -> tuple[str, str]:
    """Apply the gates in order and return ("PASS", "") or ("FAIL", label).

    Order matters only for which label a multiply-failing config reports; the
    cheapest, most fundamental objection is checked first.
    """
    if row["trades"] < MIN_TRADES:
        return "FAIL", "too-few-trades"
    if row["trades_per_day"] > MAX_TRADES_PER_DAY:
        return "FAIL", "churn"
    if row["fee_drag"] > MAX_FEE_DRAG:
        return "FAIL", "fee-drag"
    if row["folds_traded"] < MIN_FOLDS_TRADED:
        return "FAIL", "insufficient-folds"
    if row["avg_is"] > 0 and row["avg_oos"] < 0:
        return "FAIL", "overfit"
    # Gate 6, added 2026-07-23 by owner decision, after the first real scan
    # surfaced `1h rsi+trend` (edge +43.51%, net_return -1.16%) — a config
    # that only "beat" buy-and-hold because BTC fell harder over the sample.
    # A losing configuration is not deployable however well it beat holding.
    # Placed last: a config is labelled `losing` only once every more
    # fundamental gate above has already been cleared. See the dated
    # amendment in docs/superpowers/specs/2026-07-23-measurement-harness-design.md.
    if row["net_return"] <= 0:
        return "FAIL", "losing"
    return "PASS", ""


def scan_one(df, symbol: str, timeframe: str, strategy_name: str, *,
             cash: float = 10_000.0, fee: float = 0.001, warmup: int = 50,
             risk_per_trade: float = 0.01, stop_loss_pct: float = 0.05,
             splits: int = 4, trend_sma: int = 200) -> dict:
    """Measure one (strategy, timeframe) configuration and return its scan row.

    Walk-forward here evaluates the SAME fixed parameters as the headline
    metrics (`trades`, `net_return`, `edge`, `max_drawdown`, `worst_loss`,
    `fee_drag`, all built via `build_strategy`'s defaults) — not a grid
    re-optimized per fold. `walk_forward_grid`'s `make_strategy` is still used
    (it correctly wraps `TrendFilter` for the `+trend` variants), but its grid
    is replaced by a single entry from `default_params`, so `best_params` for
    every valid fold is that same fixed tuple. This makes every gate on a scan
    row — including `overfit` and `insufficient-folds`, which read straight
    off the walk-forward folds — judge one object instead of two: the pinned
    configuration is what a soak test actually runs, so the gates must judge
    that configuration, not a fold-by-fold re-optimized one.

    Whether the strategy FAMILY has edge under per-fold re-optimization is a
    separate question — the `walkforward` CLI command still answers it, using
    the full grid from `walk_forward_grid` unpinned.
    """
    config = scan_risk_config(risk_per_trade=risk_per_trade, stop_loss_pct=stop_loss_pct)
    strategy = build_strategy(strategy_name, trend_sma=trend_sma)
    res = simulate(df, strategy, config, cash=cash, fee=fee, warmup=warmup)

    net = total_return(res.equity) if len(res.equity) else 0.0
    # Baseline buy&hold over the SAME window the strategy was measured on: the
    # equity series starts at bar `warmup`, not bar 0, so comparing against a
    # bar-0 baseline would subtract returns measured over different spans.
    # Guarded the same way as `net`: an empty equity series means warmup >=
    # len(df), and `df["close"].iloc[warmup:]` would then be empty too.
    hold = buy_and_hold_return(df["close"].iloc[warmup:], fee=fee) if len(res.equity) else 0.0

    # Pin the walk-forward grid to the same fixed params `build_strategy` used
    # above, instead of the full `walk_forward_grid` (which re-optimizes per
    # fold). NOT `None` and NOT an empty list: `walk_forward` treats
    # `best_params is None` after its optimization loop as "fold invalid",
    # so the sentinel for "don't search, just use this" has to be an actual
    # one-entry grid, or every fold would report invalid even when it traded.
    _, make_strategy = walk_forward_grid(strategy_name, trend_sma=trend_sma)
    pinned_grid = [default_params(strategy_name)]
    try:
        folds = walk_forward(df, make_strategy, pinned_grid, n_splits=splits,
                             initial_cash=cash, fee=fee, warmup=warmup,
                             risk_config=config)
    except ValueError:
        folds = []          # not enough data to split at all
    traded = [f for f in folds if f["valid"] and f["oos_trades"] > 0]
    avg_is = sum(f["in_sample_return"] for f in traded) / len(traded) if traded else 0.0
    avg_oos = sum(f["oos_return"] for f in traded) / len(traded) if traded else 0.0

    span_days = 0.0
    if len(df.index) >= 2:
        span_days = (pd.Timestamp(df.index[-1]) - pd.Timestamp(df.index[0])).total_seconds() / 86_400.0

    row = {
        "symbol": symbol,
        "timeframe": timeframe,
        "strategy": strategy_name,
        "bars": len(df),
        "days": span_days,
        "trades": len(res.trades),
        "trades_per_day": trades_per_day(len(res.trades), df.index),
        "net_return": net,
        "edge": net - hold,
        "max_drawdown": max_drawdown(res.equity) if len(res.equity) else 0.0,
        "worst_loss": worst_cumulative_loss(res.trades, cash),
        "fee_drag": fee_drag(res.fills, res.trades),
        "avg_is": avg_is,
        "avg_oos": avg_oos,
        "oos_gap": avg_is - avg_oos,
        "folds_traded": len(traded),
    }
    row["verdict"], row["reason"] = verdict(row)
    return row


def rank(rows: list) -> list:
    """Passing configurations first, best edge first. Failures follow, grouped by
    reason — they are kept, never dropped: a named rejection is information."""
    passing = sorted([r for r in rows if r["verdict"] == "PASS"],
                     key=lambda r: r["edge"], reverse=True)
    failing = sorted([r for r in rows if r["verdict"] != "PASS"],
                     key=lambda r: (r["reason"], r["strategy"], r["timeframe"]))
    return passing + failing


def format_table(rows: list) -> str:
    """Render scan rows as an aligned table.

    `days` and `trades_per_day` are printed at higher precision than the other
    columns on purpose: `trades_per_day` sits right at the churn gate boundary
    in real data (e.g. 6.0004 vs a 6.0 ceiling), and rounding either column
    toward the passing side would make a genuine FAIL look like an arithmetic
    PASS. `avgIS`/`avgOOS` are printed (rather than just their gap) so the
    `overfit` gate's condition (`avg_is > 0 and avg_oos < 0`) can be checked
    directly against the row that failed it.

    `format(float("inf"), spec)` already pads correctly under a float spec —
    used directly here (no wrapper) so the "fee_drag = inf" row keeps its
    column width instead of collapsing to a bare "inf" and shifting every
    later column.
    """
    header = (f"{'symbol':<10} {'tf':>4} {'strategy':<10} {'bars':>6} {'days':>8} "
              f"{'trades':>6} {'tr/day':>9} {'net':>8} {'edge':>8} {'maxDD':>7} "
              f"{'worst':>7} {'feedrag':>8} {'avgIS':>8} {'avgOOS':>8} {'folds':>5}  verdict")
    lines = [header, "-" * len(header)]
    for r in rows:
        tag = r["verdict"] if r["verdict"] == "PASS" else f"FAIL {r['reason']}"
        lines.append(
            f"{r['symbol']:<10} {r['timeframe']:>4} {r['strategy']:<10} "
            f"{r['bars']:>6} {r['days']:>8.3f} {r['trades']:>6} "
            f"{r['trades_per_day']:>9.4f} {r['net_return']:>8.2%} "
            f"{r['edge']:>+8.2%} {r['max_drawdown']:>7.1%} {r['worst_loss']:>7.1%} "
            f"{r['fee_drag']:>8.2f} {r['avg_is']:>+8.2%} {r['avg_oos']:>+8.2%} "
            f"{r['folds_traded']:>5}  {tag}"
        )
    return "\n".join(lines)
