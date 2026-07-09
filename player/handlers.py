import curses
import os
import shutil

from .config import THEME_NAMES, COLORS
from .file_utils import list_dir as _list_dir, is_media as _is_media_file, is_url as _is_url
from .stack import StackItem
from . import keybindings as kb


def handle_listen(app, key: int) -> None:
    SEEK_STEP = 5000
    if key in (ord("\t"),):
        h, w = app.stdscr.getmaxyx()
        if h >= 16 and w >= 61:
            app.show_stack_view = True
            app.stack_cursor = max(0, min(app.stack_cursor, len(app.stack.items) - 1)) if app.stack.items else 0
            app.stack_scroll = 0
        else:
            app.show_stack_view = len(app.stack.items) > 0
            app.stack_scroll = 0
        curses.flushinp()
        return
    if key in (curses.KEY_LEFT, ord("h")):
        cur = app.audio.get_time()
        app.audio.player.set_time(max(0, cur - SEEK_STEP))
    elif key in (curses.KEY_RIGHT, ord("l")):
        cur = app.audio.get_time()
        dur = app.audio.get_length()
        app.audio.player.set_time(min(dur, cur + SEEK_STEP))
    elif key == ord("g"):
        if app.audio.get_length() > 0:
            cur_s = app.audio.get_time() // 1000
            app.goto_mins = cur_s // 60
            app.goto_secs = cur_s % 60
            app.goto_field = 0
            app.goto_mode = True
            curses.curs_set(0)
    elif key == ord("o"):
        _prompt(app, "URL de stream", _add_url_cb)


def _add_url_cb(app, url: str) -> None:
    url = url.strip()
    if not url or not _is_url(url):
        return
    name = url.split("//", 1)[-1].split("/")[0] if "//" in url else url
    item = StackItem(path=url, name=name)
    app.stack.append(item)
    if app.stack.playhead == 0 and not app.audio.playing:
        app._play_current()


def handle_stack_view(app, key: int) -> None:
    if key in (ord("u"), ord("U")):
        if key == ord("u"):
            app._undo()
        else:
            app._redo()
        return
    if key in (ord("\t"), 27):
        app.show_stack_view = False
        curses.flushinp()
        return
    if key in (ord("n"),):
        app._play_next()
        return
    if key in (ord("b"),):
        app._play_prev()
        return
    if key == ord("+"):
        app.audio.set_volume(app.audio.volume + 5)
        return
    if key == ord("-"):
        app.audio.set_volume(app.audio.volume - 5)
        return
    if key == ord("o"):
        _prompt(app, "URL de stream", _add_url_cb)
        return
    if not app.stack.items:
        return
    if key in (ord("\n"), ord("\r"), curses.KEY_ENTER):
        app.stack.playhead = app.stack_cursor
        app._play_current()
        app.show_stack_view = False
        return
    if key in (curses.KEY_DOWN, ord("j")):
        app.stack_cursor = min(app.stack_cursor + 1, len(app.stack.items) - 1)
    elif key in (curses.KEY_UP, ord("k")):
        app.stack_cursor = max(app.stack_cursor - 1, 0)
    elif key in (ord("d"),):
        app._push_snapshot()
        app.stack.remove(app.stack_cursor)
        if app.stack_cursor >= len(app.stack.items) and app.stack_cursor > 0:
            app.stack_cursor -= 1
    elif key in (ord("x"),):
        _confirm(app, "¿Limpiar toda la pila?", lambda: _do_clear_stack(app))
    elif key in (ord("s"),):
        if app.stack.items:
            _prompt(app, "Guardar pila como lista", _save_stack_as_playlist_cb)
    elif key == ord("K"):
        if app.stack_cursor > 0:
            app._push_snapshot()
            app.stack.swap(app.stack_cursor, app.stack_cursor - 1)
            app.stack_cursor -= 1
    elif key == ord("J"):
        if app.stack_cursor < len(app.stack.items) - 1:
            app._push_snapshot()
            app.stack.swap(app.stack_cursor, app.stack_cursor + 1)
            app.stack_cursor += 1
    elif key in (ord("r"), ord("R")):
        app.stack.cycle_item_mode(app.stack_cursor)
    elif key == ord("g"):
        app.stack_cursor = 0
        app.stack_scroll = 0
    elif key == ord("G"):
        app.stack_cursor = len(app.stack.items) - 1
    elif key in (curses.KEY_NPAGE,):
        h, _ = app.stdscr.getmaxyx()
        page = h - 8
        app.stack_cursor = min(app.stack_cursor + page, len(app.stack.items) - 1)
    elif key in (curses.KEY_PPAGE,):
        h, _ = app.stdscr.getmaxyx()
        page = h - 8
        app.stack_cursor = max(app.stack_cursor - page, 0)

    h, _ = app.stdscr.getmaxyx()
    list_h = h - 8
    if app.stack_cursor < app.stack_scroll:
        app.stack_scroll = app.stack_cursor
    elif app.stack_cursor >= app.stack_scroll + list_h:
        app.stack_scroll = app.stack_cursor - list_h + 1


