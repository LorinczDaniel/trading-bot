"""Early read on whatever microstructure data has landed.

Significance threshold established BEFORE seeing data, from the synthetic
validation: an IC must clear roughly +/-0.053 to mean anything.
"""
import glob
import os

import numpy as np
import pandas as pd

from data.provider import MarketDataProvider

THRESH = 0.053
prov = MarketDataProvider(exchange=None)

for path in sorted(glob.glob("cache/microstructure/*.parquet")):
    name = os.path.basename(path)[:-8]
    sym, kind = name.rsplit("_", 1)
    micro = pd.read_parquet(path)
    base = sym.replace("USDT", "")
    try:
        px = prov.load_cached(f"{base}/USDT", "1d")["close"].dropna()
    except FileNotFoundError:
        print(f"{name}: no price data")
        continue
    idx = micro.index.intersection(px.index)
    if len(idx) < 100:
        print(f"{name}: only {len(idx)} overlapping days")
        continue
    micro, px = micro.loc[idx], px.loc[idx]
    print(f"\n=== {sym} {kind} — {len(idx)} days, "
          f"{idx[0].date()} -> {idx[-1].date()} ===")
    print(f"  {'signal':<22}{'IC 1d':>9}{'IC 5d':>9}   verdict")
    for col in micro.columns:
        sig = micro[col]
        if col == "open_interest":
            sig = sig.pct_change(5)          # level is non-stationary; use change
            label = "open_interest %chg5"
        elif col == "open_interest_usd":
            continue
        else:
            label = col
        ics = []
        for h in (1, 5):
            fwd = px.shift(-h) / px - 1.0
            ics.append(sig.corr(fwd, method="spearman"))
        flag = "SIGNAL" if any(abs(i) > THRESH for i in ics if pd.notna(i)) else "noise"
        print(f"  {label:<22}{ics[0]:>+9.3f}{ics[1]:>+9.3f}   {flag}")
