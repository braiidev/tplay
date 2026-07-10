from __future__ import annotations

import os
from typing import Any

AUDIO_EXT: tuple[str, ...] = (".mp3", ".flac", ".wav", ".ogg")
VIDEO_EXT: tuple[str, ...] = (".mp4", ".mkv", ".avi", ".mov")
PLAYLIST_EXT: tuple[str, ...] = (".m3u", ".pls")
ALLOWED_EXT: tuple[str, ...] = AUDIO_EXT + VIDEO_EXT + PLAYLIST_EXT
EXT_LABEL: dict[str, str] = {".mp3": "mp3", ".flac": "flac", ".wav": "wav", ".ogg": "ogg",
                             ".mp4": "vid", ".mkv": "vid", ".avi": "vid", ".mov": "vid",
                             ".m3u": "PL", ".pls": "PL"}


def is_media(name: str) -> bool:
    return name.lower().endswith(ALLOWED_EXT)


def list_dir(path: str) -> list[tuple[str, bool, str]]:
    try:
        items = os.listdir(path)
    except PermissionError:
        return []
    dirs: list[tuple[str, bool, str]] = []
    files: list[tuple[str, bool, str]] = []
    for name in items:
        full = os.path.join(path, name)
        if name.startswith("."):
            continue
        if os.path.isdir(full):
            dirs.append((name, True, full))
        elif is_media(name):
            files.append((name, False, full))
    dirs.sort(key=lambda x: x[0].lower())
    files.sort(key=lambda x: x[0].lower())
    return dirs + files


def human_size(path: str) -> str:
    try:
        size = os.path.getsize(path)
        if size < 1024:
            return f"{size}B"
        elif size < 1024 ** 2:
            return f"{size // 1024}KB"
        else:
            return f"{size / (1024 ** 2):.1f}MB"
    except OSError:
        return ""


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
