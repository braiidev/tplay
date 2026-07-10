from __future__ import annotations

import curses
import os
from typing import TYPE_CHECKING

from ..file_utils import is_url as _is_url
from ..stack import StackItem
from .shared import _prompt, _toast, _confirm, _clamp_scroll
from .shared import _do_clear_stack, _save_stack_as_playlist_cb, _prompt_export_m3u
from .shared import _prompt_import_m3u_pls
from .shared import _open_tag_editor

if TYPE_CHECKING:
    from player.app import PlayerApp


def handle_listen(app: PlayerApp, key: int) -> None:
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
    elif key == ord("I"):
        cur_item = app.stack.current
        if cur_item and not _is_url(cur_item.path) and os.path.isfile(cur_item.path):
            _open_tag_editor(app, cur_item.path)
        else:
            _toast(app, "No hay archivo para editar")
    elif key == ord("o"):
        _prompt(app, "URL de stream", _add_url_cb)


def _add_url_cb(app: PlayerApp, url: str) -> None:
    url = url.strip()
    if not url or not _is_url(url):
        return
    name = url.split("//", 1)[-1].split("/")[0] if "//" in url else url
    item = StackItem(path=url, name=name)
    app.stack.append(item)
    if app.stack.playhead == 0 and not app.audio.playing:
        app._play_current()


def handle_stack_view(app: PlayerApp, key: int) -> None:
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
    if key in (10, 13):
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
    elif key in (ord("X"),):
        _prompt_export_m3u(app)
    elif key in (ord("O"),):
        _prompt_import_m3u_pls(app)
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
    app.stack_scroll = _clamp_scroll(app.stack_cursor, app.stack_scroll, h - 8)


def handle_goto(app: PlayerApp, key: int) -> None:
    if key == 27:
        app.goto_mode = False
        curses.flushinp()
        return
    if key in (10, 13):
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
