# Running the bot unattended

The live loop already survives *transient* errors (a failed API call is logged
and retried on the next poll). The **supervisor** (`supervisor.py`) adds the
next layer: if the bot process dies **hard** (unhandled crash, OOM kill), it
restarts it — with crash-loop protection so a persistent bad state (e.g. a
reconcile `halt`) doesn't spin forever.

```
supervisor.py  →  restarts  →  cli.py run --live --loop  →  the trading loop
   (crash?)                        (transient error?)          (each candle)
```

## Quick start (WSL / this machine)

```bash
bash scripts/run-unattended.sh          # launch, detached
tail -f logs/bot.log                    # watch it
bash scripts/stop-unattended.sh         # stop cleanly
```

`run-unattended.sh` starts the bot under the supervisor with `nohup`, so it
keeps running after you close the terminal. Edit the command inside that script
to change strategy / symbol / timeframe / alert level. Everything (supervisor
messages + bot output) lands in `logs/bot.log`.

## ⚠️ The WSL ceiling — read this

On WSL you get "survives closing the terminal", **not** true 24/7:

- **WSL shuts its VM down** a few seconds after the last WSL process/handle
  closes. Detaching with `nohup` keeps a process alive, so the VM stays up — but…
- **Windows sleep or reboot kills everything.** No supervisor can survive the
  host going down. If the laptop sleeps, the bot stops.

Mitigations on Windows, roughly in order of effort:

1. Keep the machine awake and a WSL process alive (the `nohup` supervisor does
   the latter). Set Windows to never sleep while plugged in.
2. Start it automatically after a reboot with **Windows Task Scheduler** →
   "At log on" → `wsl -d Ubuntu -e bash -lc 'cd ~/personal/trading_bot && bash scripts/run-unattended.sh'`.
3. For real always-on, run it on a small **Linux VPS** instead (below).

For a *testnet* bot, option 1 is fine. Don't chase 24/7 on a laptop.

## True 24/7: a Linux VPS with systemd

A small always-on Linux box (a cheap VPS) is the right home for a 24/7 bot.
There the supervisor is optional — `systemd` itself does the restart-on-crash
and start-on-boot. Drop-in unit (`/etc/systemd/system/trading-bot.service`):

```ini
[Unit]
Description=Crypto trading bot (live testnet)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=YOURUSER
WorkingDirectory=/home/YOURUSER/trading_bot
ExecStart=/home/YOURUSER/trading_bot/.venv/bin/python cli.py run --live --loop \
  --poll 20 --strategy rsi --symbol BTC/USDT --timeframe 1m \
  --alert-level 2 --reconcile halt
Restart=on-failure
RestartSec=10
StartLimitIntervalSec=60
StartLimitBurst=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now trading-bot
journalctl -u trading-bot -f          # live logs
```

`Restart=on-failure` + `StartLimitBurst` mirror the supervisor's restart +
crash-loop behavior, so on a VPS you can skip `supervisor.py` and let systemd
own the lifecycle. The Python supervisor stays useful where you don't control
init (WSL, a shared host) or when a future GUI drives the bot directly.

## Supervisor options

`python supervisor.py [opts] -- <command...>`

| Option | Default | Meaning |
|---|---|---|
| `--log PATH` | `logs/bot.log` | combined supervisor + child log |
| `--pidfile PATH` | `state/supervisor.pid` | supervisor PID (used by the stop script) |
| `--max-restarts N` | `5` | give up after N crashes within the window |
| `--window S` | `60` | rolling window (seconds) for counting crashes |
| `--backoff S` | `10` | wait this long before each restart |

A clean stop (Ctrl+C / SIGTERM, or the stop script) does **not** restart the
bot. Only a hard crash does — up to the crash-loop limit.
