import argparse
import os

import ccxt
import pandas as pd

from config.settings import load_settings
from data.provider import MarketDataProvider
from strategies.factory import build_strategy, walk_forward_grid, STRATEGY_NAMES
from backtest.simulate import simulate, scan_risk_config, live_risk_config
from backtest.metrics import total_return, max_drawdown, sharpe_ratio, buy_and_hold_return
from backtest.walkforward import walk_forward
from backtest.scan import scan_one, rank, format_table
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
from tradelog import CsvTradeLog
from report import summarize, equity_curve
from live_runner import fetch_candles, act_and_save, run_forever


def cmd_fetch(args):
    settings = load_settings()
    # Public mainnet client on purpose: testnet OHLCV history is sparse and
    # partly synthetic, and would poison every backtest built on it.
    exchange = getattr(ccxt, settings.exchange_id)({"enableRateLimit": True})
    prov = MarketDataProvider(exchange)
    if args.days:
        df = prov.backfill(args.symbol, args.timeframe, days=args.days)
        if df.empty:
            print(f"No candles returned for {args.symbol} {args.timeframe}.")
            return
        print(f"Backfilled {len(df)} candles for {args.symbol} {args.timeframe} "
              f"({df.index[0]} -> {df.index[-1]}); cached.")
        return
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
    make_config = live_risk_config if args.kill_switch else scan_risk_config
    config = make_config(risk_per_trade=args.risk, stop_loss_pct=args.stop)
    res = simulate(df, strategy, config, cash=args.cash, fee=args.fee, warmup=args.warmup)

    if len(res.equity) == 0:
        raise SystemExit(
            f"--warmup {args.warmup} leaves no bars to replay "
            f"({args.symbol} {args.timeframe} has {len(df)} bars). Use a smaller --warmup."
        )

    strat_ret = total_return(res.equity)
    hold_ret = buy_and_hold_return(df["close"])
    edge = strat_ret - hold_ret
    fees = sum(float(f.get("fee") or 0.0) for f in res.fills)
    print(f"Strategy:      {args.strategy}")
    print(f"Bars:          {len(res.equity)}")
    print(f"Final equity:  {res.final_equity:,.2f}   (started {args.cash:,.2f})")
    print(f"Total return:  {strat_ret:.2%}")
    print(f"Max drawdown:  {max_drawdown(res.equity):.2%}")
    print(f"Sharpe:        {sharpe_ratio(res.equity):.2f}")
    print(f"Round-trips:   {len(res.trades)}   (fills: {len(res.fills)})")
    print(f"Fees paid:     {fees:,.2f}")
    print(f"Buy & hold:    {hold_ret:.2%}")
    print(f"Edge vs hold:  {edge:+.2%}  ({'BEAT hold' if edge > 0 else 'LOST to hold'})")
    print(f"Kill-switch:   {'live thresholds' if args.kill_switch else 'disabled (measurement mode)'}")


def cmd_walkforward(args):
    prov = MarketDataProvider(exchange=None)
    df = prov.load_cached(args.symbol, args.timeframe)
    grid, make_strategy = walk_forward_grid(args.strategy, trend_sma=args.trend_sma)
    results = walk_forward(df, make_strategy, grid, n_splits=args.splits)
    traded = [r for r in results if r["valid"] and r["oos_trades"] > 0]
    print(f"Strategy: {args.strategy}")
    for r in results:
        if not r["valid"]:
            print(f"fold {r['fold']}: no parameter set made enough trades to judge")
            continue
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
            f"or had no valid parameters.\n"
            f"         Fetch more data (fetch --days), use fewer --splits, "
            f"or a smaller --trend-sma."
        )


def cmd_scan(args):
    import time

    prov = MarketDataProvider(exchange=None)
    timeframes = [t.strip() for t in args.timeframes.split(",") if t.strip()]
    strategies = [s.strip() for s in args.strategies.split(",") if s.strip()]

    rows, skipped = [], []
    for tf in timeframes:
        try:
            df = prov.load_cached(args.symbol, tf)
        except FileNotFoundError:
            skipped.append(f"{tf} (no cached data — run: fetch --timeframe {tf} --days N)")
            continue
        for name in strategies:
            started = time.time()
            row = scan_one(df, args.symbol, tf, name, cash=args.cash, fee=args.fee,
                           warmup=args.warmup, risk_per_trade=args.risk,
                           stop_loss_pct=args.stop, splits=args.splits,
                           trend_sma=args.trend_sma)
            rows.append(row)
            print(f"  scanned {name} {tf} in {time.time() - started:.1f}s", flush=True)

    if not rows:
        raise SystemExit("Nothing to scan. " + "; ".join(skipped))

    print()
    print(format_table(rank(rows)))
    print()
    passing = [r for r in rows if r["verdict"] == "PASS"]
    if passing:
        best = max(passing, key=lambda r: r["edge"])
        print(f"{len(passing)}/{len(rows)} configurations passed. "
              f"Best by edge: {best['strategy']} on {best['timeframe']} "
              f"({best['edge']:+.2%} vs buy & hold).")
    else:
        print(f"0/{len(rows)} configurations passed. That is a finding, not a bug: "
              f"no tested configuration is worth soaking. Do not loosen the "
              f"thresholds to manufacture a winner.")
    for note in skipped:
        print(f"SKIPPED {note}")


def _ledger_path(mode, symbol, timeframe):
    return os.path.join("ledger", f"{mode}_{symbol.replace('/', '-')}_{timeframe}.csv")


