"""Handler para la vista Web Explorer (V7)."""
from __future__ import annotations

import curses
import os
import threading
from typing import Any, TYPE_CHECKING

from .shared import _toast, _clamp_scroll, _prompt

if TYPE_CHECKING:
    from player.app import PlayerApp
    from player.platforms import Platform


def handle_web(app: PlayerApp, key: int) -> None:
    """Handler principal para V7 con 3 modos."""
    if app.web_motor_edit_mode:
        _handle_motor_edit(app, key)
        return

    if app.web_download_mode:
        _handle_download_mode(app, key)
        return

    if app.web_motor_mode:
        _handle_motor_mode(app, key)
        return

    if app.web_search_mode:
        _handle_search_input(app, key)
        return

    _handle_normal_mode(app, key)


def _handle_normal_mode(app: PlayerApp, key: int) -> None:
    """Modo normal: navegar lista de resultados."""
    total = len(app.web_results)

    if key == ord("/"):
        app.web_search_mode = True
        app.web_search_buf = ""
        curses.curs_set(1)
        curses.flushinp()
        return

    if key == 9:
        app.web_motor_mode = True
        return

    if key in (curses.KEY_DOWN, ord("j")):
        app.web_cursor = min(app.web_cursor + 1, max(0, total - 1))
    elif key in (curses.KEY_UP, ord("k")):
        app.web_cursor = max(app.web_cursor - 1, 0)
    elif key == ord("g"):
        app.web_cursor = 0
    elif key == ord("G"):
        app.web_cursor = max(0, total - 1)
    elif key in (curses.KEY_NPAGE,):
        h, _ = app.stdscr.getmaxyx()
        page = h - 8
        app.web_cursor = min(app.web_cursor + page, max(0, total - 1))
    elif key in (curses.KEY_PPAGE,):
        h, _ = app.stdscr.getmaxyx()
        page = h - 8
        app.web_cursor = max(app.web_cursor - page, 0)
    elif key in (10, 13) and total > 0:
        _play_web_result(app)
        return
    elif key == ord("D") and total > 0:
        _download_web_result(app, with_config=False)
        return
    elif key == ord("d") and total > 0:
        _download_web_result(app, with_config=True)
        return
    elif key in (ord("A"), ord("a")) and total > 0:
        _add_to_queue(app)
        return
    elif key == ord("x"):
        _clear_results(app)
        return
    elif key == 27:
        app.current_view = app.V_LISTEN
        curses.flushinp()
        return

    h, _ = app.stdscr.getmaxyx()
    list_h = h - 8
    app.web_scroll = _clamp_scroll(app.web_cursor, app.web_scroll, list_h)


def _handle_search_input(app: PlayerApp, key: int) -> None:
    """Modo search: input de búsqueda."""
    if key == 27:
        app.web_search_mode = False
        curses.curs_set(0)
        return

    if key == 9:
        app.web_search_mode = False
        app.web_motor_mode = True
        curses.curs_set(0)
        return

    if key in (10, 13):
        app.web_search_mode = False
        curses.curs_set(0)
        query = app.web_search_buf.strip()
        if not query:
            return
        app.web_last_query = query
        _add_to_history(app, query)
        _do_search(app, query)
        return

    if key in (curses.KEY_BACKSPACE, 127):
        app.web_search_buf = app.web_search_buf[:-1]
    elif 32 <= key <= 126:
        app.web_search_buf += chr(key)


