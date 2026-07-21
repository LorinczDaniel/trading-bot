from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Order:
    symbol: str
    side: str            # "buy" | "sell"
    qty: float
    type: str = "market"
    price: float | None = None
    client_id: str | None = None


class Broker(ABC):
    @abstractmethod
    def fetch_ohlcv(self, symbol, timeframe="1h", limit=500): ...

    @abstractmethod
    def fetch_balance(self) -> dict: ...

    @abstractmethod
    def place_order(self, order: Order) -> dict: ...

    @abstractmethod
    def cancel_order(self, order_id: str, symbol: str) -> dict: ...

    @abstractmethod
    def fetch_open_orders(self, symbol=None) -> list: ...