def handle_explorer(app, key: int) -> None:
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
        app.explorer_filtered = list(range(len(app.entries)))
        app.cursor = 0
        app.scroll = 0
        curses.curs_set(1)
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
    elif key in (ord("\n"), 10, 13, curses.KEY_RIGHT):
        if app.entries:
            name, is_dir, full = app.entries[app.cursor]
            if is_dir:
                app.current_dir = full
                app.entries = _list_dir(full)
                app.cursor = 0
                app.scroll = 0
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
    elif key == ord("R"):
        app.entries = _list_dir(app.current_dir)
        app.cursor = 0
        app.scroll = 0
    elif key == ord("P"):
        _play_folder(app)
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
    elif key == ord("u"):
        if not app._undo_file_op() and app.undo_stack:
            app._undo()
    elif key == ord("U"):
        app._redo()

    h, _ = app.stdscr.getmaxyx()
    list_h = h - app.LIST_H
    if app.cursor < app.scroll:
        app.scroll = app.cursor
    elif app.cursor >= app.scroll + list_h:
        app.scroll = app.cursor - list_h + 1


def handle_playlist(app, key: int) -> None:
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
    elif key in (ord("\n"), 10, 13):
        if app.playlist:
            _play_playlist_enter(app)
    elif key == ord("d"):
        if not app.playlist:
            return
        name = app.playlist[app.playlist_cursor][0]
        _confirm(app, f"¿Eliminar '{name}' de la lista?", lambda: _do_playlist_remove(app, app.playlist_cursor))
    elif key == ord("x"):
        _confirm(app, "¿Limpiar toda la lista?", lambda: _do_playlist_clear(app))
    elif key == ord("c"):
        _prompt(app, "Nombre de la nueva lista", _create_playlist_cb)
    elif key == ord("e"):
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
        if len(names) > 1:
            app._push_snapshot()
            idx = names.index(app.active_name)
            _switch_playlist(app, names[(idx - 1) % len(names)])
    elif key in (curses.KEY_RIGHT, ord("]")):
        names = list(app.playlist_data.keys())
        if len(names) > 1:
            app._push_snapshot()
            idx = names.index(app.active_name)
            _switch_playlist(app, names[(idx + 1) % len(names)])
    elif key == ord("s"):
        _save_playlist(app)

    h, _ = app.stdscr.getmaxyx()
    list_h = h - app.LIST_H
    if app.playlist_cursor < app.playlist_scroll:
        app.playlist_scroll = app.playlist_cursor
    elif app.playlist_cursor >= app.playlist_scroll + list_h:
        app.playlist_scroll = app.playlist_cursor - list_h + 1


