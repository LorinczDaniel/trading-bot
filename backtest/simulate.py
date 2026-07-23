"""The single simulation path.

Backtest, walk-forward, paper replay, and live trading all run the same rules
through `Trader.step`. This module wires a Trader to a PaperBroker over
historical candles; it deliberately does NOT reimplement sizing, stops, or
fills, because a second implementation is exactly how the old
backtest-vs-live divergence appeared.
"""

from dataclasses import dataclass

import pandas as pd

from broker.paper_broker import PaperBroker
from monitoring.notifier import Notifier
from risk.manager import RiskConfig, RiskManager, RiskState
from tradelog import MemoryTradeLog
from trader import Trader


def scan_risk_config(risk_per_trade: float = 0.01,
                     stop_loss_pct: float = 0.05) -> RiskConfig:
    """Risk config for measurement: sizing and stops intact, kill-switch off.

    RiskState.realized_pnl accumulates for a whole run and never resets, so the
    session-loss halt latches permanently once crossed. Over a multi-year sample
    any config that trades enough to be worth judging will cross it and then
    stop trading — which would make the kill-switch a near-universal reject
    rather than a measure of config quality. It belongs on the live bot.
    """
    return RiskConfig(
        risk_per_trade=risk_per_trade,
        stop_loss_pct=stop_loss_pct,
        max_drawdown=1.0,
        max_session_loss=1.0,
    )


def live_risk_config(risk_per_trade: float = 0.01,
                     stop_loss_pct: float = 0.05) -> RiskConfig:
    """Production thresholds — what the live bot actually runs with."""
    return RiskConfig(
        risk_per_trade=risk_per_trade,
        stop_loss_pct=stop_loss_pct,
        max_drawdown=0.20,
        max_session_loss=0.10,
    )


@dataclass
class BacktestResult:
    equity: pd.Series      # per-bar equity, indexed by candle timestamp
    trades: list           # round-trips: {"entry", "exit", "pnl"}
    final_equity: float
    fills: list            # raw ledger rows, one per buy/sell


def _round_trips(fills: list) -> list:
    """Pair each buy with the sell that closed it."""
    trades, entry = [], None
    for fill in fills:
        if fill["side"] == "buy":
            entry = fill
        elif fill["side"] == "sell" and entry is not None:
            trades.append({
                "entry": float(entry["price"]),
                "exit": float(fill["price"]),
                "pnl": float(fill["realized_pnl"]),
            })
            entry = None
    return trades


def simulate(df: pd.DataFrame, strategy, risk_config: RiskConfig | None = None,
             cash: float = 10_000.0, fee: float = 0.001,
             warmup: int = 50) -> BacktestResult:
    """Replay `strategy` over `df` through the real Trader and return the result."""
    config = risk_config if risk_config is not None else scan_risk_config()
    broker = PaperBroker(cash=cash, fee=fee)
    log = MemoryTradeLog()
    trader = Trader(
        "SIM", broker, strategy, RiskManager(config), RiskState(cash),
        Notifier(echo=False), fee=fee, tradelog=log,
    )
    equity = trader.run_replay(df, warmup=warmup)
    fills = [row for row in log.rows if row.get("side") in ("buy", "sell")]
    final = float(equity.iloc[-1]) if len(equity) else float(cash)
    return BacktestResult(
        equity=equity, trades=_round_trips(fills), final_equity=final, fills=fills,
    )
