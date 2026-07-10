from __future__ import annotations

import curses
import os
from typing import TYPE_CHECKING

from ..stack import StackItem
from .shared import _prompt, _toast, _confirm, _clamp_scroll
from .shared import _open_tag_editor, _rename_file, _prompt_export_m3u, _prompt_import_m3u_pls

if TYPE_CHECKING:
    from player.app import PlayerApp


def handle_playlist(app: PlayerApp, key: int) -> None:
    if app.playlist_filter_mode:
        _handle_playlist_filter(app, key)
        return

    if key in (ord("u"), ord("U")):
        if key == ord("u"):
            app._undo()
        else:
            app._redo()
        _save_playlist(app)
        return

    if key == ord("/"):
        if not app.playlist:
            return
        app.playlist_filter_mode = True
        app.playlist_filter = ""
        app.playlist_filtered = list(range(len(app.playlist)))
        app.playlist_cursor = 0
        app.playlist_scroll = 0
        curses.curs_set(1)
        return
    if key == curses.KEY_DOWN:
        if app.playlist:
            app.playlist_cursor = min(app.playlist_cursor + 1, len(app.playlist) - 1)
    elif key == curses.KEY_UP:
        app.playlist_cursor = max(app.playlist_cursor - 1, 0)
    elif key in (curses.KEY_NPAGE,):
        if app.playlist:
            h, _ = app.stdscr.getmaxyx()
            page = h - app.LIST_H
            app.playlist_cursor = min(app.playlist_cursor + page, len(app.playlist) - 1)
    elif key in (curses.KEY_PPAGE,):
        if app.playlist:
            h, _ = app.stdscr.getmaxyx()
            page = h - app.LIST_H
            app.playlist_cursor = max(app.playlist_cursor - page, 0)
    elif key == ord("g"):
        app.playlist_cursor = 0
    elif key == ord("G"):
        app.playlist_cursor = len(app.playlist) - 1
    elif key in (10, 13):
        if app.playlist:
            _play_playlist_enter(app)
    elif key == ord("d"):
        if not app.playlist:
            return
        name = app.playlist[app.playlist_cursor][0]
        _confirm(app, f"¿Eliminar '{name}' de la lista?", lambda: _do_playlist_remove(app, app.playlist_cursor))
    elif key == ord("x"):
        _confirm(app, "¿Limpiar toda la lista?", lambda: _do_playlist_clear(app))
    elif key == ord("I"):
        if not app.playlist:
            return
        _, path = app.playlist[app.playlist_cursor]
        if os.path.isfile(path):
            _open_tag_editor(app, path)
        else:
            _toast(app, "Archivo inexistente")
    elif key == ord("E"):
        if not app.playlist:
            return
        name, full = app.playlist[app.playlist_cursor]
        if not os.path.isfile(full):
            _toast(app, "Archivo inexistente")
            return

        def _on_rename(app: PlayerApp, old_path: str, new_path: str) -> None:
            idx = app.playlist_cursor
            if 0 <= idx < len(app.playlist):
                app.playlist[idx] = (os.path.basename(new_path), new_path)
                _save_playlist(app)
            for entry in app.history:
                if entry.get("path") == old_path:
                    entry["path"] = new_path
                    entry["name"] = os.path.basename(new_path)

        _rename_file(app, full, name, _on_rename)
    elif key == ord("c"):
        _prompt(app, "Nombre de la nueva lista", _create_playlist_cb)
    elif key == ord("R"):
        if app.active_name == "default":
            return
        _prompt(app, f"Renombrar '{app.active_name}' a", _rename_playlist_cb)
    elif key == ord("D"):
        if len(app.playlist_data) > 1:
            _confirm(app, f"¿Borrar '{app.active_name}'?", lambda: _do_delete_playlist(app))
    elif key == ord("K"):
        if app.playlist_cursor > 0 and app.playlist:
            app._push_snapshot()
            i = app.playlist_cursor
            pl = app.playlist
            pl[i], pl[i - 1] = pl[i - 1], pl[i]
            app.playlist_cursor -= 1
            _save_playlist(app)
    elif key == ord("J"):
        if app.playlist_cursor < len(app.playlist) - 1:
            app._push_snapshot()
            i = app.playlist_cursor
            pl = app.playlist
            pl[i], pl[i + 1] = pl[i + 1], pl[i]
            app.playlist_cursor += 1
            _save_playlist(app)
    elif key in (curses.KEY_LEFT, ord("[")):
        names = list(app.playlist_data.keys())
        if len(names) > 1 and app.active_name in app.playlist_data:
            app._push_snapshot()
            idx = names.index(app.active_name)
            _switch_playlist(app, names[(idx - 1) % len(names)])
    elif key in (curses.KEY_RIGHT, ord("]")):
        names = list(app.playlist_data.keys())
        if len(names) > 1 and app.active_name in app.playlist_data:
            app._push_snapshot()
            idx = names.index(app.active_name)
            _switch_playlist(app, names[(idx + 1) % len(names)])
    elif key == ord("s"):
        _save_playlist(app)
    elif key == ord("X"):
        _prompt_export_m3u(app)
    elif key == ord("O"):
        _prompt_import_m3u_pls(app)

    h, _ = app.stdscr.getmaxyx()
    app.playlist_scroll = _clamp_scroll(app.playlist_cursor, app.playlist_scroll, h - app.LIST_H)


