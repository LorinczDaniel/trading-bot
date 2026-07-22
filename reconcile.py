"""Startup reconciliation for live runs.

Before a live run trades, compare the persisted managed-ledger state against
reality and refuse (or warn) if they disagree. The managed ledger is virtual
and intentionally decoupled from the account's (pre-funded) balances, so this
checks only what can be verified honestly:

  1. Internal consistency  — a held position must have an entry and a stop
                             (a position with neither is the crash-mid-cycle
                             signature); balances must not be negative/malformed.
  2. Sellability           — if the bot believes it holds `base`, the exchange
                             must have at least that much FREE base to sell it.

Limitation: it CANNOT detect a bot-created position the state file has
forgotten (state reset to flat while coins linger on the exchange) — pre-funding
makes such coins indistinguishable from the account's own without a recorded
baseline, which is fragile on a shared account. It catches the dangerous
direction (state claims something the exchange can't honor), not that one.
"""

_EPS = 1e-12


def check_state(state: dict, free_base: float):
    """Pure reconciliation logic (no network).

    `state`     — persisted ledger dict (base, quote, entry_price, stop_price).
    `free_base` — the exchange's FREE base balance (e.g. free BTC).
    Returns (ok: bool, problems: list[str], summary: str).
    """
    base = float(state.get("base", 0.0))
    quote = float(state.get("quote", 0.0))
    entry = float(state.get("entry_price", 0.0))
    stop = float(state.get("stop_price", 0.0))

    problems = []
    if base < 0:
        problems.append(f"state base is negative ({base:.6f})")
    if quote < 0:
        problems.append(f"state quote is negative ({quote:.2f})")

    holding = base > 0
    if holding:
        if entry <= 0:
            problems.append(f"holding {base:.6f} base but entry_price is {entry:.2f} (no entry recorded)")
        if stop <= 0:
            problems.append(f"holding {base:.6f} base but stop_price is {stop:.2f} (no stop set)")
        if free_base + _EPS < base:
            problems.append(
                f"state claims {base:.6f} base but exchange free is {free_base:.6f} "
                f"— position not fully sellable"
            )

    if holding:
        summary = (f"holding {base:.6f} base (entry {entry:.2f}, stop {stop:.2f}) "
                   f"— exchange free {free_base:.6f}")
    else:
        summary = f"flat (quote budget {quote:.2f}) — exchange free base {free_base:.6f}"
    return (not problems), problems, summary


def reconcile(state: dict, free_base: float, mode: str = "halt", emit=print) -> None:
    """Apply the reconciliation policy. `mode` is halt | warn | off.

    halt (default): raise SystemExit on any mismatch — refuse to trade.
    warn:           print the mismatch and continue trading.
    off:            skip the check entirely.
    """
    if mode == "off":
        emit("Reconcile: skipped (--reconcile off)")
        return

    ok, problems, summary = check_state(state, free_base)
    if ok:
        if float(state.get("base", 0.0)) > 0:
            # a tracked position we actually verified: has a stop, and is sellable
            emit(f"Reconcile: OK — {summary}")
        else:
            # flat state verifies only internal consistency — it CANNOT confirm
            # there is no untracked/forgotten position (e.g. a crash after buying
            # but before saving state). Say so rather than imply "all clear".
            emit(f"Reconcile: no tracked position — {summary}. "
                 f"NOTE: cannot detect an untracked position on a pre-funded account "
                 f"(e.g. a crash mid-buy) — verify the exchange manually if unsure.")
        return

    for p in problems:
        emit(f"[WARN] reconcile: {p}")
    if mode == "halt":
        raise SystemExit(
            "Reconciliation failed (see warnings above). Refusing to start.\n"
            "Investigate, then fix/clear state/ or re-run with --reconcile warn to override."
        )
    emit("[WARN] reconcile: continuing despite drift (--reconcile warn)")


def fetch_free_base(exchange, symbol: str) -> float:
    """Read the exchange's FREE base balance for `symbol` (thin ccxt I/O)."""
    base_ccy = exchange.market(symbol)["base"]
    bal = exchange.fetch_balance()
    free = (bal.get("free") or {}).get(base_ccy)
    if free is None:
        free = (bal.get(base_ccy) or {}).get("free", 0.0)
    return float(free or 0.0)


def reconcile_live(exchange, symbol: str, state: dict, mode: str = "halt", emit=print) -> None:
    """Fetch the live free base and run reconciliation. Skips the network call
    entirely when mode is off."""
    if mode == "off":
        emit("Reconcile: skipped (--reconcile off)")
        return
    reconcile(state, fetch_free_base(exchange, symbol), mode=mode, emit=emit)
