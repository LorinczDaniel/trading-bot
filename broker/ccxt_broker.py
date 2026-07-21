import ccxt

from broker.base import Broker, Order


class CcxtBroker(Broker):
    def __init__(self, exchange_id: str, api_key: str = "", api_secret: str = "", testnet: bool = True):
        exchange_class = getattr(ccxt, exchange_id)
        self.exchange = exchange_class(
            {
                "apiKey": api_key,
                "secret": api_secret,
                "enableRateLimit": True,
                # WSL clocks drift; let ccxt sync timestamps to the server to
                # avoid Binance -1021 "timestamp ahead of server time" errors.
                "options": {"adjustForTimeDifference": True},
            }
        )
        if testnet:
            self.exchange.set_sandbox_mode(True)

    def fetch_ohlcv(self, symbol, timeframe="1h", limit=500):
        return self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    def fetch_balance(self) -> dict:
        return self.exchange.fetch_balance()

    def place_order(self, order: Order) -> dict:
        params = {}
        if order.client_id:
            params["clientOrderId"] = order.client_id
        return self.exchange.create_order(
            symbol=order.symbol,
            type=order.type,
            side=order.side,
            amount=order.qty,
            price=order.price,
            params=params,
        )

    def cancel_order(self, order_id: str, symbol: str) -> dict:
        return self.exchange.cancel_order(order_id, symbol)

    def fetch_open_orders(self, symbol=None) -> list:
        return self.exchange.fetch_open_orders(symbol)
