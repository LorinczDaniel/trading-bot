import time
import urllib.parse
import urllib.request

from monitoring.notifier import Notifier


class TelegramNotifier(Notifier):
    """Notifier that ALSO pushes phone-worthy events to a Telegram chat.

    Trades (`info`) and problems (`warn`) are ALWAYS sent. Heartbeats are sent
    according to `alert_level`:
        1 = never (terminal only)                     -- signal, not noise
        2 = throttled to one per `heartbeat_every` s   -- ~hourly "still alive"
        3 = every heartbeat (~every poll)              -- verbose

    Sends go over the Telegram Bot API using only the standard library (no
    extra dependency). A send failure is caught and logged locally so a
    Telegram outage can NEVER crash the trading loop. `sender`/`now` are
    injectable so the class is unit-testable without touching the network.
    """

    API = "https://api.telegram.org/bot{token}/sendMessage"

    def __init__(self, token: str, chat_id: str, alert_level: int = 1,
                 echo: bool = True, heartbeat_every: float = 3600.0,
                 sender=None, now=time.time):
        super().__init__(echo=echo)
        self.token = token
        self.chat_id = chat_id
        self.alert_level = alert_level
        self.heartbeat_every = heartbeat_every
        self._sender = sender or self._http_send
        self._now = now
        self._last_beat_sent = None

    def info(self, msg: str) -> None:
        super().info(msg)
        self._send(f"ℹ️ {msg}")

    def warn(self, msg: str) -> None:
        super().warn(msg)
        self._send(f"⚠️ {msg}")

    def heartbeat(self, msg: str) -> None:
        super().heartbeat(msg)  # always print/record locally
        if self.alert_level >= 3:
            self._send(f"\U0001f493 {msg}")
        elif self.alert_level == 2:
            now = self._now()
            if self._last_beat_sent is None or (now - self._last_beat_sent) >= self.heartbeat_every:
                self._last_beat_sent = now
                self._send(f"\U0001f493 {msg}")

    def _send(self, text: str) -> None:
        """Fire-and-forget send; a failure is logged, never raised."""
        try:
            self._sender(text)
        except Exception as exc:  # a notification must never take down the bot
            self._emit("WARN", f"telegram send failed ({type(exc).__name__}): {exc or 'no detail'}")

    def _http_send(self, text: str) -> None:
        url = self.API.format(token=self.token)
        data = urllib.parse.urlencode({"chat_id": self.chat_id, "text": text}).encode()
        with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=10) as resp:
            resp.read()
