import argparse

import ccxt

from config.settings import load_settings
from data.provider import MarketDataProvider
from strategies.ma_crossover import MACrossover
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
    res = run_backtest(df, MACrossover(fast=args.fast, slow=args.slow))
    strat_ret = total_return(res.equity)
    hold_ret = buy_and_hold_return(df["close"])
    edge = strat_ret - hold_ret
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
    grid = [(f, s) for f in (5, 10, 20) for s in (30, 50, 100) if f < s]
    results = walk_forward(df, lambda p: MACrossover(*p), grid, n_splits=args.splits)
    avg_is = sum(r["in_sample_return"] for r in results) / len(results)
    avg_oos = sum(r["oos_return"] for r in results) / len(results)
    for r in results:
        print(
            f"fold {r['fold']}: best params {str(r['best_params']):>10}"
            f"  in-sample {r['in_sample_return']:+.2%}  out-of-sample {r['oos_return']:+.2%}"
        )
    print("-" * 60)
    print(f"AVG in-sample:      {avg_is:+.2%}")
    print(f"AVG out-of-sample:  {avg_oos:+.2%}")
    print(f"Overfitting gap:    {avg_is - avg_oos:+.2%}  (big gap => curve-fit, not real edge)")


def build_parser():
    p = argparse.ArgumentParser(prog="trading-bot")
    sub = p.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch", help="fetch & cache candles from the exchange")
    f.add_argument("--symbol", default="BTC/USDT")
    f.add_argument("--timeframe", default="1h")
    f.add_argument("--limit", type=int, default=500)
    f.set_defaults(func=cmd_fetch)

    b = sub.add_parser("backtest", help="run MA-crossover backtest on cached candles")
    b.add_argument("--symbol", default="BTC/USDT")
    b.add_argument("--timeframe", default="1h")
    b.add_argument("--fast", type=int, default=20)
    b.add_argument("--slow", type=int, default=50)
    b.set_defaults(func=cmd_backtest)

    w = sub.add_parser("walkforward", help="walk-forward validation (in-sample vs out-of-sample)")
    w.add_argument("--symbol", default="BTC/USDT")
    w.add_argument("--timeframe", default="1h")
    w.add_argument("--splits", type=int, default=4)
    w.set_defaults(func=cmd_walkforward)

    return p


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
