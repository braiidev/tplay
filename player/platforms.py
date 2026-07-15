"""Registry de plataformas soportadas para Web Explorer."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field

PLATFORMS_FILE: str = os.path.expanduser("~/.config/tplay/data/platforms.json")

DEFAULT_PLATFORMS: list[dict[str, str | int | bool]] = [
    {
        "name": "YouTube",
        "url": "https://www.youtube.com",
        "search_pattern": "/results?search_query={query}",
        "download_pattern": "/watch?v={id}",
        "search_prefix": "ytsearch",
        "downloads": 0,
        "is_default": True,
    },
    {
        "name": "SoundCloud",
        "url": "https://soundcloud.com",
        "search_pattern": "/search?q={query}",
        "download_pattern": "/{id}",
        "search_prefix": "scsearch",
        "downloads": 0,
        "is_default": True,
    },
    {
        "name": "Vimeo",
        "url": "https://vimeo.com",
        "search_pattern": "/search?q={query}",
        "download_pattern": "/{id}",
        "search_prefix": "vpsearch",
        "downloads": 0,
        "is_default": True,
    },
    {
        "name": "Dailymotion",
        "url": "https://www.dailymotion.com",
        "search_pattern": "/search/{query}/videos",
        "download_pattern": "/video/{id}",
        "search_prefix": "dmsearch",
        "downloads": 0,
        "is_default": True,
    },
    {
        "name": "Twitch",
        "url": "https://www.twitch.tv",
        "search_pattern": "/search?term={query}",
        "download_pattern": "/videos/{id}",
        "search_prefix": "twsearch",
        "downloads": 0,
        "is_default": True,
    },
    {
        "name": "Niconico",
        "url": "https://www.nicovideo.jp",
        "search_pattern": "/search/{query}",
        "download_pattern": "/watch/{id}",
        "search_prefix": "nicosearch",
        "downloads": 0,
        "is_default": True,
    },
]


@dataclass
class Platform:
    """Plataforma de streaming soportada."""

    name: str
    url: str
    search_pattern: str
    download_pattern: str
    search_prefix: str
    downloads: int = 0
    is_default: bool = False

    @property
    def has_search(self) -> bool:
        """True si la plataforma soporta búsqueda nativa."""
        return bool(self.search_prefix)


def load_platforms() -> list[Platform]:
    """Carga plataformas desde archivo o crea defaults."""
    try:
        with open(PLATFORMS_FILE) as f:
            data = json.load(f)
        return [_dict_to_platform(p) for p in data]
    except (FileNotFoundError, json.JSONDecodeError, TypeError):
        return [_dict_to_platform(p) for p in DEFAULT_PLATFORMS]


def _dict_to_platform(d: dict[str, str | int | bool]) -> Platform:
    """Convierte un dict a Platform."""
    return Platform(
        name=str(d.get("name", "")),
        url=str(d.get("url", "")),
        search_pattern=str(d.get("search_pattern", "")),
        download_pattern=str(d.get("download_pattern", "")),
        search_prefix=str(d.get("search_prefix", "")),
        downloads=int(d.get("downloads", 0)),
        is_default=bool(d.get("is_default", False)),
    )


def save_platforms(platforms: list[Platform]) -> None:
    """Guarda plataformas a archivo."""
    try:
        os.makedirs(os.path.dirname(PLATFORMS_FILE), exist_ok=True)
        with open(PLATFORMS_FILE, "w") as f:
            json.dump([asdict(p) for p in platforms], f, indent=2)
    except OSError:
        pass


def get_search_prefix(platforms: list[Platform], name: str) -> str:
    """Retorna el search_prefix para una plataforma."""
    for p in platforms:
        if p.name.lower() == name.lower():
            return p.search_prefix
    return ""


def get_platform(platforms: list[Platform], name: str) -> Platform | None:
    """Retorna una plataforma por nombre."""
    for p in platforms:
        if p.name.lower() == name.lower():
            return p
    return None


def increment_downloads(platforms: list[Platform], name: str) -> None:
    """Incrementa el contador de descargas de una plataforma."""
    for p in platforms:
        if p.name.lower() == name.lower():
            p.downloads += 1
            break


def can_delete(platforms: list[Platform], name: str) -> bool:
    """True si la plataforma puede ser eliminada (no es default)."""
    for p in platforms:
        if p.name.lower() == name.lower():
            return not p.is_default
    return False