def handle_history(app, key: int) -> None:
    if key == 27:
        app.current_view = app.V_LISTEN
        curses.flushinp()
        return
    if not app.history:
        return
    if key in (ord("\n"), 10, 13):
        entry = app.history[app.history_cursor]
        path = entry.get("path", "")
        if os.path.isfile(path):
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
    if key == curses.KEY_DOWN:
        app.history_cursor = min(app.history_cursor + 1, len(app.history) - 1)
    elif key == curses.KEY_UP:
        app.history_cursor = max(app.history_cursor - 1, 0)
    h, _ = app.stdscr.getmaxyx()
    list_h = h - app.LIST_H
    if app.history_cursor < app.history_scroll:
        app.history_scroll = app.history_cursor
    elif app.history_cursor >= app.history_scroll + list_h:
        app.history_scroll = app.history_cursor - list_h + 1


def handle_config(app, key: int) -> None:
    total = len(app.config_items)
    if key == ord("["):
        app.config_tab_idx = (app.config_tab_idx - 1) % len(app.config_tabs)
        app.config_cursor = 0
        app.config_scroll = 0
        return
    elif key == ord("]"):
        app.config_tab_idx = (app.config_tab_idx + 1) % len(app.config_tabs)
        app.config_cursor = 0
        app.config_scroll = 0
        return

    if key == curses.KEY_DOWN:
        app.config_cursor = min(app.config_cursor + 1, total - 1)
    elif key == curses.KEY_UP:
        app.config_cursor = max(app.config_cursor - 1, 0)
    elif key in (curses.KEY_RIGHT, ord("\n"), 10, 13):
        if total == 0:
            return
        key_name, _, ctype = app.config_items[app.config_cursor]
        if ctype == "choice":
            _cycle_theme(app, 1)
        elif ctype == "color":
            _cycle_color(app, key_name, 1)
        elif ctype == "int":
            _config_int_inc(app, key_name)
        elif ctype == "action" and key_name == "keybindings":
            _open_keybindings(app)
        elif ctype == "action" and key_name == "update":
            _handle_update(app)
    elif key == curses.KEY_LEFT:
        if total == 0:
            return
        key_name, _, ctype = app.config_items[app.config_cursor]
        if ctype == "choice":
            _cycle_theme(app, -1)
        elif ctype == "color":
            _cycle_color(app, key_name, -1)
        elif ctype == "int":
            _config_int_dec(app, key_name)

    h, _ = app.stdscr.getmaxyx()
    list_h = h - 5
    if app.config_cursor < app.config_scroll:
        app.config_scroll = app.config_cursor
    elif app.config_cursor >= app.config_scroll + list_h:
        app.config_scroll = app.config_cursor - list_h + 1


def handle_keybindings(app, key: int) -> None:
    if key == 27:
        _save_keybindings(app)
        app.kb_keybinding_view = False
        app.current_view = app.V_CONFIG
        curses.flushinp()
        return

    if app.kb_capturing:
        if key in kb.RESERVED_KEYS or key in (27,):
            app.kb_capturing = False
            app.kb_capturing_action = None
            return
        if 32 <= key <= 126:
            app.kb_capturing = False
            _assign_key(app, app.kb_capturing_action, key)
            app.kb_capturing_action = None
            return
        return

    if key in (curses.KEY_LEFT, curses.KEY_RIGHT):
        _toggle_keybinding_mode(app)
        return

    if app.keybinding_mode != "custom":
        return

    if key == curses.KEY_DOWN:
        app.kb_cursor = min(app.kb_cursor + 1, len(kb.BINDABLE_ACTIONS) - 1)
    elif key == curses.KEY_UP:
        app.kb_cursor = max(app.kb_cursor - 1, 0)
    elif key in (ord("\n"), 10, 13):
        action = kb.BINDABLE_ACTIONS[app.kb_cursor]
        app.kb_capturing = True
        app.kb_capturing_action = action
        app.kb_conflict_msg = ""


# ── Helpers ──

