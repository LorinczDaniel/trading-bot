import pytest

from broker.base import Order
from broker.paper_broker import PaperBroker


def test_buy_then_sell_updates_balances():
    b = PaperBroker(cash=1000.0, fee=0.0)
    b.set_price(100.0)
    b.place_order(Order("BTC/USDT", "buy", 2))
    assert b.fetch_balance() == {"quote": 800.0, "base": 2.0}
    b.set_price(120.0)
    b.place_order(Order("BTC/USDT", "sell", 2))
    bal = b.fetch_balance()
    assert bal["quote"] == 1040.0
    assert bal["base"] == 0.0


def test_fee_is_applied_on_buy():
    b = PaperBroker(cash=1000.0, fee=0.01)
    b.set_price(100.0)
    b.place_order(Order("BTC/USDT", "buy", 1))
    assert b.fetch_balance()["quote"] == pytest.approx(899.0)  # 100 * 1.01


def test_insufficient_cash_raises():
    b = PaperBroker(cash=50.0, fee=0.0)
    b.set_price(100.0)
    with pytest.raises(ValueError):
        b.place_order(Order("BTC/USDT", "buy", 1))


def test_equity_marks_to_market():
    b = PaperBroker(cash=1000.0, fee=0.0)
    b.set_price(100.0)
    b.place_order(Order("BTC/USDT", "buy", 5))  # spend 500, hold 5 units
    assert b.equity(120.0) == pytest.approx(1100.0)  # 500 cash + 5 * 120
