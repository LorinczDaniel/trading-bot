import csv

import pandas as pd

from tradelog import TradeLog, CsvTradeLog
from broker.paper_broker import PaperBroker
from risk.manager import RiskConfig, RiskManager, RiskState
from monitoring.notifier import Notifier
from strategies.base import Strategy, Signal
from trader import Trader


class Scripted(Strategy):
    def __init__(self, actions):
        self.actions = actions

    def generate(self, df):
        return Signal(self.actions.get(len(df) - 1, "HOLD"))


def test_noop_tradelog_records_nothing():
    TradeLog().record({"side": "buy"})  # must not raise, must persist nothing


def test_csv_tradelog_writes_header_then_appends(tmp_path):
    path = str(tmp_path / "l.csv")
    log = CsvTradeLog(path)
    log.record({"timestamp": 1, "side": "buy", "symbol": "BTC/USDT", "qty": 0.1,
                "price": 100, "fee": 0.01, "reason": "x", "realized_pnl": "", "equity_after": 990})
    log.record({"timestamp": 2, "side": "sell", "symbol": "BTC/USDT", "qty": 0.1,
                "price": 110, "fee": 0.011, "reason": "y", "realized_pnl": 0.98, "equity_after": 1000})
    rows = list(csv.DictReader(open(path)))
    assert [r["side"] for r in rows] == ["buy", "sell"]
    assert rows[1]["realized_pnl"] == "0.98"          # header written once, both rows present


def test_trader_records_buy_and_sell(tmp_path):
    path = str(tmp_path / "l.csv")
    broker = PaperBroker(cash=1000.0, fee=0.0)
    trader = Trader("BTC/USDT", broker, Scripted({2: "BUY", 4: "SELL"}),
                    RiskManager(RiskConfig(stop_loss_pct=0.05)), RiskState(1000.0),
                    Notifier(echo=False), fee=0.0, tradelog=CsvTradeLog(path))
    df = pd.DataFrame({"close": [100.0, 100.0, 100.0, 110.0, 120.0]})
    trader.run_replay(df, warmup=0)

    rows = list(csv.DictReader(open(path)))
    assert [r["side"] for r in rows] == ["buy", "sell"]
    assert float(rows[1]["realized_pnl"]) > 0          # bought ~100, sold 120
    assert rows[0]["realized_pnl"] == ""               # buys don't realize pnl


def test_default_trader_has_noop_tradelog():
    # a Trader built without a tradelog must not crash when it fills
    broker = PaperBroker(cash=1000.0, fee=0.0)
    trader = Trader("BTC/USDT", broker, Scripted({2: "BUY", 4: "SELL"}),
                    RiskManager(RiskConfig(stop_loss_pct=0.05)), RiskState(1000.0),
                    Notifier(echo=False), fee=0.0)
    trader.run_replay(pd.DataFrame({"close": [100.0, 100.0, 100.0, 110.0, 120.0]}), warmup=0)
    assert broker.fetch_balance()["base"] == 0.0       # ran a full round trip cleanly
