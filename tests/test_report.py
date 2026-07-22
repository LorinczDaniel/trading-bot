import pandas as pd

from report import summarize, equity_curve


def _ledger():
    # 3 round trips: +30, -10, +20  (2 wins, 1 loss)
    return pd.DataFrame([
        {"timestamp": 1, "side": "buy",  "fee": 1.0, "realized_pnl": "",    "equity_after": 999.0},
        {"timestamp": 2, "side": "sell", "fee": 1.1, "realized_pnl": 30.0,  "equity_after": 1029.0},
        {"timestamp": 3, "side": "buy",  "fee": 1.0, "realized_pnl": "",    "equity_after": 1028.0},
        {"timestamp": 4, "side": "sell", "fee": 1.2, "realized_pnl": -10.0, "equity_after": 1018.0},
        {"timestamp": 5, "side": "buy",  "fee": 1.0, "realized_pnl": "",    "equity_after": 1017.0},
        {"timestamp": 6, "side": "sell", "fee": 1.3, "realized_pnl": 20.0,  "equity_after": 1037.0},
    ])


def test_summarize_core_stats():
    s = summarize(_ledger())
    assert s["fills"] == 6
    assert s["buys"] == 3
    assert s["round_trips"] == 3
    assert round(s["realized_pnl"], 2) == 40.0
    assert round(s["net_pnl"], 2) == 38.0            # equity 999 -> 1037
    assert round(s["win_rate"], 4) == round(2 / 3, 4)
    assert round(s["total_fees"], 2) == 6.6
    assert s["equity_end"] == 1037.0
    assert s["equity_peak"] == 1037.0
    # profit factor = gross win / gross loss = (30 + 20) / 10 = 5
    assert round(s["profit_factor"], 2) == 5.0


def test_baseline_row_gives_true_start_and_net_pnl():
    # 'start' row = real starting capital; net_pnl (from equity, fee-inclusive)
    # is the honest figure and reads LOWER than the buy-fee-blind realized_pnl.
    led = pd.DataFrame([
        {"timestamp": 0, "side": "start", "fee": "", "realized_pnl": "",   "equity_after": 10000.0},
        {"timestamp": 1, "side": "buy",   "fee": 2.0, "realized_pnl": "",   "equity_after": 9998.0},
        {"timestamp": 2, "side": "sell",  "fee": 2.0, "realized_pnl": 30.0, "equity_after": 10026.0},
    ])
    s = summarize(led)
    assert s["fills"] == 2                 # 'start' row excluded from counts
    assert s["round_trips"] == 1
    assert s["equity_start"] == 10000.0    # true capital, not the post-first-buy 9998
    assert round(s["net_pnl"], 2) == 26.0  # honest: 10026 - 10000, entry fee included
    assert round(s["realized_pnl"], 2) == 30.0  # gross of entry fee -> overstates by ~4


def test_profit_factor_infinite_when_no_losses():
    winners_only = pd.DataFrame([
        {"side": "sell", "fee": 1.0, "realized_pnl": 5.0, "equity_after": 1005.0},
        {"side": "sell", "fee": 1.0, "realized_pnl": 7.0, "equity_after": 1012.0},
    ])
    assert summarize(winners_only)["profit_factor"] == float("inf")


def test_summarize_empty_ledger_is_safe():
    empty = pd.DataFrame(columns=["side", "fee", "realized_pnl", "equity_after", "timestamp"])
    s = summarize(empty)
    assert s["round_trips"] == 0
    assert s["realized_pnl"] == 0.0
    assert s["max_drawdown"] == 0.0


def test_equity_curve_one_row_per_trade():
    ec = equity_curve(_ledger())
    assert len(ec) == 6
    assert list(ec["equity_after"]) == [999.0, 1029.0, 1028.0, 1018.0, 1017.0, 1037.0]
    assert list(ec["trade"]) == [1, 2, 3, 4, 5, 6]
