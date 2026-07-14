"""yt-dlp wrapper para Web Explorer."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WebResult:
    title: str
    url: str
    duration: int
    channel: str
    webpage_url: str
    platform: str


def is_available() -> bool:
    try:
        import yt_dlp  # noqa: F401
        return True
    except ImportError:
        return False


def search(query: str, max_results: int = 5) -> list[WebResult]:
    if not is_available():
        raise RuntimeError("yt-dlp no instalado: pip install --break-system-packages yt-dlp")
    results: list[WebResult] = []
    try:
        import yt_dlp
    except ImportError:
        return results
    opts: dict[str, object] = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "default_search": "ytsearch",
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
            if not info or "entries" not in info:
                return results
            for entry in info["entries"]:
                if entry is None:
                    continue
                stream_url: str = entry.get("url", "")
                if not stream_url and entry.get("formats"):
                    audio_fmts = [f for f in entry["formats"]
                                  if f.get("acodec") != "none"]
                    if audio_fmts:
                        best = max(audio_fmts, key=lambda f: f.get("abr", 0))
                        stream_url = best.get("url", "")
                if not stream_url:
                    continue
                duration = entry.get("duration") or 0
                results.append(WebResult(
                    title=entry.get("title", "Sin título"),
                    url=stream_url,
                    duration=int(duration),
                    channel=entry.get("channel", entry.get("uploader", "")),
                    webpage_url=entry.get("webpage_url", ""),
                    platform=entry.get("extractor", "unknown"),
                ))
    except Exception:
        return results
    return results


def format_duration(seconds: int) -> str:
    if seconds <= 0:
        return "--:--"
    h, remainder = divmod(seconds, 3600)
    m, s = divmod(remainder, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"
