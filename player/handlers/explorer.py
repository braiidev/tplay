from __future__ import annotations

import curses
import os
import shutil
from typing import TYPE_CHECKING

from ..file_utils import list_dir as _list_dir
from ..file_utils import is_playlist_file as _is_playlist_file
from ..stack import StackItem
from .shared import _prompt, _toast, _confirm, _clamp_scroll
from .shared import _page_size, _play_file_direct, _rename_file
from .shared import _open_tag_editor, _parse_m3u, _parse_pls, _toggle_favorite

if TYPE_CHECKING:
    from player.app import PlayerApp


def handle_explorer(app: PlayerApp, key: int) -> None:
    if app.file_op_mode:
        _handle_file_op_picker(app, key)
        return
    if app.explorer_filter_mode:
        _handle_explorer_filter(app, key)
        return
    if not app.entries:
        return

    if key == ord("/"):
        app.explorer_filter_mode = True
        app.explorer_filter = ""
        app.explorer_filter_cursor = 0
        app.explorer_filtered = list(range(len(app.entries)))
        app.cursor = 0
        app.scroll = 0
        return

    if key == curses.KEY_DOWN:
        if app.entries:
            app.cursor = min(app.cursor + 1, len(app.entries) - 1)
    elif key == curses.KEY_UP:
        app.cursor = max(app.cursor - 1, 0)
    elif key == curses.KEY_NPAGE:
        app.cursor = min(app.cursor + _page_size(app), len(app.entries) - 1)
    elif key == curses.KEY_PPAGE:
        app.cursor = max(app.cursor - _page_size(app), 0)
    elif key == ord("g"):
        app.cursor = 0
    elif key == ord("G"):
        app.cursor = len(app.entries) - 1
    elif key == ord("\t"):
        idx = app.cursor
        if idx in app.explorer_marked:
            app.explorer_marked.discard(idx)
        else:
            app.explorer_marked.add(idx)
        if app.cursor < len(app.entries) - 1:
            app.cursor += 1
    elif key in (10, 13, curses.KEY_RIGHT):
        if app.entries:
            name, is_dir, full = app.entries[app.cursor]
            if is_dir:
                app.current_dir = full
                app.entries = _list_dir(full)
                app.cursor = 0
                app.scroll = 0
                app.explorer_marked.clear()
            elif _is_playlist_file(full):
                ext = os.path.splitext(full)[1].lower()
                paths = _parse_pls(full) if ext == ".pls" else _parse_m3u(full)
                if not paths:
                    _toast(app, "Playlist vacía o inválida")
                else:
                    items = [StackItem(path=p, name=os.path.basename(p)) for p in paths]
                    app.stack.items = items
                    app._play_current()
                    app.current_view = app.V_LISTEN
            elif app.explorer_marked:
                _play_marked(app)
            else:
                _play_file_direct(app, full)
    elif key == ord("a"):
        _add_from_explorer(app, insert_mode="append")
    elif key == ord("A"):
        _add_from_explorer(app, insert_mode="after_current")
    elif key == ord("C"):
        _start_file_op(app, "copy")
    elif key == ord("V"):
        _start_file_op(app, "move")
    elif key == ord("E"):
        _start_rename(app)
    elif key == ord("I"):
        _start_tag_edit(app)
    elif key == ord("d"):
        _start_delete(app)
    elif key == ord("M"):
        _start_mkdir(app)
    elif key == ord("F"):
        app.current_view = app.V_FAVORITES
    elif key == ord("f"):
        if app.entries:
            name, is_dir, full = app.entries[app.cursor]
            if not is_dir:
                _toggle_favorite(app, full, name)
    elif key == curses.KEY_F5:
        app.entries = _list_dir(app.current_dir)
        app.cursor = 0
        app.scroll = 0
        app.explorer_marked.clear()
    elif key == ord("P"):
        _play_folder(app)
    elif key in (curses.KEY_LEFT, 127, curses.KEY_BACKSPACE):
        parent = os.path.dirname(app.current_dir)
        if parent and parent != app.current_dir:
            app.current_dir = parent
            app.entries = _list_dir(parent)
            app.cursor = 0
            app.scroll = 0
            app.explorer_marked.clear()
    elif key == ord("~"):
        app.current_dir = os.path.expanduser("~")
        app.entries = _list_dir(app.current_dir)
        app.cursor = 0
        app.scroll = 0
        app.explorer_marked.clear()
    elif key == ord("u") and app.undo_stack:
        app._undo()
    elif key == ord("U"):
        app._redo()

    h, _ = app.stdscr.getmaxyx()
    app.scroll = _clamp_scroll(app.cursor, app.scroll, h - app.LIST_H)


