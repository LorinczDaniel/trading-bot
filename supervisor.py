"""Keep the bot running unattended: restart it if it crashes, but give up if it
crash-loops (so a persistent bad state, e.g. a reconcile halt, doesn't spin
forever). The `supervise()` core is pure and injectable so the restart policy is
unit-tested; `main()` is the thin process/logging/signal wiring around it.

The engine is deliberately decoupled from the CLI so a future GUI (Linux or
Windows) can drive the same supervision logic instead of a shell script.
"""

import argparse
import os
import signal
import subprocess
import sys
import time

# Exit codes we treat as an intentional, clean stop (do NOT restart):
#   0   normal exit           130  Ctrl+C (SIGINT)
#  -2   killed by SIGINT      -15  killed by SIGTERM  (we asked it to stop)
_CLEAN = frozenset({0, 130, -2, -15})

_USAGE = ("usage: python supervisor.py [--log PATH] [--pidfile PATH] "
          "[--max-restarts N] [--window S] [--backoff S] -- <command ...>")


def supervise(run, should_stop=lambda: False, *, max_restarts=5, window=60.0,
              backoff=5.0, sleep=time.sleep, now=time.monotonic, emit=print,
              is_clean_exit=lambda code: code in _CLEAN):
    """Run `run()` (returns a process exit code) repeatedly until it exits
    cleanly, we're asked to stop, or it crash-loops.

    Restarts on a non-clean exit after `backoff` seconds. Gives up once it has
    crashed `max_restarts` times within a rolling `window` seconds. Returns the
    last child exit code.
    """
    crashes = []  # monotonic timestamps of recent crashes, within `window`
    while not should_stop():
        code = run()
        if should_stop():
            # an intentional stop is a success, not a failure — report exit 0
            emit(f"stopped by signal (child exit {code})")
            return 0
        if is_clean_exit(code):
            emit(f"child exited cleanly (code {code}); not restarting")
            return code

        t = now()
        crashes = [c for c in crashes if t - c <= window]
        crashes.append(t)
        if len(crashes) >= max_restarts:
            emit(f"{len(crashes)} crashes within {window:.0f}s — giving up (crash loop). "
                 f"Last exit {code}. Fix the cause, then relaunch.")
            return code
        emit(f"child crashed (exit {code}); restart {len(crashes)}/{max_restarts} in {backoff:.0f}s")
        sleep(backoff)
    return 0


def _parse_args(argv):
    if "--" not in argv:
        raise SystemExit(_USAGE)
    split = argv.index("--")
    opts, cmd = argv[:split], argv[split + 1:]
    p = argparse.ArgumentParser(prog="supervisor", usage=_USAGE)
    p.add_argument("--log", default="logs/bot.log")
    p.add_argument("--pidfile", default="state/supervisor.pid")
    p.add_argument("--max-restarts", type=int, default=5)
    p.add_argument("--window", type=float, default=60.0)
    p.add_argument("--backoff", type=float, default=5.0)
    ns = p.parse_args(opts)
    if not cmd:
        raise SystemExit(_USAGE)
    return ns, cmd


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    ns, cmd = _parse_args(argv)

    for path in (ns.log, ns.pidfile):
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)

    log = open(ns.log, "a", buffering=1)
    ctx = {"stop": False, "proc": None}

    def emit(msg):
        line = f"[supervisor] {msg}"
        print(line, file=log)
        print(line)  # also to the console (captured by nohup)

    def handle_stop(_signum, _frame):
        ctx["stop"] = True
        proc = ctx["proc"]
        if proc is not None and proc.poll() is None:
            proc.terminate()

    signal.signal(signal.SIGTERM, handle_stop)
    signal.signal(signal.SIGINT, handle_stop)

    def run():
        ctx["proc"] = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
        ctx["proc"].wait()
        return ctx["proc"].returncode

    with open(ns.pidfile, "w") as f:
        f.write(str(os.getpid()))
    emit(f"starting (pid {os.getpid()}): {' '.join(cmd)}  | log {ns.log}")
    try:
        code = supervise(run, should_stop=lambda: ctx["stop"],
                         max_restarts=ns.max_restarts, window=ns.window,
                         backoff=ns.backoff, emit=emit)
    finally:
        try:
            os.remove(ns.pidfile)
        except OSError:
            pass
        emit("supervisor exited")
        log.close()
    return code


if __name__ == "__main__":
    sys.exit(main())
