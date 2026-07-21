from broker.base import Order
from broker.ccxt_broker import CcxtBroker


class FakeCcxt:
    def __init__(self):
        self.calls = []

    def create_order(self, **kwargs):
        self.calls.append(("create_order", kwargs))
        return {"id": "1"}

    def fetch_ohlcv(self, symbol, timeframe="1h", limit=500):
        self.calls.append(("fetch_ohlcv", symbol, timeframe, limit))
        return []


def test_order_defaults():
    o = Order(symbol="BTC/USDT", side="buy", qty=0.1)
    assert o.type == "market"
    assert o.price is None
    assert o.client_id is None


def test_place_order_maps_client_id():
    broker = CcxtBroker("binance", testnet=True)  # offline construction
    broker.exchange = FakeCcxt()                   # swap in a recorder
    broker.place_order(Order(symbol="BTC/USDT", side="buy", qty=0.1, client_id="bot-abc"))
    name, kwargs = broker.exchange.calls[0]
    assert name == "create_order"
    assert kwargs["side"] == "buy"
    assert kwargs["amount"] == 0.1
    assert kwargs["params"]["clientOrderId"] == "bot-abc"


def test_fetch_ohlcv_delegates():
    broker = CcxtBroker("binance", testnet=True)
    broker.exchange = FakeCcxt()
    broker.fetch_ohlcv("ETH/USDT", "4h", 10)
    assert broker.exchange.calls[0] == ("fetch_ohlcv", "ETH/USDT", "4h", 10)
