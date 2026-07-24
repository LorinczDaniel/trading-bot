import pytest

from data.universe import candidate_symbols, EXCLUDED_BASES


class FakeExchange:
    def __init__(self, markets, tickers):
        self._markets = markets
        self._tickers = tickers

    def load_markets(self):
        return self._markets

    def fetch_tickers(self):
        return self._tickers


def _market(symbol, quote="USDT", active=True, spot=True):
    base = symbol.split("/")[0]
    return {"symbol": symbol, "base": base, "quote": quote,
            "active": active, "spot": spot}


def _ex(rows):
    """rows: list of (symbol, quoteVolume, active)."""
    markets = {s: _market(s, active=a) for s, _, a in rows}
    tickers = {s: {"symbol": s, "quoteVolume": v} for s, v, _ in rows}
    return FakeExchange(markets, tickers)


def test_symbols_are_ranked_by_quote_volume():
    ex = _ex([("BTC/USDT", 500.0, True),
              ("ETH/USDT", 900.0, True),
              ("XRP/USDT", 100.0, True)])
    assert candidate_symbols(ex, limit=3) == ["ETH/USDT", "BTC/USDT", "XRP/USDT"]


def test_limit_truncates_the_ranking():
    ex = _ex([("BTC/USDT", 500.0, True),
              ("ETH/USDT", 900.0, True),
              ("XRP/USDT", 100.0, True)])
    assert candidate_symbols(ex, limit=2) == ["ETH/USDT", "BTC/USDT"]


def test_inactive_symbols_are_kept():
    """The whole point. A delisted coin is exactly the evidence a
    survivorship-free universe needs; filtering on `active` would rebuild the
    bias this module exists to avoid. See
    docs/research/2026-07-24-multi-coin-data-integrity.md."""
    ex = _ex([("BTC/USDT", 500.0, True), ("FTT/USDT", 900.0, False)])
    assert "FTT/USDT" in candidate_symbols(ex, limit=5)


def test_only_the_requested_quote_currency_is_returned():
    markets = {"BTC/USDT": _market("BTC/USDT"),
               "BTC/EUR": _market("BTC/EUR", quote="EUR")}
    tickers = {"BTC/USDT": {"quoteVolume": 10.0},
               "BTC/EUR": {"quoteVolume": 99.0}}
    ex = FakeExchange(markets, tickers)
    assert candidate_symbols(ex, limit=5) == ["BTC/USDT"]


def test_leveraged_tokens_are_excluded():
    """UP/DOWN/BULL/BEAR tokens are daily-rebalanced derivatives whose prices
    decay by construction. They are not coins and would pollute a
    cross-sectional ranking with mechanical trends."""
    ex = _ex([("BTC/USDT", 500.0, True),
              ("BTCUP/USDT", 900.0, True),
              ("ETHDOWN/USDT", 800.0, True),
              ("XRPBULL/USDT", 700.0, True),
              ("EOSBEAR/USDT", 600.0, True)])
    assert candidate_symbols(ex, limit=10) == ["BTC/USDT"]


def test_stablecoins_are_excluded():
    """A stablecoin's cross-sectional trend rank is meaningless — it is the
    numeraire, not a bet. This includes the FAILED algorithmic stablecoins
    (UST/USTC): they were designed to be flat, so their collapse is a peg break
    rather than a price trend, and ranking them alongside real coins would
    score a de-pegging as a momentum signal."""
    ex = _ex([("BTC/USDT", 100.0, True),
              ("USDC/USDT", 900.0, True),
              ("UST/USDT", 850.0, True),
              ("FDUSD/USDT", 800.0, True)])
    assert candidate_symbols(ex, limit=10) == ["BTC/USDT"]
    assert "USDC" in EXCLUDED_BASES
    assert "UST" in EXCLUDED_BASES


def test_non_spot_markets_are_excluded():
    markets = {"BTC/USDT": _market("BTC/USDT"),
               "ETH/USDT": _market("ETH/USDT", spot=False)}
    tickers = {"BTC/USDT": {"quoteVolume": 10.0},
               "ETH/USDT": {"quoteVolume": 99.0}}
    ex = FakeExchange(markets, tickers)
    assert candidate_symbols(ex, limit=5) == ["BTC/USDT"]


def test_a_missing_or_null_volume_sorts_last_instead_of_raising():
    """Delisted symbols routinely report no volume. They must still be
    reachable rather than crashing the ranking."""
    markets = {"BTC/USDT": _market("BTC/USDT"),
               "FTT/USDT": _market("FTT/USDT", active=False)}
    tickers = {"BTC/USDT": {"quoteVolume": 10.0},
               "FTT/USDT": {"quoteVolume": None}}
    ex = FakeExchange(markets, tickers)
    assert candidate_symbols(ex, limit=5) == ["BTC/USDT", "FTT/USDT"]


def test_a_symbol_absent_from_tickers_is_still_offered():
    markets = {"BTC/USDT": _market("BTC/USDT"),
               "DEAD/USDT": _market("DEAD/USDT", active=False)}
    tickers = {"BTC/USDT": {"quoteVolume": 10.0}}
    ex = FakeExchange(markets, tickers)
    assert candidate_symbols(ex, limit=5) == ["BTC/USDT", "DEAD/USDT"]


def test_extra_symbols_are_included_even_below_the_limit():
    """Lets a caller force known-dead coins into the download set, which is
    how the survivorship gap gets closed deliberately rather than by luck."""
    ex = _ex([("BTC/USDT", 500.0, True), ("ETH/USDT", 900.0, True)])
    out = candidate_symbols(ex, limit=1, extra=["ETH/USDT", "LUNA/USDT"])
    assert out[0] == "ETH/USDT"
    assert "LUNA/USDT" in out
    assert len(out) == len(set(out))
