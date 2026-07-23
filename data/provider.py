import os
import time

import pandas as pd

OHLCV_COLUMNS = ["ts", "open", "high", "low", "close", "volume"]

_TIMEFRAME_MS = {
    "1m": 60_000, "3m": 180_000, "5m": 300_000, "15m": 900_000,
    "30m": 1_800_000, "1h": 3_600_000, "2h": 7_200_000, "4h": 14_400_000,
    "6h": 21_600_000, "12h": 43_200_000, "1d": 86_400_000,
}


def timeframe_to_ms(timeframe: str) -> int:
    """Bar duration in milliseconds — used to advance the backfill cursor."""
    try:
        return _TIMEFRAME_MS[timeframe]
    except KeyError:
        raise ValueError(
            f"unsupported timeframe: {timeframe!r} (known: {sorted(_TIMEFRAME_MS)})"
        ) from None


def _to_dataframe(raw: list) -> pd.DataFrame:
    df = pd.DataFrame(raw, columns=OHLCV_COLUMNS)
    df["ts"] = pd.to_datetime(df["ts"], unit="ms")
    return df.set_index("ts")


class MarketDataProvider:
    def __init__(self, exchange, cache_dir: str = "cache"):
        self.exchange = exchange
        self.cache_dir = cache_dir

    def _cache_path(self, symbol: str, timeframe: str) -> str:
        safe = symbol.replace("/", "-")
        return os.path.join(self.cache_dir, f"{safe}_{timeframe}.parquet")

    def fetch(self, symbol: str, timeframe: str = "1h", limit: int = 500) -> pd.DataFrame:
        raw = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = _to_dataframe(raw)
        os.makedirs(self.cache_dir, exist_ok=True)
        df.to_parquet(self._cache_path(symbol, timeframe))
        return df

    def load_cached(self, symbol: str, timeframe: str = "1h") -> pd.DataFrame:
        path = self._cache_path(symbol, timeframe)
        if not os.path.exists(path):
            raise FileNotFoundError(f"No cached data at {path}")
        return pd.read_parquet(path)

    def backfill(self, symbol: str, timeframe: str = "1h", days: int = 365,
                 page_limit: int = 1000, now_ms: int | None = None) -> pd.DataFrame:
        """Page backwards-to-forwards through history, one exchange page at a time.

        A single `fetch_ohlcv` call is capped (1000 bars at Binance), so anything
        longer than that must be assembled from consecutive pages. The cursor
        advances past the last bar of each page; if it fails to advance the
        exchange is ignoring `since` and we stop rather than loop forever.
        """
        bar_ms = timeframe_to_ms(timeframe)
        now = now_ms if now_ms is not None else int(time.time() * 1000)
        cursor = now - days * 86_400_000
        rows: list = []

        while cursor < now:
            page = self.exchange.fetch_ohlcv(
                symbol, timeframe=timeframe, since=cursor, limit=page_limit
            )
            if not page:
                break
            rows.extend(page)
            next_cursor = page[-1][0] + bar_ms
            if next_cursor <= cursor:
                break          # exchange clamped `since`; no progress to be made
            cursor = next_cursor

        if not rows:
            return _to_dataframe([])
        df = _to_dataframe(rows)
        return df[~df.index.duplicated(keep="last")].sort_index()
