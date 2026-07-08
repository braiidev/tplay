import curses
import os

from .config import THEME_NAMES, COLORS
from .file_utils import list_dir as _list_dir, is_media as _is_media_file
from . import keybindings as kb


def handle_explorer(app, key: int) -> None:
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
        if app.entries:
            name, is_dir, full = app.entries[app.cursor]
            if not is_dir:
                _playlist_append(app, full)
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

    h, _ = app.stdscr.getmaxyx()
    list_h = h - app.LIST_H
    if app.cursor < app.scroll:
        app.scroll = app.cursor
    elif app.cursor >= app.scroll + list_h:
        app.scroll = app.cursor - list_h + 1


def handle_history(app, key: int) -> None:
    if key == 27:
        app.current_view = 3
        curses.flushinp()
        return
    if not app.history:
        return
    if key in (ord("\n"), 10, 13):
        _, path = app.history[app.history_cursor]
        app.audio.play_file(path)
        app.current_view = 3
        return
    if key == ord("x"):
        app.history.clear()
        app.history_cursor = 0
        app.history_scroll = 0
        return
    if key == curses.KEY_DOWN:
        app.history_cursor = min(app.history_cursor + 1, len(app.history) - 1)
    elif key == curses.KEY_UP:
        app.history_cursor = max(app.history_cursor - 1, 0)
    h, _ = app.stdscr.getmaxyx()
    list_h = h - 5
    if app.history_cursor < app.history_scroll:
        app.history_scroll = app.history_cursor
    elif app.history_cursor >= app.history_scroll + list_h:
        app.history_scroll = app.history_cursor - list_h + 1


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
            _play_playlist_idx(app, app.playlist_cursor)
    elif key == ord("d"):
        app._push_snapshot()
        _playlist_remove(app, app.playlist_cursor)
        if app.playlist_cursor >= len(app.playlist) and app.playlist_cursor > 0:
            app.playlist_cursor -= 1
    elif key == ord("x"):
        app._push_snapshot()
        app.playlist.clear()
        app.playlist_idx = -1
        app.playlist_cursor = 0
        app.audio.stop()
        _save_playlist(app)
    elif key == ord("["):
        names = list(app.playlist_data.keys())
        if len(names) > 1:
            app._push_snapshot()
            idx = names.index(app.active_name)
            _switch_playlist(app, names[(idx - 1) % len(names)])
    elif key == ord("]"):
        names = list(app.playlist_data.keys())
        if len(names) > 1:
            app._push_snapshot()
            idx = names.index(app.active_name)
            _switch_playlist(app, names[(idx + 1) % len(names)])
    elif key == ord("C"):
        app._push_snapshot()
        _prompt(app, "Nombre de la nueva playlist", _create_playlist_cb)
    elif key == ord("E"):
        if app.active_name == "default":
            return
        app._push_snapshot()
        _prompt(app, f"Renombrar '{app.active_name}' a", _rename_playlist_cb)
    elif key == ord("D"):
        if len(app.playlist_data) > 1 and app.active_name != "default":
            app._push_snapshot()
            _confirm(app, f"¿Borrar '{app.active_name}'?", lambda: _do_delete_playlist(app))
    elif key == ord("K"):
        if app.playlist_cursor > 0:
            app._push_snapshot()
            i = app.playlist_cursor
            pl = app.playlist
            pl[i], pl[i - 1] = pl[i - 1], pl[i]
            app.playlist_cursor -= 1
            if app.playlist_idx == i:
                app.playlist_idx = i - 1
            elif app.playlist_idx == i - 1:
                app.playlist_idx = i
            _save_playlist(app)
    elif key == ord("J"):
        if app.playlist_cursor < len(app.playlist) - 1:
            app._push_snapshot()
            i = app.playlist_cursor
            pl = app.playlist
            pl[i], pl[i + 1] = pl[i + 1], pl[i]
            app.playlist_cursor += 1
            if app.playlist_idx == i:
                app.playlist_idx = i + 1
            elif app.playlist_idx == i + 1:
                app.playlist_idx = i
            _save_playlist(app)

    h, _ = app.stdscr.getmaxyx()
    list_h = h - app.LIST_H
    if app.playlist_cursor < app.playlist_scroll:
        app.playlist_scroll = app.playlist_cursor
    elif app.playlist_cursor >= app.playlist_scroll + list_h:
        app.playlist_scroll = app.playlist_cursor - list_h + 1


