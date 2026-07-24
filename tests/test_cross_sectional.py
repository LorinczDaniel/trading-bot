import pandas as pd
import pytest

from backtest.cross_sectional import (
    run_cross_sectional,
    momentum_rank,
)


def _panel(data, start="2026-01-01"):
    idx = pd.date_range(start, periods=len(next(iter(data.values()))), freq="1D")
    return pd.DataFrame(data, index=idx)


def _flat(n, value=100.0):
    return [value] * n


# --- look-ahead ------------------------------------------------------------
# The single property everything else depends on. Tested by capturing what the
# ranker is HANDED rather than by checking returns, so it cannot pass by
# coincidence on data where the lookahead happens not to pay.


def test_the_ranker_never_sees_the_bar_it_trades_on():
    seen = []

    def spy(history):
        seen.append(history.index[-1])
        return pd.Series({c: 1.0 for c in history.columns})

    panel = _panel({"A/USDT": _flat(40), "B/USDT": _flat(40)})
    run_cross_sectional(panel, spy, top_k=1, rebalance_days=10, warmup=10)

    assert seen, "ranker was never called"
    # Every rebalance must have been ranked on strictly earlier data.
    for executed, ranked_through in zip(_rebalance_dates(panel, 10, 10), seen):
        assert ranked_through < executed


def _rebalance_dates(panel, warmup, every):
    return list(panel.index[warmup::every])


def test_the_ranker_receives_history_not_a_single_row():
    seen = []

    def spy(history):
        seen.append(len(history))
        return pd.Series({c: 1.0 for c in history.columns})

    panel = _panel({"A/USDT": _flat(40)})
    run_cross_sectional(panel, spy, top_k=1, rebalance_days=10, warmup=10)
    assert all(n > 1 for n in seen)


# --- selection and weighting ----------------------------------------------


def test_the_top_k_coins_by_rank_are_held():
    # C ranks highest, then B, then A.
    ranks = {"A/USDT": 1.0, "B/USDT": 2.0, "C/USDT": 3.0}
    panel = _panel({s: _flat(30) for s in ranks})
    res = run_cross_sectional(panel, lambda h: pd.Series(ranks),
                              top_k=2, rebalance_days=10, warmup=10)
    held = res.rebalances[0]["held"]
    assert set(held) == {"C/USDT", "B/USDT"}


def test_positions_are_equally_weighted():
    ranks = {"A/USDT": 2.0, "B/USDT": 1.0}
    panel = _panel({"A/USDT": _flat(30, 100.0), "B/USDT": _flat(30, 50.0)})
    res = run_cross_sectional(panel, lambda h: pd.Series(ranks), top_k=2,
                              rebalance_days=10, warmup=10, cash=10_000.0, fee=0.0)
    weights = res.rebalances[0]["weights"]
    assert weights["A/USDT"] == pytest.approx(weights["B/USDT"], rel=1e-6)


def test_holding_fewer_coins_than_top_k_does_not_crash():
    """Early in a sample only a handful of coins exist. The engine must hold
    what it can rather than refusing to run — refusing would silently restrict
    every backtest to the recent, survivor-heavy era."""
    panel = _panel({"A/USDT": _flat(30)})
    res = run_cross_sectional(panel, lambda h: pd.Series({"A/USDT": 1.0}),
                              top_k=5, rebalance_days=10, warmup=10)
    assert len(res.rebalances[0]["held"]) == 1


def test_a_coin_with_no_price_today_is_not_eligible():
    """It cannot be bought, so it must not be ranked into the portfolio however
    good its history looks."""
    a = _flat(30)
    b = _flat(30)
    b[10] = float("nan")           # no price on the first rebalance date
    panel = _panel({"A/USDT": a, "B/USDT": b})
    ranks = pd.Series({"A/USDT": 1.0, "B/USDT": 99.0})
    res = run_cross_sectional(panel, lambda h: ranks, top_k=1,
                              rebalance_days=10, warmup=10)
    assert res.rebalances[0]["held"] == ["A/USDT"]


# --- accounting ------------------------------------------------------------


def test_a_flat_market_with_no_fees_preserves_capital():
    panel = _panel({"A/USDT": _flat(30), "B/USDT": _flat(30)})
    res = run_cross_sectional(panel, lambda h: pd.Series({"A/USDT": 1.0, "B/USDT": 2.0}),
                              top_k=2, rebalance_days=10, warmup=10,
                              cash=10_000.0, fee=0.0)
    assert res.final_equity == pytest.approx(10_000.0, rel=1e-9)


def test_fees_are_charged_and_erode_a_flat_market():
    """The mechanism that killed sixteen single-asset configurations must be
    present here too, or this engine would flatter every result it produces."""
    panel = _panel({"A/USDT": _flat(30), "B/USDT": _flat(30)})
    res = run_cross_sectional(panel, lambda h: pd.Series({"A/USDT": 1.0, "B/USDT": 2.0}),
                              top_k=2, rebalance_days=10, warmup=10,
                              cash=10_000.0, fee=0.01)
    assert res.final_equity < 10_000.0


