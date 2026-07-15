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
    """Handler principal para V7 con modos: normal, search, download config, motor edit."""
    if app.web_motor_edit_mode:
        _handle_motor_edit(app, key)
        return

    if app.web_download_mode:
        _handle_download_mode(app, key)
        return

    if app.web_search_mode:
        _handle_search_input(app, key)
        return

    _handle_normal_mode(app, key)


def _cycle_platform(app: PlayerApp, direction: int) -> None:
    """Cicla plataformas con h/l."""
    total = len(app.web_platforms)
    if total == 0:
        return
    app.web_active_platform = (app.web_active_platform + direction) % total
    p = app.web_platforms[app.web_active_platform]
    _toast(app, f"Motor: {p.name}")


def _handle_normal_mode(app: PlayerApp, key: int) -> None:
    """Modo normal: navegar lista de resultados + gestión de motor inline."""
    total = len(app.web_results)

    if key == ord("/"):
        app.web_search_mode = True
        app.web_search_buf = ""
        curses.curs_set(1)
        curses.flushinp()
        return

    if key == 9:
        app.web_search_mode = True
        app.web_search_buf = ""
        curses.curs_set(1)
        curses.flushinp()
        return

    if key == ord("h"):
        _cycle_platform(app, -1)
        return
    elif key == ord("l"):
        _cycle_platform(app, 1)
        return
    elif key == ord("H"):
        app.current_view = app.V_DL_HISTORY
        app.dl_history_cursor = 0
        app.dl_history_scroll = 0
        app.dl_history_filter_mode = False
        app.dl_history_filter = ""
        app.dl_history_tab = 0
        app.dl_history_filtered = list(range(len(app.download_history)))
        return

    if key == ord("e"):
        _enter_motor_edit(app, is_new=False)
        return
    elif key == ord("a") and total == 0:
        _enter_motor_edit(app, is_new=True)
        return
    elif key == ord("d") and total == 0:
        _delete_platform(app)
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
        _handle_download_key(app, with_config=False)
        return
    elif key == ord("d") and total > 0:
        _handle_download_key(app, with_config=True)
        return
    elif key == ord("a") and total > 0:
        _add_to_queue(app)
        return
    elif key == ord("A") and total > 0:
        _add_to_queue_next(app)
        return
    elif key == ord("x"):
        _clear_results(app)
        return
    elif key == ord("c"):
        _cancel_download(app)
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


def _enter_motor_edit(app: PlayerApp, is_new: bool) -> None:
    """Abre editor de plataforma (nueva o existente)."""
    if is_new:
        app.web_motor_edit_mode = True
        app.web_motor_edit_is_new = True
        app.web_motor_edit_fields = {
            "name": "",
            "url": "https://",
            "search_pattern": "",
            "download_pattern": "",
            "search_prefix": "",
        }
    else:
        platforms = app.web_platforms
        if not platforms:
            return
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


def _delete_platform(app: PlayerApp) -> None:
    """Elimina la plataforma activa (no default)."""
    platforms = app.web_platforms
    if not platforms:
        return
    p = platforms[app.web_active_platform]
    if p.is_default:
        _toast(app, "No se puede eliminar plataforma default")
        return
    app.web_platforms = [x for x in platforms if x.name.lower() != p.name.lower()]
    _save_platforms(app)
    if app.web_active_platform >= len(app.web_platforms):
        app.web_active_platform = max(0, len(app.web_platforms) - 1)
    _toast(app, f"Eliminada: {p.name}")


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

    if key == 27:
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
    """Modo descarga: configuración cíclica con ←→/hl."""
    fields_order = ["format", "quality"]
    options: dict[str, list[str]] = {
        "format": ["audio", "video"],
        "quality": ["worst", "144p", "240p", "480p", "720p", "1080p", "best"],
    }

    if key == 27:
        app.web_download_mode = False
        app.current_view = app.V_WEB
    elif key in (ord("j"), curses.KEY_DOWN):
        app.web_download_cursor = min(
            app.web_download_cursor + 1, len(fields_order) - 1
        )
    elif key in (ord("k"), curses.KEY_UP):
        app.web_download_cursor = max(app.web_download_cursor - 1, 0)
    elif key in (ord("h"), curses.KEY_LEFT):
        field = fields_order[app.web_download_cursor]
        vals = options[field]
        cur_val = app.web_download_fields.get(field, vals[0])
        idx = vals.index(cur_val) if cur_val in vals else 0
        app.web_download_fields[field] = vals[(idx - 1) % len(vals)]
    elif key in (ord("l"), curses.KEY_RIGHT):
        field = fields_order[app.web_download_cursor]
        vals = options[field]
        cur_val = app.web_download_fields.get(field, vals[0])
        idx = vals.index(cur_val) if cur_val in vals else 0
        app.web_download_fields[field] = vals[(idx + 1) % len(vals)]
    elif key in (10, 13):
        app.web_download_mode = False
        _do_download(app)


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
    else:
        _toast(app, "No se pudo obtener contenido de la URL")


