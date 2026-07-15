"""Handler para la vista de historial unificado (descargas + streams)."""
from __future__ import annotations

import curses
import os
from typing import TYPE_CHECKING

from .shared import _toast, _clamp_scroll, _page_size, _navigate_cursor, _confirm

if TYPE_CHECKING:
    from player.app import PlayerApp

TAB_DOWNLOADS: int = 0
TAB_STREAMS: int = 1
TAB_NAMES: list[str] = ["Descargas", "Streams"]


def handle_download_history(app: PlayerApp, key: int) -> None:
    """Maneja teclas en la vista de historial unificado."""
    if key in (curses.KEY_LEFT, 127, curses.KEY_BACKSPACE, 27):
        app.current_view = app.V_WEB
        return

    if key == ord("["):
        _switch_tab(app, -1)
        return
    elif key == ord("]"):
        _switch_tab(app, 1)
        return

    items = _get_current_items(app)
    total = len(items)

    if not total:
        return

    if key == ord("/"):
        app.dl_history_filter_mode = True
        app.dl_history_filter = ""
        app.dl_history_cursor = 0
        app.dl_history_scroll = 0
        app.dl_history_filtered = list(range(total))
        return

    if app.dl_history_filter_mode:
        _handle_filter(app, key)
        return

    if key == curses.KEY_DOWN:
        app.dl_history_cursor = _navigate_cursor(app.dl_history_cursor, key, total, _page_size(app))
    elif key == curses.KEY_UP:
        app.dl_history_cursor = _navigate_cursor(app.dl_history_cursor, key, total, _page_size(app))
    elif key == curses.KEY_NPAGE:
        app.dl_history_cursor = _navigate_cursor(app.dl_history_cursor, key, total, _page_size(app))
    elif key == curses.KEY_PPAGE:
        app.dl_history_cursor = _navigate_cursor(app.dl_history_cursor, key, total, _page_size(app))
    elif key == ord("g"):
        app.dl_history_cursor = _navigate_cursor(app.dl_history_cursor, key, total, _page_size(app))
    elif key == ord("G"):
        app.dl_history_cursor = _navigate_cursor(app.dl_history_cursor, key, total, _page_size(app))
    elif key == ord("Enter") or key == 10 or key == 13:
        _play_entry(app)
    elif key == ord("d"):
        _re_download(app)
    elif key == ord("c"):
        _remove_from_history(app)
    elif key == ord("x"):
        _remove_and_delete(app)
    elif key == ord("X"):
        _clear_tab(app)

    list_h = _get_list_h(app)
    app.dl_history_scroll = _clamp_scroll(
        app.dl_history_cursor, app.dl_history_scroll, list_h
    )


def _switch_tab(app: PlayerApp, direction: int) -> None:
    """Cambia entre tabs Descargas/Streams."""
    app.dl_history_tab = (app.dl_history_tab + direction) % 2
    app.dl_history_cursor = 0
    app.dl_history_scroll = 0
    app.dl_history_filter_mode = False
    app.dl_history_filter = ""
    items = _get_current_items(app)
    app.dl_history_filtered = list(range(len(items)))


def _get_current_items(app: PlayerApp) -> list[int]:
    """Retorna índices del historial según tab activa."""
    from ..downloads import get_downloads, get_streams
    if app.dl_history_tab == TAB_STREAMS:
        return get_streams(app.download_history)
    return get_downloads(app.download_history)


def _rebuild_filtered(app: PlayerApp) -> None:
    """Reconstruye la lista filtrada después de eliminar."""
    items = _get_current_items(app)
    app.dl_history_filtered = list(range(len(items)))
    app.dl_history_cursor = min(app.dl_history_cursor, max(0, len(items) - 1))
    list_h = _get_list_h(app)
    app.dl_history_scroll = _clamp_scroll(
        app.dl_history_cursor, app.dl_history_scroll, list_h
    )


