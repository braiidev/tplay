from __future__ import annotations

import curses
import os
from typing import TYPE_CHECKING

from ..file_utils import is_url as _is_url
from ..stack import StackItem
from ..state import save_history
from .shared import _toast, _confirm, _clamp_scroll
from .shared import _play_file_direct, _open_tag_editor, _toggle_favorite
from ..ui import COMPACT_THRESHOLD

if TYPE_CHECKING:
    from player.app import PlayerApp


def handle_history(app: PlayerApp, key: int) -> None:
    if key == 27:
        app.current_view = app.V_LISTEN
        curses.flushinp()
        return
    if not app.history:
        return
    if key in (10, 13):
        entry = app.history[app.history_cursor]
        path = entry.get("path", "")
        if _is_url(path) or os.path.isfile(path):
            _play_file_direct(app, path)
        return
    if key == ord("d"):
        _confirm(app, "¿Eliminar entrada del historial?", lambda: _do_history_remove(app))
        return
    if key == ord("x"):
        _confirm(app, "¿Limpiar todo el historial?", lambda: _do_history_clear(app))
        return
    if key == ord("a"):
        _add_from_history(app, insert_mode="append")
        return
    if key == ord("A"):
        _add_from_history(app, insert_mode="after_current")
        return
    if key == ord("I"):
        entry = app.history[app.history_cursor]
        path = entry.get("path", "")
        if os.path.isfile(path):
            _open_tag_editor(app, path)
        else:
            _toast(app, "Archivo inexistente")
        return
    if key == ord("f"):
        entry = app.history[app.history_cursor]
        path = entry.get("path", "")
        name = entry.get("name", os.path.basename(path))
        _toggle_favorite(app, path, name)
        return
    if key == ord("g"):
        app.history_cursor = 0
    elif key == ord("G"):
        app.history_cursor = max(0, len(app.history) - 1)
    elif key == curses.KEY_DOWN:
        app.history_cursor = min(app.history_cursor + 1, len(app.history) - 1)
    elif key == curses.KEY_UP:
        app.history_cursor = max(app.history_cursor - 1, 0)
    h, _ = app.stdscr.getmaxyx()
    app.history_scroll = _clamp_scroll(app.history_cursor, app.history_scroll, h - app.LIST_H - (0 if h < COMPACT_THRESHOLD else 1))


def _add_from_history(app: PlayerApp, insert_mode: str = "append") -> None:
    if not app.history:
        return
    entry = app.history[app.history_cursor]
    path = entry.get("path", "")
    if not os.path.isfile(path):
        return
    item = StackItem(path=path, name=os.path.basename(path))
    if insert_mode == "after_current":
        app.stack.insert_after_current(item)
    else:
        app.stack.append(item)
    if app.stack.playhead == 0 and not app.audio.playing:
        app._play_current()


def _do_history_remove(app: PlayerApp) -> None:
    if 0 <= app.history_cursor < len(app.history):
        app.history.pop(app.history_cursor)
        save_history(app.history)
        if app.history_cursor > 0:
            app.history_cursor -= 1


def _do_history_clear(app: PlayerApp) -> None:
    app.history.clear()
    save_history(app.history)
    app.history_cursor = 0
    app.history_scroll = 0
