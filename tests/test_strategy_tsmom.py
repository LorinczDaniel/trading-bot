import numpy as np
import pandas as pd
import pytest

from strategies.timeseries_momentum import TimeSeriesMomentum


def _df(closes):
    return pd.DataFrame({"close": [float(c) for c in closes]})


def test_holds_until_there_is_enough_history():
    s = TimeSeriesMomentum(window=3, hold=2, history=10)
    assert s.generate(_df([100, 101, 102])).action == "HOLD"


def test_buys_when_trailing_return_is_in_the_top_third():
    # flat for a long stretch, then a sharp rally: the final trailing return
    # is the highest in its own history, so it must clear the top-third cut
    s = TimeSeriesMomentum(window=3, hold=1, history=10)
    closes = [100.0] * 20 + [110.0, 125.0, 145.0]
    sig = s.generate(_df(closes))
    assert sig.action == "BUY", sig.reason


def test_sells_when_trailing_return_is_not_in_the_top_third():
    # flat for a long stretch, then a sharp fall: trailing return is the worst
    s = TimeSeriesMomentum(window=3, hold=1, history=10)
    closes = [100.0] * 20 + [95.0, 88.0, 80.0]
    sig = s.generate(_df(closes))
    assert sig.action == "SELL", sig.reason


def test_stays_long_for_the_hold_window_after_the_signal_stops_firing():
    """The published rule is 'enter on signal, hold N bars' — not 'exit the
    moment the signal drops out'. Without this, the strategy would churn."""
    # The rally must sit more than `window` bars back, otherwise the trailing
    # 3-bar return still spans it and the signal legitimately still fires.
    # Here the last 3-bar return is ~+0.4%, well outside the top third, but the
    # rally bar is still inside a 5-bar hold window.
    closes = [100.0] * 20 + [110.0, 125.0, 145.0] + [145.5, 146.0, 146.2, 146.1]
    short_hold = TimeSeriesMomentum(window=3, hold=1, history=10)
    long_hold = TimeSeriesMomentum(window=3, hold=5, history=10)

    assert short_hold.generate(_df(closes)).action == "SELL"
    assert long_hold.generate(_df(closes)).action == "BUY"


def test_lookback_covers_return_window_history_and_hold():
    """`window` is the return-measurement window; `lookback` is the Strategy
    protocol's 'bars of history I need', which is strictly larger."""
    s = TimeSeriesMomentum(window=28, hold=5, history=365)
    assert s.lookback == 28 + 365 + 5 + 1


def test_rejects_nonsense_parameters():
    with pytest.raises(ValueError):
        TimeSeriesMomentum(window=0)
    with pytest.raises(ValueError):
        TimeSeriesMomentum(hold=0)
    with pytest.raises(ValueError):
        TimeSeriesMomentum(quantile=1.5)


def test_signal_is_unchanged_by_extra_leading_history():
    """The replay passes a bounded tail window, so a signal must depend only on
    the trailing window — not on how much older data happens to be prepended."""
    s = TimeSeriesMomentum(window=3, hold=2, history=10)
    tail = [100.0] * 20 + [110.0, 125.0, 145.0]
    rng = np.random.default_rng(0)
    noise = list(100 + rng.normal(0, 20, 500))

    assert s.generate(_df(tail)).action == s.generate(_df(noise + tail)).action
