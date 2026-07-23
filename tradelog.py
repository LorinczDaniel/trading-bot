"""Append-only trade ledger. The Trader records one row per fill so a run's
performance can be reviewed afterwards (see report.py / `cli.py report`)."""

import csv
import os

FIELDS = ["timestamp", "side", "symbol", "qty", "price", "fee",
          "reason", "realized_pnl", "equity_after"]


class TradeLog:
    """No-op sink — the Trader's default, so logging is opt-in and tests stay
    clean. Subclasses persist real records."""

    def record(self, trade: dict) -> None:
        pass

    def record_start(self, equity: float, timestamp="") -> None:
        pass


class CsvTradeLog(TradeLog):
    """Append one CSV row per fill, writing the header when the file is new."""

    def __init__(self, path: str, fields=FIELDS):
        self.path = path
        self.fields = list(fields)
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)

    def record(self, trade: dict) -> None:
        is_new = (not os.path.exists(self.path)) or os.path.getsize(self.path) == 0
        with open(self.path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.fields, extrasaction="ignore")
            if is_new:
                writer.writeheader()
            writer.writerow({k: trade.get(k, "") for k in self.fields})

    def record_start(self, equity: float, timestamp="") -> None:
        """Write a baseline 'start' row capturing true starting capital — only
        if the ledger is new/empty. Lets the report compute honest net P&L
        (equity_end - start) instead of summing buy-fee-blind per-trade pnl."""
        if os.path.exists(self.path) and os.path.getsize(self.path) > 0:
            return
        self.record({"timestamp": timestamp, "side": "start", "equity_after": equity})


class MemoryTradeLog(TradeLog):
    """In-memory sink for simulation. Backtests need trade counts and fee totals
    but must not touch the ledger directory — a scan runs thousands of sims."""

    def __init__(self):
        self.rows: list[dict] = []

    def record(self, trade: dict) -> None:
        self.rows.append(dict(trade))

    def record_start(self, equity: float, timestamp="") -> None:
        """Same baseline-'start'-row rationale as `CsvTradeLog.record_start`,
        just gated on an empty in-memory list instead of an empty file."""
        if self.rows:
            return
        self.record({"timestamp": timestamp, "side": "start", "equity_after": equity})
