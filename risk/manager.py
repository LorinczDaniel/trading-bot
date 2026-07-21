from dataclasses import dataclass


@dataclass
class RiskConfig:
    risk_per_trade: float = 0.01     # fraction of equity risked per trade
    stop_loss_pct: float = 0.05      # stop distance below entry (also used for sizing)
    max_drawdown: float = 0.20       # halt if equity falls this far below its peak
    max_session_loss: float = 0.10   # halt if realized loss reaches this fraction of start
    max_positions: int = 1           # max concurrent open positions


class RiskState:
    """Accumulates the session facts the kill-switch reads."""

    def __init__(self, starting_equity: float):
        self.starting_equity = starting_equity
        self.peak = starting_equity
        self.realized_pnl = 0.0

    def update_peak(self, equity: float) -> None:
        self.peak = max(self.peak, equity)

    def record_realized(self, pnl: float) -> None:
        self.realized_pnl += pnl


def position_size(equity: float, entry: float, stop: float, risk_per_trade: float) -> float:
    """Size a position so that being stopped out loses exactly `risk_per_trade` of equity."""
    per_unit_risk = abs(entry - stop)
    if per_unit_risk == 0:
        return 0.0
    return (equity * risk_per_trade) / per_unit_risk


class RiskManager:
    def __init__(self, config: RiskConfig):
        self.config = config

    def approve(
        self,
        *,
        equity: float,
        peak: float,
        realized_pnl: float,
        starting_equity: float,
        open_positions: int,
    ) -> tuple[bool, str]:
        """Gate a proposed new position against the portfolio guardrails."""
        drawdown = max(0.0, 1.0 - equity / peak) if peak > 0 else 0.0
        if drawdown >= self.config.max_drawdown:
            return False, f"KILL-SWITCH: drawdown {drawdown:.1%} >= max {self.config.max_drawdown:.0%}"

        session_loss = (-realized_pnl / starting_equity) if realized_pnl < 0 else 0.0
        if session_loss >= self.config.max_session_loss:
            return False, f"session loss {session_loss:.1%} >= max {self.config.max_session_loss:.0%}"

        if open_positions >= self.config.max_positions:
            return False, f"max positions ({self.config.max_positions}) reached"

        return True, "ok"
