"""yt-dlp wrapper para Web Explorer — subprocess approach."""
from __future__ import annotations

import glob
import json
import os
import subprocess
import threading
from dataclasses import dataclass, field
from typing import Any

from .config import load as _load_config


_YTDLP_BIN = "yt-dlp"
_YTDLP_COMMON = [_YTDLP_BIN, "--no-warnings", "--ignore-errors", "--no-colors"]
_ytdlp_available: bool | None = None


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
    """Verifica si yt-dlp está instalado (cached)."""
    global _ytdlp_available
    if _ytdlp_available is not None:
        return _ytdlp_available
    try:
        r = subprocess.run(
            [_YTDLP_BIN, "--version"],
            capture_output=True, text=True, timeout=5,
        )
        _ytdlp_available = r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        _ytdlp_available = False
    return _ytdlp_available


def _classify_error(msg: str) -> str:
    """Clasifica errores de yt-dlp en mensajes amigables."""
    low = msg.lower()
    if "sign in to confirm" in low or "bot" in low:
        return "YouTube requiere autenticación — no se puede descargar"
    if "http error 403" in low:
        return "Acceso denegado (403) — video restringido"
    if "http error 429" in low:
        return "Demasiadas solicitudes — esperá un momento"
    if "unavailable" in low or "no longer available" in low:
        return "Video no disponible"
    if "requested format" in low or "no video" in low:
        return "Formato no disponible para este video"
    if "network" in low or "connection" in low or "timeout" in low:
        return "Error de conexión — verificá tu red"
    return f"Error: {msg}"


def _build_search_cmd(
    query: str, max_results: int, search_prefix: str,
) -> list[str]:
    """Construye comando para búsqueda."""
    cmd = list(_YTDLP_COMMON)
    cmd.extend(["--flat-playlist", "--dump-json"])
    cmd.append(f"{search_prefix}{max_results}:{query}")
    return cmd


def _build_stream_cmd(
    webpage_url: str, platform_name: str | None = None,
) -> list[str]:
    """Construye comando para obtener stream URL."""
    cmd = list(_YTDLP_COMMON)
    cmd.extend(["--get-url", "-f", "bestaudio/best"])

    cmd.append(webpage_url)
    return cmd


def _build_download_cmd(
    webpage_url: str,
    output_path: str,
    fmt: str = "audio",
    quality: str = "480p",
    platform_name: str | None = None,
) -> list[str]:
    """Construye comando para descarga."""
    cmd = list(_YTDLP_COMMON)

    outtmpl = os.path.join(output_path, "%(title)s.%(ext)s")

    if fmt == "audio":
        cmd.extend([
            "-x", "--audio-format", "mp3",
            "-f", "bestaudio/best",
            "-o", outtmpl,
        ])
    else:
        quality_map: dict[str, str] = {
            "worst": "worst",
            "144p": "bestvideo[height<=144]+bestaudio/best[height<=144]",
            "240p": "bestvideo[height<=240]+bestaudio/best[height<=240]",
            "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
            "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
            "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "best": "bestvideo+bestaudio/best",
        }
        fmt_selector = quality_map.get(quality, quality_map["480p"])
        cmd.extend([
            "-f", fmt_selector,
            "--merge-output-format", "mp4",
            "-o", outtmpl,
        ])

    cmd.append(webpage_url)
    return cmd


def search(
    query: str, max_results: int = 5, search_prefix: str = "ytsearch",
) -> list[WebResult]:
    """Busca en la plataforma indicada via subprocess."""
    if not is_available():
        raise RuntimeError("yt-dlp no instalado")

    results: list[WebResult] = []
    cmd = _build_search_cmd(query, max_results, search_prefix)

    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("Búsqueda timeout — intentá de nuevo")
    except FileNotFoundError:
        raise RuntimeError("yt-dlp no encontrado en PATH")

    if proc.returncode != 0 and not proc.stdout.strip():
        err = proc.stderr.strip()
        if err:
            raise RuntimeError(_classify_error(err))
        return results

    for line in proc.stdout.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        if entry is None:
            continue

        entry_url = entry.get("url") or entry.get("webpage_url", "")
        if not entry_url:
            continue

        results.append(
            WebResult(
                title=entry.get("title", "Sin título"),
                url=entry_url,
                duration=int(entry.get("duration") or 0),
                channel=entry.get("channel", entry.get("uploader", "")),
                webpage_url=entry.get("webpage_url", entry_url),
                platform=entry.get("extractor", "unknown"),
            )
        )

    return results


def get_stream_url(webpage_url: str) -> str | None:
    """Obtiene la stream URL directa via subprocess.

    Returns:
        Stream URL o None si falla.
    """
    if not is_available():
        return None

    cmd = _build_stream_cmd(webpage_url)

    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=15,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None

    if proc.returncode != 0:
        return None

    url = proc.stdout.strip().split("\n")[0].strip()
    return url if url.startswith("http") else None


def _cleanup_part_files(directory: str) -> None:
    """Elimina archivos .part dejados por yt-dlp al ser interrumpido."""
    try:
        for f in glob.glob(os.path.join(directory, "*.part")):
            os.remove(f)
    except OSError:
        pass


def download(
    url: str,
    output_path: str,
    fmt: str = "audio",
    quality: str = "480p",
    progress_hook: Any = None,
    resume: bool = False,
    cancel_event: threading.Event | None = None,
) -> tuple[bool, str]:
    """Descarga un archivo con yt-dlp via subprocess.

    Args:
        resume: ignorado (mantenido por compatibilidad de interfaz).
        cancel_event: evento de threading para cancelar la descarga.

    Returns:
        (success, filename) o (False, error_message)
    """
    if not is_available():
        return False, "yt-dlp no instalado"

    cmd = _build_download_cmd(url, output_path, fmt, quality)

    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1,
        )
    except FileNotFoundError:
        return False, "yt-dlp no encontrado en PATH"

    filename = ""

    for line in proc.stdout or []:
        if cancel_event and cancel_event.is_set():
            proc.kill()
            proc.wait()
            _cleanup_part_files(output_path)
            return False, "Cancelado por usuario"

        line = line.strip()
        if not line:
            continue

        if progress_hook is not None:
            hook_data: dict[str, Any] = {}

            if "[download]" in line:
                pct_str = line.split("%")[0].split()[-1]
                try:
                    pct = int(float(pct_str))
                    hook_data = {
                        "status": "downloading",
                        "downloaded_bytes": pct,
                        "total_bytes": 100,
                    }
                except (ValueError, IndexError):
                    pass

                if "Destination:" in line:
                    filename = line.split("Destination:")[-1].strip()
                elif "has already" in line:
                    filename = line.split("has already")[-1].strip()
            elif "[ExtractAudio]" in line:
                hook_data = {"status": "postprocessor"}
            elif "ERROR" in line or "error" in line.lower():
                hook_data = {"status": "error", "message": line}

            if hook_data:
                try:
                    progress_hook(hook_data)
                except Exception:
                    pass

    proc.wait()

    if proc.returncode != 0:
        stderr_text = ""
        try:
            _, stderr_text = proc.communicate(timeout=5)
        except Exception:
            pass
        return False, _classify_error(stderr_text or "Error desconocido")

    if not filename:
        title = url.split("/")[-1].split("?")[0][:50]
        ext = "mp3" if fmt == "audio" else "mp4"
        filename = f"{title}.{ext}"

    return True, filename


def format_duration(seconds: int) -> str:
    """Formatea duración en HH:MM:SS o MM:SS."""
    if seconds <= 0:
        return "--:--"
    h, remainder = divmod(seconds, 3600)
    m, s = divmod(remainder, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"
