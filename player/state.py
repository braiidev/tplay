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
        return {"playing": False, "file": "", "position": 0,
                "stack_items": [], "playhead": -1, "shuffle": False,
                "repeat": False, "volume": 75, "rate": 1.0}


def save_state(playing: bool, file: str = "", position: int = 0,
               stack_items: list[dict[str, Any]] | None = None,
               playhead: int = -1, shuffle: bool = False,
               repeat: bool = False, volume: int = 75,
               rate: float = 1.0, eq_enabled: bool = False,
               eq_bands: list[float] | None = None,
               eq_preamp: float = 0.0,
               eq_preset: str = "Flat") -> None:
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(STATE_FILE, "w") as f:
            json.dump({
                "playing": playing,
                "file": file,
                "position": position,
                "stack_items": stack_items or [],
                "playhead": playhead,
                "shuffle": shuffle,
                "repeat": repeat,
                "volume": volume,
                "rate": rate,
                "eq_enabled": eq_enabled,
                "eq_bands": eq_bands or [0.0] * 10,
                "eq_preamp": eq_preamp,
                "eq_preset": eq_preset,
            }, f)
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
