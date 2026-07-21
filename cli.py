import argparse

import ccxt

from config.settings import load_settings
from data.provider import MarketDataProvider
from strategies.factory import build_strategy, walk_forward_grid, STRATEGY_NAMES
from backtest.engine import run_backtest
from backtest.metrics import total_return, max_drawdown, sharpe_ratio, buy_and_hold_return
from backtest.walkforward import walk_forward


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


def _add_strategy_args(parser):
    parser.add_argument("--strategy", choices=STRATEGY_NAMES, default="ma")
    parser.add_argument("--trend-sma", type=int, default=200, help="SMA period for the trend filter")


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
    b.add_argument("--fast", type=int, default=20)
    b.add_argument("--slow", type=int, default=50)
    b.add_argument("--rsi-period", type=int, default=14)
    b.add_argument("--rsi-low", type=float, default=30.0)
    b.add_argument("--rsi-high", type=float, default=70.0)
    b.set_defaults(func=cmd_backtest)

    w = sub.add_parser("walkforward", help="walk-forward validation (in-sample vs out-of-sample)")
    w.add_argument("--symbol", default="BTC/USDT")
    w.add_argument("--timeframe", default="1h")
    _add_strategy_args(w)
    w.add_argument("--splits", type=int, default=4)
    w.set_defaults(func=cmd_walkforward)

    return p


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