def handle_goto(app, key: int) -> None:
    if key == 27:
        app.goto_mode = False
        curses.flushinp()
        return
    if key in (ord("\n"), 10, 13):
        target = app.goto_mins * 60 + app.goto_secs
        app.audio.player.set_time(target * 1000)
        app.goto_mode = False
        curses.flushinp()
        return
    if key in (curses.KEY_LEFT, ord("h")):
        app.goto_field = 0
        return
    if key in (curses.KEY_RIGHT, ord("l")):
        app.goto_field = 1
        return
    if key in (curses.KEY_UP, ord("k")):
        if app.goto_field == 0:
            app.goto_mins = min(app.goto_mins + 1, 999)
        else:
            app.goto_secs = min(app.goto_secs + 1, 59)
        return
    if key in (curses.KEY_DOWN, ord("j")):
        if app.goto_field == 0:
            app.goto_mins = max(app.goto_mins - 1, 0)
        else:
            app.goto_secs = max(app.goto_secs - 1, 0)
        return


def _page_size(app) -> int:
    h, _ = app.stdscr.getmaxyx()
    return max(1, h - app.LIST_H)


def _play_file_direct(app, path: str) -> None:
    if not os.path.isfile(path):
        return
    app.stack.items = [StackItem(path=path, name=os.path.basename(path))]
    app.audio.play_file(path)
    app.current_view = app.V_LISTEN


def _play_playlist_enter(app) -> None:
    pl = app.playlist
    if not pl:
        return
    items = [StackItem(path=p, name=n) for n, p in pl]
    app.stack.items = items
    app.audio.play_file(pl[0][1])
    app.current_view = app.V_LISTEN


def _add_from_explorer(app, insert_mode: str = "append") -> None:
    if not app.entries:
        return
    _, is_dir, full = app.entries[app.cursor]
    if is_dir or not os.path.isfile(full):
        return
    has_playlists = len(app.playlist_data) > 0 and any(
        len(songs) > 0 for songs in app.playlist_data.values()
    )
    if has_playlists:
        app.awaiting_dest = True
        app._pending_add_path = full
        app._pending_add_mode = insert_mode
    else:
        item = StackItem(path=full, name=os.path.basename(full))
        if insert_mode == "after_current":
            app.stack.insert_after_current(item)
        else:
            app.stack.append(item)
        if app.stack.playhead == 0 and not app.audio.playing:
            app._play_current()


def _add_from_history(app, insert_mode: str = "append") -> None:
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


def _do_clear_stack(app) -> None:
    app._push_snapshot()
    app.audio.stop()
    app.stack.clear()


def _save_stack_as_playlist_cb(app, name: str) -> None:
    if name and name not in app.playlist_data:
        app.playlist_data[name] = [(item.name, item.path) for item in app.stack.items]
        _save_playlist(app)
        _toast(app, f"Lista '{name}' creada desde pila")


def _start_delete(app) -> None:
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


def _do_delete(app, path: str) -> None:
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


def _start_mkdir(app) -> None:
    _prompt(app, "Nombre del nuevo directorio", _do_mkdir)


def _do_mkdir(app, buf: str) -> None:
    if not buf:
        return
    try:
        path = os.path.join(app.current_dir, buf)
        os.makedirs(path, exist_ok=True)
        app.entries = _list_dir(app.current_dir)
    except Exception as e:
        _toast(app, f"Error al crear directorio: {e}")


def _play_folder(app) -> None:
    if not app.entries:
        return
    _, is_dir, full = app.entries[app.cursor]
    if not is_dir:
        return
    items = _list_dir(full)
    media = [StackItem(path=p, name=n) for n, d, p in items if not d]
    if not media:
        return
    app.stack.items = media
    app._play_current()


def _start_rename(app) -> None:
    if not app.entries:
        return
    name, _, full = app.entries[app.cursor]
    _, ext = os.path.splitext(name)

    def _cb(app, buf):
        if not buf or buf == name:
            return
        if not os.path.splitext(buf)[1]:
            buf += ext
        new_path = os.path.join(os.path.dirname(full), buf)
        try:
            app._push_snapshot()
            os.rename(full, new_path)
            app.entries = _list_dir(app.current_dir)
        except Exception as e:
            _toast(app, f"Error al renombrar: {e}")

    _prompt(app, "Renombrar a", _cb, name)


