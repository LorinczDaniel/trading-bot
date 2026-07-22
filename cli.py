import argparse
import os

import ccxt

from config.settings import load_settings
from data.provider import MarketDataProvider
from strategies.factory import build_strategy, walk_forward_grid, STRATEGY_NAMES
from backtest.engine import run_backtest
from backtest.metrics import total_return, max_drawdown, sharpe_ratio, buy_and_hold_return
from backtest.walkforward import walk_forward
from broker.base import Order
from broker.paper_broker import PaperBroker
from broker.ccxt_broker import CcxtBroker
from broker.live_broker import LiveBroker
from risk.manager import RiskConfig, RiskManager, RiskState
from monitoring.notifier import Notifier
from monitoring.telegram_notifier import TelegramNotifier
from trader import Trader
from livestate import load_state, save_state
from reconcile import reconcile_live
from live_runner import fetch_candles, act_and_save, run_forever


def cmd_fetch(args):
    settings = load_settings()
    exchange = getattr(ccxt, settings.exchange_id)({"enableRateLimit": True})
    prov = MarketDataProvider(exchange)
    df = prov.fetch(args.symbol, args.timeframe, args.limit)
    print(f"Fetched {len(df)} candles for {args.symbol} {args.timeframe}; cached.")


def cmd_backtest(args):
    prov = MarketDataProvider(exchange=None)
    df = prov.load_cached(args.symbol, args.timeframe)
    strategy = build_strategy(
        args.strategy,
        fast=args.fast,
        slow=args.slow,
        rsi_period=args.rsi_period,
        rsi_low=args.rsi_low,
        rsi_high=args.rsi_high,
        trend_sma=args.trend_sma,
    )
    res = run_backtest(df, strategy)
    strat_ret = total_return(res.equity)
    hold_ret = buy_and_hold_return(df["close"])
    edge = strat_ret - hold_ret
    print(f"Strategy:      {args.strategy}")
    print(f"Bars:          {len(res.equity)}")
    print(f"Final equity:  {res.final_equity:,.2f}")
    print(f"Total return:  {strat_ret:.2%}")
    print(f"Max drawdown:  {max_drawdown(res.equity):.2%}")
    print(f"Sharpe:        {sharpe_ratio(res.equity):.2f}")
    print(f"Trades:        {len(res.trades)}")
    print(f"Buy & hold:    {hold_ret:.2%}")
    print(f"Edge vs hold:  {edge:+.2%}  ({'BEAT hold' if edge > 0 else 'LOST to hold'})")


def cmd_walkforward(args):
    prov = MarketDataProvider(exchange=None)
    df = prov.load_cached(args.symbol, args.timeframe)
    grid, make_strategy = walk_forward_grid(args.strategy, trend_sma=args.trend_sma)
    results = walk_forward(df, make_strategy, grid, n_splits=args.splits)
    traded = [r for r in results if r["oos_trades"] > 0]
    print(f"Strategy: {args.strategy}")
    for r in results:
        oos = f"{r['oos_return']:+.2%}" if r["oos_trades"] > 0 else "n/a (0 trades)"
        print(
            f"fold {r['fold']}: best params {str(r['best_params']):>16}"
            f"  in-sample {r['in_sample_return']:+.2%} ({r['in_sample_trades']} tr)"
            f"  out-of-sample {oos}"
        )
    print("-" * 72)
    if traded:
        avg_is = sum(r["in_sample_return"] for r in traded) / len(traded)
        avg_oos = sum(r["oos_return"] for r in traded) / len(traded)
        print(f"AVG in-sample:      {avg_is:+.2%}   (over {len(traded)} folds that traded)")
        print(f"AVG out-of-sample:  {avg_oos:+.2%}")
        print(f"Overfitting gap:    {avg_is - avg_oos:+.2%}  (big gap => curve-fit, not real edge)")
    else:
        print("No fold produced any trades — nothing to measure.")
    if len(traded) < len(results):
        print(
            f"WARNING: {len(results) - len(traded)}/{len(results)} folds made 0 trades "
            f"(fold too short for the strategy's lookback).\n"
            f"         Fetch more data, use fewer --splits, or a smaller --trend-sma."
        )


def _build_notifier(settings, alert_level, echo=True):
    """A TelegramNotifier when both token+chat_id are configured, else the plain
    terminal Notifier. Keeps the bot fully functional with no Telegram set up."""
    if settings.telegram_bot_token and settings.telegram_chat_id:
        return TelegramNotifier(
            settings.telegram_bot_token, settings.telegram_chat_id,
            alert_level=alert_level, echo=echo,
        )
    return Notifier(echo=echo)


