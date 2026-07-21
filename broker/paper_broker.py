from broker.base import Broker, Order


class PaperBroker(Broker):
    """A simulated single-symbol exchange for paper trading. It is the source of
    truth for balances (quote cash + base holdings) and fills market orders at
    the price last set via `set_price`, applying a fee. No network, no keys.
    """

    def __init__(self, cash: float = 10_000.0, fee: float = 0.001):
        self.quote = cash    # quote currency (e.g. USDT)
        self.base = 0.0      # base asset (e.g. BTC)
        self.fee = fee
        self._price = None

    def set_price(self, price: float) -> None:
        self._price = price

    def place_order(self, order: Order) -> dict:
        price = order.price if order.price is not None else self._price
        if price is None:
            raise ValueError("no fill price set (call set_price first)")
        if order.side == "buy":
            cost = order.qty * price * (1 + self.fee)
            if cost > self.quote + 1e-9:
                raise ValueError("insufficient cash for buy")
            self.quote -= cost
            self.base += order.qty
        elif order.side == "sell":
            if order.qty > self.base + 1e-9:
                raise ValueError("insufficient position for sell")
            self.quote += order.qty * price * (1 - self.fee)
            self.base -= order.qty
        else:
            raise ValueError(f"unknown side: {order.side}")
        return {
            "id": "paper",
            "symbol": order.symbol,
            "side": order.side,
            "amount": order.qty,
            "price": price,
            "status": "closed",
        }

    def equity(self, price: float) -> float:
        return self.quote + self.base * price

    def fetch_balance(self) -> dict:
        return {"quote": self.quote, "base": self.base}

    def fetch_ohlcv(self, symbol, timeframe="1h", limit=500):
        raise NotImplementedError("PaperBroker has no market data; use MarketDataProvider")

    def cancel_order(self, order_id: str, symbol: str) -> dict:
        return {"id": order_id, "status": "canceled"}

    def fetch_open_orders(self, symbol=None) -> list:
        return []  # paper orders fill immediately, so nothing is ever open
