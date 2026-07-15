"""Historial unificado (descargas + streams) — persistencia en downloads.json."""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

DOWNLOADS_FILE: str = os.path.expanduser("~/.config/tplay/data/downloads.json")
TMP_DIR: str = os.path.expanduser("~/.config/tplay/data/tmp")
TEMP_MAX_AGE_DAYS: int = 7


@dataclass
class DownloadEntry:
    """Entrada en el historial unificado (download o stream temporal)."""

    title: str
    url: str
    webpage_url: str
    file_path: str
    format: str
    quality: str
    platform: str
    downloaded_at: str
    file_size_bytes: int = 0
    is_temp: bool = False
    duration: int = 0
    channel: str = ""
    play_count: int = 0

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
        from .file_utils import atomic_write
        atomic_write(DOWNLOADS_FILE, json.dumps([asdict(e) for e in history], indent=2))
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
    is_temp: bool = False,
    duration: int = 0,
    channel: str = "",
) -> DownloadEntry:
    """Agrega una entrada al historial. Si ya existe por webpage_url, incrementa play_count."""
    existing = find_by_webpage_url(history, webpage_url)
    if existing:
        existing.play_count += 1
        existing.downloaded_at = datetime.now().isoformat(timespec="seconds")
        return existing

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
        is_temp=is_temp,
        duration=duration,
        channel=channel,
        play_count=1,
    )
    history.insert(0, entry)
    return entry


def find_by_webpage_url(
    history: list[DownloadEntry], webpage_url: str
) -> DownloadEntry | None:
    """Busca una entrada por webpage_url."""
    for e in history:
        if e.webpage_url == webpage_url:
            return e
    return None


def remove_entry(history: list[DownloadEntry], index: int) -> DownloadEntry | None:
    """Elimina una entrada del historial por índice."""
    if 0 <= index < len(history):
        return history.pop(index)
    return None


def get_downloads(history: list[DownloadEntry]) -> list[int]:
    """Retorna índices de entradas permanentes (no temporales)."""
    return [i for i, e in enumerate(history) if not e.is_temp]


def get_streams(history: list[DownloadEntry]) -> list[int]:
    """Retorna índices de entradas temporales (streams)."""
    return [i for i, e in enumerate(history) if e.is_temp]


def clean_old_temps(history: list[DownloadEntry]) -> int:
    """Elimina entradas temp con archivo > TEMP_MAX_AGE_DAYS. Retorna cantidad eliminada."""
    cutoff = time.time() - (TEMP_MAX_AGE_DAYS * 86400)
    to_remove: list[int] = []
    for i, e in enumerate(history):
        if e.is_temp and e.file_path and os.path.isfile(e.file_path):
            try:
                if os.path.getmtime(e.file_path) < cutoff:
                    os.remove(e.file_path)
                    to_remove.append(i)
            except OSError:
                pass
    for i in reversed(to_remove):
        history.pop(i)
    return len(to_remove)


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
        is_temp=bool(d.get("is_temp", False)),
        duration=int(d.get("duration", 0)),
        channel=str(d.get("channel", "")),
        play_count=int(d.get("play_count", 0)),
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


def format_duration(seconds: int) -> str:
    """Formatea duración en segundos a MM:SS o HH:MM:SS."""
    if seconds <= 0:
        return ""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"
