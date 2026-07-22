class Notifier:
    """Minimal notifier: prints and records messages. A real Telegram/Discord
    sender can subclass this and override `_emit` (Phase 2.5). Recording the
    messages keeps the trader easy to test.
    """

    def __init__(self, echo: bool = True):
        self.echo = echo
        self.messages: list[str] = []

    def _emit(self, level: str, msg: str) -> None:
        line = f"[{level}] {msg}"
        self.messages.append(line)
        if self.echo:
            print(line)

    def info(self, msg: str) -> None:
        self._emit("INFO", msg)

    def warn(self, msg: str) -> None:
        self._emit("WARN", msg)

    def heartbeat(self, msg: str) -> None:
        """Liveness ping. For the terminal notifier this is identical to info;
        TelegramNotifier routes it separately (throttled/off) so a phone isn't
        buzzed on every poll."""
        self._emit("INFO", msg)
