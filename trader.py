import pandas as pd

from broker.base import Order
from risk.manager import RiskManager, RiskState, position_size
from tradelog import TradeLog


class Trader:
    """The live trading loop for a single symbol. Each `step` takes the latest
    candles, asks the strategy for a signal, enforces stop-loss and the risk
    kill-switch, and routes orders through the broker. It works with any Broker
    that exposes `set_price`, `fetch_balance` and `equity` (e.g. PaperBroker).
    """

    def __init__(self, symbol, broker, strategy, risk_manager: RiskManager,
                 risk_state: RiskState, notifier, fee: float = 0.001, tradelog=None):
        self.symbol = symbol
        self.broker = broker
        self.strategy = strategy
        self.risk = risk_manager
        self.state = risk_state
        self.notifier = notifier
        self.fee = fee
        self.tradelog = tradelog or TradeLog()
        self.entry_price = 0.0
        self.stop_price = 0.0

    def step(self, df: pd.DataFrame) -> None:
        price = float(df["close"].iloc[-1])
        ts = df.index[-1]
        self.broker.set_price(price)
        base = self.broker.fetch_balance()["base"]
        equity = self.broker.equity(price)
        self.state.update_peak(equity)

        # 1. stop-loss takes priority over any signal
        if base > 0 and price <= self.stop_price:
            self._sell(price, base, "stop-loss hit", ts)
            return

        signal = self.strategy.generate(df)

        if signal.action == "BUY" and base == 0:
            stop = price * (1 - self.risk.config.stop_loss_pct)
            ok, why = self.risk.approve(
                equity=equity,
                peak=self.state.peak,
                realized_pnl=self.state.realized_pnl,
                starting_equity=self.state.starting_equity,
                open_positions=0,
            )
            if not ok:
                self.notifier.warn(f"blocked BUY: {why}")
                return
            qty = position_size(equity, price, stop, self.risk.config.risk_per_trade)
            affordable = (self.broker.fetch_balance()["quote"] * (1 - self.fee)) / price
            qty = min(qty, affordable)
            if qty <= 0:
                return
            self.broker.place_order(Order(self.symbol, "buy", qty))
            self.entry_price = price
            self.stop_price = stop
            self.tradelog.record({
                "timestamp": ts, "side": "buy", "symbol": self.symbol,
                "qty": qty, "price": price, "fee": qty * price * self.fee,
                "reason": signal.reason, "realized_pnl": "",
                "equity_after": self.broker.equity(price),
            })
            self.notifier.info(
                f"BUY {qty:.6f} {self.symbol} @ {price:.2f} (stop {stop:.2f}) — {signal.reason}"
            )
        elif signal.action == "SELL" and base > 0:
            self._sell(price, base, signal.reason, ts)

    def _sell(self, price: float, qty: float, reason: str, ts) -> None:
        self.broker.place_order(Order(self.symbol, "sell", qty))
        pnl = qty * price * (1 - self.fee) - qty * self.entry_price
        self.state.record_realized(pnl)
        self.tradelog.record({
            "timestamp": ts, "side": "sell", "symbol": self.symbol,
            "qty": qty, "price": price, "fee": qty * price * self.fee,
            "reason": reason, "realized_pnl": pnl,
            "equity_after": self.broker.equity(price),
        })
        self.notifier.info(
            f"SELL {qty:.6f} {self.symbol} @ {price:.2f} (pnl {pnl:+.2f}) — {reason}"
        )
        self.entry_price = 0.0
        self.stop_price = 0.0

    def run_replay(self, df: pd.DataFrame, warmup: int = 50) -> None:
        """Drive the loop bar-by-bar over historical candles (a paper session)."""
        for i in range(warmup, len(df)):
            self.step(df.iloc[: i + 1])
