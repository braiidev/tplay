from __future__ import annotations

import json
import os
from typing import Any, cast

from .config import CONFIG_DIR

STATE_FILE: str = os.path.join(CONFIG_DIR, "state.json")


def load_state() -> dict[str, Any]:
    try:
        with open(STATE_FILE) as f:
            return cast(dict[str, Any], json.load(f))
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return {"playing": False, "file": "", "position": 0}


def save_state(playing: bool, file: str = "", position: int = 0) -> None:
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(STATE_FILE, "w") as f:
            json.dump({"playing": playing, "file": file, "position": position}, f)
    except (OSError, PermissionError):
        pass


HISTORY_FILE: str = os.path.join(CONFIG_DIR, "history.json")


def save_history(history: list[Any]) -> None:
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(HISTORY_FILE, "w") as f:
            json.dump(history[:100], f, indent=2)
    except (OSError, PermissionError):
        pass


def load_history() -> list[Any]:
    try:
        with open(HISTORY_FILE) as f:
            return cast(list[Any], json.load(f))
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return []
