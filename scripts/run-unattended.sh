#!/usr/bin/env bash
# Launch the bot under the supervisor, DETACHED — it keeps running after you
# close this terminal (but NOT after Windows sleeps/reboots; see
# docs/running-unattended.md). Edit the bot command below to taste, then:
#     bash scripts/run-unattended.sh
set -euo pipefail
cd "$(dirname "$0")/.."

# shellcheck disable=SC1091
source .venv/bin/activate
mkdir -p logs state

nohup python supervisor.py \
    --log logs/bot.log --pidfile state/supervisor.pid \
    --max-restarts 5 --window 60 --backoff 10 -- \
  python cli.py run --live --loop --poll 20 \
    --strategy rsi --symbol BTC/USDT --timeframe 1m \
    --alert-level 2 --reconcile halt \
  >> logs/supervisor.out 2>&1 &

echo "Supervisor started (pid $!)."
echo "  logs:  tail -f logs/bot.log"
echo "  stop:  bash scripts/stop-unattended.sh"
