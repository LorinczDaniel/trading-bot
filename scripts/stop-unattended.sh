#!/usr/bin/env bash
# Cleanly stop the detached supervisor (and the bot it manages).
set -euo pipefail
cd "$(dirname "$0")/.."

PIDFILE="state/supervisor.pid"
if [[ ! -f "$PIDFILE" ]]; then
    echo "No supervisor PID file ($PIDFILE) — nothing to stop."
    exit 0
fi

PID="$(cat "$PIDFILE")"
if kill -0 "$PID" 2>/dev/null; then
    kill "$PID"   # SIGTERM -> supervisor stops its child and exits, no restart
    echo "Sent stop to supervisor (pid $PID)."
else
    echo "Supervisor (pid $PID) not running; removing stale PID file."
    rm -f "$PIDFILE"
fi
