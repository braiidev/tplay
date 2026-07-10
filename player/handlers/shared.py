from __future__ import annotations

import curses
import os
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from ..file_utils import is_media as _is_media_file
from ..stack import StackItem

if TYPE_CHECKING:
    from player.app import PlayerApp


def _prompt(app: PlayerApp, label: str, callback: Callable[..., None],
            initial: str = "") -> None:
    app.dialog = {"type": "prompt", "label": label, "buf": initial,
                  "callback": callback, "scroll": 0}
    curses.curs_set(1)
    curses.flushinp()


def _toast(app: PlayerApp, msg: str) -> None:
    app.toast(msg)


def _confirm(app: PlayerApp, label: str, callback: Callable[..., None]) -> None:
    app.dialog = {"type": "confirm", "label": label, "callback": callback}
    curses.flushinp()


def _clamp_scroll(cursor: int, scroll: int, list_h: int) -> int:
    if cursor < scroll:
        return cursor
    if cursor >= scroll + list_h:
        return cursor - list_h + 1
    return scroll


def _page_size(app: PlayerApp) -> int:
    h, _ = app.stdscr.getmaxyx()
    return int(max(1, h - app.LIST_H))


def _play_file_direct(app: PlayerApp, path: str) -> None:
    if not os.path.isfile(path):
        return
    app.stack.items = [StackItem(path=path, name=os.path.basename(path))]
    app.audio.play_file(path)
    app.current_view = app.V_LISTEN


def _do_clear_stack(app: PlayerApp) -> None:
    app._push_snapshot()
    app.audio.stop()
    app.stack.clear()


def _save_stack_as_playlist_cb(app: PlayerApp, name: str) -> None:
    if name and name not in app.playlist_data:
        app.playlist_data[name] = [(item.name, item.path) for item in app.stack.items]
        from ..playlist import save_all as _save_all
        _save_all(app.playlist_data, app.active_name)
        _toast(app, f"Lista '{name}' creada desde pila")


def _rename_file(app: PlayerApp, full: str, name: str,
                 on_rename: Callable[..., None] | None = None) -> None:
    _, ext = os.path.splitext(name)

    def _do_rename(app: PlayerApp, old_path: str, new_path: str) -> None:
        try:
            app._push_snapshot()
            os.rename(old_path, new_path)
            if on_rename:
                on_rename(app, old_path, new_path)
        except Exception as e:
            _toast(app, f"Error al renombrar: {e}")

    def _cb(app: PlayerApp, buf: str) -> None:
        if not buf or buf == name:
            return
        if not os.path.splitext(buf)[1]:
            buf += ext
        new_path = os.path.join(os.path.dirname(full), buf)
        if new_path == full:
            return
        if os.path.exists(new_path):
            _confirm(app,
                     f"'{buf}' ya existe. Si continuas se sobreescribirá. ¿Continuar?",
                     lambda: _do_rename(app, full, new_path))
        else:
            _do_rename(app, full, new_path)

    _prompt(app, "Renombrar a", _cb, name)


def _update_refs_after_rename(app: PlayerApp, old_path: str, new_path: str) -> None:
    new_name = os.path.basename(new_path)
    for pl_name in app.playlist_data:
        songs = app.playlist_data[pl_name]
        for i, (n, p) in enumerate(songs):
            if p == old_path:
                songs[i] = (new_name, new_path)
    if app.active_name in app.playlist_data:
        from ..playlist import save_all as _save_all
        _save_all(app.playlist_data, app.active_name)
    for entry in app.history:
        if entry.get("path") == old_path:
            entry["path"] = new_path
            entry["name"] = new_name


def _open_tag_editor(app: PlayerApp, full: str) -> None:
    if not _is_media_file(full):
        _toast(app, "No es un archivo multimedia")
        return
    meta = app.meta_cache.get(full)
    app.meta_edit_file = full
    app.meta_edit_fields = [
        ('Título', 'title', (meta and meta.get('title')) or ''),
        ('Artista', 'artist', (meta and meta.get('artist')) or ''),
        ('Álbum', 'album', (meta and meta.get('album')) or ''),
        ('Género', 'genre', (meta and meta.get('genre')) or ''),
    ]
    app.meta_edit_changed = {}
    app.meta_edit_cursor = 0
    app.meta_edit_editing = False
    app.meta_edit_mode = True


def _handle_update(app: PlayerApp) -> None:
    app._check_updates()
    if app.update_available:
        n = app.update_behind
        s = "s" if n != 1 else ""
        _confirm(app, f"Actualización disp. ({n} commit{s}) ¿Descargar?", lambda: _do_update(app))
    else:
        _toast(app, "Sin actualizaciones disponibles")


def _do_update(app: PlayerApp) -> None:
    ok, msg = app._apply_updates()
    if ok:
        app.update_available = False
        _restart_app(app)
    else:
        _toast(app, msg)


def _restart_app(app: PlayerApp) -> None:
    import sys
    try:
        app._save_session()
        app.audio.player.stop()
        curses.endwin()
        app_path = os.path.join(app._repo_dir, "app.py")
        os.execv(sys.executable, [sys.executable, app_path])
    except Exception:
        _toast(app, "Error al reiniciar, reiniciá manualmente")
