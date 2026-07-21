import pandas as pd

from data.provider import MarketDataProvider
from strategies.ma_crossover import MACrossover
from backtest.engine import run_backtest
from backtest.metrics import total_return, max_drawdown


class FakeExchange:
    def fetch_ohlcv(self, symbol, timeframe="1h", limit=500):
        # Deterministic V-shape: down then up, 60 bars so warmup(50) is satisfied.
        prices = [100 - i for i in range(30)] + [70 + i for i in range(30)]
        base_ts = 1609459200000
        return [[base_ts + i * 3600000, p, p, p, float(p), 1.0] for i, p in enumerate(prices)]


def test_fetch_then_backtest_end_to_end(tmp_path):
    prov = MarketDataProvider(FakeExchange(), cache_dir=str(tmp_path))
    prov.fetch("BTC/USDT", "1h", limit=60)
    df = prov.load_cached("BTC/USDT", "1h")

    res = run_backtest(df, MACrossover(fast=5, slow=10), initial_cash=1000.0, fee=0.001, warmup=10)

    assert isinstance(res.equity, pd.Series)
    assert len(res.equity) == 60
    assert res.final_equity > 0
    # metrics compute without error
    assert isinstance(total_return(res.equity), float)
    assert max_drawdown(res.equity) <= 0.0
