from risk.manager import RiskConfig, RiskState, RiskManager, position_size


def test_position_size():
    # risk 1% of 10_000 = 100; stop 5 away => 100/5 = 20 units
    assert position_size(10_000, entry=100, stop=95, risk_per_trade=0.01) == 20.0


def test_position_size_zero_distance_is_zero():
    assert position_size(10_000, entry=100, stop=100, risk_per_trade=0.01) == 0.0


def test_approve_ok_within_limits():
    rm = RiskManager(RiskConfig())
    ok, _ = rm.approve(
        equity=10_000, peak=10_000, realized_pnl=0.0, starting_equity=10_000, open_positions=0
    )
    assert ok


def test_approve_blocks_on_drawdown():
    rm = RiskManager(RiskConfig(max_drawdown=0.20))
    ok, why = rm.approve(
        equity=7_000, peak=10_000, realized_pnl=0.0, starting_equity=10_000, open_positions=0
    )
    assert not ok and "drawdown" in why.lower()


def test_approve_blocks_on_session_loss():
    rm = RiskManager(RiskConfig(max_session_loss=0.05))
    ok, why = rm.approve(
        equity=9_400, peak=10_000, realized_pnl=-600.0, starting_equity=10_000, open_positions=0
    )
    assert not ok and "session" in why.lower()


def test_approve_blocks_on_max_positions():
    rm = RiskManager(RiskConfig(max_positions=1))
    ok, why = rm.approve(
        equity=10_000, peak=10_000, realized_pnl=0.0, starting_equity=10_000, open_positions=1
    )
    assert not ok and "position" in why.lower()


def test_risk_state_tracks_peak_and_realized():
    s = RiskState(10_000)
    s.update_peak(10_500)
    s.update_peak(10_200)
    assert s.peak == 10_500
    s.record_realized(-50)
    s.record_realized(20)
    assert s.realized_pnl == -30