def _play_web_result(app: PlayerApp) -> None:
    """Reproduce un resultado de la lista (async: get_stream_url en thread)."""
    if app.web_cursor >= len(app.web_results):
        return
    result = app.web_results[app.web_cursor]

    app.web_playing_idx = app.web_cursor

    from .. import web

    def _run() -> None:
        stream_url = web.get_stream_url(result.webpage_url)
        if not stream_url:
            app.web_playing_idx = -1
            _toast(app, "No se puede reproducir — video restringido o no disponible")
            return

        from ..downloads import add_entry, save_history, TMP_DIR
        from ..stack import StackItem

        os.makedirs(TMP_DIR, exist_ok=True)
        entry = add_entry(
            app.download_history,
            title=result.title,
            url=stream_url,
            webpage_url=result.webpage_url,
            file_path="",
            fmt="audio",
            quality="480p",
            platform=result.platform,
            is_temp=True,
            duration=result.duration,
            channel=result.channel,
        )
        save_history(app.download_history)

        dm = web.get_download_manager()
        dm.add_download(
            result.webpage_url, result.title,
            "audio", "480p", result.platform,
            output_dir=TMP_DIR,
        )

        item = StackItem(path=stream_url, name=result.title)
        app.stack.items = [item]
        app.stack.playhead = 0
        app.audio.play_file(stream_url)
        app.current_view = app.V_LISTEN
        _toast(app, f"▶ {result.title}")

    t = threading.Thread(target=_run, daemon=True)
    t.start()


def _handle_download_key(app: PlayerApp, with_config: bool) -> None:
    """d/D toggle: inicia, pausa o reanuda segun estado del item."""
    if app.web_cursor >= len(app.web_results):
        return

    from .. import web
    dm = web.get_download_manager()
    result = app.web_results[app.web_cursor]
    dl_item = dm.find_by_url(result.webpage_url)

    if dl_item:
        if dl_item.state == web.DownloadState.DOWNLOADING:
            dm.pause_item(dl_item.id)
            _toast(app, "Descarga pausada (d/D para reanudar)")
            return
        if dl_item.state == web.DownloadState.PAUSED:
            dm.resume_item(dl_item.id)
            _toast(app, f"Reanudando: {result.title}")
            return
        if dl_item.state in (web.DownloadState.QUEUED, web.DownloadState.FAILED, web.DownloadState.STOPPED):
            pass

    if with_config:
        app.web_download_mode = True
        app.web_download_idx = app.web_cursor
        app.web_download_cursor = 0
        cfg = app.config
        app.web_download_fields = {
            "format": cfg.get("online_download_format", "audio"),
            "quality": cfg.get("online_download_quality", "480p"),
        }
        return

    cfg = app.config
    fmt = cfg.get("online_download_format", "audio")
    quality = cfg.get("online_download_quality", "480p")
    dm.add_download(result.webpage_url, result.title, fmt, quality, result.platform)
    _toast(app, f"Encolado: {result.title}")


def _do_download_direct(app: PlayerApp) -> None:
    """Ejecuta descarga directa con configuracion guardada."""
    idx = app.web_download_idx
    if idx >= len(app.web_results):
        return

    from .. import web
    dm = web.get_download_manager()
    result = app.web_results[idx]
    cfg = app.config
    fmt = cfg.get("online_download_format", "audio")
    quality = cfg.get("online_download_quality", "480p")
    dm.add_download(result.webpage_url, result.title, fmt, quality, result.platform)
    _toast(app, f"Encolado: {result.title}")


def _do_download(app: PlayerApp) -> None:
    """Ejecuta descarga con configuracion del editor."""
    idx = app.web_download_idx
    if idx >= len(app.web_results):
        return

    from .. import web
    dm = web.get_download_manager()
    result = app.web_results[idx]
    fmt = app.web_download_fields.get("format", "audio")
    quality = app.web_download_fields.get("quality", "480p")
    dm.add_download(result.webpage_url, result.title, fmt, quality, result.platform)
    _toast(app, f"Encolado: {result.title}")


def _add_to_queue(app: PlayerApp) -> None:
    """Añade resultado al final de la cola de reproducción (resuelve stream URL async)."""
    if app.web_cursor >= len(app.web_results):
        return
    result = app.web_results[app.web_cursor]
    from .. import web

    def _run() -> None:
        stream_url = web.get_stream_url(result.webpage_url)
        if not stream_url:
            _toast(app, "No se puede añadir — video no disponible")
            return
        from ..stack import StackItem
        item = StackItem(path=stream_url, name=result.title)
        app.stack.items.append(item)
        _toast(app, f"Añadido: {result.title}")

    import threading
    t = threading.Thread(target=_run, daemon=True)
    t.start()


def _add_to_queue_next(app: PlayerApp) -> None:
    """Añade resultado siguiente al playhead en la cola (resuelve stream URL async)."""
    if app.web_cursor >= len(app.web_results):
        return
    result = app.web_results[app.web_cursor]
    from .. import web

    def _run() -> None:
        stream_url = web.get_stream_url(result.webpage_url)
        if not stream_url:
            _toast(app, "No se puede añadir — video no disponible")
            return
        from ..stack import StackItem
        item = StackItem(path=stream_url, name=result.title)
        insert_pos = app.stack.playhead + 1
        app.stack.items.insert(insert_pos, item)
        _toast(app, f"Añadido después del actual: {result.title}")

    import threading
    t = threading.Thread(target=_run, daemon=True)
    t.start()


def _clear_results(app: PlayerApp) -> None:
    """Limpia la lista de resultados."""
    app.web_results = []
    app.web_cursor = 0
    app.web_scroll = 0
    _toast(app, "Lista limpiada")


def _cancel_download(app: PlayerApp) -> None:
    """Cancela la descarga del item actual."""
    from .. import web
    dm = web.get_download_manager()

    if app.web_cursor >= len(app.web_results):
        return

    result = app.web_results[app.web_cursor]
    dl_item = dm.find_by_url(result.webpage_url)
    if not dl_item:
        return

    if dm.stop_item(dl_item.id):
        _toast(app, "Descarga cancelada")


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
