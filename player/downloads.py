"""Historial de descargas — persistencia en downloads.json."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

DOWNLOADS_FILE: str = os.path.expanduser("~/.config/tplay/data/downloads.json")


@dataclass
class DownloadEntry:
    """Entrada en el historial de descargas."""

    title: str
    url: str
    webpage_url: str
    file_path: str
    format: str
    quality: str
    platform: str
    downloaded_at: str
    file_size_bytes: int = 0

    @property
    def exists(self) -> bool:
        return os.path.isfile(self.file_path)


def load_history() -> list[DownloadEntry]:
    """Carga historial desde archivo."""
    try:
        with open(DOWNLOADS_FILE) as f:
            data = json.load(f)
        return [_dict_to_entry(d) for d in data]
    except (FileNotFoundError, json.JSONDecodeError, TypeError):
        return []


def save_history(history: list[DownloadEntry]) -> None:
    """Guarda historial a archivo."""
    try:
        os.makedirs(os.path.dirname(DOWNLOADS_FILE), exist_ok=True)
        with open(DOWNLOADS_FILE, "w") as f:
            json.dump([asdict(e) for e in history], f, indent=2)
    except OSError:
        pass


def add_entry(
    history: list[DownloadEntry],
    title: str,
    url: str,
    webpage_url: str,
    file_path: str,
    fmt: str,
    quality: str,
    platform: str,
    file_size_bytes: int = 0,
) -> DownloadEntry:
    """Agrega una entrada al historial."""
    entry = DownloadEntry(
        title=title,
        url=url,
        webpage_url=webpage_url,
        file_path=file_path,
        format=fmt,
        quality=quality,
        platform=platform,
        downloaded_at=datetime.now().isoformat(timespec="seconds"),
        file_size_bytes=file_size_bytes,
    )
    history.insert(0, entry)
    return entry


def remove_entry(history: list[DownloadEntry], index: int) -> DownloadEntry | None:
    """Elimina una entrada del historial por índice."""
    if 0 <= index < len(history):
        return history.pop(index)
    return None


def _dict_to_entry(d: dict[str, Any]) -> DownloadEntry:
    """Convierte un dict a DownloadEntry."""
    return DownloadEntry(
        title=str(d.get("title", "")),
        url=str(d.get("url", "")),
        webpage_url=str(d.get("webpage_url", "")),
        file_path=str(d.get("file_path", "")),
        format=str(d.get("format", "audio")),
        quality=str(d.get("quality", "480p")),
        platform=str(d.get("platform", "")),
        downloaded_at=str(d.get("downloaded_at", "")),
        file_size_bytes=int(d.get("file_size_bytes", 0)),
    )


def format_size(size_bytes: int) -> str:
    """Formatea tamaño en bytes a string legible."""
    if size_bytes <= 0:
        return ""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.0f}K"
    return f"{size_bytes / (1024 * 1024):.1f}M"