def _handle_filter(app: PlayerApp, key: int) -> None:
    """Maneja el modo filtro."""
    items = _get_current_items(app)
    if key == 27:
        app.dl_history_filter_mode = False
        app.dl_history_filter = ""
        app.dl_history_filtered = list(range(len(items)))
        app.dl_history_cursor = 0
        app.dl_history_scroll = 0
        return
    if key in (10, 13):
        app.dl_history_filter_mode = False
        return
    if key in (curses.KEY_BACKSPACE, 127):
        app.dl_history_filter = app.dl_history_filter[:-1]
    elif 32 <= key < 256:
        app.dl_history_filter += chr(key)

    query = app.dl_history_filter.lower()
    history = app.download_history
    if not query:
        app.dl_history_filtered = list(range(len(items)))
    else:
        app.dl_history_filtered = [
            i for i in items
            if query in history[i].title.lower()
            or query in history[i].platform.lower()
            or query in history[i].channel.lower()
        ]
    app.dl_history_cursor = 0
    app.dl_history_scroll = 0


def _play_entry(app: PlayerApp) -> None:
    """Reproduce una entrada del historial."""
    items = app.dl_history_filtered
    if app.dl_history_cursor >= len(items):
        return
    idx = items[app.dl_history_cursor]
    entry = app.download_history[idx]

    if not entry.exists:
        _toast(app, "Archivo no encontrado")
        return

    from ..stack import StackItem
    app.stack.items = [StackItem(path=entry.file_path, name=entry.title)]
    app.stack.playhead = 0
    app.audio.play_file(entry.file_path)
    app.current_view = app.V_LISTEN
    _toast(app, f"▶ {entry.title}")


def _re_download(app: PlayerApp) -> None:
    """Re-descarga (download) o re-busca (stream) el item seleccionado."""
    items = app.dl_history_filtered
    if app.dl_history_cursor >= len(items):
        return
    idx = items[app.dl_history_cursor]
    entry = app.download_history[idx]

    if entry.is_temp:
        app.web_search_buf = entry.title
        app.web_search_mode = True
        app.current_view = app.V_WEB
        curses.curs_set(1)
        _toast(app, f"Buscando: {entry.title}")
        from .webexplorer import _do_search
        _do_search(app, entry.title)
    else:
        from ..web import get_download_manager
        dm = get_download_manager()
        dm.add_download(
            entry.webpage_url, entry.title,
            entry.format, entry.quality, entry.platform,
        )
        _toast(app, f"Encolado: {entry.title}")


def _remove_from_history(app: PlayerApp) -> None:
    """Elimina el item del historial. Si es temp, borra el archivo."""
    from ..downloads import remove_entry, save_history

    items = app.dl_history_filtered
    if app.dl_history_cursor >= len(items):
        return
    idx = items[app.dl_history_cursor]
    entry = app.download_history[idx]

    if entry.is_temp and entry.file_path and os.path.isfile(entry.file_path):
        try:
            os.remove(entry.file_path)
        except OSError:
            pass

    remove_entry(app.download_history, idx)
    save_history(app.download_history)
    _toast(app, f"Eliminado: {entry.title}")
    _rebuild_filtered(app)


def _remove_and_delete(app: PlayerApp) -> None:
    """Elimina del historial + borra el archivo."""
    from ..downloads import remove_entry, save_history

    items = app.dl_history_filtered
    if app.dl_history_cursor >= len(items):
        return
    idx = items[app.dl_history_cursor]
    entry = app.download_history[idx]

    def _do() -> None:
        if entry.exists:
            try:
                os.remove(entry.file_path)
            except OSError:
                pass
        remove_entry(app.download_history, idx)
        save_history(app.download_history)
        _toast(app, f"Borrado: {entry.title}")
        _rebuild_filtered(app)

    _confirm(app, f"Borrar archivo: {entry.title}?", _do)


def _clear_tab(app: PlayerApp) -> None:
    """Limpia todas las entradas del tab activo + borra archivos."""
    from ..downloads import save_history, get_downloads, get_streams

    history = app.download_history
    if app.dl_history_tab == TAB_STREAMS:
        indices = get_streams(history)
        label = "streams"
    else:
        indices = get_downloads(history)
        label = "descargas"

    def _do() -> None:
        deleted = 0
        for i in reversed(indices):
            entry = history[i]
            if entry.exists:
                try:
                    os.remove(entry.file_path)
                    deleted += 1
                except OSError:
                    pass
            history.pop(i)
        save_history(history)
        _toast(app, f"Limpiados {deleted} {label}")
        _rebuild_filtered(app)

    _confirm(app, f"Limpiar todo el tab de {label}?", _do)


def _get_list_h(app: PlayerApp) -> int:
    """Altura usable para la lista."""
    h, _ = app.stdscr.getmaxyx()
    return h - 4
