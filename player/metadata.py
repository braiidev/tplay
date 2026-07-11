from __future__ import annotations

from typing import Any

import mutagen
from collections import OrderedDict


def _safe_tag(d: Any, key: str) -> str | None:
    v = d.get(key)
    if not v:
        return None
    try:
        result: str = v[0]
        return result
    except (IndexError, TypeError):
        return None


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
                    'title': _safe_tag(audio, 'title'),
                    'artist': _safe_tag(audio, 'artist'),
                    'album': _safe_tag(audio, 'album'),
                    'genre': _safe_tag(audio, 'genre'),
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
