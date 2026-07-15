"""yt-dlp wrapper para Web Explorer — subprocess approach."""
from __future__ import annotations

import enum
import glob
import json
import os
import queue
import signal
import subprocess
import threading
from dataclasses import dataclass, field
from typing import Any, Callable

from .config import load as _load_config


_YTDLP_BIN = "yt-dlp"
_YTDLP_COMMON = [_YTDLP_BIN, "--no-warnings", "--ignore-errors", "--no-colors"]
_ytdlp_available: bool | None = None


class DownloadState(enum.Enum):
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


@dataclass
class DownloadItem:
    """Item de descarga con estado independiente."""
    id: int
    url: str
    title: str
    fmt: str = "audio"
    quality: str = "480p"
    state: DownloadState = DownloadState.QUEUED
    progress: float = 0.0
    file_path: str = ""
    error: str = ""
    _process: subprocess.Popen[str] | None = None
    _cancel_event: threading.Event = field(default_factory=threading.Event)
    _partial_path: str = ""


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
    cmd.append("--continue")

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


_next_dl_id = 0
_next_dl_lock = threading.Lock()


def _alloc_dl_id() -> int:
    global _next_dl_id
    with _next_dl_lock:
        _next_dl_id += 1
        return _next_dl_id


class DownloadManager:
    """Gestiona cola de descargas con estado por-item y concurrencia limitada."""

    def __init__(self, max_concurrent: int = 3) -> None:
        self._items: list[DownloadItem] = []
        self._queue: queue.Queue[DownloadItem] = queue.Queue()
        self._active_count = 0
        self._active_lock = threading.Lock()
        self._max_concurrent = max_concurrent
        self._running = True
        self._lock = threading.Lock()
        self._callbacks: list[Callable[[], None]] = []
        self._worker_thread = threading.Thread(
            target=self._worker_loop, daemon=True,
        )
        self._worker_thread.start()

    def add_callback(self, cb: Callable[[], None]) -> None:
        self._callbacks.append(cb)

    def _notify(self) -> None:
        for cb in self._callbacks:
            try:
                cb()
            except Exception:
                pass

    def add_download(
        self, url: str, title: str, fmt: str = "audio",
        quality: str = "480p",
    ) -> DownloadItem:
        item = DownloadItem(
            id=_alloc_dl_id(), url=url, title=title,
            fmt=fmt, quality=quality,
        )
        with self._lock:
            self._items.append(item)
        self._queue.put(item)
        self._notify()
        return item

    def pause_item(self, item_id: int) -> bool:
        with self._lock:
            item = self._find(item_id)
            if not item or item.state != DownloadState.DOWNLOADING:
                return False
            if item._process:
                try:
                    item._process.send_signal(signal.SIGSTOP)
                except (OSError, ProcessLookupError):
                    return False
            item.state = DownloadState.PAUSED
        self._notify()
        return True

    def resume_item(self, item_id: int) -> bool:
        with self._lock:
            item = self._find(item_id)
            if not item or item.state != DownloadState.PAUSED:
                return False
            if item._process:
                try:
                    item._process.send_signal(signal.SIGCONT)
                except (OSError, ProcessLookupError):
                    return False
            item.state = DownloadState.DOWNLOADING
        self._notify()
        return True

    def stop_item(self, item_id: int) -> bool:
        with self._lock:
            item = self._find(item_id)
            if not item:
                return False
            if item.state in (DownloadState.COMPLETED, DownloadState.STOPPED):
                return False
            if item.state == DownloadState.QUEUED:
                item.state = DownloadState.STOPPED
                self._notify()
                return True
            if item._process:
                item._cancel_event.set()
                try:
                    item._process.terminate()
                    item._process.wait(timeout=3)
                except Exception:
                    try:
                        item._process.kill()
                    except Exception:
                        pass
                if item._partial_path:
                    _cleanup_single_file(item._partial_path)
            item.state = DownloadState.STOPPED
            item.progress = 0
        self._notify()
        return True

    def get_items(self) -> list[DownloadItem]:
        with self._lock:
            return list(self._items)

    def get_item(self, item_id: int) -> DownloadItem | None:
        with self._lock:
            return self._find(item_id)

    def active_count(self) -> int:
        with self._active_lock:
            return self._active_count

    def pending_count(self) -> int:
        return self._queue.qsize()

    def has_active(self) -> bool:
        with self._active_lock:
            return self._active_count > 0
        return False

    def _find(self, item_id: int) -> DownloadItem | None:
        for item in self._items:
            if item.id == item_id:
                return item
        return None

    def _worker_loop(self) -> None:
        while self._running:
            try:
                item = self._queue.get(timeout=1)
            except queue.Empty:
                continue
            if item.state == DownloadState.STOPPED:
                continue
            while self._active_count >= self._max_concurrent:
                if not self._running:
                    return
                threading.Event().wait(0.5)
            with self._active_lock:
                self._active_count += 1
            t = threading.Thread(
                target=self._download_worker, args=(item,), daemon=True,
            )
            t.start()

    def _download_worker(self, item: DownloadItem) -> None:
        cfg = _load_config()
        music_dir = cfg.get("music_dir", os.path.expanduser("~/Music"))
        os.makedirs(music_dir, exist_ok=True)
        cmd = _build_download_cmd(item.url, music_dir, item.fmt, item.quality)
        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
            )
            item._process = proc
            item.state = DownloadState.DOWNLOADING
            self._notify()
            filename = ""
            for line in proc.stdout or []:
                if item._cancel_event.is_set():
                    proc.kill()
                    proc.wait()
                    return
                line = line.strip()
                if not line:
                    continue
                if "[download]" in line:
                    pct_str = line.split("%")[0].split()[-1]
                    try:
                        item.progress = float(pct_str)
                        self._notify()
                    except (ValueError, IndexError):
                        pass
                    if "Destination:" in line:
                        filename = line.split("Destination:")[-1].strip()
                        item._partial_path = filename + ".part"
                    elif "has already" in line:
                        filename = line.split("has already")[-1].strip()
                elif "[ExtractAudio]" in line:
                    pass
                elif "ERROR" in line or "error" in line.lower():
                    item.error = line
            proc.wait()
            if item._cancel_event.is_set():
                return
            if proc.returncode == 0:
                item.state = DownloadState.COMPLETED
                item.progress = 100
                item.file_path = filename
            else:
                item.state = DownloadState.FAILED
                item.error = item.error or "Error desconocido"
        except Exception as e:
            item.state = DownloadState.FAILED
            item.error = str(e)
        finally:
            item._process = None
            with self._active_lock:
                self._active_count -= 1
            self._notify()

    def shutdown(self) -> None:
        self._running = False
        with self._lock:
            for item in self._items:
                if item.state in (DownloadState.DOWNLOADING, DownloadState.PAUSED):
                    self.stop_item(item.id)


def _cleanup_single_file(path: str) -> None:
    """Elimina un archivo específico."""
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


def _cleanup_part_files(directory: str) -> None:
    """Elimina archivos .part dejados por yt-dlp al ser interrumpido."""
    try:
        for f in glob.glob(os.path.join(directory, "*.part")):
            os.remove(f)
    except OSError:
        pass


_download_manager: DownloadManager | None = None


def get_download_manager() -> DownloadManager:
    """Retorna la instancia global del DownloadManager (singleton)."""
    global _download_manager
    if _download_manager is None:
        cfg = _load_config()
        max_dl = cfg.get("online_download_max", 3)
        _download_manager = DownloadManager(max_concurrent=max_dl)
    return _download_manager
