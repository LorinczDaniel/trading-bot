from reconcile import check_state, reconcile


def _state(base=0.0, quote=1000.0, entry=0.0, stop=0.0):
    return {"base": base, "quote": quote, "entry_price": entry, "stop_price": stop}


# --- pure logic (check_state) ---

def test_flat_state_is_ok():
    ok, problems, _ = check_state(_state(), free_base=5.0)
    assert ok and problems == []


def test_healthy_position_is_ok():
    ok, problems, _ = check_state(_state(base=0.5, entry=100, stop=95), free_base=1.0)
    assert ok and problems == []


def test_position_without_stop_is_flagged():
    ok, problems, _ = check_state(_state(base=0.5, entry=100, stop=0.0), free_base=1.0)
    assert not ok
    assert any("stop" in p for p in problems)


def test_position_without_entry_is_flagged():
    ok, problems, _ = check_state(_state(base=0.5, entry=0.0, stop=95), free_base=1.0)
    assert not ok
    assert any("entry" in p for p in problems)


def test_unsellable_position_is_flagged():
    # bot thinks it holds 0.5 but the exchange only has 0.1 free
    ok, problems, _ = check_state(_state(base=0.5, entry=100, stop=95), free_base=0.1)
    assert not ok
    assert any("sellable" in p for p in problems)


def test_prefunding_does_not_false_trip():
    # a tiny bot position against a pre-funded (large) free balance -> sellable
    ok, problems, _ = check_state(_state(base=0.0003, entry=100, stop=95), free_base=1.0)
    assert ok and problems == []


def test_negative_base_is_flagged():
    ok, problems, _ = check_state(_state(base=-0.1), free_base=5.0)
    assert not ok


# --- policy (reconcile) ---

def test_reconcile_halt_raises_on_drift():
    msgs = []
    raised = False
    try:
        reconcile(_state(base=0.5, entry=100, stop=0.0), free_base=1.0, mode="halt", emit=msgs.append)
    except SystemExit:
        raised = True
    assert raised
    assert any("stop" in m for m in msgs)


def test_reconcile_warn_continues_without_raising():
    msgs = []
    reconcile(_state(base=0.5, entry=100, stop=0.0), free_base=1.0, mode="warn", emit=msgs.append)
    assert any("continuing despite drift" in m for m in msgs)


def test_reconcile_off_skips_even_broken_state():
    msgs = []
    reconcile(_state(base=0.5, entry=100, stop=0.0), free_base=0.0, mode="off", emit=msgs.append)
    assert any("skip" in m.lower() for m in msgs)


def test_reconcile_verified_position_emits_ok():
    # a held position that passed every check earns a genuine "OK"
    msgs = []
    reconcile(_state(base=0.5, entry=100, stop=95), free_base=1.0, mode="halt", emit=msgs.append)
    assert any(m.startswith("Reconcile: OK") for m in msgs)


def test_reconcile_flat_does_not_claim_ok_and_names_the_gap():
    # flat state verifies nothing about untracked positions -> must NOT imply "all clear"
    msgs = []
    reconcile(_state(base=0.0, quote=500), free_base=2.0, mode="halt", emit=msgs.append)
    assert not any(m.startswith("Reconcile: OK") for m in msgs)
    assert any("untracked" in m for m in msgs)