def handle_search(app, key: int) -> None:
    if key == 27:
        app.current_view = 1
        curses.curs_set(0)
        return
    if key == ord("\n") or key == 10 or key == 13:
        if app.search_results:
            path = app.search_results[app.search_cursor]
            _play_file_direct(app, path)
            app.current_view = 3
        curses.curs_set(0)
        return
    if key == curses.KEY_DOWN:
        if app.search_results:
            app.search_cursor = min(app.search_cursor + 1, len(app.search_results) - 1)
    elif key == curses.KEY_UP:
        app.search_cursor = max(app.search_cursor - 1, 0)
    elif key == 127 or key == curses.KEY_BACKSPACE:
        app.search_query = app.search_query[:-1]
        _do_search(app)
    elif 32 <= key <= 126:
        app.search_query += chr(key)
        _do_search(app)

    h, _ = app.stdscr.getmaxyx()
    list_h = h - app.SEARCH_LIST_H
    if app.search_cursor < app.search_scroll:
        app.search_scroll = app.search_cursor
    elif app.search_cursor >= app.search_scroll + list_h:
        app.search_scroll = app.search_cursor - list_h + 1


def handle_config(app, key: int) -> None:
    if key == curses.KEY_DOWN:
        app.config_cursor = min(app.config_cursor + 1, len(app.config_items) - 1)
    elif key == curses.KEY_UP:
        app.config_cursor = max(app.config_cursor - 1, 0)
    elif key in (curses.KEY_RIGHT, ord("\n"), 10, 13):
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
        key_name, _, ctype = app.config_items[app.config_cursor]
        if ctype == "choice":
            _cycle_theme(app, -1)
        elif ctype == "color":
            _cycle_color(app, key_name, -1)
        elif ctype == "int":
            _config_int_dec(app, key_name)
    elif key == ord("/") or key == ord("e"):
        key_name, _, ctype = app.config_items[app.config_cursor]
        if ctype == "path" and key_name == "music_dir":
            app.current_view = 1
            curses.flushinp()
    elif key == curses.KEY_F2:
        _open_keybindings(app)


def handle_now_playing(app, key: int) -> None:
    if key in (ord("\t"),):
        app.show_temp_queue = True
        app.tq_cursor = 0
        app.tq_scroll = 0
        curses.flushinp()
        return
    SEEK_STEP = 5000
    if key in (curses.KEY_LEFT,):
        cur = app.audio.get_time()
        app.audio.player.set_time(max(0, cur - SEEK_STEP))
    elif key in (curses.KEY_RIGHT,):
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