def _handle_playlist_filter(app: PlayerApp, key: int) -> None:
    if key == 27:
        app.playlist_filter_mode = False
        app.playlist_filter = ""
        app.playlist_filtered = []
        app.playlist_cursor = 0
        app.playlist_scroll = 0
        curses.curs_set(0)
        return
    if key in (10, 13):
        if app.playlist_filtered and app.playlist_cursor < len(app.playlist_filtered):
            idx = app.playlist_filtered[app.playlist_cursor]
            app.playlist_cursor = idx
            _play_playlist_enter(app)
            app.playlist_filter_mode = False
            app.playlist_filter = ""
            app.playlist_filtered = []
            curses.curs_set(0)
        return
    if key == curses.KEY_DOWN:
        if app.playlist_filtered:
            app.playlist_cursor = min(app.playlist_cursor + 1, len(app.playlist_filtered) - 1)
        h, _ = app.stdscr.getmaxyx()
        app.playlist_scroll = _clamp_scroll(app.playlist_cursor, app.playlist_scroll, h - app.FILTER_LIST_H)
        return
    if key == curses.KEY_UP:
        app.playlist_cursor = max(app.playlist_cursor - 1, 0)
        h, _ = app.stdscr.getmaxyx()
        app.playlist_scroll = _clamp_scroll(app.playlist_cursor, app.playlist_scroll, h - app.FILTER_LIST_H)
        return
    if key in (127, curses.KEY_BACKSPACE):
        app.playlist_filter = app.playlist_filter[:-1]
        _do_playlist_filter(app)
        return
    if 32 <= key <= 126:
        app.playlist_filter += chr(key)
        _do_playlist_filter(app)
        return


def _do_playlist_filter(app: PlayerApp) -> None:
    q = app.playlist_filter.lower().strip()
    if not q:
        app.playlist_filtered = list(range(len(app.playlist)))
    else:
        app.playlist_filtered = [i for i, (name, path) in enumerate(app.playlist)
                                  if q in name.lower() or q in path.lower()]
    app.playlist_cursor = 0
    app.playlist_scroll = 0


def _play_playlist_enter(app: PlayerApp) -> None:
    pl = app.playlist
    if not pl:
        return
    items = [StackItem(path=p, name=n) for n, p in pl]
    app.stack.items = items
    app.audio.play_file(pl[0][1])
    app.current_view = app.V_LISTEN


def _do_playlist_remove(app: PlayerApp, idx: int) -> None:
    if idx < 0 or idx >= len(app.playlist):
        return
    app._push_snapshot()
    app.playlist.pop(idx)
    _save_playlist(app)


def _do_playlist_clear(app: PlayerApp) -> None:
    app._push_snapshot()
    app.playlist.clear()
    _save_playlist(app)


def _save_playlist(app: PlayerApp) -> None:
    from ..playlist import save_all as _save_all
    _save_all(app.playlist_data, app.active_name)


def _switch_playlist(app: PlayerApp, name: str) -> None:
    if name in app.playlist_data:
        app.active_name = name
        app.playlist_cursor = 0
        app.playlist_scroll = 0
        app.current_view = app.V_PLAYLIST
        app.playlist_filter_mode = False
        app.playlist_filter = ""
        app.playlist_filtered = []
        curses.curs_set(0)


def _create_playlist_cb(app: PlayerApp, name: str) -> None:
    if name and name not in app.playlist_data:
        app.playlist_data[name] = []
        _switch_playlist(app, name)
        _save_playlist(app)


def _do_delete_playlist(app: PlayerApp) -> None:
    if len(app.playlist_data) > 1:
        app.playlist_data.pop(app.active_name, None)
        names = list(app.playlist_data.keys())
        if names:
            _switch_playlist(app, names[0])
            _save_playlist(app)


def _rename_playlist_cb(app: PlayerApp, new_name: str) -> None:
    if new_name and new_name != app.active_name and new_name not in app.playlist_data:
        app.playlist_data[new_name] = app.playlist_data.pop(app.active_name)
        app.active_name = new_name
        _save_playlist(app)
