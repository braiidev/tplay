from __future__ import annotations

import json
import os
from typing import Any, cast

from .config import CONFIG_DIR

RADIOS_FILE: str = os.path.join(CONFIG_DIR, "radios.json")


def load_radios() -> list[dict[str, str]]:
    try:
        with open(RADIOS_FILE) as f:
            return cast(list[dict[str, str]], json.load(f))
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return []


def save_radios(radios: list[dict[str, str]]) -> None:
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        from .file_utils import atomic_write
        atomic_write(RADIOS_FILE, json.dumps(radios, indent=2))
    except (OSError, PermissionError):
        pass
