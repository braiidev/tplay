"""yt-dlp wrapper para Web Explorer."""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Any

from .config import load as _load_config


@dataclass
class WebResult:
    """Resultado de búsqueda web."""

    title: str
    url: str
    duration: int
    channel: str
    webpage_url: str
    platform: str
    download_url: str = ""


def is_available() -> bool:
    """Verifica si yt-dlp está instalado."""
    try:
        import yt_dlp  # noqa: F401
        return True
    except ImportError:
        return False


def search(
    query: str, max_results: int = 5, search_prefix: str = "ytsearch"
) -> list[WebResult]:
    """
    Busca en la plataforma indicada.

    1. extract_flat=True → obtiene lista de entries (rápido, sin stream URLs)
    2. Para cada entry → extract_info para obtener stream URL
    """
    if not is_available():
        raise RuntimeError(
            "yt-dlp no instalado: pip install --break-system-packages yt-dlp"
        )

    results: list[WebResult] = []
    try:
        import yt_dlp
    except ImportError:
        return results

    list_opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
    }
    try:
        with yt_dlp.YoutubeDL(list_opts) as ydl:
            info = ydl.extract_info(
                f"{search_prefix}{max_results}:{query}", download=False
            )
            if not info or "entries" not in info:
                return results
            entries = list(info["entries"])
    except Exception:
        return results

    extract_opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "skip_download": True,
    }
    for entry in entries:
        if entry is None:
            continue
        entry_url = entry.get("url") or entry.get("webpage_url", "")
        if not entry_url:
            continue
        try:
            with yt_dlp.YoutubeDL(extract_opts) as ydl:
                detail = ydl.extract_info(entry_url, download=False)
                if not detail:
                    continue
                stream_url = detail.get("url", "")
                if not stream_url and detail.get("formats"):
                    audio_fmts = [
                        f for f in detail["formats"] if f.get("acodec") != "none"
                    ]
                    if audio_fmts:
                        best = max(audio_fmts, key=lambda f: f.get("abr") or 0)
                        stream_url = best.get("url", "")
                if not stream_url:
                    continue
                download_url = _get_download_url(detail)
                results.append(
                    WebResult(
                        title=detail.get("title", entry.get("title", "Sin título")),
                        url=stream_url,
                        duration=int(detail.get("duration") or 0),
                        channel=detail.get("channel", detail.get("uploader", "")),
                        webpage_url=detail.get("webpage_url", entry_url),
                        platform=detail.get("extractor", "unknown"),
                        download_url=download_url,
                    )
                )
        except Exception:
            continue

    return results


def _get_download_url(info: dict[str, Any]) -> str:
    """Obtiene la mejor URL de descarga desde info dict."""
    if info.get("url"):
        return str(info["url"])

    if not info.get("formats"):
        return ""

    cfg = _load_config()
    fmt = cfg.get("online_download_format", "audio")
    quality = cfg.get("online_download_quality", "480p")

    if fmt == "audio":
        candidates = [
            f
            for f in info["formats"]
            if f.get("acodec") != "none" and f.get("vcodec") == "none"
        ]
        if candidates:
            best = max(candidates, key=lambda f: f.get("abr") or 0)
            return str(best.get("url", ""))

    quality_map: dict[str, int] = {
        "480p": 480,
        "720p": 720,
        "1080p": 1080,
        "best": 9999,
    }
    target_height = quality_map.get(quality, 480)

    video_fmts = [
        f
        for f in info["formats"]
        if f.get("vcodec") != "none" and f.get("acodec") != "none"
    ]
    if video_fmts:
        if target_height == 9999:
            best = max(video_fmts, key=lambda f: f.get("height", 0))
        else:
            suitable = [f for f in video_fmts if f.get("height", 0) <= target_height]
            best = max(suitable, key=lambda f: f.get("height", 0)) if suitable else max(
                video_fmts, key=lambda f: f.get("height", 0)
            )
        return str(best.get("url", ""))

    all_fmts = [f for f in info["formats"] if f.get("url")]
    if all_fmts:
        best = max(all_fmts, key=lambda f: f.get("height", 0))
        return str(best.get("url", ""))

    return ""


def download(
    url: str,
    output_path: str,
    fmt: str = "audio",
    quality: str = "480p",
    progress_hook: Any = None,
) -> tuple[bool, str]:
    """
    Descarga un archivo con yt-dlp.

    Returns:
        (success, filename) o (False, error_message)
    """
    if not is_available():
        return False, "yt-dlp no instalado"

    try:
        import yt_dlp
    except ImportError:
        return False, "yt-dlp no disponible"

    cfg = _load_config()
    outtmpl = os.path.join(output_path, "%(title)s.%(ext)s")
    devnull = open(os.devnull, "w")

    quality_map: dict[str, str] = {
        "worst": "worst",
        "144p": "bestvideo[height<=144]+bestaudio/best[height<=144]",
        "240p": "bestvideo[height<=240]+bestaudio/best[height<=240]",
        "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
        "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "best": "bestvideo+bestaudio/best",
    }

    if fmt == "audio":
        opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "outtmpl": outtmpl,
            "stdout": devnull,
            "stderr": devnull,
        }
    else:
        fmt_selector = quality_map.get(quality, quality_map["480p"])
        opts = {
            "quiet": True,
            "no_warnings": True,
            "format": fmt_selector,
            "merge_output_format": "mp4",
            "outtmpl": outtmpl,
            "stdout": devnull,
            "stderr": devnull,
        }

    if progress_hook is not None:
        opts["progress_hooks"] = [progress_hook]

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info:
                title = info.get("title", "download")
                ext = "mp3" if fmt == "audio" else "mp4"
                filename = f"{title}.{ext}"
                return True, filename
            return False, "No se pudo obtener info del video"
    except Exception as e:
        return False, str(e)
    finally:
        devnull.close()


def format_duration(seconds: int) -> str:
    """Formatea duración en HH:MM:SS o MM:SS."""
    if seconds <= 0:
        return "--:--"
    h, remainder = divmod(seconds, 3600)
    m, s = divmod(remainder, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"