def cmd_report(args):
    path = _ledger_path(args.mode, args.symbol, args.timeframe)
    if not os.path.exists(path):
        raise SystemExit(f"No {args.mode} ledger at {path} — run the bot in {args.mode} mode first.")
    trades = pd.read_csv(path)
    if trades.empty:
        raise SystemExit(f"Ledger {path} has no trades yet.")
    s = summarize(trades)
    pf = "inf" if s["profit_factor"] == float("inf") else f"{s['profit_factor']:.2f}"
    print(f"REPORT — {args.mode} {args.symbol} {args.timeframe}   ({path})")
    print("-" * 72)
    print(f"Net PnL:       {s['net_pnl']:+,.2f}   (equity {s['equity_start']:,.2f} -> {s['equity_end']:,.2f})")
    print(f"Return:        {s['return_pct']:+.2%}    Max drawdown: {s['max_drawdown']:.2%}   Peak: {s['equity_peak']:,.2f}")
    print(f"Fills:         {s['fills']}  ({s['buys']} buys / {s['round_trips']} round-trips)")
    print(f"Win rate:      {s['win_rate']:.1%}   (avg win {s['avg_win']:+,.2f} / avg loss {s['avg_loss']:+,.2f})")
    print(f"Profit factor: {pf}   (gross, excl. entry fees)")
    print(f"Total fees:    {s['total_fees']:,.2f}")
    print(f"Realized PnL:  {s['realized_pnl']:+,.2f}   (gross of entry fees — Net PnL above is the true figure)")
    eq_path = path.replace(".csv", "_equity.csv")
    equity_curve(trades).to_csv(eq_path, index=False)
    print("-" * 72)
    print(f"Equity curve ({s['fills']} fills) written to {eq_path}")


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
        trailing_stop=not args.no_trailing,
    )
    rstate = RiskState(args.cash)
    rstate.peak = st["peak"]
    rstate.realized_pnl = st["realized_pnl"]
    live_tradelog = CsvTradeLog(_ledger_path("live", symbol, tf))
    live_tradelog.record_start(args.cash)  # baseline on a new ledger; no-op if it already has rows
    trader = Trader(
        symbol, live, _build_strategy_from_args(args), RiskManager(config),
        rstate, _build_notifier(settings, args.alert_level), fee=args.fee,
        tradelog=live_tradelog,
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
        trailing_stop=not args.no_trailing,
    )
    # a paper replay is one self-contained experiment: start its ledger fresh
    ledger_path = _ledger_path("paper", args.symbol, args.timeframe)
    if os.path.exists(ledger_path):
        os.remove(ledger_path)
    tradelog = CsvTradeLog(ledger_path)
    tradelog.record_start(args.cash)  # baseline = true starting capital
    trader = Trader(
        args.symbol, broker, strategy, RiskManager(config), RiskState(args.cash),
        Notifier(echo=not args.quiet), fee=args.fee, tradelog=tradelog,
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
    f.add_argument("--days", type=int, default=None,
                   help="backfill this many days of history (paginated, merges into "
                        "the cache). Suggested depth: 1h=365, 4h=730, 3m=30, 1m=7")
    f.set_defaults(func=cmd_fetch)

    b = sub.add_parser("backtest", help="backtest a strategy on cached candles")
    b.add_argument("--symbol", default="BTC/USDT")
    b.add_argument("--timeframe", default="1h")
    _add_strategy_args(b)
    _add_param_args(b)
    b.add_argument("--cash", type=float, default=10_000.0)
    b.add_argument("--fee", type=float, default=0.001)
    b.add_argument("--risk", type=float, default=0.01, help="fraction of equity risked per trade")
    b.add_argument("--stop", type=float, default=0.05, help="stop-loss distance below entry")
    b.add_argument("--warmup", type=int, default=50)
    b.add_argument("--kill-switch", action="store_true",
                   help="apply the live drawdown/session-loss halts. Off by default: "
                        "they latch permanently over long samples and would truncate "
                        "the measurement rather than describe it.")
    b.set_defaults(func=cmd_backtest)

    w = sub.add_parser("walkforward", help="walk-forward validation (in-sample vs out-of-sample)")
    w.add_argument("--symbol", default="BTC/USDT")
    w.add_argument("--timeframe", default="1h")
    _add_strategy_args(w)
    w.add_argument("--splits", type=int, default=4)
    w.set_defaults(func=cmd_walkforward)

    sc = sub.add_parser("scan", help="rank strategy/timeframe configurations against the gates")
    sc.add_argument("--symbol", default="BTC/USDT")
    sc.add_argument("--timeframes", default="1h,4h",
                    help="comma-separated, e.g. 1h,4h,3m,1m (needs cached data for each)")
    sc.add_argument("--strategies", default=",".join(STRATEGY_NAMES),
                    help="comma-separated subset of " + ",".join(STRATEGY_NAMES))
    sc.add_argument("--trend-sma", type=int, default=200)
    sc.add_argument("--splits", type=int, default=4)
    sc.add_argument("--cash", type=float, default=10_000.0)
    sc.add_argument("--fee", type=float, default=0.001)
    sc.add_argument("--risk", type=float, default=0.01)
    sc.add_argument("--stop", type=float, default=0.05)
    sc.add_argument("--warmup", type=int, default=50)
    sc.set_defaults(func=cmd_scan)

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
    r.add_argument("--no-trailing", action="store_true",
                   help="disable the trailing stop; use a fixed stop at entry (trailing is on by default)")
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

    rep = sub.add_parser("report", help="summarize a run's trade ledger + write an equity-curve CSV")
    rep.add_argument("--symbol", default="BTC/USDT")
    rep.add_argument("--timeframe", default="1h")
    rep.add_argument("--mode", choices=["live", "paper"], default="live",
                     help="which ledger to read: live_* or paper_*")
    rep.set_defaults(func=cmd_report)

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
