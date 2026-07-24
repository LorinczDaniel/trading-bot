"""Pull the microstructure archives."""
import sys

import pandas as pd

from data.binance_archive import download

KIND = sys.argv[1]
SYMBOLS = sys.argv[2].split(",")
START = sys.argv[3]

dates = pd.date_range(START, "2026-07-23", freq="D")
for sym in SYMBOLS:
    df = download(sym, KIND, dates)
    if df.empty:
        print(f"  {sym:<14} nothing", flush=True)
    else:
        print(f"  {sym:<14} {len(df):>5} days  {df.index[0].date()} -> "
              f"{df.index[-1].date()}  cols {list(df.columns)}", flush=True)
