"""Binance's free historical market-data archive (data.binance.vision).

Two datasets the REST API cannot give you, which this project wrongly recorded
as untestable:

  bookDepth  — L2 liquidity in +/-1..5% bands around mid, ~3-second snapshots,
               available from 2023. The REST order book is live-only, so this
               was recorded as "no history"; the archive has it.
  metrics    — open interest and long/short positioning ratios at 5-minute
               resolution, available from 2021. The REST endpoint serves only
               ~30 days, so this was recorded as "too short to backtest".

Both are aggregated to one row per day on download. Raw bookDepth is ~450 KB per
symbol-day (28k rows); a multi-year multi-symbol pull would be gigabytes of data
to answer a daily-bar question. The summary keeps what a daily signal can use.
"""

import io
import os
import urllib.request
import zipfile

import pandas as pd

BASE = "https://data.binance.vision/data/futures/um/daily"

#: Depth bands summarised. 1% is the tight book (what actually absorbs a market
#: order); 5% is total visible liquidity.
BOOK_LEVELS = (1, 5)


def summarise_book_depth(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse raw depth snapshots to one row per day.

    Sign convention: **positive imbalance means bid-heavy**, i.e. more resting
    demand than supply. Inverting this would silently flip every downstream
    result, so it is pinned by a test.

    `imbalance_5` uses the whole book out to 5%, not the 5% band alone — the
    outer band by itself is a thin slice, not total depth.
    """
    if df.empty:
        return pd.DataFrame(columns=[f"imbalance_{l}" for l in BOOK_LEVELS]
                            + ["depth_total"])
    d = df.copy()
    d["timestamp"] = pd.to_datetime(d["timestamp"])
    d["day"] = d["timestamp"].dt.floor("D")

    out = {}
    for level in BOOK_LEVELS:
        bids = d[(d["percentage"] < 0) & (d["percentage"] >= -level)]
        asks = d[(d["percentage"] > 0) & (d["percentage"] <= level)]
        b = bids.groupby([bids["day"], bids["timestamp"]])["depth"].sum()
        a = asks.groupby([asks["day"], asks["timestamp"]])["depth"].sum()
        joined = pd.concat({"bid": b, "ask": a}, axis=1).fillna(0.0)
        total = joined["bid"] + joined["ask"]
        imb = ((joined["bid"] - joined["ask"]) / total.replace(0, pd.NA))
        # Average the per-snapshot imbalance, rather than the ratio of daily
        # sums: the latter would let one deep snapshot dominate the day.
        out[f"imbalance_{level}"] = imb.groupby(level=0).mean()

    depth = d.groupby("day")["depth"].sum()
    out["depth_total"] = depth
    res = pd.DataFrame(out)
    res.index.name = None
    return res


def summarise_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse 5-minute positioning metrics to one row per day.

    Open interest is a STOCK, so the day's last reading is kept — averaging it
    blurs the level a next-day signal would actually have observed at the close.
    The ratios are flows and are averaged.

    Binance's schema changed over the years and early files lack some columns,
    so every field is optional.
    """
    if df.empty:
        return pd.DataFrame()
    d = df.copy()
    d["create_time"] = pd.to_datetime(d["create_time"])
    d = d.set_index("create_time").sort_index()
    day = d.index.floor("D")

    out = {}
    if "sum_open_interest" in d:
        out["open_interest"] = d.groupby(day)["sum_open_interest"].last()
    if "sum_open_interest_value" in d:
        out["open_interest_usd"] = d.groupby(day)["sum_open_interest_value"].last()
    for src, dst in [("sum_toptrader_long_short_ratio", "toptrader_ls"),
                     ("count_toptrader_long_short_ratio", "toptrader_count_ls"),
                     ("count_long_short_ratio", "all_accounts_ls"),
                     ("sum_taker_long_short_vol_ratio", "taker_buy_sell")]:
        if src in d:
            out[dst] = d.groupby(day)[src].mean()
    res = pd.DataFrame(out)
    res.index.name = None
    return res


def _fetch_zip_csv(url: str) -> pd.DataFrame | None:
    """Download one daily archive. Returns None when the day is absent."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
    except Exception:
        return None
    try:
        z = zipfile.ZipFile(io.BytesIO(raw))
        with z.open(z.namelist()[0]) as f:
            return pd.read_csv(f)
    except Exception:
        return None


def download(symbol: str, kind: str, dates, cache_dir="cache/microstructure"):
    """Download and summarise `kind` for `symbol` over `dates`, caching per symbol.

    Days already cached are skipped, so an interrupted run resumes cheaply.
    """
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, f"{symbol}_{kind}.parquet")
    existing = pd.read_parquet(path) if os.path.exists(path) else pd.DataFrame()
    have = set(existing.index) if len(existing) else set()

    summarise = summarise_book_depth if kind == "bookDepth" else summarise_metrics
    chunks = []
    for d in dates:
        stamp = d.strftime("%Y-%m-%d")
        if pd.Timestamp(stamp) in have:
            continue
        raw = _fetch_zip_csv(f"{BASE}/{kind}/{symbol}/{symbol}-{kind}-{stamp}.zip")
        if raw is None or raw.empty:
            continue
        s = summarise(raw)
        if not s.empty:
            chunks.append(s)

    if not chunks and len(existing) == 0:
        return pd.DataFrame()
    combined = pd.concat([existing] + chunks) if chunks else existing
    combined = combined[~combined.index.duplicated(keep="last")].sort_index()
    combined.to_parquet(path)
    return combined