def _handle_explorer_filter(app: PlayerApp, key: int) -> None:
    if key == 27:
        app.explorer_filter_mode = False
        app.explorer_filter = ""
        app.explorer_filtered = []
        app.explorer_filter_cursor = 0
        app.cursor = 0
        app.scroll = 0
        return
    if key in (10, 13):
        if app.explorer_filtered and app.cursor < len(app.explorer_filtered):
            idx = app.explorer_filtered[app.cursor]
            name, is_dir, full = app.entries[idx]
            if is_dir:
                app.current_dir = full
                app.entries = _list_dir(full)
                app.cursor = 0
                app.scroll = 0
            else:
                _play_file_direct(app, full)
            app.explorer_filter_mode = False
            app.explorer_filter = ""
            app.explorer_filtered = []
            app.explorer_filter_cursor = 0
        return
    if key == curses.KEY_DOWN:
        if app.explorer_filtered:
            app.cursor = min(app.cursor + 1, len(app.explorer_filtered) - 1)
        return
    if key == curses.KEY_UP:
        app.cursor = max(app.cursor - 1, 0)
        return
    cur = app.explorer_filter_cursor
    if key in (curses.KEY_LEFT, ord("h")):
        if cur > 0:
            app.explorer_filter_cursor = cur - 1
        return
    if key in (curses.KEY_RIGHT, ord("l")):
        if cur < len(app.explorer_filter):
            app.explorer_filter_cursor = cur + 1
        return
    if key in (127, curses.KEY_BACKSPACE):
        if cur > 0:
            app.explorer_filter = app.explorer_filter[:cur - 1] + app.explorer_filter[cur:]
            app.explorer_filter_cursor = cur - 1
            _do_explorer_filter(app)
        return
    if 32 <= key <= 126:
        app.explorer_filter = app.explorer_filter[:cur] + chr(key) + app.explorer_filter[cur:]
        app.explorer_filter_cursor = cur + 1
        _do_explorer_filter(app)


def _do_explorer_filter(app: PlayerApp) -> None:
    q = app.explorer_filter.lower().strip()
    if not q:
        app.explorer_filtered = list(range(len(app.entries)))
    else:
        app.explorer_filtered = [i for i, (name, _, _) in enumerate(app.entries)
                                  if q in name.lower()]
    app.cursor = 0
    app.scroll = 0


def _start_delete(app: PlayerApp) -> None:
    if not app.entries:
        return
    name, is_dir, full = app.entries[app.cursor]
    if is_dir:
        try:
            if os.listdir(full):
                _toast(app, f"'{name}': directorio no vacío")
                return
        except PermissionError:
            _toast(app, f"'{name}': sin permisos")
            return
    _confirm(app, f"¿Eliminar '{name}'?", lambda: _do_delete(app, full))


def _do_delete(app: PlayerApp, path: str) -> None:
    try:
        app._push_snapshot()
        if os.path.isdir(path):
            os.rmdir(path)
        else:
            os.remove(path)
        app.entries = _list_dir(app.current_dir)
        app.cursor = 0
        app.scroll = 0
    except Exception as e:
        _toast(app, f"Error al eliminar: {e}")


def _start_mkdir(app: PlayerApp) -> None:
    _prompt(app, "Nombre del nuevo directorio", _do_mkdir)


def _do_mkdir(app: PlayerApp, buf: str) -> None:
    if not buf:
        return
    try:
        path = os.path.join(app.current_dir, buf)
        os.makedirs(path, exist_ok=True)
        app.entries = _list_dir(app.current_dir)
    except Exception as e:
        _toast(app, f"Error al crear directorio: {e}")


def _play_folder(app: PlayerApp) -> None:
    if not app.entries:
        return
    _, is_dir, full = app.entries[app.cursor]
    if not is_dir:
        return
    items = _list_dir(full)
    media = [StackItem(path=p, name=n) for n, d, p in items if not d]
    if not media:
        return
    app._push_snapshot()
    app.stack.items = media
    app._play_current()


def _play_marked(app: PlayerApp) -> None:
    if not app.explorer_marked or not app.entries:
        return
    items: list[StackItem] = []
    for idx in sorted(app.explorer_marked):
        if idx < len(app.entries):
            name, is_dir, full = app.entries[idx]
            if not is_dir:
                items.append(StackItem(path=full, name=name))
    if not items:
        _toast(app, "No hay archivos marcados")
        return
    app._push_snapshot()
    app.stack.items = items
    app.explorer_marked.clear()
    app._play_current()


def _start_rename(app: PlayerApp) -> None:
    if not app.entries:
        return
    name, _, full = app.entries[app.cursor]

    def _on_rename(app: PlayerApp, old_path: str, new_path: str) -> None:
        app.entries = _list_dir(app.current_dir)
        from .shared import _update_refs_after_rename
        _update_refs_after_rename(app, old_path, new_path)

    _rename_file(app, full, name, _on_rename)


def _start_tag_edit(app: PlayerApp) -> None:
    if not app.entries:
        return
    _, is_dir, full = app.entries[app.cursor]
    if is_dir:
        return
    _open_tag_editor(app, full)


