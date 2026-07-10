from __future__ import annotations

import json
import os
from typing import Any, cast

from .config import CONFIG_DIR

FAVORITES_FILE: str = os.path.join(CONFIG_DIR, "favorites.json")


def load_favorites() -> list[dict[str, str]]:
    try:
        with open(FAVORITES_FILE) as f:
            return cast(list[dict[str, str]], json.load(f))
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return []


def save_favorites(favorites: list[dict[str, str]]) -> None:
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(FAVORITES_FILE, "w") as f:
            json.dump(favorites, f, indent=2)
    except (OSError, PermissionError):
        pass
