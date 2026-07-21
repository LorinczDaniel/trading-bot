import pandas as pd
import pytest

from data.provider import MarketDataProvider


class FakeExchange:
    def fetch_ohlcv(self, symbol, timeframe="1h", limit=500):
        return [
            [1609459200000, 1.0, 2.0, 0.5, 1.5, 100.0],
            [1609462800000, 1.5, 2.5, 1.0, 2.0, 120.0],
        ]


def test_fetch_shapes_and_caches(tmp_path):
    prov = MarketDataProvider(FakeExchange(), cache_dir=str(tmp_path))
    df = prov.fetch("BTC/USDT", "1h", limit=2)
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]
    assert df.index.name == "ts"
    assert len(df) == 2
    assert df["close"].iloc[-1] == 2.0


def test_load_cached_roundtrip(tmp_path):
    prov = MarketDataProvider(FakeExchange(), cache_dir=str(tmp_path))
    prov.fetch("BTC/USDT", "1h", limit=2)
    df2 = prov.load_cached("BTC/USDT", "1h")
    assert len(df2) == 2
    assert df2["close"].iloc[-1] == 2.0


def test_load_cached_missing_raises(tmp_path):
    prov = MarketDataProvider(FakeExchange(), cache_dir=str(tmp_path))
    with pytest.raises(FileNotFoundError):
        prov.load_cached("ETH/USDT", "1h")
