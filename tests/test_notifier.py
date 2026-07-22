from monitoring.notifier import Notifier
from monitoring.telegram_notifier import TelegramNotifier


class FakeSender:
    """Records the texts it would have sent; can be told to fail."""

    def __init__(self, fail=False):
        self.sent = []
        self.fail = fail

    def __call__(self, text):
        if self.fail:
            raise RuntimeError("network down")
        self.sent.append(text)


def _tg(alert_level=1, sender=None, now=None, heartbeat_every=3600.0):
    return TelegramNotifier(
        token="T", chat_id="C", alert_level=alert_level, echo=False,
        heartbeat_every=heartbeat_every, sender=sender or FakeSender(),
        now=now or (lambda: 0.0),
    )


def test_base_heartbeat_records_like_info():
    n = Notifier(echo=False)
    n.heartbeat("live price 100")
    assert any("price" in m for m in n.messages)  # run_forever test relies on this


def test_trades_and_problems_always_send():
    s = FakeSender()
    n = _tg(alert_level=1, sender=s)
    n.info("BUY 0.1 BTC")
    n.warn("blocked BUY: kill-switch")
    assert len(s.sent) == 2
    assert "BUY 0.1 BTC" in s.sent[0]


def test_level1_never_sends_heartbeat():
    s = FakeSender()
    n = _tg(alert_level=1, sender=s)
    n.heartbeat("live price 100")
    assert s.sent == []
    assert any("price" in m for m in n.messages)  # still recorded locally


def test_level3_sends_every_heartbeat():
    s = FakeSender()
    n = _tg(alert_level=3, sender=s)
    n.heartbeat("live price 100")
    n.heartbeat("live price 101")
    assert len(s.sent) == 2


def test_level2_throttles_heartbeat_to_the_window():
    s = FakeSender()
    clock = {"t": 0.0}
    n = _tg(alert_level=2, sender=s, now=lambda: clock["t"], heartbeat_every=3600.0)
    n.heartbeat("beat A")      # first ever -> sends
    clock["t"] = 1000.0
    n.heartbeat("beat B")      # only 1000s later -> throttled
    clock["t"] = 4000.0
    n.heartbeat("beat C")      # >3600s since last send -> sends
    assert len(s.sent) == 2
    assert "beat A" in s.sent[0]
    assert "beat C" in s.sent[1]


def test_send_failure_is_swallowed_and_logged():
    s = FakeSender(fail=True)
    n = _tg(alert_level=1, sender=s)
    n.info("BUY")  # underlying sender raises -> must not propagate
    assert any("telegram send failed" in m for m in n.messages)
