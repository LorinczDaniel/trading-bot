import json
import os

import pandas as pd

from broker.paper_broker import PaperBroker
from risk.manager import RiskConfig, RiskManager, RiskState
from monitoring.notifier import Notifier
from strategies.base import Strategy, Signal
from trader import Trader
from live_runner import fetch_closed_candles, act_and_save, run_forever


class HoldStrategy(Strategy):
    def generate(self, df):
        return Signal("HOLD")


class FakeCb:
    def __init__(self, rows):
        self.rows = rows

    def fetch_ohlcv(self, symbol, timeframe="1h", limit=500):
        return self.rows


def _rows(n):
    base = 1609459200000
    return [[base + i * 3600000, 100 + i, 100 + i, 100 + i, float(100 + i), 1.0] for i in range(n)]


def _trader():
    broker = PaperBroker(cash=1000.0, fee=0.0)
    trader = Trader(
        "BTC/USDT", broker, HoldStrategy(), RiskManager(RiskConfig()),
        RiskState(1000.0), Notifier(echo=False),
    )
    return trader, broker


def test_fetch_closed_drops_forming_candle():
    df = fetch_closed_candles(FakeCb(_rows(5)), "BTC/USDT", "1h", warmup=0)
    assert len(df) == 4  # the last (forming) bar is dropped


def test_act_and_save_persists_state(tmp_path):
    trader, broker = _trader()
    path = str(tmp_path / "s.json")
    act_and_save(trader, broker, pd.DataFrame({"close": [100.0, 101.0, 102.0]}), path)
    st = json.load(open(path))
    assert set(st) >= {"quote", "base", "entry_price", "stop_price", "realized_pnl", "peak"}


def test_run_forever_heartbeats_and_evaluates_new_candle_once(tmp_path):
    trader, broker = _trader()
    cb = FakeCb(_rows(6))  # constant data -> a single distinct latest candle
    calls = {"n": 0}

    def fake_sleep(_seconds):
        calls["n"] += 1
        if calls["n"] >= 3:
            raise KeyboardInterrupt

    try:
        run_forever(cb, broker, trader, "BTC/USDT", "1h", 0, str(tmp_path / "s.json"),
                    poll=0, sleep=fake_sleep)
    except KeyboardInterrupt:
        pass

    beats = [m for m in trader.notifier.messages if "price" in m]
    assert len(beats) == 3               # one heartbeat per poll
    assert sum("evaluated" in m for m in beats) == 1  # candle evaluated only once
    assert calls["n"] == 3
