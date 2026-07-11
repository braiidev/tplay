from __future__ import annotations

import os
import json
from typing import Any

from .config import CONFIG_DIR

PLAYLIST_FILE: str = os.path.join(CONFIG_DIR, "playlist.json")


def load_all() -> tuple[dict[str, list[tuple[str, str]]], str]:
    try:
        with open(PLAYLIST_FILE) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {"default": []}, "default"

    pls: list[Any] = data.get("playlists", [])
    active: str = data.get("active", "default")
    result: dict[str, list[tuple[str, str]]] = {}
    if not pls:
        return {"default": []}, "default"
    for pl in pls:
        name = pl.get("name", "default")
        songs = pl.get("songs", [])
        valid: list[tuple[str, str]] = []
        for s in songs:
            if isinstance(s, str) and os.path.exists(s):
                valid.append((os.path.basename(s), s))
        result[name] = valid
    if active not in result:
        active = next(iter(result.keys()), "default")
    return result, active


def save_all(playlist_data: dict[str, list[tuple[str, str]]], active_name: str) -> None:
    pls = [{"name": name, "songs": [path for _, path in songs]}
           for name, songs in playlist_data.items()]
    data = {"active": active_name, "playlists": pls}
    try:
        with open(PLAYLIST_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass
