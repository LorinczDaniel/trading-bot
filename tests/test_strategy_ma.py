import pandas as pd
import pytest

from strategies.ma_crossover import MACrossover


def _df(prices):
    return pd.DataFrame({"close": prices})


def test_invalid_params_raise():
    with pytest.raises(ValueError):
        MACrossover(fast=5, slow=5)


def test_buy_on_upward_cross():
    # fast(2)=3.0 vs slow(3)=2.33 on last bar; equal on prev bar -> BUY
    sig = MACrossover(fast=2, slow=3).generate(_df([1, 1, 1, 1, 5]))
    assert sig.action == "BUY"


def test_sell_on_downward_cross():
    sig = MACrossover(fast=2, slow=3).generate(_df([5, 5, 5, 5, 1]))
    assert sig.action == "SELL"


def test_hold_when_no_cross():
    sig = MACrossover(fast=2, slow=3).generate(_df([1, 2, 3, 4, 5]))
    assert sig.action == "HOLD"


def test_hold_when_not_enough_data():
    sig = MACrossover(fast=2, slow=3).generate(_df([1, 2, 3]))
    assert sig.action == "HOLD"
    assert "not enough data" in sig.reason


def test_ma_lookback_covers_the_previous_bar():
    # generate() reads fast.iloc[-2], so slow bars alone are not enough
    assert MACrossover(fast=10, slow=30).lookback == 31


# --- cost band -------------------------------------------------------------
# A hairline cross costs a full round trip in fees and predicts almost nothing.
# The band replaces the single `slow` line with two: entries must clear
# slow*(1+band), exits must break slow*(1-band). See
# docs/research/2026-07-23-crypto-strategy-findings.md (fee drag is the
# dominant killer) for why this is the first mechanic tried.


def test_band_defaults_to_zero_so_existing_behaviour_is_unchanged():
    """The band must be opt-in. A silent default would retroactively change
    every measurement already recorded in the research docs."""
    assert MACrossover(fast=2, slow=3).band == 0.0
    assert MACrossover(fast=2, slow=3).generate(_df([1, 1, 1, 1, 5])).action == "BUY"
    assert MACrossover(fast=2, slow=3).generate(_df([5, 5, 5, 5, 1])).action == "SELL"
    assert MACrossover(fast=2, slow=3).generate(_df([1, 2, 3, 4, 5])).action == "HOLD"


def test_a_shallow_upward_cross_is_suppressed_by_the_band():
    """fast=3.00 against slow=2.333: it clears the raw line but not the
    2.333*1.30 = 3.033 band, so the round trip is not worth paying for."""
    sig = MACrossover(fast=2, slow=3, band=0.30).generate(_df([1, 1, 1, 1, 5]))
    assert sig.action == "HOLD"
    assert "band" in sig.reason


def test_a_decisive_upward_cross_still_buys_through_the_band():
    """Same bars, smaller band: 3.00 clears 2.333*1.10 = 2.567."""
    sig = MACrossover(fast=2, slow=3, band=0.10).generate(_df([1, 1, 1, 1, 5]))
    assert sig.action == "BUY"


def test_a_shallow_downward_cross_is_suppressed_by_the_band():
    """fast=3.00 against slow=3.667: below the raw line but not below the
    3.667*0.70 = 2.567 lower band."""
    sig = MACrossover(fast=2, slow=3, band=0.30).generate(_df([5, 5, 5, 5, 1]))
    assert sig.action == "HOLD"
    assert "band" in sig.reason


def test_a_decisive_downward_cross_still_sells_through_the_band():
    """Same bars, smaller band: 3.00 breaks 3.667*0.90 = 3.30."""
    sig = MACrossover(fast=2, slow=3, band=0.10).generate(_df([5, 5, 5, 5, 1]))
    assert sig.action == "SELL"


def test_the_band_is_measured_against_the_previous_bar_too():
    """The entry test is a CROSS of the upper line, not merely sitting above
    it — otherwise every bar of a sustained uptrend re-fires BUY and the band
    would increase churn instead of cutting it.

    Bars 3 and 4 both sit above the banded line, so the cross happened
    earlier; the only correct answer on bar 4 is HOLD.
    """
    sig = MACrossover(fast=2, slow=3, band=0.05).generate(_df([1, 1, 5, 9, 13]))
    assert sig.action == "HOLD"


def test_a_negative_band_is_rejected():
    with pytest.raises(ValueError):
        MACrossover(fast=2, slow=3, band=-0.01)


def test_a_band_of_one_or_more_is_rejected():
    """band >= 1 would put the lower line at or below zero, so no price could
    ever trigger a SELL and a position could never be exited on signal."""
    with pytest.raises(ValueError):
        MACrossover(fast=2, slow=3, band=1.0)