def _start_tag_edit(app) -> None:
    if not app.entries:
        return
    _, is_dir, full = app.entries[app.cursor]
    if is_dir or not _is_media_file(full):
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


def _do_playlist_remove(app, idx: int) -> None:
    if idx < 0 or idx >= len(app.playlist):
        return
    app._push_snapshot()
    app.playlist.pop(idx)
    _save_playlist(app)


def _do_playlist_clear(app) -> None:
    app._push_snapshot()
    app.playlist.clear()
    _save_playlist(app)


def _do_history_remove(app) -> None:
    if 0 <= app.history_cursor < len(app.history):
        app.history.pop(app.history_cursor)
        if app.history_cursor > 0:
            app.history_cursor -= 1


def _do_history_clear(app) -> None:
    app.history.clear()
    app.history_cursor = 0
    app.history_scroll = 0


def _handle_explorer_filter(app, key: int) -> None:
    if key == 27:
        app.explorer_filter_mode = False
        app.explorer_filter = ""
        app.explorer_filtered = []
        app.cursor = 0
        app.scroll = 0
        curses.curs_set(0)
        return
    if key in (ord("\n"), 10, 13):
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
            curses.curs_set(0)
        return
    if key == curses.KEY_DOWN:
        if app.explorer_filtered:
            app.cursor = min(app.cursor + 1, len(app.explorer_filtered) - 1)
        return
    if key == curses.KEY_UP:
        app.cursor = max(app.cursor - 1, 0)
        return
    if key in (127, curses.KEY_BACKSPACE):
        app.explorer_filter = app.explorer_filter[:-1]
        _do_explorer_filter(app)
        return
    if 32 <= key <= 126:
        app.explorer_filter += chr(key)
        _do_explorer_filter(app)


def _do_explorer_filter(app) -> None:
    q = app.explorer_filter.lower().strip()
    if not q:
        app.explorer_filtered = list(range(len(app.entries)))
    else:
        app.explorer_filtered = [i for i, (name, _, _) in enumerate(app.entries)
                                  if q in name.lower()]
    app.cursor = 0
    app.scroll = 0


def _handle_playlist_filter(app, key: int) -> None:
    if key == 27:
        app.playlist_filter_mode = False
        app.playlist_filter = ""
        app.playlist_filtered = []
        app.playlist_cursor = 0
        app.playlist_scroll = 0
        curses.curs_set(0)
        return
    if key in (ord("\n"), 10, 13):
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
        list_h = h - app.FILTER_LIST_H
        if app.playlist_cursor >= app.playlist_scroll + list_h:
            app.playlist_scroll = app.playlist_cursor - list_h + 1
        return
    if key == curses.KEY_UP:
        app.playlist_cursor = max(app.playlist_cursor - 1, 0)
        if app.playlist_cursor < app.playlist_scroll:
            app.playlist_scroll = app.playlist_cursor
        return
    if key in (127, curses.KEY_BACKSPACE):
        app.playlist_filter = app.playlist_filter[:-1]
        _do_playlist_filter(app)
        return
    if 32 <= key <= 126:
        app.playlist_filter += chr(key)
        _do_playlist_filter(app)
        return


def _do_playlist_filter(app) -> None:
    q = app.playlist_filter.lower().strip()
    if not q:
        app.playlist_filtered = list(range(len(app.playlist)))
    else:
        app.playlist_filtered = [i for i, (name, path) in enumerate(app.playlist)
                                  if q in name.lower() or q in path.lower()]
    app.playlist_cursor = 0
    app.playlist_scroll = 0


def _save_playlist(app) -> None:
    from .playlist import save_all
    save_all(app.playlist_data, app.active_name)