def _handle_motor_mode(app: PlayerApp, key: int) -> None:
    """Modo motor: gestionar plataformas."""
    platforms = app.web_platforms
    total = len(platforms)

    if key == 9:
        app.web_motor_mode = False
        app.web_search_mode = True
        app.web_search_buf = ""
        curses.curs_set(1)
        curses.flushinp()
        return

    if key == 27:
        app.web_motor_mode = False
        return

    if key in (curses.KEY_DOWN, ord("j")):
        app.web_active_platform = min(app.web_active_platform + 1, max(0, total - 1))
    elif key in (curses.KEY_UP, ord("k")):
        app.web_active_platform = max(app.web_active_platform - 1, 0)
    elif key == ord("a"):
        app.web_motor_edit_mode = True
        app.web_motor_edit_is_new = True
        app.web_motor_edit_fields = {
            "name": "",
            "url": "https://",
            "search_pattern": "",
            "download_pattern": "",
            "search_prefix": "",
        }
        app.web_motor_edit_cursor = 0
        app.web_motor_edit_buf = ""
        app.web_motor_edit_cursor_pos = 0
        return
    elif key == ord("e") and total > 0:
        p = platforms[app.web_active_platform]
        app.web_motor_edit_mode = True
        app.web_motor_edit_is_new = False
        app.web_motor_edit_fields = {
            "name": p.name,
            "url": p.url,
            "search_pattern": p.search_pattern,
            "download_pattern": p.download_pattern,
            "search_prefix": p.search_prefix,
        }
        app.web_motor_edit_cursor = 0
        app.web_motor_edit_buf = ""
        app.web_motor_edit_cursor_pos = 0
        return
    elif key == ord("d") and total > 0:
        p = platforms[app.web_active_platform]
        if not p.is_default:
            app.web_platforms = [
                x for x in platforms if x.name.lower() != p.name.lower()
            ]
            _save_platforms(app)
            if app.web_active_platform >= len(app.web_platforms):
                app.web_active_platform = max(0, len(app.web_platforms) - 1)
            _toast(app, f"Eliminada: {p.name}")
        else:
            _toast(app, "No se puede eliminar plataforma default")
        return
    elif key in (10, 13) and total > 0:
        app.web_motor_mode = False
        _toast(app, f"Motor: {platforms[app.web_active_platform].name}")
        return

    h, _ = app.stdscr.getmaxyx()
    list_h = h - 6
    app.web_scroll = _clamp_scroll(app.web_active_platform, app.web_scroll, list_h)


def _handle_motor_edit(app: PlayerApp, key: int) -> None:
    """Editor de plataformas (patrón meta_editor)."""
    fields_order = ["name", "url", "search_pattern", "download_pattern", "search_prefix"]
    labels = {
        "name": "Nombre",
        "url": "URL",
        "search_pattern": "Patrón búsqueda",
        "download_pattern": "Patrón descarga",
        "search_prefix": "Search prefix",
    }

    if app.web_motor_edit_editing:
        cur = app.web_motor_edit_cursor_pos
        buf = app.web_motor_edit_buf

        if key == 27:
            app.web_motor_edit_editing = False
        elif key in (10, 13):
            field = fields_order[app.web_motor_edit_cursor]
            app.web_motor_edit_fields[field] = buf.strip()
            app.web_motor_edit_editing = False
        elif key == curses.KEY_LEFT:
            if cur > 0:
                app.web_motor_edit_cursor_pos = cur - 1
        elif key == curses.KEY_RIGHT:
            if cur < len(buf):
                app.web_motor_edit_cursor_pos = cur + 1
        elif key in (127, curses.KEY_BACKSPACE):
            if cur > 0:
                app.web_motor_edit_buf = buf[: cur - 1] + buf[cur:]
                app.web_motor_edit_cursor_pos = cur - 1
        elif 32 <= key <= 126 and len(buf) < 60:
            app.web_motor_edit_buf = buf[:cur] + chr(key) + buf[cur:]
            app.web_motor_edit_cursor_pos = cur + 1
        return

    if key in (ord("q"), 27):
        app.web_motor_edit_mode = False
    elif key == ord("s"):
        _save_motor_edit(app)
    elif key in (ord("j"), curses.KEY_DOWN):
        app.web_motor_edit_cursor = min(
            app.web_motor_edit_cursor + 1, len(fields_order) - 1
        )
    elif key in (ord("k"), curses.KEY_UP):
        app.web_motor_edit_cursor = max(app.web_motor_edit_cursor - 1, 0)
    elif key in (10, 13):
        app.web_motor_edit_editing = True
        field = fields_order[app.web_motor_edit_cursor]
        app.web_motor_edit_buf = app.web_motor_edit_fields.get(field, "")
        app.web_motor_edit_cursor_pos = len(app.web_motor_edit_buf)


def _save_motor_edit(app: PlayerApp) -> None:
    """Guarda la edición de plataforma."""
    from ..platforms import Platform, save_platforms

    fields = app.web_motor_edit_fields
    name = fields.get("name", "").strip()
    if not name:
        _toast(app, "Nombre requerido")
        return

    url = fields.get("url", "").strip()
    if not url:
        _toast(app, "URL requerida")
        return

    download_pattern = fields.get("download_pattern", "").strip()
    if not download_pattern:
        _toast(app, "Patrón descarga requerido")
        return

    new_platform = Platform(
        name=name,
        url=url,
        search_pattern=fields.get("search_pattern", "").strip(),
        download_pattern=download_pattern,
        search_prefix=fields.get("search_prefix", "").strip(),
        downloads=0,
        is_default=False,
    )

    if app.web_motor_edit_is_new:
        existing = [p.name.lower() for p in app.web_platforms]
        if name.lower() in existing:
            _toast(app, "Plataforma ya existe")
            return
        app.web_platforms.append(new_platform)
    else:
        old_name = app.web_motor_edit_fields.get("name", "")
        for i, p in enumerate(app.web_platforms):
            if p.name.lower() == old_name.lower():
                new_platform.is_default = p.is_default
                new_platform.downloads = p.downloads
                app.web_platforms[i] = new_platform
                break

    _save_platforms(app)
    app.web_motor_edit_mode = False
    _toast(app, f"Guardada: {name}")


