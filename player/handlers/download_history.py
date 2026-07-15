"""Handler para la vista de historial de descargas."""
from __future__ import annotations

import curses
import os
from typing import TYPE_CHECKING

from .shared import _toast, _clamp_scroll, _page_size

if TYPE_CHECKING:
    from player.app import PlayerApp


def handle_download_history(app: PlayerApp, key: int) -> None:
    """Maneja teclas en la vista de historial de descargas."""
    history = app.download_history

    if key in (curses.KEY_LEFT, 127, curses.KEY_BACKSPACE, 27):
        app.current_view = app.V_WEB
        return

    if not history:
        return

    if key == ord("/"):
        app.dl_history_filter_mode = True
        app.dl_history_filter = ""
        app.dl_history_cursor = 0
        app.dl_history_scroll = 0
        app.dl_history_filtered = list(range(len(history)))
        return

    if app.dl_history_filter_mode:
        _handle_filter(app, key)
        return

    items = app.dl_history_filtered
    total = len(items)

    if key == curses.KEY_DOWN:
        app.dl_history_cursor = min(app.dl_history_cursor + 1, total - 1)
    elif key == curses.KEY_UP:
        app.dl_history_cursor = max(app.dl_history_cursor - 1, 0)
    elif key == curses.KEY_NPAGE:
        app.dl_history_cursor = min(
            app.dl_history_cursor + _page_size(app), total - 1
        )
    elif key == curses.KEY_PPAGE:
        app.dl_history_cursor = max(
            app.dl_history_cursor - _page_size(app), 0
        )
    elif key == ord("g"):
        app.dl_history_cursor = 0
    elif key == ord("G"):
        app.dl_history_cursor = max(0, total - 1)
    elif key == ord("d") or key == ord("D"):
        _redownload(app)
    elif key == ord("c"):
        _remove_from_history(app)
    elif key == ord("x"):
        _remove_and_delete(app)

    list_h = _get_list_h(app)
    app.dl_history_scroll = _clamp_scroll(
        app.dl_history_cursor, app.dl_history_scroll, list_h
    )


def _handle_filter(app: PlayerApp, key: int) -> None:
    """Maneja el modo filtro."""
    history = app.download_history
    if key == 27:
        app.dl_history_filter_mode = False
        app.dl_history_filter = ""
        app.dl_history_filtered = list(range(len(history)))
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
    if not query:
        app.dl_history_filtered = list(range(len(history)))
    else:
        app.dl_history_filtered = [
            i for i, e in enumerate(history)
            if query in e.title.lower() or query in e.platform.lower()
        ]
    app.dl_history_cursor = 0
    app.dl_history_scroll = 0


def _redownload(app: PlayerApp) -> None:
    """Re-descarga el item seleccionado."""
    from ..web import get_download_manager
    dm = get_download_manager()

    items = app.dl_history_filtered
    if app.dl_history_cursor >= len(items):
        return
    idx = items[app.dl_history_cursor]
    entry = app.download_history[idx]

    dm.add_download(
        entry.webpage_url, entry.title,
        entry.format, entry.quality, entry.platform,
    )
    _toast(app, f"Encolado: {entry.title}")


def _remove_from_history(app: PlayerApp) -> None:
    """Elimina el item del historial (sin borrar archivo)."""
    from ..downloads import remove_entry, save_history

    items = app.dl_history_filtered
    if app.dl_history_cursor >= len(items):
        return
    idx = items[app.dl_history_cursor]
    entry = remove_entry(app.download_history, idx)
    if entry:
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
    if entry.exists:
        try:
            os.remove(entry.file_path)
        except OSError:
            pass
    remove_entry(app.download_history, idx)
    save_history(app.download_history)
    _toast(app, f"Borrado: {entry.title}")
    _rebuild_filtered(app)


def _rebuild_filtered(app: PlayerApp) -> None:
    """Reconstruye la lista filtrada después de eliminar."""
    total = len(app.download_history)
    app.dl_history_filtered = list(range(total))
    app.dl_history_cursor = min(app.dl_history_cursor, max(0, total - 1))
    list_h = _get_list_h(app)
    app.dl_history_scroll = _clamp_scroll(
        app.dl_history_cursor, app.dl_history_scroll, list_h
    )


def _get_list_h(app: PlayerApp) -> int:
    """Altura usable para la lista."""
    h, _ = app.stdscr.getmaxyx()
    return h - 4