def _switch_playlist(app, name: str) -> None:
    if name in app.playlist_data:
        app.active_name = name
        app.playlist_cursor = 0
        app.playlist_scroll = 0
        app.current_view = app.V_PLAYLIST
        app.playlist_filter_mode = False
        app.playlist_filter = ""
        app.playlist_filtered = []
        curses.curs_set(0)


def _create_playlist_cb(app, name: str) -> None:
    if name and name not in app.playlist_data:
        app.playlist_data[name] = []
        _switch_playlist(app, name)
        _save_playlist(app)


def _do_delete_playlist(app) -> None:
    if len(app.playlist_data) > 1:
        del app.playlist_data[app.active_name]
        new_name = next(n for n in app.playlist_data if n != app.active_name)
        _switch_playlist(app, new_name)
        _save_playlist(app)


def _rename_playlist_cb(app, new_name: str) -> None:
    if new_name and new_name != app.active_name and new_name not in app.playlist_data:
        app.playlist_data[new_name] = app.playlist_data.pop(app.active_name)
        app.active_name = new_name
        _save_playlist(app)


# ── File Operations ──

def _start_file_op(app, mode: str) -> None:
    if not app.entries:
        return
    _, is_dir, full = app.entries[app.cursor]
    if is_dir:
        return
    app.file_op_mode = mode
    app.file_op_source = full


def _do_file_op(app, dest_dir: str) -> None:
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


def _confirm_file_op(app, dest_dir: str) -> None:
    src = app.file_op_source
    mode = app.file_op_mode
    if not src or not os.path.isdir(dest_dir):
        return
    label = "Copiar" if mode == "copy" else "Mover"
    name = os.path.basename(src)
    dest_name = os.path.basename(dest_dir)
    _confirm(app, f"¿{label} '{name}' a '{dest_name}'?", lambda: _do_file_op(app, dest_dir))


def _handle_file_op_picker(app, key: int) -> None:
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
    elif key in (ord("\n"), 10, 13, ord("C"), ord("V")):
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
    elif key in (ord("u"), ord("U")):
        if key == ord("u"):
            app._undo_file_op()
        else:
            app._redo()
        return

    h, _ = app.stdscr.getmaxyx()
    list_h = h - app.LIST_H - (1 if app.file_op_mode else 0)
    if app.cursor < app.scroll:
        app.scroll = app.cursor
    elif app.cursor >= app.scroll + list_h:
        app.scroll = app.cursor - list_h + 1


# ── Config helpers ──

def _cycle_theme(app, direction: int) -> None:
    try:
        idx = THEME_NAMES.index(app.config["theme"])
    except ValueError:
        idx = 0
    new_theme = THEME_NAMES[(idx + direction) % len(THEME_NAMES)]
    app.config["theme"] = new_theme
    app._build_config_tabs()
    app.config_cursor = min(app.config_cursor, len(app.config_items) - 1)
    app._apply_theme()
    from .config import save as save_config
    save_config(app.config)


def _cycle_color(app, key_name: str, direction: int) -> None:
    colors = list(COLORS.keys())
    cc = app.config.setdefault("custom_colors", {})
    current = cc.get(key_name, "Blanco")
    try:
        idx = colors.index(current)
    except ValueError:
        idx = 0
    cc[key_name] = colors[(idx + direction) % len(colors)]
    app._apply_theme()
    from .config import save as save_config
    save_config(app.config)


def _config_int_inc(app, key_name: str) -> None:
    from .config import save as save_config
    if key_name == "volume":
        app.audio.set_volume(app.audio.volume + 5)
    elif key_name == "sleep_timer_minutes":
        val = app.config.get("sleep_timer_minutes", 30)
        app.config["sleep_timer_minutes"] = min(val + 1, 999)
    save_config(app.config)


def _config_int_dec(app, key_name: str) -> None:
    from .config import save as save_config
    if key_name == "volume":
        app.audio.set_volume(app.audio.volume - 5)
    elif key_name == "sleep_timer_minutes":
        val = app.config.get("sleep_timer_minutes", 30)
        app.config["sleep_timer_minutes"] = max(val - 1, 1)
    save_config(app.config)