def _handle_download_mode(app: PlayerApp, key: int) -> None:
    """Modo descarga: configuración de descarga."""
    fields_order = ["format", "quality"]
    labels = {"format": "Formato", "quality": "Calidad"}

    if app.web_download_editing:
        cur = app.web_download_cursor_pos
        buf = app.web_download_buf

        if key == 27:
            app.web_download_mode = False
        elif key in (10, 13):
            field = fields_order[app.web_download_cursor]
            app.web_download_fields[field] = buf.strip()
            app.web_download_mode = False
            _do_download(app)
        elif key == curses.KEY_LEFT:
            if cur > 0:
                app.web_download_cursor_pos = cur - 1
        elif key == curses.KEY_RIGHT:
            if cur < len(buf):
                app.web_download_cursor_pos = cur + 1
        elif key in (127, curses.KEY_BACKSPACE):
            if cur > 0:
                app.web_download_buf = buf[: cur - 1] + buf[cur:]
                app.web_download_cursor_pos = cur - 1
        elif 32 <= key <= 126 and len(buf) < 20:
            app.web_download_buf = buf[:cur] + chr(key) + buf[cur:]
            app.web_download_cursor_pos = cur + 1
        return

    if key in (ord("q"), 27):
        app.web_download_mode = False
    elif key in (ord("j"), curses.KEY_DOWN):
        app.web_download_cursor = min(
            app.web_download_cursor + 1, len(fields_order) - 1
        )
    elif key in (ord("k"), curses.KEY_UP):
        app.web_download_cursor = max(app.web_download_cursor - 1, 0)
    elif key in (10, 13):
        app.web_download_editing = True
        field = fields_order[app.web_download_cursor]
        app.web_download_buf = app.web_download_fields.get(field, "")
        app.web_download_cursor_pos = len(app.web_download_buf)


def _do_search(app: PlayerApp, query: str) -> None:
    """Ejecuta búsqueda en la plataforma activa."""
    from .. import web
    from ..platforms import load_platforms, get_search_prefix
    from ..config import load as _load_config

    platforms = load_platforms()
    cfg = _load_config()
    max_results = cfg.get("online_max_results", 5)

    platform = platforms[app.web_active_platform] if app.web_platforms else None
    if not platform:
        _toast(app, "Sin plataformas configuradas")
        return

    prefix = platform.search_prefix
    if not prefix:
        if query.startswith("http://") or query.startswith("https://"):
            _handle_url_input(app, query, platform)
        else:
            _toast(app, f"{platform.name} no tiene búsqueda nativa. Ingresá una URL completa.")
        return

    app.web_loading = True

    def _run() -> None:
        try:
            results = web.search(query, max_results, search_prefix=prefix)
        except RuntimeError as e:
            results = []
            app.web_loading = False
            _toast(app, str(e))
            return

        app.web_results = results
        app.web_cursor = 0
        app.web_scroll = 0
        app.web_result_status = ["[-]"] * len(results)
        app.web_loading = False
        if not results:
            _toast(app, f"Sin resultados: {query}")

    t = threading.Thread(target=_run, daemon=True)
    t.start()


def _handle_url_input(app: PlayerApp, url: str, platform: Platform) -> None:
    """Maneja URL directa para plataformas sin búsqueda."""
    from .. import web

    try:
        results = web.search(url, 1, search_prefix="")
    except Exception as e:
        _toast(app, f"Error: {e}")
        return

    if results:
        app.web_results = results
        app.web_cursor = 0
        app.web_scroll = 0
        app.web_result_status = ["[-]"] * len(results)
    else:
        _toast(app, "No se pudo obtener contenido de la URL")


