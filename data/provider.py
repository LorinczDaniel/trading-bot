import os

import pandas as pd

OHLCV_COLUMNS = ["ts", "open", "high", "low", "close", "volume"]


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
