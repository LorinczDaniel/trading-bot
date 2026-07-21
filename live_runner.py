import time

from data.provider import _to_dataframe
from livestate import save_state


def fetch_closed_candles(cb, symbol, timeframe, warmup):
    """Fetch candles and drop the last (still-forming) one, so the bot only
    ever decides on CLOSED bars."""
    raw = cb.fetch_ohlcv(symbol, timeframe=timeframe, limit=max(warmup + 5, 250))
    return _to_dataframe(raw).iloc[:-1]


def act_and_save(trader, live, df, state_path):
    """Run one trader decision on `df` and persist the resulting state."""
    trader.step(df)
    bal = live.fetch_balance()
    save_state(state_path, {
        "quote": bal["quote"],
        "base": bal["base"],
        "entry_price": trader.entry_price,
        "stop_price": trader.stop_price,
        "realized_pnl": trader.state.realized_pnl,
        "peak": trader.state.peak,
    })
    return bal


def run_forever(cb, live, trader, symbol, timeframe, warmup, state_path, poll, sleep=time.sleep):
    """Poll forever: every `poll` seconds, refresh candles, evaluate the strategy
    when a NEW candle has closed, and emit a heartbeat so you can see it's alive.

    Network errors in a cycle are logged and skipped (the bot keeps running).
    `sleep` is injectable so the loop can be unit-tested. Stops on KeyboardInterrupt.
    """
    last_ts = None
    while True:
        try:
            df = fetch_closed_candles(cb, symbol, timeframe, warmup)
            ts = df.index[-1]
            price = float(df["close"].iloc[-1])
            note = ""
            if ts != last_ts:
                last_ts = ts
                bal = act_and_save(trader, live, df, state_path)
                note = "  [new candle -> evaluated]"
            else:
                bal = live.fetch_balance()
            trader.notifier.info(
                f"price {price:,.2f} | equity {live.equity(price):,.2f} | "
                f"pos {bal['base']:.6f} | realized {trader.state.realized_pnl:+,.2f}{note}"
            )
        except KeyboardInterrupt:
            raise
        except Exception as exc:  # keep the bot alive through transient errors
            trader.notifier.warn(f"cycle error: {exc}")
        sleep(poll)
