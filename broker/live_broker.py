from broker.base import Order


class LiveBroker:
    """Executes real market orders on a ccxt exchange while keeping a *managed
    ledger* (a virtual budget seeded at `cash`, plus the position the bot itself
    opened). This keeps the bot's accounting independent of any pre-existing
    balances in the account (a testnet account is pre-funded with many coins).

    It exposes the same surface the Trader uses against PaperBroker:
    `set_price`, `fetch_balance` -> {quote, base}, `equity`, `place_order`.
    """

    def __init__(self, exchange, symbol: str, cash: float, base: float = 0.0):
        self.exchange = exchange       # a ccxt exchange instance with markets loaded
        self.symbol = symbol
        self.quote = float(cash)       # managed quote budget (e.g. USDT)
        self.base = float(base)        # bot-managed base position (e.g. BTC)
        self._price = None

    def set_price(self, price: float) -> None:
        self._price = price

    def fetch_balance(self) -> dict:
        return {"quote": self.quote, "base": self.base}

    def equity(self, price: float) -> float:
        return self.quote + self.base * price

    def _min_notional(self) -> float:
        limits = (self.exchange.market(self.symbol).get("limits", {}) or {})
        cost_min = (limits.get("cost", {}) or {}).get("min")
        return float(cost_min) if cost_min else 0.0

    def place_order(self, order: Order) -> dict:
        price = order.price if order.price is not None else self._price
        if price is None:
            raise ValueError("no reference price set (call set_price first)")
        amount = float(self.exchange.amount_to_precision(self.symbol, order.qty))
        if amount <= 0:
            raise ValueError("amount rounds to zero (below lot size)")
        min_notional = self._min_notional()
        if min_notional and amount * price < min_notional:
            raise ValueError(
                f"order notional {amount * price:.2f} below exchange minimum {min_notional:.2f}"
            )

        result = self.exchange.create_order(self.symbol, "market", order.side, amount)

        filled = float(result.get("filled") or amount)
        avg = float(result.get("average") or price)
        fee = result.get("fee") or {}
        fee_cost = float(fee.get("cost") or 0.0)

        if order.side == "buy":
            self.quote -= filled * avg + fee_cost
            self.base += filled
        else:
            self.quote += filled * avg - fee_cost
            self.base -= filled
        return result