def _add_from_explorer(app: PlayerApp, insert_mode: str = "append") -> None:
    if not app.entries:
        return
    _, is_dir, full = app.entries[app.cursor]
    if is_dir or not os.path.isfile(full):
        return
    if _is_playlist_file(full):
        ext = os.path.splitext(full)[1].lower()
        paths = _parse_pls(full) if ext == ".pls" else _parse_m3u(full)
        if not paths:
            _toast(app, "Playlist vacía o inválida")
            return
        pl_name = os.path.splitext(os.path.basename(full))[0]
        app._push_snapshot()
        for p in paths:
            entry = (os.path.basename(p), p)
            if pl_name not in app.playlist_data:
                app.playlist_data[pl_name] = []
            app.playlist_data[pl_name].append(entry)
        from ..playlist import save_all as _save_all
        _save_all(app.playlist_data, app.active_name)
        _toast(app, f"Importada '{pl_name}' con {len(paths)} canciones")
        return
    has_playlists = len(app.playlist_data) > 0
    if has_playlists:
        app.dialog = {"type": "dest", "path": full, "mode": insert_mode}
    else:
        item = StackItem(path=full, name=os.path.basename(full))
        if insert_mode == "after_current":
            app.stack.insert_after_current(item)
        else:
            app.stack.append(item)
        if app.stack.playhead == 0 and not app.audio.playing:
            app._play_current()


def _start_file_op(app: PlayerApp, mode: str) -> None:
    if not app.entries:
        return
    _, is_dir, full = app.entries[app.cursor]
    if is_dir:
        return
    app.file_op_mode = mode
    app.file_op_source = full


def _do_file_op(app: PlayerApp, dest_dir: str) -> None:
    src = app.file_op_source
    mode = app.file_op_mode
    app.file_op_mode = None
    app.file_op_source = None
    if not src or not mode or not os.path.isdir(dest_dir):
        return
    dest = os.path.join(dest_dir, os.path.basename(src))
    label = "Copiar" if mode == "copy" else "Mover"
    try:
        app._push_snapshot()
        if mode == "copy":
            shutil.copy2(src, dest)
        elif mode == "move":
            shutil.move(src, dest)
        app._file_undo = {"type": mode, "src": src, "dest": dest}
        app.entries = _list_dir(app.current_dir)
    except Exception as e:
        _toast(app, f"Error: {e}")
        return
    _toast(app, f"{label}: {os.path.basename(src)} listo")


def _confirm_file_op(app: PlayerApp, dest_dir: str) -> None:
    src = app.file_op_source
    mode = app.file_op_mode
    if not src or not os.path.isdir(dest_dir):
        return
    label = "Copiar" if mode == "copy" else "Mover"
    name = os.path.basename(src)
    dest_name = os.path.basename(dest_dir)
    dest = os.path.join(dest_dir, name)
    if os.path.exists(dest):
        _confirm(app, f"'{name}' ya existe en '{dest_name}'. Si continuas se sobreescribirá. ¿Continuar?",
                 lambda: _do_file_op(app, dest_dir))
    else:
        _confirm(app, f"¿{label} '{name}' a '{dest_name}'?", lambda: _do_file_op(app, dest_dir))


def _handle_file_op_picker(app: PlayerApp, key: int) -> None:
    if not app.entries:
        return
    if key == 27:
        app.file_op_mode = None
        app.file_op_source = None
        return

    if key in (curses.KEY_DOWN,):
        if app.entries:
            app.cursor = min(app.cursor + 1, len(app.entries) - 1)
    elif key in (curses.KEY_UP,):
        app.cursor = max(app.cursor - 1, 0)
    elif key in (curses.KEY_NPAGE,):
        app.cursor = min(app.cursor + _page_size(app), len(app.entries) - 1)
    elif key in (curses.KEY_PPAGE,):
        app.cursor = max(app.cursor - _page_size(app), 0)
    elif key == ord("g"):
        app.cursor = 0
    elif key == ord("G"):
        app.cursor = len(app.entries) - 1
    elif key in (10, 13, ord("C"), ord("V")):
        if app.entries:
            _, is_dir, full = app.entries[app.cursor]
            if is_dir:
                _confirm_file_op(app, full)
            else:
                _confirm_file_op(app, app.current_dir)
    elif key in (curses.KEY_RIGHT, ord("l")):
        if app.entries:
            _, is_dir, full = app.entries[app.cursor]
            if is_dir:
                app.current_dir = full
                app.entries = _list_dir(full)
                app.cursor = 0
                app.scroll = 0
    elif key in (curses.KEY_LEFT, 127, curses.KEY_BACKSPACE):
        parent = os.path.dirname(app.current_dir)
        if parent and parent != app.current_dir:
            app.current_dir = parent
            app.entries = _list_dir(parent)
            app.cursor = 0
            app.scroll = 0
    elif key == ord("~"):
        app.current_dir = os.path.expanduser("~")
        app.entries = _list_dir(app.current_dir)
        app.cursor = 0
        app.scroll = 0
    elif key == ord("u") and app.undo_stack:
        app._undo()
        return
    elif key == ord("U"):
        app._redo()
        return

    h, _ = app.stdscr.getmaxyx()
    list_h = h - app.LIST_H - (1 if app.file_op_mode else 0)
    if app.cursor < app.scroll:
        app.scroll = app.cursor
    elif app.cursor >= app.scroll + list_h:
        app.scroll = app.cursor - list_h + 1
