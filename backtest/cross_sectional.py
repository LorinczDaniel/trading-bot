"""Cross-sectional portfolio backtest: rank many coins, hold the top few.

**Why this is a second simulation path, and what that costs.**

This project deleted `backtest/engine.py` because it sized positions differently
from the live `Trader`, so backtests never predicted live behaviour. That lesson
applies here and must be stated plainly rather than discovered later:
`run_cross_sectional` is a THIRD code path, and it does not run `Trader.step`.

It is justified only because `Trader` is a single-symbol, signal-driven state
machine — it holds one position, reacts to BUY/SELL/HOLD, and enforces a stop
per symbol. A cross-sectional portfolio has no per-symbol signal and no stop; it
ranks the whole universe and rebalances into the top K on a schedule. Forcing
that through `Trader` would mean reimplementing ranking inside a class built for
something else.

The difference from the `engine.py` mistake is that engine.py diverged from an
EXISTING live path. There is no live cross-sectional trader. **If anything here
ever earns the right to trade real money, the live path must be built FROM this
module — not written alongside it.** That is the specific mitigation; without it
this becomes the same defect under a new name.

Everything measured here is deliberately pessimistic where a choice exists, on
the principle that a research instrument should not flatter its own subject.
"""

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class CrossSectionalResult:
    equity: pd.Series          # marked every bar, not only at rebalances
    rebalances: list           # per-rebalance detail: date, held, weights
    final_equity: float
    turnover: float            # mean fraction of the portfolio replaced
    forced_exits: int          # holdings liquidated because their data ended
    fees_paid: float = 0.0
    trades: list = field(default_factory=list)


def momentum_rank(window: int = 28):
    """Rank by trailing `window`-bar return — the simplest cross-sectional trend.

    Deliberately not the paper's 28-indicator elastic net. The question this
    harness answers first is whether cross-sectional ranking has any edge at all
    on our data; a faithful reproduction is only worth building if the cheap
    version shows something. Coins without a full window of history score NaN
    and are excluded rather than being ranked on a partial window, which would
    let a two-day-old listing outrank a year-old one on noise.
    """
    def rank(history: pd.DataFrame) -> pd.Series:
        if len(history) <= window:
            return pd.Series(dtype=float)
        past = history.iloc[-(window + 1)]
        now = history.iloc[-1]
        # A coin missing either endpoint has no measurable return over the
        # window; NaN propagates and the caller drops it.
        return (now / past) - 1.0
    return rank


