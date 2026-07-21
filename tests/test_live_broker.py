import math

import pytest

from broker.base import Order
from broker.live_broker import LiveBroker


class FakeExchange:
    """Mimics the ccxt methods LiveBroker uses."""

    def __init__(self, avg=100.0, min_cost=10.0):
        self.avg = avg
        self.min_cost = min_cost
        self.orders = []

    def market(self, symbol):
        return {"limits": {"cost": {"min": self.min_cost}}}

    def amount_to_precision(self, symbol, amount):
        # ccxt truncates amounts to the lot step (never rounds up past balance)
        return f"{math.floor(float(amount) * 1e5) / 1e5:.5f}"  # 5-decimal lot

    def create_order(self, symbol, type_, side, amount):
        self.orders.append((symbol, type_, side, amount))
        return {"id": "1", "filled": amount, "average": self.avg, "fee": {"cost": 0.0}, "status": "closed"}


def test_buy_updates_managed_ledger():
    ex = FakeExchange(avg=100.0)
    b = LiveBroker(ex, "BTC/USDT", cash=1000.0)
    b.set_price(100.0)
    b.place_order(Order("BTC/USDT", "buy", 2))
    assert b.fetch_balance() == {"quote": 800.0, "base": 2.0}
    assert ex.orders[0] == ("BTC/USDT", "market", "buy", 2.0)


def test_sell_updates_managed_ledger():
    ex = FakeExchange(avg=120.0)
    b = LiveBroker(ex, "BTC/USDT", cash=800.0, base=2.0)
    b.set_price(120.0)
    b.place_order(Order("BTC/USDT", "sell", 2))
    bal = b.fetch_balance()
    assert bal["base"] == 0.0
    assert bal["quote"] == pytest.approx(1040.0)


def test_below_min_notional_raises():
    ex = FakeExchange(min_cost=10.0)
    b = LiveBroker(ex, "BTC/USDT", cash=1000.0)
    b.set_price(100.0)
    with pytest.raises(ValueError):
        b.place_order(Order("BTC/USDT", "buy", 0.05))  # notional 5 < 10


def test_amount_is_rounded_to_precision():
    ex = FakeExchange()
    b = LiveBroker(ex, "BTC/USDT", cash=1000.0)
    b.set_price(100.0)
    b.place_order(Order("BTC/USDT", "buy", 0.123456))  # -> 0.12345
    assert ex.orders[0][3] == 0.12345


def test_equity_uses_managed_ledger():
    ex = FakeExchange()
    b = LiveBroker(ex, "BTC/USDT", cash=500.0, base=5.0)
    assert b.equity(120.0) == pytest.approx(1100.0)
