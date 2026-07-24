"""Equity price data, cached in the same shape as the crypto cache.

Writes lowercase OHLCV parquet with a tz-naive DatetimeIndex, so everything
downstream — `backtest/simulate.py`, `backtest/scan.py`,
`backtest/cross_sectional.py`, `data/panel.py` — runs on equities unchanged.
Load with `MarketDataProvider(exchange=None, cache_dir="cache/equity")` or with
`EquityProvider.load_cached`.

MEASURED LIMITATION, read this before designing anything cross-sectional
=======================================================================
yfinance does **not** serve delisted tickers. Probed 2026-07-24: LEHMQ (Lehman),
ENRNQ (Enron), SIVBQ (SVB), FTCH (Farfetch) and BBBYQ (Bed Bath & Beyond) all
return EMPTY.

This is worse than the crypto situation, where Binance kept serving delisted
coins and a survivorship-free universe could be reconstructed
(`docs/research/2026-07-24-multi-coin-data-integrity.md`). Here it cannot.

What that permits and forbids:

  OK    index and single-name time-series work — SPY back to 1993, AAPL to
        1980. Deep history directly addresses the evidence floor that was the
        binding constraint on crypto
        (`docs/research/2026-07-24-daily-bars-and-the-evidence-floor.md`).

  NOT OK  cross-sectional stock selection on this source. Ranking today's
        listed names over history is exactly the defect that produced a +573%
        result which collapsed to -99.7% once membership was made
        point-in-time (`docs/research/2026-07-24-point-in-time-cross-sectional.md`).
        Index membership history is reconstructible; the PRICES of the names
        that left are not, and that is the half that matters.

Honest cross-sectional equity work needs a survivorship-free source (CRSP,
Norgate, Sharadar). That costs money. Until then, treat any stock-picking
backtest built on this provider as measuring survivors only, and say so.
"""

import os

import pandas as pd

SURVIVORSHIP_WARNING = (
    "yfinance does not serve DELISTED tickers (verified: LEHMQ, ENRNQ, SIVBQ, "
    "FTCH, BBBYQ all return empty). Index/single-name work is fine; "
    "CROSS-SECTIONAL stock selection on this source measures survivors only "
    "and will overstate results the way the crypto top-30 universe did."
)


class EquityProvider:
    """Fetch and cache equity OHLCV in the project's standard parquet shape.

    `client` is anything exposing yfinance's `history()`; injected so the
    provider is testable without network access, matching how `MarketDataProvider`
    takes an exchange.
    """

    def __init__(self, client=None, cache_dir: str = "cache/equity"):
        if client is None:                      # pragma: no cover - real use
            import yfinance
            client = _YFinanceClient(yfinance)
        self.client = client
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def _path(self, symbol: str, timeframe: str) -> str:
        safe = symbol.replace("/", "-")
        return os.path.join(self.cache_dir, f"{safe}_{timeframe}.parquet")

    def load_cached(self, symbol: str, timeframe: str = "1d") -> pd.DataFrame:
        path = self._path(symbol, timeframe)
        if not os.path.exists(path):
            raise FileNotFoundError(f"No cached data at {path}")
        return pd.read_parquet(path)

    def backfill(self, symbol: str, timeframe: str = "1d",
                 period: str = "max", start=None) -> pd.DataFrame:
        """Fetch and MERGE into the cache, newest bar winning on a duplicate.

        Merging rather than overwriting is the rule the crypto cache arrived at
        the hard way: an overwriting fetch silently truncates history a later,
        shorter request did not cover.
        """
        raw = self.client.history(symbol, period=period, start=start,
                                  interval=timeframe, auto_adjust=True)
        if raw is None or len(raw) == 0:
            raise ValueError(
                f"no data for {symbol!r}. If it is delisted this source cannot "
                f"serve it. {SURVIVORSHIP_WARNING}"
            )

        df = raw.rename(columns={c: c.lower() for c in raw.columns})
        keep = [c for c in ("open", "high", "low", "close", "volume")
                if c in df.columns]
        df = df[keep]
        # yfinance returns exchange-local timestamps. A tz-aware index will not
        # align with the tz-naive crypto cache, and build_panel would quietly
        # produce a frame of NaNs rather than raising.
        if getattr(df.index, "tz", None) is not None:
            df.index = df.index.tz_localize(None)
        df.index = pd.DatetimeIndex(df.index)

        path = self._path(symbol, timeframe)
        if os.path.exists(path):
            old = pd.read_parquet(path)
            df = pd.concat([old, df])
            df = df[~df.index.duplicated(keep="last")]
        df = df.sort_index()
        df.to_parquet(path)
        return df


class _YFinanceClient:                          # pragma: no cover - thin shim
    """Adapts yfinance's Ticker API to the single `history()` call used here."""

    def __init__(self, yfinance):
        self._yf = yfinance

    def history(self, symbol, period=None, start=None, interval="1d",
                auto_adjust=True):
        t = self._yf.Ticker(symbol)
        if start is not None:
            return t.history(start=start, interval=interval,
                             auto_adjust=auto_adjust)
        return t.history(period=period or "max", interval=interval,
                         auto_adjust=auto_adjust)
