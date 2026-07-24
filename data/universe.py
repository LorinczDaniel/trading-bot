"""Choosing which coins to download for cross-sectional work.

**This module picks download candidates, not universe membership.** The
distinction is the whole point, so it is stated here rather than in a docstring
nobody reads: ranking by *today's* volume and applying that set to 2023 is
look-ahead, of the same class as the data-snooping this project has rejected
twice. Membership at each rebalance date must be re-derived from trailing volume
in the cached data itself.

What this module is for is the unavoidable discovery step — an exchange will not
tell us what was liquid three years ago, so we start from what exists now,
deliberately keep the coins that died, and let `extra` force in any known-dead
symbol the current ranking would miss.

See `docs/research/2026-07-24-multi-coin-data-integrity.md` for the measurements
behind both rules.
"""

#: Bases that are not bets. Stablecoins are the numeraire, so their
#: cross-sectional trend rank is noise around zero by construction.
EXCLUDED_BASES = {
    "USDT", "USDC", "BUSD", "FDUSD", "TUSD", "DAI", "USDP", "UST", "USTC",
    "EUR", "GBP", "AEUR",
}

#: Leveraged-token suffixes. These are daily-rebalanced derivatives whose prices
#: decay mechanically regardless of the underlying, so they would inject
#: artificial trends into any ranking.
_LEVERAGED_SUFFIXES = ("UP", "DOWN", "BULL", "BEAR")


def _is_leveraged(base: str) -> bool:
    # Guard against a base that IS the suffix (e.g. a coin literally named
    # "UP"), which would otherwise be excluded on an empty stem.
    return any(base.endswith(s) and len(base) > len(s) for s in _LEVERAGED_SUFFIXES)


def candidate_symbols(exchange, quote: str = "USDT", limit: int = 50,
                      extra=None) -> list:
    """Return up to `limit` spot symbols quoted in `quote`, ranked by current
    quote volume, plus any `extra` symbols appended if not already present.

    Inactive (delisted) markets are **deliberately kept**. Filtering them out is
    what makes a reconstructed universe survivorship-biased, and the exchange
    still serves their history — measured, not assumed.

    Symbols missing from `fetch_tickers` or reporting a null volume sort last
    rather than raising: that is the normal condition for a dead coin, and
    dropping them would quietly reintroduce the bias.
    """
    markets = exchange.load_markets()
    try:
        tickers = exchange.fetch_tickers()
    except Exception:
        # Ranking is a convenience; losing it must not make the universe
        # unbuildable, because the download set matters more than its order.
        tickers = {}

    eligible = []
    for symbol, m in markets.items():
        if m.get("quote") != quote:
            continue
        if not m.get("spot", True):
            continue
        base = m.get("base") or symbol.split("/")[0]
        if base in EXCLUDED_BASES or _is_leveraged(base):
            continue
        vol = (tickers.get(symbol) or {}).get("quoteVolume")
        eligible.append((symbol, float(vol) if vol else 0.0))

    eligible.sort(key=lambda pair: pair[1], reverse=True)
    out = [symbol for symbol, _ in eligible[:limit]]

    for symbol in (extra or []):
        if symbol not in out:
            out.append(symbol)
    return out
