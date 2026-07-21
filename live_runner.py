import time

from data.provider import _to_dataframe
from livestate import save_state


def fetch_candles(cb, symbol, timeframe, warmup):
    """Return (closed_df, live_price).

    closed_df drops the last (still-forming) bar, so the bot only ever *decides*
    on CLOSED candles. live_price is that forming bar's current close — the live
    market price — used only for display/equity, at no extra API cost.
    """
    raw = cb.fetch_ohlcv(symbol, timeframe=timeframe, limit=max(warmup + 5, 250))
    full = _to_dataframe(raw)
    return full.iloc[:-1], float(full["close"].iloc[-1])


def fetch_closed_candles(cb, symbol, timeframe, warmup):
    """Just the closed candles (used by the single-cycle path)."""
    return fetch_candles(cb, symbol, timeframe, warmup)[0]


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
            df, live_price = fetch_candles(cb, symbol, timeframe, warmup)
            ts = df.index[-1]
            note = ""
            if ts != last_ts:
                last_ts = ts
                bal = act_and_save(trader, live, df, state_path)
                note = "  [new candle -> evaluated]"
            else:
                bal = live.fetch_balance()
            trader.notifier.info(
                f"live price {live_price:,.2f} | equity {live.equity(live_price):,.2f} | "
                f"pos {bal['base']:.6f} | realized {trader.state.realized_pnl:+,.2f}{note}"
            )
        except KeyboardInterrupt:
            raise
        except Exception as exc:  # keep the bot alive through transient errors
            trader.notifier.warn(f"cycle error: {exc}")
        sleep(poll)
