"""Point-in-time universe membership.

The defect that invalidated `2026-07-24-cross-sectional-results.md` was not the
strategy or the engine — it was deciding *which coins to rank* using today's
volume and applying that set to 2023. A coin that ran hard in 2025 is in today's
top-30 because it ran, so the recent window was structurally stacked with
winners and the backtest reported an edge that vanished under control.

This module answers the question the right way round: at each rebalance date,
who was actually liquid *then*, judged only on data available *then*.
"""

import pandas as pd

#: Bars of trailing history a coin must have before it can be a member. A
#: two-week-old listing has no record to rank on, and admitting it lets a brand
#: new coin displace an established one on a few days of launch-hype volume —
#: which is the same "select on recent excitement" bias in miniature.
MIN_HISTORY_BARS = 90


def build_volume_panel(frames: dict) -> pd.DataFrame:
    """Wide panel of **quote** volume (price x base volume), one column per symbol.

    Quote volume, not base volume: liquidity is a money quantity. Ranking on base
    volume would put a coin priced at $0.0001 above one priced at $50,000 purely
    because more units change hands.

    NaN wherever a symbol had no bar, matching `data.panel.build_panel` so the
    two align index-for-index.
    """
    columns = {}
    for symbol, df in frames.items():
        close = pd.to_numeric(df["close"], errors="coerce")
        volume = pd.to_numeric(df["volume"], errors="coerce")
        columns[symbol] = close * volume
    if not columns:
        return pd.DataFrame()
    return pd.concat(columns, axis=1, sort=False).sort_index()


def members_at(volume_panel: pd.DataFrame, date, top_n: int = 50,
               lookback: int = 30) -> list:
    """Symbols that were the most liquid `top_n` as of `date`, most liquid first.

    Uses only rows strictly at or before `date`, so membership can never be
    informed by what a coin went on to do. A symbol qualifies when it has at
    least `MIN_HISTORY_BARS` observations by that date and non-zero average
    quote volume over the trailing `lookback` bars.
    """
    if volume_panel.empty:
        return []

    history = volume_panel.loc[:date]
    if history.empty:
        return []

    # Vectorized on purpose: this runs once per rebalance over hundreds of
    # columns, and a per-symbol Python loop made the full backtest take minutes.
    counts = history.notna().sum()                    # observations so far
    avg = history.tail(lookback).mean()               # trailing liquidity
    eligible = counts[counts >= MIN_HISTORY_BARS].index
    scores = avg[eligible].dropna()
    scores = scores[scores > 0]                       # not trading, not investable
    return list(scores.sort_values(ascending=False).index[:top_n])
