from __future__ import annotations

from typing import Any

import mutagen
from collections import OrderedDict


class MetadataCache:
    def __init__(self, maxsize: int = 10000) -> None:
        self._maxsize: int = maxsize
        self._cache: OrderedDict[str, dict[str, Any]] = OrderedDict()

    def get(self, path: str) -> dict[str, Any]:
        if path in self._cache:
            self._cache.move_to_end(path)
            return self._cache[path]
        try:
            audio = mutagen.File(path, easy=True)  # type: ignore[attr-defined]
            if audio is None:
                tags = {}
            else:
                tags = {
                    'title': audio.get('title', [None])[0],
                    'artist': audio.get('artist', [None])[0],
                    'album': audio.get('album', [None])[0],
                    'genre': audio.get('genre', [None])[0],
                    'length': int(audio.info.length) if audio.info else 0,
                }
            self._cache[path] = tags
            if len(self._cache) > self._maxsize:
                self._cache.popitem(last=False)
            return tags
        except Exception:
            self._cache[path] = {}
            if len(self._cache) > self._maxsize:
                self._cache.popitem(last=False)
            return {}

    def clear(self) -> None:
        self._cache.clear()
