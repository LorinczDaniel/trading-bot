import pandas as pd
import pytest

from backtest.simulate import simulate, scan_risk_config, live_risk_config
from strategies.base import Strategy, Signal


class ScriptedStrategy(Strategy):
    """Emits a preset action at specific *index labels*.

    Keyed on the index label rather than len(df) because run_replay passes a
    bounded tail window — positional indices inside the window are not absolute
    bar numbers.
    """

    lookback = 1

    def __init__(self, actions):
        self.actions = actions

    def generate(self, df):
        return Signal(self.actions.get(df.index[-1], "HOLD"))


def test_risk_sized_buy_then_sell():
    # cash 1000, risk 1%, stop 5% -> risk $10 over a $5 stop distance = 2 units.
    # The old all-in engine would have bought 10 units; this is the divergence
    # the whole change exists to remove.
    df = pd.DataFrame({"close": [100.0, 100.0, 100.0, 110.0, 120.0]})
    res = simulate(df, ScriptedStrategy({2: "BUY", 4: "SELL"}),
                   cash=1000.0, fee=0.0, warmup=0)

    assert res.fills[0]["qty"] == pytest.approx(2.0)
    assert res.final_equity == pytest.approx(1040.0)
    assert len(res.trades) == 1
    assert res.trades[0] == pytest.approx({"entry": 100.0, "exit": 120.0, "pnl": 40.0})


def test_equity_curve_covers_every_replayed_bar():
    df = pd.DataFrame({"close": [100.0, 100.0, 100.0, 110.0, 120.0]})
    res = simulate(df, ScriptedStrategy({}), cash=1000.0, fee=0.0, warmup=0)
    assert len(res.equity) == 5
    assert res.equity.iloc[-1] == pytest.approx(1000.0)


def test_no_signals_preserves_cash():
    df = pd.DataFrame({"close": [100.0, 105.0, 110.0]})
    res = simulate(df, ScriptedStrategy({}), cash=500.0, fee=0.0, warmup=0)
    assert res.final_equity == pytest.approx(500.0)
    assert res.trades == []


def test_stop_loss_exits_the_position():
    # buy 2 @ 100 with a stop at 95; bar 3 prints 90 and the stop fires
    df = pd.DataFrame({"close": [100.0, 100.0, 100.0, 90.0]})
    res = simulate(df, ScriptedStrategy({2: "BUY"}), cash=1000.0, fee=0.0, warmup=0)

    assert len(res.trades) == 1
    assert res.trades[0]["pnl"] == pytest.approx(-20.0)
    assert res.fills[-1]["reason"] == "stop-loss hit"
    assert res.final_equity == pytest.approx(980.0)


def test_scan_config_disables_the_kill_switch_but_live_config_halts():
    """The kill-switch is a live-ops control, not a selection criterion.

    A single oversized losing trade puts realized P&L at -10% of starting
    capital. Under live thresholds that latches trading off for the rest of the
    run; under scan thresholds the bot keeps trading and the sample stays usable.
    """
    df = pd.DataFrame({"close": [100.0, 100.0, 100.0, 90.0, 90.0, 100.0]})
    actions = {2: "BUY", 5: "BUY"}

    halting = simulate(df, ScriptedStrategy(actions), cash=1000.0, fee=0.0, warmup=0,
                       risk_config=live_risk_config(risk_per_trade=0.5))
    scanning = simulate(df, ScriptedStrategy(actions), cash=1000.0, fee=0.0, warmup=0,
                        risk_config=scan_risk_config(risk_per_trade=0.5))

    assert len(halting.fills) == 2      # buy + stop-out, then blocked
    assert len(scanning.fills) == 3     # buy + stop-out + the second buy


def test_config_factories_have_the_specified_thresholds():
    scan = scan_risk_config()
    assert scan.max_drawdown == 1.0
    assert scan.max_session_loss == 1.0
    assert scan.risk_per_trade == 0.01      # sizing is unchanged
    assert scan.stop_loss_pct == 0.05       # stops are unchanged

    live = live_risk_config()
    assert live.max_drawdown == 0.20
    assert live.max_session_loss == 0.10
