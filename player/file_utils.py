from __future__ import annotations

import os
from typing import Any

AUDIO_EXT: tuple[str, ...] = (".mp3", ".flac", ".wav", ".ogg", ".m4a", ".aac", ".opus", ".weba", ".wma", ".aiff", ".aif")
VIDEO_EXT: tuple[str, ...] = (".mp4", ".mkv", ".avi", ".mov", ".flv", ".wmv")
PLAYLIST_EXT: tuple[str, ...] = (".m3u", ".pls")
ALLOWED_EXT: tuple[str, ...] = AUDIO_EXT + VIDEO_EXT + PLAYLIST_EXT
EXT_LABEL: dict[str, str] = {".mp3": "mp3", ".flac": "flac", ".wav": "wav", ".ogg": "ogg",
                             ".m4a": "m4a", ".aac": "aac", ".opus": "opus", ".weba": "webm",
                             ".wma": "wma", ".aiff": "aiff", ".aif": "aiff",
                             ".mp4": "vid", ".mkv": "vid", ".avi": "vid", ".mov": "vid",
                             ".flv": "vid", ".wmv": "vid",
                             ".m3u": "PL", ".pls": "PL"}


def is_media(name: str) -> bool:
    return name.lower().endswith(ALLOWED_EXT)


def list_dir(path: str) -> list[tuple[str, bool, str]]:
    try:
        entries_it = os.scandir(path)
    except PermissionError:
        return []
    dirs: list[tuple[str, bool, str]] = []
    files: list[tuple[str, bool, str]] = []
    with entries_it:
        for entry in entries_it:
            name = entry.name
            if name.startswith("."):
                continue
            try:
                is_dir = entry.is_dir(follow_symlinks=True)
            except OSError:
                continue
            if is_dir:
                dirs.append((name, True, entry.path))
            elif is_media(name):
                files.append((name, False, entry.path))
    dirs.sort(key=lambda x: x[0].lower())
    files.sort(key=lambda x: x[0].lower())
    return dirs + files


def time_str(secs: int | None) -> str:
    if secs is None or secs < 0:
        return "--:--"
    m, s = divmod(int(secs), 60)
    return f"{m}:{s:02d}"


def ext_label(name: str) -> str:
    _, ext = os.path.splitext(name)
    return EXT_LABEL.get(ext.lower(), "??")


_URL_SCHEMES: tuple[str, ...] = ("http://", "https://", "rtmp://", "mms://", "rtsp://", "ftp://")


def is_url(path: str) -> bool:
    return path.lower().startswith(_URL_SCHEMES)


def is_video_file(path: str) -> bool:
    return path.lower().endswith(VIDEO_EXT)


def is_playlist_file(path: str) -> bool:
    return path.lower().endswith(PLAYLIST_EXT)


def atomic_write(path: str, data: str) -> None:
    """Escribe contenido de forma atómica (temp + replace)."""
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        f.write(data)
    os.replace(tmp, path)