def _build_strategy_from_args(args):
    return build_strategy(
        args.strategy,
        fast=args.fast,
        slow=args.slow,
        rsi_period=args.rsi_period,
        rsi_low=args.rsi_low,
        rsi_high=args.rsi_high,
        trend_sma=args.trend_sma,
    )


def _live_exchange(settings):
    """Build an authenticated ccxt exchange, refusing anything but testnet."""
    if not settings.use_testnet:
        raise SystemExit(
            "Refusing to run: USE_TESTNET is not true. This bot is testnet-only "
            "(fake money). Real-money trading is a deliberate future step."
        )
    if not settings.exchange_api_key or not settings.exchange_api_secret:
        raise SystemExit("No API keys in .env (EXCHANGE_API_KEY / EXCHANGE_API_SECRET).")
    cb = CcxtBroker(
        settings.exchange_id, settings.exchange_api_key, settings.exchange_api_secret, testnet=True
    )
    cb.exchange.load_markets()
    return cb


def cmd_testnet_order(args):
    """Place ONE small market order on the testnet to prove the pipeline works."""
    cb = _live_exchange(load_settings())
    price = float(cb.exchange.fetch_ticker(args.symbol)["last"])
    live = LiveBroker(cb.exchange, args.symbol, cash=0.0)
    live.set_price(price)
    qty = args.usdt / price
    print(f"Placing TESTNET {args.side.upper()} ~{args.usdt:.2f} USDT of {args.symbol} "
          f"(~{qty:.6f} @ {price:,.2f})...")
    result = live.place_order(Order(args.symbol, args.side, qty))
    print(f"  -> filled {result.get('filled')} @ {result.get('average')}  "
          f"id={result.get('id')}  status={result.get('status')}")


def cmd_run_live(args):
    settings = load_settings()
    cb = _live_exchange(settings)
    symbol, tf = args.symbol, args.timeframe
    state_path = os.path.join("state", f"live_{symbol.replace('/', '-')}_{tf}.json")
    default = {
        "quote": args.cash, "base": 0.0, "entry_price": 0.0,
        "stop_price": 0.0, "realized_pnl": 0.0, "peak": args.cash,
    }
    st = load_state(state_path, default)

    live = LiveBroker(cb.exchange, symbol, cash=st["quote"], base=st["base"])
    config = RiskConfig(
        risk_per_trade=args.risk, stop_loss_pct=args.stop,
        max_drawdown=args.max_dd, max_session_loss=args.max_loss,
    )
    rstate = RiskState(args.cash)
    rstate.peak = st["peak"]
    rstate.realized_pnl = st["realized_pnl"]
    trader = Trader(
        symbol, live, _build_strategy_from_args(args), RiskManager(config),
        rstate, _build_notifier(settings, args.alert_level), fee=args.fee,
    )
    trader.entry_price = st["entry_price"]
    trader.stop_price = st["stop_price"]

    if isinstance(trader.notifier, TelegramNotifier):
        print(f"Telegram alerts: ON (level {args.alert_level})")
    else:
        print("Telegram alerts: off (set TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID in .env to enable)")

    # Compare persisted state against the live exchange before trading a cent.
    reconcile_live(cb.exchange, symbol, st, args.reconcile)

    if args.loop:
        print(f"LIVE TESTNET LOOP — {args.strategy} on {symbol} {tf} | "
              f"polling every {args.poll}s | Ctrl+C to stop")
        print("-" * 72)
        try:
            run_forever(cb, live, trader, symbol, tf, args.warmup, state_path, args.poll)
        except KeyboardInterrupt:
            print("\nStopped by user. State saved.")
        return

    # single cycle: decide on the latest closed candle, then exit
    df, price_now = fetch_candles(cb, symbol, tf, args.warmup)
    print(f"LIVE TESTNET — {args.strategy} on {symbol} {tf}  "
          f"(managed budget {st['quote']:,.2f} quote / {st['base']:.6f} base)")
    print("-" * 72)
    bal = act_and_save(trader, live, df, state_path)
    print("-" * 72)
    print(f"Equity: {live.equity(price_now):,.2f}   position(base): {bal['base']:.6f}   "
          f"realized: {rstate.realized_pnl:+,.2f}")
    print(f"State saved to {state_path}")


