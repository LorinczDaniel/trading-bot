import os

from livestate import load_state, save_state


def test_load_missing_returns_default(tmp_path):
    default = {"quote": 10_000.0, "base": 0.0}
    got = load_state(str(tmp_path / "nope.json"), default)
    assert got == default


def test_save_then_load_roundtrip(tmp_path):
    path = str(tmp_path / "sub" / "state.json")  # nested dir must be created
    state = {"quote": 8_000.0, "base": 0.0307, "entry_price": 65000.0}
    save_state(path, state)
    assert os.path.exists(path)
    assert load_state(path, {}) == state


def test_load_default_is_not_mutated(tmp_path):
    default = {"quote": 10_000.0, "base": 0.0}
    got = load_state(str(tmp_path / "nope.json"), default)
    got["base"] = 999
    assert default["base"] == 0.0  # returned a copy, not the original
