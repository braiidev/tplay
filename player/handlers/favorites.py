from __future__ import annotations

import curses
import os
from typing import TYPE_CHECKING

from .shared import _toast, _clamp_scroll, _toggle_favorite

if TYPE_CHECKING:
    from player.app import PlayerApp

from ..favorites import save_favorites
from ..stack import StackItem


def handle_favorites(app: PlayerApp, key: int) -> None:
    if not app.favorites:
        if key in (10, 13, ord("d"), ord("a"), ord("A")):
            _toast(app, "Sin favoritos")
        return

    if key == curses.KEY_DOWN:
        app.favorites_cursor = min(app.favorites_cursor + 1, len(app.favorites) - 1)
    elif key == curses.KEY_UP:
        app.favorites_cursor = max(app.favorites_cursor - 1, 0)
    elif key == curses.KEY_NPAGE:
        h, _ = app.stdscr.getmaxyx()
        page = h - 4
        app.favorites_cursor = min(app.favorites_cursor + page, len(app.favorites) - 1)
    elif key == curses.KEY_PPAGE:
        h, _ = app.stdscr.getmaxyx()
        page = h - 4
        app.favorites_cursor = max(app.favorites_cursor - page, 0)
    elif key == ord("g"):
        app.favorites_cursor = 0
    elif key == ord("G"):
        app.favorites_cursor = len(app.favorites) - 1
    elif key in (10, 13):
        entry = app.favorites[app.favorites_cursor]
        path = entry["path"]
        app.stack.items = [StackItem(path=path, name=entry.get("name", os.path.basename(path)))]
        app._play_current()
        app.current_view = app.V_LISTEN
    elif key == ord("d"):
        idx = app.favorites_cursor
        if 0 <= idx < len(app.favorites):
            removed = app.favorites.pop(idx)
            save_favorites(app.favorites)
            _toast(app, f"Eliminado: {removed.get('name', '')}")
            if app.favorites:
                app.favorites_cursor = min(app.favorites_cursor, len(app.favorites) - 1)
            else:
                app.favorites_cursor = 0
    elif key == ord("a"):
        entry = app.favorites[app.favorites_cursor]
        path = entry["path"]
        app.stack.append(StackItem(path=path, name=entry.get("name", os.path.basename(path))))
        _toast(app, "Añadido a la pila")
    elif key == ord("A"):
        entry = app.favorites[app.favorites_cursor]
        path = entry["path"]
        app.stack.insert_after_current(StackItem(path=path, name=entry.get("name", os.path.basename(path))))
        _toast(app, "Añadido tras actual")
    elif key == ord("f"):
        entry = app.favorites[app.favorites_cursor]
        _toggle_favorite(app, entry["path"], entry.get("name", ""))

    h, _ = app.stdscr.getmaxyx()
    list_h = h - 4
    app.favorites_scroll = _clamp_scroll(app.favorites_cursor, app.favorites_scroll, list_h)