def cmd_run(args):
    if args.live:
        return cmd_run_live(args)
    prov = MarketDataProvider(exchange=None)
    df = prov.load_cached(args.symbol, args.timeframe)
    strategy = _build_strategy_from_args(args)
    broker = PaperBroker(cash=args.cash, fee=args.fee)
    config = RiskConfig(
        risk_per_trade=args.risk,
        stop_loss_pct=args.stop,
        max_drawdown=args.max_dd,
        max_session_loss=args.max_loss,
    )
    trader = Trader(
        args.symbol, broker, strategy, RiskManager(config), RiskState(args.cash),
        Notifier(echo=not args.quiet), fee=args.fee,
    )
    print(
        f"PAPER RUN — {args.strategy} on {args.symbol} {args.timeframe}  "
        f"(cash {args.cash:,.0f}, risk {args.risk:.0%}/trade, stop {args.stop:.0%}, "
        f"kill-switch dd {args.max_dd:.0%})"
    )
    print("-" * 72)
    trader.run_replay(df, warmup=args.warmup)
    final_price = float(df["close"].iloc[-1])
    print("-" * 72)
    print(f"Final equity: {broker.equity(final_price):,.2f}  (started {args.cash:,.2f})")
    print(f"Realized PnL: {trader.state.realized_pnl:+,.2f}")
    print(f"Peak equity:  {trader.state.peak:,.2f}")


def _add_strategy_args(parser):
    parser.add_argument("--strategy", choices=STRATEGY_NAMES, default="ma")
    parser.add_argument("--trend-sma", type=int, default=200, help="SMA period for the trend filter")


def _add_param_args(parser):
    parser.add_argument("--fast", type=int, default=20)
    parser.add_argument("--slow", type=int, default=50)
    parser.add_argument("--rsi-period", type=int, default=14)
    parser.add_argument("--rsi-low", type=float, default=30.0)
    parser.add_argument("--rsi-high", type=float, default=70.0)


def build_parser():
    p = argparse.ArgumentParser(prog="trading-bot")
    sub = p.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch", help="fetch & cache candles from the exchange")
    f.add_argument("--symbol", default="BTC/USDT")
    f.add_argument("--timeframe", default="1h")
    f.add_argument("--limit", type=int, default=500)
    f.set_defaults(func=cmd_fetch)

    b = sub.add_parser("backtest", help="backtest a strategy on cached candles")
    b.add_argument("--symbol", default="BTC/USDT")
    b.add_argument("--timeframe", default="1h")
    _add_strategy_args(b)
    _add_param_args(b)
    b.set_defaults(func=cmd_backtest)

    w = sub.add_parser("walkforward", help="walk-forward validation (in-sample vs out-of-sample)")
    w.add_argument("--symbol", default="BTC/USDT")
    w.add_argument("--timeframe", default="1h")
    _add_strategy_args(w)
    w.add_argument("--splits", type=int, default=4)
    w.set_defaults(func=cmd_walkforward)

    r = sub.add_parser("run", help="run the bot in PAPER mode over cached candles (no real orders)")
    r.add_argument("--symbol", default="BTC/USDT")
    r.add_argument("--timeframe", default="1h")
    _add_strategy_args(r)
    _add_param_args(r)
    r.add_argument("--cash", type=float, default=10_000.0)
    r.add_argument("--fee", type=float, default=0.001)
    r.add_argument("--risk", type=float, default=0.01, help="fraction of equity risked per trade")
    r.add_argument("--stop", type=float, default=0.05, help="stop-loss distance below entry")
    r.add_argument("--max-dd", type=float, default=0.20, help="kill-switch: max drawdown")
    r.add_argument("--max-loss", type=float, default=0.10, help="kill-switch: max session realized loss")
    r.add_argument("--warmup", type=int, default=50)
    r.add_argument("--quiet", action="store_true", help="suppress per-trade log lines")
    r.add_argument("--live", action="store_true",
                   help="place REAL orders on the exchange TESTNET (fake money) instead of paper replay")
    r.add_argument("--loop", action="store_true",
                   help="with --live: run continuously, checking each candle, until Ctrl+C")
    r.add_argument("--poll", type=int, default=60, help="seconds between checks in --loop mode")
    r.add_argument("--alert-level", type=int, choices=[1, 2, 3], default=1,
                   help="Telegram verbosity (live only, needs TELEGRAM_* in .env): "
                        "1=trades+problems, 2=+hourly heartbeat, 3=+every heartbeat")
    r.add_argument("--reconcile", choices=["halt", "warn", "off"], default="halt",
                   help="live only: on startup, compare saved state vs the exchange. "
                        "halt=refuse to start on drift (default), warn=log & continue, off=skip")
    r.set_defaults(func=cmd_run)

    t = sub.add_parser("testnet-order", help="place ONE market order on the testnet (connectivity smoke test)")
    t.add_argument("--symbol", default="BTC/USDT")
    t.add_argument("--side", choices=["buy", "sell"], default="buy")
    t.add_argument("--usdt", type=float, default=20.0, help="approx notional in quote currency")
    t.set_defaults(func=cmd_testnet_order)

    return p


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
