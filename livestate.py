import json
import os


def load_state(path: str, default: dict) -> dict:
    """Load persisted live-bot state, or a copy of `default` if none exists."""
    if not os.path.exists(path):
        return dict(default)
    with open(path) as f:
        return json.load(f)


def save_state(path: str, state: dict) -> None:
    """Persist live-bot state, creating the parent directory if needed."""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w") as f:
        json.dump(state, f, indent=2)