def handle_temp_queue(app, key: int) -> None:
    if key in (ord("u"), ord("U")):
        if key == ord("u"):
            app._undo()
        else:
            app._redo()
        _save_playlist(app)
        return
    if key in (ord("\t"), 27):
        app.show_temp_queue = False
        curses.flushinp()
        return
    if key in (ord("n"),):
        if not app._auto_next_temp():
            app.audio.next(app.playlist)
        return
    if key in (ord("p"),):
        app._auto_prev_temp()
        return
    if key == ord("+"):
        app.audio.set_volume(app.audio.volume + 5)
        return
    if key == ord("-"):
        app.audio.set_volume(app.audio.volume - 5)
        return
    if not app.temp_queue:
        return
    if key in (ord("\n"), ord("\r"), curses.KEY_ENTER):
        path, consumable = app.temp_queue[app.tq_cursor]
        if consumable:
            app.temp_queue.pop(app.tq_cursor)
            if app.tq_cursor >= len(app.temp_queue) and app.tq_cursor > 0:
                app.tq_cursor -= 1
            if app.tq_playhead > app.tq_cursor:
                app.tq_playhead -= 1
            elif app.tq_playhead == app.tq_cursor:
                app.tq_playhead = -1
        else:
            app.tq_playhead = app.tq_cursor
        app.audio.play_file(path)
        app.current_view = 3
        return
    if key in (curses.KEY_DOWN, ord("j")):
        app.tq_cursor = min(app.tq_cursor + 1, len(app.temp_queue) - 1)
    elif key in (curses.KEY_UP, ord("k")):
        app.tq_cursor = max(app.tq_cursor - 1, 0)
    elif key == ord("d"):
        app._push_snapshot()
        app.temp_queue.pop(app.tq_cursor)
        if app.tq_cursor >= len(app.temp_queue) and app.tq_cursor > 0:
            app.tq_cursor -= 1
        if app.tq_playhead >= len(app.temp_queue):
            app.tq_playhead = len(app.temp_queue) - 1
        if app.tq_cursor <= app.tq_playhead and app.tq_playhead >= 0:
            app.tq_playhead -= 1
    elif key == ord("x"):
        app._push_snapshot()
        app.temp_queue.clear()
        app.tq_cursor = 0
        app.tq_playhead = -1
        app.tq_scroll = 0
    elif key == ord("K"):
        if app.tq_cursor > 0:
            app._push_snapshot()
            i = app.tq_cursor
            app.temp_queue[i], app.temp_queue[i - 1] = app.temp_queue[i - 1], app.temp_queue[i]
            app.tq_cursor -= 1
            if app.tq_playhead == i:
                app.tq_playhead = i - 1
            elif app.tq_playhead == i - 1:
                app.tq_playhead = i
    elif key == ord("J"):
        if app.tq_cursor < len(app.temp_queue) - 1:
            app._push_snapshot()
            i = app.tq_cursor
            app.temp_queue[i], app.temp_queue[i + 1] = app.temp_queue[i + 1], app.temp_queue[i]
            app.tq_cursor += 1
            if app.tq_playhead == i:
                app.tq_playhead = i + 1
            elif app.tq_playhead == i + 1:
                app.tq_playhead = i
    elif key == ord("s"):
        if app.temp_queue:
            _prompt(app, "Guardar cola como playlist", _save_temp_queue_cb)
    elif key == ord("N"):
        app._push_snapshot()
        item = app.temp_queue.pop(app.tq_cursor)
        app.temp_queue.insert(0, (item[0], True))
        if app.tq_cursor == app.tq_playhead:
            app.tq_playhead = 0
        elif app.tq_cursor > app.tq_playhead:
            app.tq_playhead += 1
        app.tq_cursor = 0
        app.tq_scroll = 0
    elif key == ord("g"):
        app.tq_cursor = 0
        app.tq_scroll = 0
    elif key == ord("G"):
        app.tq_cursor = len(app.temp_queue) - 1
    elif key in (curses.KEY_NPAGE,):
        h, _ = app.stdscr.getmaxyx()
        page = h - 8
        app.tq_cursor = min(app.tq_cursor + page, len(app.temp_queue) - 1)
    elif key in (curses.KEY_PPAGE,):
        h, _ = app.stdscr.getmaxyx()
        page = h - 8
        app.tq_cursor = max(app.tq_cursor - page, 0)
    h, _ = app.stdscr.getmaxyx()
    list_h = h - 8
    if app.tq_cursor < app.tq_scroll:
        app.tq_scroll = app.tq_cursor
    elif app.tq_cursor >= app.tq_scroll + list_h:
        app.tq_scroll = app.tq_cursor - list_h + 1


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


def handle_keybindings(app, key: int) -> None:
    if key == 27:
        _save_keybindings(app)
        app.current_view = 0
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


# ── Internal helpers used by handlers ──

def _page_size(app) -> int:
    h, _ = app.stdscr.getmaxyx()
    return max(1, h - app.LIST_H)


def _play_file_direct(app, path: str) -> None:
    app.temp_queue.clear()
    app.tq_playhead = -1
    app.audio.play_file(path)
    app.current_view = 3


def _play_playlist_idx(app, idx: int) -> None:
    if idx < 0 or idx >= len(app.playlist):
        return
    app.playlist_idx = idx
    app.temp_queue.clear()
    app.tq_playhead = -1
    app.audio.play_file(app.playlist[idx][1])


def _playlist_append(app, path: str) -> None:
    app._push_snapshot()
    name = os.path.basename(path)
    app.playlist.append((name, path))
    _save_playlist(app)
    if app.playlist_idx == -1:
        app.playlist_idx = 0
        app.temp_queue.clear()
        app.tq_playhead = -1
        app.audio.play_file(path)


def _playlist_remove(app, idx: int) -> None:
    if idx < 0 or idx >= len(app.playlist):
        return
    is_current = (idx == app.playlist_idx and app.audio.playing)
    app.playlist.pop(idx)
    if idx < app.playlist_idx:
        app.playlist_idx -= 1
    if not app.playlist:
        app.playlist_idx = -1
    elif app.playlist_idx >= len(app.playlist):
        app.playlist_idx = len(app.playlist) - 1
    _save_playlist(app)
    if is_current:
        app.audio.stop()
        if app.playlist and app.playlist_idx >= 0:
            _play_playlist_idx(app, app.playlist_idx)


def _save_playlist(app) -> None:
    from .playlist import save_all
    save_all(app.playlist_data, app.active_name)


