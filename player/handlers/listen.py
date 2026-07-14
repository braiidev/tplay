from __future__ import annotations

import curses
import os
from typing import TYPE_CHECKING

from ..file_utils import is_url as _is_url
from .shared import _prompt, _toast, _confirm, _clamp_scroll
from .shared import _do_clear_stack, _save_stack_as_playlist_cb, _prompt_export_m3u
from .shared import _open_tag_editor, _toggle_favorite

if TYPE_CHECKING:
    from player.app import PlayerApp


def _do_stack_remove(app: PlayerApp, index: int) -> None:
    app._push_snapshot()
    app.stack.remove(index)
    if not app.stack.items:
        app.audio.stop()
    elif app.stack_cursor >= len(app.stack.items):
        app.stack_cursor = len(app.stack.items) - 1


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
    elif key in (ord("s"),):
        app.audio.stop()
        app.audio.sleep_timer_active = False
        app.audio.sleep_timer_expired = False
    elif key in (ord("k"),):
        app.audio.set_volume(app.audio.volume + 5)
    elif key in (ord("j"),):
        app.audio.set_volume(app.audio.volume - 5)
    elif key == ord("r"):
        app.stack.shuffle = not app.stack.shuffle
        _toast(app, "Aleatorio: " + ("ON" if app.stack.shuffle else "OFF"))
    elif key == ord("R"):
        app.stack.repeat = not app.stack.repeat
        _toast(app, "Repetir: " + ("ON" if app.stack.repeat else "OFF"))
    elif key == ord("m"):
        app.audio.toggle_mute()
    elif key == ord("w"):
        app.audio.set_rate(app.audio.rate + 0.25)
        _toast(app, f"Velocidad: {app.audio.rate:.2f}x")
    elif key == ord("W"):
        app.audio.set_rate(app.audio.rate - 0.25)
        _toast(app, f"Velocidad: {app.audio.rate:.2f}x")
    elif key == ord("f"):
        cur_item = app.stack.current
        if cur_item and not _is_url(cur_item.path):
            _toggle_favorite(app, cur_item.path, cur_item.name)
        elif app.current_file and not _is_url(app.current_file):
            _toggle_favorite(app, app.current_file, os.path.basename(app.current_file))
        else:
            _toast(app, "No hay archivo local para añadir")
    elif key == ord("t"):
        app._toggle_sleep_timer()
    elif key == ord("T"):
        _prompt(app, "Minutos temporizador",
                lambda a, b: app._setup_sleep_timer(b),
                str(app.config.get("sleep_timer_minutes", 30)))
    elif key == ord("E"):
        app.audio._eq_enabled = not app.audio._eq_enabled
        if app.audio._eq_enabled:
            preset_name = app.config.get("eq_preset", "Flat")
            from ..config import EQ_PRESETS
            bands = EQ_PRESETS.get(preset_name, [0.0] * 10)
            preamp = app.config.get("eq_preamp", 0.0)
            app.audio.set_equalizer(bands, preamp)
        else:
            app.audio.disable_equalizer()
        _toast(app, f"EQ: {'ON' if app.audio._eq_enabled else 'OFF'}")


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
        if app.stack.items:
            idx = app.stack_cursor
            name = app.stack.items[idx].name
            _confirm(app, f"¿Eliminar '{name}'?", lambda i=idx: _do_stack_remove(app, i))
    elif key == ord("f"):
        if app.stack.items and app.stack_cursor < len(app.stack.items):
            item = app.stack.items[app.stack_cursor]
            _toggle_favorite(app, item.path, item.name)
    elif key in (ord("x"),):
        _confirm(app, "¿Limpiar toda la pila?", lambda: _do_clear_stack(app))
    elif key in (ord("s"),):
        if app.stack.items:
            _prompt(app, "Guardar pila como lista", _save_stack_as_playlist_cb)
    elif key in (ord("X"),):
        _prompt_export_m3u(app)
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
