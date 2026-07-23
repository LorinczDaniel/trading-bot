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


from data.provider import timeframe_to_ms

HOUR_MS = 3_600_000


def _bars(start_ms, count, step_ms=HOUR_MS):
    """Synthetic OHLCV rows: [ts, open, high, low, close, volume]."""
    return [[start_ms + i * step_ms, 100.0, 101.0, 99.0, 100.0 + i, 1.0]
            for i in range(count)]


class FakePagingExchange:
    """Serves bars from an in-memory list, honouring `since` and `limit`."""

    def __init__(self, bars):
        self.bars = bars
        self.since_calls = []

    def fetch_ohlcv(self, symbol, timeframe="1h", since=None, limit=1000):
        self.since_calls.append(since)
        page = [b for b in self.bars if since is None or b[0] >= since]
        return page[:limit]


def test_timeframe_to_ms_known_values():
    assert timeframe_to_ms("1m") == 60_000
    assert timeframe_to_ms("1h") == HOUR_MS
    assert timeframe_to_ms("4h") == 4 * HOUR_MS


def test_timeframe_to_ms_rejects_unknown():
    with pytest.raises(ValueError):
        timeframe_to_ms("7s")


def test_backfill_pages_past_the_limit(tmp_path):
    now = 3000 * HOUR_MS
    start = now - 2500 * HOUR_MS
    ex = FakePagingExchange(_bars(start, 2500))
    prov = MarketDataProvider(ex, cache_dir=str(tmp_path))

    df = prov.backfill("BTC/USDT", "1h", days=200, page_limit=1000, now_ms=now)

    assert len(df) == 2500                      # not capped at one page
    assert len(ex.since_calls) >= 3             # 2500 bars needs >= 3 pages
    assert df.index.is_monotonic_increasing
    assert not df.index.has_duplicates


def test_backfill_stops_when_exchange_makes_no_progress(tmp_path):
    """An exchange that ignores `since` must not loop forever."""
    now = 100 * HOUR_MS

    class StuckExchange:
        def __init__(self):
            self.calls = 0

        def fetch_ohlcv(self, symbol, timeframe="1h", since=None, limit=1000):
            self.calls += 1
            return _bars(0, 3)   # always the same three ancient bars

    ex = StuckExchange()
    prov = MarketDataProvider(ex, cache_dir=str(tmp_path))
    df = prov.backfill("BTC/USDT", "1h", days=5, page_limit=1000, now_ms=now)

    assert ex.calls <= 2         # detected no progress and gave up
    assert len(df) == 3


def test_backfill_on_empty_page_returns_what_it_has(tmp_path):
    class EmptyExchange:
        def fetch_ohlcv(self, symbol, timeframe="1h", since=None, limit=1000):
            return []

    prov = MarketDataProvider(EmptyExchange(), cache_dir=str(tmp_path))
    df = prov.backfill("BTC/USDT", "1h", days=5, now_ms=100 * HOUR_MS)
    assert df.empty
