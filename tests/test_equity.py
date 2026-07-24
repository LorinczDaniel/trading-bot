import pandas as pd
import pytest

from data.equity import EquityProvider, SURVIVORSHIP_WARNING


class FakeYF:
    """Stands in for yfinance. Returns capitalised columns like the real one."""

    def __init__(self, frames):
        self.frames = frames
        self.calls = []

    def history(self, symbol, period=None, start=None, interval="1d",
                auto_adjust=True):
        self.calls.append({"symbol": symbol, "period": period, "start": start,
                           "interval": interval, "auto_adjust": auto_adjust})
        return self.frames.get(symbol, pd.DataFrame())


def _yf_frame(n=5, start="2026-01-01"):
    idx = pd.date_range(start, periods=n, freq="1D", tz="America/New_York")
    return pd.DataFrame({
        "Open": [100.0] * n, "High": [101.0] * n, "Low": [99.0] * n,
        "Close": [100.0 + i for i in range(n)], "Volume": [1_000] * n,
    }, index=idx)


def test_columns_are_lowercased_to_match_the_crypto_cache(tmp_path):
    yf = FakeYF({"AAPL": _yf_frame()})
    p = EquityProvider(yf, cache_dir=str(tmp_path))
    df = p.backfill("AAPL")
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]


def test_the_index_is_tz_naive_so_it_aligns_with_cached_crypto(tmp_path):
    """yfinance returns exchange-local timestamps. A tz-aware index will not
    align with the tz-naive crypto cache, and `panel.build_panel` would produce
    a frame of NaNs rather than an error."""
    yf = FakeYF({"AAPL": _yf_frame()})
    df = EquityProvider(yf, cache_dir=str(tmp_path)).backfill("AAPL")
    assert df.index.tz is None


def test_adjusted_prices_are_requested_not_raw(tmp_path):
    """Splits are the equity analogue of the LUNA ticker-reuse splice: an
    unadjusted series shows a 4:1 split as a fabricated -75% single-day return,
    which any momentum or trend rule would read as a real move."""
    yf = FakeYF({"AAPL": _yf_frame()})
    EquityProvider(yf, cache_dir=str(tmp_path)).backfill("AAPL")
    assert yf.calls[0]["auto_adjust"] is True


def test_data_round_trips_through_the_cache(tmp_path):
    yf = FakeYF({"AAPL": _yf_frame()})
    p = EquityProvider(yf, cache_dir=str(tmp_path))
    p.backfill("AAPL")
    loaded = p.load_cached("AAPL")
    assert len(loaded) == 5
    assert loaded["close"].iloc[-1] == 104.0


def test_an_empty_response_raises_rather_than_caching_nothing(tmp_path):
    """A delisted ticker returns empty from yfinance. Silently caching an empty
    frame would make the symbol look merely absent instead of unavailable, and
    absence is exactly the bias the universe work exists to surface."""
    yf = FakeYF({})
    p = EquityProvider(yf, cache_dir=str(tmp_path))
    with pytest.raises(ValueError, match="no data"):
        p.backfill("LEHMQ")


def test_load_cached_missing_symbol_raises(tmp_path):
    p = EquityProvider(FakeYF({}), cache_dir=str(tmp_path))
    with pytest.raises(FileNotFoundError):
        p.load_cached("NOPE")


def test_backfill_merges_rather_than_overwriting(tmp_path):
    """Same rule the crypto cache learned: an overwriting fetch silently
    truncates history that a later, shorter request did not cover."""
    first = _yf_frame(5, start="2026-01-01")
    yf = FakeYF({"AAPL": first})
    p = EquityProvider(yf, cache_dir=str(tmp_path))
    p.backfill("AAPL")

    later = _yf_frame(3, start="2026-01-06")
    yf.frames["AAPL"] = later
    p.backfill("AAPL")

    merged = p.load_cached("AAPL")
    assert len(merged) == 8
    assert merged.index.is_monotonic_increasing


def test_the_newest_bar_wins_on_a_duplicate_timestamp(tmp_path):
    yf = FakeYF({"AAPL": _yf_frame(3)})
    p = EquityProvider(yf, cache_dir=str(tmp_path))
    p.backfill("AAPL")

    revised = _yf_frame(3)
    revised["Close"] = [999.0, 998.0, 997.0]
    yf.frames["AAPL"] = revised
    p.backfill("AAPL")

    assert p.load_cached("AAPL")["close"].iloc[0] == 999.0


def test_the_survivorship_warning_names_the_specific_hazard():
    """This blocker is measured, not theoretical: yfinance returns EMPTY for
    LEHMQ, ENRNQ, SIVBQ, FTCH and BBBYQ. It must be impossible to miss."""
    w = SURVIVORSHIP_WARNING.lower()
    assert "delisted" in w
    assert "cross-sectional" in w