def _play_web_result(app: PlayerApp) -> None:
    """Reproduce un resultado de la lista."""
    if app.web_cursor >= len(app.web_results):
        return
    result = app.web_results[app.web_cursor]

    app.web_result_status[app.web_cursor] = "[►]"

    from ..stack import StackItem
    item = StackItem(path=result.url, name=result.title)
    app.stack.items = [item]
    app.stack.playhead = 0
    app.audio.play_file(result.url)
    app.current_view = app.V_LISTEN
    _toast(app, f"▶ {result.title}")


def _download_web_result(app: PlayerApp, with_config: bool) -> None:
    """Descarga un resultado de la lista."""
    if app.web_cursor >= len(app.web_results):
        return

    if len(app.web_download_queue) >= app.web_download_max:
        result = app.web_results[app.web_cursor]
        app.web_result_status[app.web_cursor] = "[Q]"
        _toast(app, f"Cola llena: {result.title} en espera")
        return

    if with_config:
        app.web_download_mode = True
        app.web_download_cursor = 0
        app.web_download_editing = False
        cfg = app.config
        app.web_download_fields = {
            "format": cfg.get("online_download_format", "audio"),
            "quality": cfg.get("online_download_quality", "480p"),
        }
        return

    _do_download_direct(app)


def _do_download_direct(app: PlayerApp) -> None:
    """Ejecuta descarga directa con configuración guardada."""
    if app.web_cursor >= len(app.web_results):
        return

    result = app.web_results[app.web_cursor]
    cfg = app.config
    fmt = cfg.get("online_download_format", "audio")
    quality = cfg.get("online_download_quality", "480p")

    _start_download(app, result, fmt, quality)


def _do_download(app: PlayerApp) -> None:
    """Ejecuta descarga con configuración del editor."""
    if app.web_cursor >= len(app.web_results):
        return

    result = app.web_results[app.web_cursor]
    fmt = app.web_download_fields.get("format", "audio")
    quality = app.web_download_fields.get("quality", "480p")

    _start_download(app, result, fmt, quality)


def _start_download(
    app: PlayerApp, result: Any, fmt: str, quality: str
) -> None:
    """Inicia una descarga en background thread."""
    from .. import web
    from ..config import load as _load_config
    from ..file_utils import list_dir as _list_dir

    cfg = _load_config()
    music_dir = cfg.get("music_dir", os.path.expanduser("~/Music"))

    if not os.path.exists(music_dir):
        os.makedirs(music_dir, exist_ok=True)

    idx = app.web_cursor
    app.web_result_status[idx] = "[D]"
    app.web_download_queue.append(result)

    def _progress(d: dict[str, Any]) -> None:
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            current = d.get("downloaded_bytes") or 0
            if total > 0:
                pct = int(current * 100 / total)
                app.web_result_status[idx] = f"[{pct:2d}%]"
        elif d.get("status") == "finished":
            app.web_result_status[idx] = "[✓]"

    def _run() -> None:
        success, msg = web.download(
            result.webpage_url, music_dir, fmt, quality, progress_hook=_progress
        )

        if success:
            app.web_result_status[idx] = "[✓]"
            _toast(app, f"Descargado: {msg}")
            if app.current_dir == os.path.realpath(music_dir):
                app.entries = _list_dir(app.current_dir)
        else:
            app.web_result_status[idx] = "[!]"
            _toast(app, f"Error: {msg}")

        if result in app.web_download_queue:
            app.web_download_queue.remove(result)

    t = threading.Thread(target=_run, daemon=True)
    t.start()


def _add_to_queue(app: PlayerApp) -> None:
    """Añade resultado a la cola de reproducción."""
    if app.web_cursor >= len(app.web_results):
        return
    result = app.web_results[app.web_cursor]
    from ..stack import StackItem
    item = StackItem(path=result.url, name=result.title)
    app.stack.items.append(item)
    _toast(app, f"Añadido: {result.title}")


def _clear_results(app: PlayerApp) -> None:
    """Limpia la lista de resultados."""
    app.web_results = []
    app.web_cursor = 0
    app.web_scroll = 0
    app.web_result_status = []
    _toast(app, "Lista limpiada")


def _add_to_history(app: PlayerApp, query: str) -> None:
    """Añade búsqueda al historial."""
    history: list[str] = app.config.get("online_search_history", [])
    history = [h for h in history if h != query]
    history.insert(0, query)
    app.config["online_search_history"] = history[:10]
    from ..config import save as _save_config
    _save_config(app.config)


def _save_platforms(app: PlayerApp) -> None:
    """Guarda plataformas al archivo."""
    from ..platforms import save_platforms
    save_platforms(app.web_platforms)