def _switch_playlist(app, name: str) -> None:
    if name in app.playlist_data:
        app.active_name = name
        app.playlist_idx = 0 if app.playlist else -1
        app.playlist_cursor = 0
        app.playlist_scroll = 0
        app.current_view = 2
        app.playlist_filter_mode = False
        app.playlist_filter = ""
        app.playlist_filtered = []
        curses.curs_set(0)


def _do_playlist_filter(app) -> None:
    q = app.playlist_filter.lower().strip()
    if not q:
        app.playlist_filtered = list(range(len(app.playlist)))
    else:
        app.playlist_filtered = [i for i, (name, path) in enumerate(app.playlist)
                                  if q in name.lower() or q in path.lower()]
    app.playlist_cursor = 0
    app.playlist_scroll = 0


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
            _play_playlist_idx(app, app.playlist_filtered[app.playlist_cursor])
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


def _do_search(app) -> None:
    q = app.search_query.lower().strip()
    if not q:
        app.search_results = []
        app.search_cursor = 0
        app.search_scroll = 0
        return
    results = []
    limit = 200

    def _walk(path):
        nonlocal results
        if len(results) >= limit:
            return
        try:
            with os.scandir(path) as entries:
                for entry in entries:
                    if len(results) >= limit:
                        return
                    if entry.name.startswith("."):
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        _walk(entry.path)
                    elif _is_media_file(entry.name) and q in entry.name.lower():
                        results.append(entry.path)
        except (PermissionError, OSError):
            pass

    _walk(app.current_dir)
    app.search_results = sorted(results)
    app.search_cursor = 0
    app.search_scroll = 0


def _cycle_theme(app, direction: int) -> None:
    idx = THEME_NAMES.index(app.config["theme"])
    new_theme = THEME_NAMES[(idx + direction) % len(THEME_NAMES)]
    app.config["theme"] = new_theme
    app._build_config_items()
    app.config_cursor = min(app.config_cursor, len(app.config_items) - 1)
    app._apply_theme()
    from .config import save as save_config
    save_config(app.config)


def _cycle_color(app, key_name: str, direction: int) -> None:
    colors = list(COLORS.keys())
    cc = app.config.setdefault("custom_colors", {})
    current = cc.get(key_name, "Blanco")
    idx = colors.index(current)
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


def _open_keybindings(app) -> None:
    app.current_view = 5
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


def _confirm(app, label: str, callback) -> None:
    app.confirm_mode = True
    app.confirm_label = label
    app.confirm_callback = callback
    app.confirm_is_info = callback is None
    curses.flushinp()


def _save_temp_queue_cb(app, name: str) -> None:
    import os as _os
    if name and name not in app.playlist_data:
        app.playlist_data[name] = [(_os.path.basename(p), p) for p, _ in app.temp_queue]
        _save_playlist(app)


def _create_playlist_cb(app, name: str) -> None:
    if name and name not in app.playlist_data:
        app.playlist_data[name] = []
        _switch_playlist(app, name)
        _save_playlist(app)


def _do_delete_playlist(app) -> None:
    if len(app.playlist_data) > 1 and app.active_name != "default":
        del app.playlist_data[app.active_name]
        new_name = next(n for n in app.playlist_data if n != app.active_name)
        _switch_playlist(app, new_name)
        _save_playlist(app)


def _rename_playlist_cb(app, new_name: str) -> None:
    if new_name and new_name != app.active_name and new_name not in app.playlist_data:
        app.playlist_data[new_name] = app.playlist_data.pop(app.active_name)
        app.active_name = new_name
        _save_playlist(app)


# ── Update ──

def _handle_update(app) -> None:
    app._check_updates()
    if app.update_available:
        n = app.update_behind
        s = "s" if n != 1 else ""
        _confirm(app, f"Actualización disp. ({n} commit{s}) ¿Descargar?", lambda: _do_update(app))
    else:
        _confirm(app, "Sin actualizaciones disponibles", None)


def _do_update(app) -> None:
    ok, msg = app._apply_updates()
    if ok:
        app.update_available = False
        _restart_app(app)
    else:
        _confirm(app, msg, None)


def _restart_app(app) -> None:
    import os, sys
    try:
        app.audio.player.stop()
        curses.endwin()
        repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        app_path = os.path.join(repo, "app.py")
        os.execv(sys.executable, [sys.executable, app_path])
    except Exception:
        _confirm(app, "Error al reiniciar, reiniciá manualmente", None)
