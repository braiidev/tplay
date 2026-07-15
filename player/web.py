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
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from .config import load as _load_config


_YTDLP_BIN = "yt-dlp"
_YTDLP_COMMON = [_YTDLP_BIN, "--no-warnings", "--ignore-errors", "--no-colors"]
_ytdlp_available: bool | None = None
_node_available: bool | None = None


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
    platform: str = ""
    output_dir: str = ""
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


def _has_node() -> bool:
    """Verifica si Node.js está disponible (cached)."""
    global _node_available
    if _node_available is not None:
        return _node_available
    try:
        r = subprocess.run(
            ["node", "--version"],
            capture_output=True, text=True, timeout=3,
        )
        _node_available = r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        _node_available = False
    return _node_available


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
    cmd.append("--")
    cmd.append(f"{search_prefix}{max_results}:{query}")
    return cmd

def _build_stream_cmd(
    webpage_url: str,
    platform_name: str | None = None,
) -> list[str]:
    """Construye comando para obtener stream URL."""
    cmd = list(_YTDLP_COMMON)
    cmd.extend(["--get-url", "-f", "bestaudio/best"])
    if _has_node():
        cmd.extend(["--js-runtime", "node"])

    cfg = _load_config()
    cookies = cfg.get("online_cookies", "none")
    if cookies and cookies != "none":
        if cookies.startswith("file:"):
            cmd.extend(["--cookies", cookies[5:]])
        else:
            cmd.extend(["--cookies-from-browser", cookies])

    cmd.append("--")
    cmd.append(webpage_url)
    return cmd


def _build_download_cmd(
    webpage_url: str,
    output_path: str,
    fmt: str = "audio",
    quality: str = "480p",
) -> list[str]:
    """Construye comando para descarga."""
    cfg = _load_config()
    cmd = list(_YTDLP_COMMON)
    cmd.append("--continue")
    if _has_node():
        cmd.extend(["--js-runtime", "node"])

    cookies = cfg.get("online_cookies", "none")
    if cookies and cookies != "none":
        if cookies.startswith("file:"):
            cmd.extend(["--cookies", cookies[5:]])
        else:
            cmd.extend(["--cookies-from-browser", cookies])

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

    cmd.append("--")
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

    @property
    def items(self) -> list[DownloadItem]:
        with self._lock:
            return list(self._items)

    @property
    def max_concurrent(self) -> int:
        return self._max_concurrent

    @max_concurrent.setter
    def max_concurrent(self, val: int) -> None:
        self._max_concurrent = val

    def _notify(self) -> None:
        cbs = list(self._callbacks)
        for cb in cbs:
            try:
                cb()
            except Exception:
                pass

    def add_download(
        self, url: str, title: str, fmt: str = "audio",
        quality: str = "480p", platform: str = "",
        output_dir: str = "",
    ) -> DownloadItem:
        item = DownloadItem(
            id=_alloc_dl_id(), url=url, title=title,
            fmt=fmt, quality=quality, platform=platform,
            output_dir=output_dir,
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

    def find_by_url(self, url: str) -> DownloadItem | None:
        """Busca un item por URL (match exacto o webpage_url)."""
        with self._lock:
            for item in reversed(self._items):
                if item.url == url:
                    return item
            return None

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
            while True:
                with self._active_lock:
                    if self._active_count < self._max_concurrent:
                        break
                if not self._running:
                    return
                time.sleep(0.5)
            with self._active_lock:
                self._active_count += 1
            t = threading.Thread(
                target=self._download_worker, args=(item,), daemon=True,
            )
            t.start()

    def _download_worker(self, item: DownloadItem) -> None:
        cfg = _load_config()
        music_dir = item.output_dir or cfg.get("music_dir", os.path.expanduser("~/Music"))
        os.makedirs(music_dir, exist_ok=True)
        cmd = _build_download_cmd(item.url, music_dir, item.fmt, item.quality)
        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, bufsize=1,
            )
            item._process = proc
            item.state = DownloadState.DOWNLOADING
            self._notify()
            filename = ""
            all_output: list[str] = []
            for line in proc.stdout or []:
                if item._cancel_event.is_set():
                    proc.kill()
                    proc.wait()
                    return
                line = line.strip()
                all_output.append(line)
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
            stderr_out = proc.stderr.read() if proc.stderr else ""
            proc.wait()
            if item._cancel_event.is_set():
                return
            if proc.returncode == 0:
                item.state = DownloadState.COMPLETED
                item.progress = 100
                item.file_path = filename
            else:
                item.state = DownloadState.FAILED
                err_msg = item.error or stderr_out.strip() or "Error desconocido"
                item.error = _classify_error(err_msg)
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
        to_stop: list[int] = []
        with self._lock:
            for item in self._items:
                if item.state in (DownloadState.DOWNLOADING, DownloadState.PAUSED):
                    to_stop.append(item.id)
        for item_id in to_stop:
            self.stop_item(item_id)
        cfg = _load_config()
        music_dir = cfg.get("music_dir", os.path.expanduser("~/Music"))
        _cleanup_part_files(music_dir)


def item_status_str(item: DownloadItem) -> str:
    """Convierte estado de DownloadItem a string de display."""
    if item.state == DownloadState.QUEUED:
        return "[Q]"
    if item.state == DownloadState.DOWNLOADING:
        return f"[{int(item.progress):2d}%]"
    if item.state == DownloadState.PAUSED:
        return "[P]"
    if item.state == DownloadState.COMPLETED:
        return "[✓]"
    if item.state == DownloadState.FAILED:
        return "[!]"
    if item.state == DownloadState.STOPPED:
        return "[C]"
    return "[-]"


def get_result_status(
    results: list[WebResult], idx: int, playing_idx: int,
) -> str:
    """Retorna string de display para un resultado de búsqueda."""
    if idx == playing_idx:
        return "[►]"
    dm = get_download_manager()
    r = results[idx]
    dl_item = dm.find_by_url(r.webpage_url)
    if dl_item:
        return item_status_str(dl_item)
    return "[-]"


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
