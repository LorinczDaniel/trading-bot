"""Multi-symbol price panel for cross-sectional work.

A cross-sectional strategy ranks coins against each other, so the panel's job is
not just to hold prices — it is to make sure the ranking is scored against a
universe that could actually have been traded. Two hazards are handled here, both
measured before this module was written
(`docs/research/2026-07-24-multi-coin-data-integrity.md`):

1. **Alignment must not invent prices.** A coin listed later must read NaN before
   its first bar and a delisted coin must read NaN after its last, so the ranking
   can never hold something that could not be bought or sold.
2. **Ticker reuse must be screened out.** Binance reassigned `LUNA/USDT` from
   Terra Classic to Terra 2.0 and left the pre-collapse history attached, so that
   symbol shows a 177,400x gain in 18 days. Any trend or momentum ranking would
   buy that at maximum weight and the backtest would be meaningless.
"""

import pandas as pd

#: A single-bar return above this multiple is treated as a redenomination rather
#: than a price move. Real assets do not gain 2,000% in one bar; renames and
#: token swaps do. Set well above genuine crypto volatility (the largest honest
#: daily moves are a few hundred percent) and far below the LUNA artifact's
#: 177,400x, so the screen has no need to be precise to catch the real cases.
MAX_BAR_RETURN = 20.0

#: Daily return standard deviation below which a series is treated as a
#: stablecoin rather than a bet. Real coins run 3-6% daily; pegged tokens run
#: under 0.1%. The gap is two orders of magnitude, so the exact threshold does
#: not need to be defended — anything in between separates them cleanly.
#:
#: Screened here rather than by name in `data/universe.py` because new
#: stablecoins keep being issued and a denylist only catches the ones already
#: known. `USD1/USDT` reached the cache exactly that way and churned on noise
#: around $1.00 at fee drag 1.14. A stablecoin is identifiable by what it does.
MIN_VOLATILITY = 0.005

#: Observations required before the volatility screen will call anything a
#: stablecoin. A few bars of quiet drift are indistinguishable from a peg, and
#: guessing wrong drops a real coin from the universe — the exact bias the
#: universe builder is written to avoid.
MIN_VOLATILITY_BARS = 30


def find_redenominations(close: pd.Series) -> list:
    """Return the timestamps where `close` jumps by more than `MAX_BAR_RETURN`.

    Flags the bar the impossible jump lands on, not the collapse that preceded
    it: the collapse is usually real (the asset did die) and it is the recovery
    on a reassigned ticker that is fictional.

    Deliberately one-sided. A crash — however violent — is left alone, because
    coins going to zero is exactly the evidence a survivorship-free universe
    exists to preserve. Only implausible *gains* are treated as artifacts.

    Zero and missing prices are ordinary in dead coins, so they are excluded
    from the ratio rather than allowed to produce inf/NaN comparisons.
    """
    prices = pd.to_numeric(close, errors="coerce")
    prev = prices.shift(1)
    # Guard the denominator: a zero previous price makes every ratio infinite,
    # which would flag every recovery from a zero print as a redenomination.
    valid = prices.notna() & prev.notna() & (prev > 0)
    ratio = prices[valid] / prev[valid]
    return list(ratio.index[ratio > MAX_BAR_RETURN])


def realized_volatility(close: pd.Series) -> float:
    """Standard deviation of simple returns, used to tell coins from pegs.

    Returns `inf` when there are fewer than `MIN_VOLATILITY_BARS` observations,
    so a short series is never mistaken for a stablecoin: absence of evidence
    must not silently exclude a coin, which would open a fresh survivorship hole
    inside the screen meant to prevent one. A handful of bars cannot distinguish
    a peg from a coin that happened to drift quietly for a week.

    Gaps are dropped rather than propagated, since delisted and thinly traded
    coins routinely have them.
    """
    prices = pd.to_numeric(close, errors="coerce").dropna()
    if len(prices) < MIN_VOLATILITY_BARS:
        return float("inf")
    returns = prices.pct_change().dropna()
    if returns.empty:
        return float("inf")
    vol = returns.std()
    return float("inf") if pd.isna(vol) else float(vol)


def build_panel(frames: dict, screen: bool = True, return_dropped: bool = False):
    """Align per-symbol OHLCV frames into one wide close-price panel.

    `frames` maps symbol -> DataFrame with a `close` column and a timestamp
    index. The result has one column per symbol on the union of all indices,
    sorted, with NaN wherever a symbol had no bar — never a filled value.

    With `screen=True` (the default) symbols are excluded if they contain a
    redenomination or are flat enough to be a stablecoin. Pass
    `return_dropped=True` to receive `(panel, dropped)` where `dropped` maps the
    excluded symbol to the reason, so a caller can report what was removed
    instead of quietly shrinking the universe.
    """
    dropped = {}
    columns = {}
    for symbol, df in frames.items():
        close = df["close"]
        if screen:
            hits = find_redenominations(close)
            if hits:
                dropped[symbol] = f"redenomination at {hits[0].date()}"
                continue
            vol = realized_volatility(close)
            if vol < MIN_VOLATILITY:
                dropped[symbol] = f"stablecoin (daily vol {vol:.4%})"
                continue
        columns[symbol] = close

    if not columns:
        panel = pd.DataFrame()
    else:
        # concat on the union of indices; absent bars stay NaN by construction,
        # which is the property the look-ahead tests pin. `sort=False` is
        # explicit because pandas deprecated the implicit sort here; the
        # ordering is then established by `sort_index()` rather than left to a
        # default that is scheduled to change.
        panel = pd.concat(columns, axis=1, sort=False).sort_index()

    if return_dropped:
        return panel, dropped
    return panel