def run_cross_sectional(panel: pd.DataFrame, rank_fn, top_k: int = 5,
                        rebalance_days: int = 7, cash: float = 10_000.0,
                        fee: float = 0.001, warmup: int = 30,
                        members_fn=None) -> CrossSectionalResult:
    """Replay an equal-weighted top-K portfolio over `panel` (wide close prices).

    At each rebalance the ranker is handed history strictly BEFORE the executing
    bar, so a signal can never be computed from the price it trades at. Coins
    with no price on the rebalance date are ineligible however well they rank —
    they could not have been bought.

    `members_fn(date) -> list` supplies point-in-time universe membership: only
    those symbols may be held on that date, and a holding that drops out is
    sold. Omitting it makes the whole panel eligible, which is what produced the
    invalidated result in `2026-07-24-cross-sectional-results.md` — kept so the
    biased and unbiased runs can be compared through one engine rather than two.

    Positions are equally weighted, fees are charged on both sides of every
    change, and equity is marked on every bar so drawdown inside a holding
    period is visible.
    """
    if panel.empty or warmup >= len(panel):
        return CrossSectionalResult(pd.Series(dtype=float), [], cash, 0.0, 0)

    holdings = {}                      # symbol -> quantity
    free_cash = cash
    rebalances, trades = [], []
    equity_points, equity_index = [], []
    turnovers = []
    forced_exits = 0
    fees_paid = 0.0

    def price_at(symbol, i):
        value = panel[symbol].iloc[i]
        return None if pd.isna(value) else float(value)

    last_seen = {}                     # symbol -> last observed price

    for i in range(warmup, len(panel)):
        # --- refresh last-known prices and force-exit anything that died -----
        for symbol in list(holdings):
            p = price_at(symbol, i)
            if p is not None:
                last_seen[symbol] = p
            else:
                # The coin stopped trading while held. Liquidating at the last
                # print is optimistic — a real delisting may be unsellable — so
                # the count is reported and any result leaning on it is suspect.
                qty = holdings.pop(symbol)
                stale = last_seen.get(symbol)
                if stale is not None:
                    proceeds = qty * stale
                    free_cash += proceeds - proceeds * fee
                    fees_paid += proceeds * fee
                forced_exits += 1

        is_rebalance = (i - warmup) % rebalance_days == 0
        if is_rebalance:
            history = panel.iloc[:i]           # strictly before the trading bar
            scores = rank_fn(history)
            if scores is None:
                scores = pd.Series(dtype=float)
            scores = scores.dropna()

            # Point-in-time membership: who was liquid enough to trade on this
            # date, judged only on data available then.
            allowed = None
            if members_fn is not None:
                allowed = set(members_fn(panel.index[i]))

            # Only coins with a price on THIS bar can actually be traded.
            eligible = [s for s in scores.index
                        if s in panel.columns and price_at(s, i) is not None
                        and (allowed is None or s in allowed)]
            ranked = sorted(eligible, key=lambda s: scores[s], reverse=True)
            target = ranked[:top_k]

            before = set(holdings)
            # Sell everything not in the target.
            for symbol in list(holdings):
                if symbol not in target:
                    p = price_at(symbol, i)
                    qty = holdings.pop(symbol)
                    if p is not None:
                        proceeds = qty * p
                        free_cash += proceeds - proceeds * fee
                        fees_paid += proceeds * fee
                        trades.append({"date": panel.index[i], "symbol": symbol,
                                       "side": "sell", "price": p, "qty": qty})

            # Mark the book, then split it equally across the target.
            book = free_cash + sum(
                q * (price_at(s, i) or last_seen.get(s, 0.0))
                for s, q in holdings.items()
            )
            if target:
                per = book / len(target)
                for symbol in target:
                    p = price_at(symbol, i)
                    held_value = holdings.get(symbol, 0.0) * p
                    delta_value = per - held_value
                    if delta_value > 0:                     # top up
                        spend = min(delta_value, free_cash)
                        if spend > 0:
                            cost_fee = spend * fee
                            qty = (spend - cost_fee) / p
                            holdings[symbol] = holdings.get(symbol, 0.0) + qty
                            free_cash -= spend
                            fees_paid += cost_fee
                            trades.append({"date": panel.index[i], "symbol": symbol,
                                           "side": "buy", "price": p, "qty": qty})
                    elif delta_value < 0:                   # trim
                        qty = min(-delta_value / p, holdings.get(symbol, 0.0))
                        if qty > 0:
                            proceeds = qty * p
                            holdings[symbol] -= qty
                            free_cash += proceeds - proceeds * fee
                            fees_paid += proceeds * fee
                    last_seen[symbol] = p

            after = set(holdings)
            # The first rebalance builds the book out of cash, which is always
            # 100% "replacement" by construction. Counting it would make the
            # reported turnover depend on sample length — a 3-rebalance run
            # would show a 33% floor and a 100-rebalance run a 1% floor — so
            # what is averaged is the steady-state replacement rate.
            if before:
                changed = len(before ^ after)
                denom = max(len(before | after), 1)
                turnovers.append(changed / denom)
            rebalances.append({
                "date": panel.index[i],
                "held": list(target),
                "weights": {s: holdings.get(s, 0.0) * (price_at(s, i) or 0.0)
                            for s in target},
            })

        # --- mark to market -------------------------------------------------
        value = free_cash
        for symbol, qty in holdings.items():
            p = price_at(symbol, i)
            if p is None:
                p = last_seen.get(symbol, 0.0)
            value += qty * p
        equity_points.append(value)
        equity_index.append(panel.index[i])

    equity = pd.Series(equity_points, index=equity_index)
    return CrossSectionalResult(
        equity=equity,
        rebalances=rebalances,
        final_equity=float(equity.iloc[-1]) if len(equity) else float(cash),
        turnover=sum(turnovers) / len(turnovers) if turnovers else 0.0,
        forced_exits=forced_exits,
        fees_paid=fees_paid,
        trades=trades,
    )