# ── Keybinding helpers ──

def _open_keybindings(app) -> None:
    app.kb_keybinding_view = True
    app.kb_cursor = 0
    app.kb_capturing = False
    app.kb_capturing_action = None
    app.kb_conflict_msg = ""
    app.kb_conflict_other = ""


def _toggle_keybinding_mode(app) -> None:
    if app.keybinding_mode == "custom":
        app.config["keybinding_mode"] = "default"
        app.config["keybindings"] = {}
        app.keybinding_mode = "default"
        app.key_lookup = {}
    else:
        app.config["keybindings"] = dict(kb.DEFAULT_BINDINGS)
        app.config["keybinding_mode"] = "custom"
        app.keybinding_mode = "custom"
        app.key_lookup = kb.build_lookup(kb.DEFAULT_BINDINGS)
    app.kb_cursor = 0
    _save_keybindings(app)


def _assign_key(app, action: str, keycode: int) -> None:
    app.kb_conflict_msg = ""
    app.kb_conflict_other = ""

    conflicts = [a for a in kb.BINDABLE_ACTIONS
                 if a != action and _get_current_key(app, a) == keycode]
    if conflicts:
        app.kb_conflict_msg = f"Colisión: {kb.key_name(keycode)} ya está en '{conflicts[0]}'"
        app.kb_conflict_other = conflicts[0]

    bindings = _build_bindings_from_current(app)
    for a in list(bindings.keys()):
        if bindings[a] == keycode and a != action:
            bindings[a] = kb.DEFAULT_BINDINGS[a]
    bindings[action] = keycode
    cleaned = kb.resolve_conflicts(bindings)
    app.config["keybindings"] = cleaned
    app.config["keybinding_mode"] = "custom"
    app.keybinding_mode = "custom"
    app.key_lookup = kb.build_lookup(cleaned)
    _save_keybindings(app)


def _get_current_key(app, action: str) -> int:
    if app.keybinding_mode == "custom":
        return app.config.get("keybindings", {}).get(action, kb.DEFAULT_BINDINGS[action])
    return kb.DEFAULT_BINDINGS[action]


def _build_bindings_from_current(app) -> dict:
    return {a: _get_current_key(app, a) for a in kb.BINDABLE_ACTIONS}


def _save_keybindings(app) -> None:
    from .config import save as save_config
    app.config["keybinding_mode"] = app.keybinding_mode
    save_config(app.config)


# ── Prompt helpers ──

def _prompt(app, label: str, callback, initial: str = "") -> None:
    app.prompt_mode = True
    app.prompt_label = label
    app.prompt_buf = initial
    app.prompt_callback = callback
    curses.curs_set(1)
    curses.flushinp()


def _toast(app, msg: str) -> None:
    app.toast(msg)


def _confirm(app, label: str, callback) -> None:
    app.confirm_mode = True
    app.confirm_label = label
    app.confirm_callback = callback
    app.confirm_is_info = callback is None
    curses.flushinp()


# ── Update ──

def _handle_update(app) -> None:
    app._check_updates()
    if app.update_available:
        n = app.update_behind
        s = "s" if n != 1 else ""
        _confirm(app, f"Actualización disp. ({n} commit{s}) ¿Descargar?", lambda: _do_update(app))
    else:
        _toast(app, "Sin actualizaciones disponibles")


def _do_update(app) -> None:
    ok, msg = app._apply_updates()
    if ok:
        app.update_available = False
        _restart_app(app)
    else:
        _toast(app, msg)


def _restart_app(app) -> None:
    import os, sys
    try:
        from .state import save_state
        if app.current_file:
            save_state(True, app.current_file, max(0, app.audio.get_time()))
        else:
            save_state(False)
        app.audio.player.stop()
        curses.endwin()
        repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        app_path = os.path.join(repo, "app.py")
        os.execv(sys.executable, [sys.executable, app_path])
    except Exception:
        _toast(app, "Error al reiniciar, reiniciá manualmente")