def test_a_rising_position_raises_equity():
    rising = [100.0 + i for i in range(30)]
    panel = _panel({"A/USDT": rising})
    res = run_cross_sectional(panel, lambda h: pd.Series({"A/USDT": 1.0}), top_k=1,
                              rebalance_days=10, warmup=10, cash=10_000.0, fee=0.0)
    assert res.final_equity > 10_000.0


def test_equity_is_marked_between_rebalances_not_only_at_them():
    """A curve sampled only at rebalances hides the drawdown inside a holding
    period, and drawdown is a reported metric."""
    prices = _flat(30)
    prices[15] = 50.0                      # a crash strictly between rebalances
    panel = _panel({"A/USDT": prices})
    res = run_cross_sectional(panel, lambda h: pd.Series({"A/USDT": 1.0}), top_k=1,
                              rebalance_days=10, warmup=10, cash=10_000.0, fee=0.0)
    assert res.equity.min() < 9_000.0


def test_equity_index_matches_the_bars_it_covers():
    panel = _panel({"A/USDT": _flat(30)})
    res = run_cross_sectional(panel, lambda h: pd.Series({"A/USDT": 1.0}), top_k=1,
                              rebalance_days=10, warmup=10)
    assert res.equity.index[0] == panel.index[10]
    assert res.equity.index[-1] == panel.index[-1]


# --- delisting -------------------------------------------------------------


def test_a_held_coin_that_stops_trading_is_force_exited_and_counted():
    """A coin whose data ends while held cannot be marked forever. It is
    liquidated at its last observed price and COUNTED, because that exit is
    optimistic — a real delisting may not be sellable at the last print — and a
    result carried by many forced exits should be visible as such.
    """
    a = _flat(30)
    dead = _flat(30)
    for i in range(14, 30):
        dead[i] = float("nan")
    panel = _panel({"A/USDT": a, "DEAD/USDT": dead})
    res = run_cross_sectional(panel, lambda h: pd.Series({"A/USDT": 1.0, "DEAD/USDT": 2.0}),
                              top_k=2, rebalance_days=10, warmup=10, fee=0.0)
    assert res.forced_exits >= 1


def test_a_dead_coin_does_not_silently_vanish_from_equity():
    """Equity must stay finite and defined after a holding dies."""
    a = _flat(30)
    dead = _flat(30)
    for i in range(14, 30):
        dead[i] = float("nan")
    panel = _panel({"A/USDT": a, "DEAD/USDT": dead})
    res = run_cross_sectional(panel, lambda h: pd.Series({"A/USDT": 1.0, "DEAD/USDT": 2.0}),
                              top_k=2, rebalance_days=10, warmup=10, fee=0.0)
    assert res.equity.notna().all()
    assert (res.equity > 0).all()


# --- turnover --------------------------------------------------------------


def test_turnover_is_zero_when_the_ranking_never_changes():
    """Also pins that building the first book out of cash is NOT counted as
    turnover. It is 100% replacement by construction, so including it would
    make the metric depend on sample length — a 3-rebalance run would floor at
    33% and a 100-rebalance run at 1%, and neither number would be comparable
    to the 68%/week the literature reports."""
    panel = _panel({"A/USDT": _flat(40), "B/USDT": _flat(40)})
    res = run_cross_sectional(panel, lambda h: pd.Series({"A/USDT": 2.0, "B/USDT": 1.0}),
                              top_k=1, rebalance_days=10, warmup=10, fee=0.0)
    assert res.turnover == pytest.approx(0.0, abs=1e-9)


def test_turnover_is_total_when_the_holding_is_replaced_every_time():
    flips = iter([
        pd.Series({"A/USDT": 2.0, "B/USDT": 1.0}),
        pd.Series({"A/USDT": 1.0, "B/USDT": 2.0}),
        pd.Series({"A/USDT": 2.0, "B/USDT": 1.0}),
    ] * 5)
    panel = _panel({"A/USDT": _flat(40), "B/USDT": _flat(40)})
    res = run_cross_sectional(panel, lambda h: next(flips), top_k=1,
                              rebalance_days=10, warmup=10, fee=0.0)
    assert res.turnover > 0.9


# --- the momentum ranker ---------------------------------------------------


def test_momentum_rank_prefers_the_stronger_trailing_return():
    rank = momentum_rank(window=5)
    history = _panel({
        "UP/USDT": [100.0, 101.0, 102.0, 103.0, 104.0, 130.0],
        "DOWN/USDT": [100.0, 99.0, 98.0, 97.0, 96.0, 80.0],
    })
    scores = rank(history)
    assert scores["UP/USDT"] > scores["DOWN/USDT"]


def test_momentum_rank_omits_coins_without_enough_history():
    rank = momentum_rank(window=5)
    history = _panel({"A/USDT": [100.0, 101.0, 102.0, 103.0, 104.0, 130.0]})
    history["NEW/USDT"] = [float("nan")] * 4 + [10.0, 12.0]
    scores = rank(history)
    assert "NEW/USDT" not in scores.dropna().index
