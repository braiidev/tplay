from __future__ import annotations

import curses
from typing import TYPE_CHECKING, Any

from ..config import THEME_NAMES, COLORS
from .. import keybindings as kb
from .shared import _toast

if TYPE_CHECKING:
    from player.app import PlayerApp


def handle_config(app: PlayerApp, key: int) -> None:
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
            from .shared import _handle_update
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


def _cycle_theme(app: PlayerApp, direction: int) -> None:
    try:
        idx = THEME_NAMES.index(app.config["theme"])
    except ValueError:
        idx = 0
    new_theme = THEME_NAMES[(idx + direction) % len(THEME_NAMES)]
    app.config["theme"] = new_theme
    app._build_config_tabs()
    app.config_cursor = min(app.config_cursor, len(app.config_items) - 1)
    app._apply_theme()
    from ..config import save as _save_config
    _save_config(app.config)


def _cycle_color(app: PlayerApp, key_name: str, direction: int) -> None:
    colors = list(COLORS.keys())
    cc = app.config.setdefault("custom_colors", {})
    current = cc.get(key_name, "Blanco")
    try:
        idx = colors.index(current)
    except ValueError:
        idx = 0
    cc[key_name] = colors[(idx + direction) % len(colors)]
    app._apply_theme()
    from ..config import save as _save_config
    _save_config(app.config)


def _config_int_inc(app: PlayerApp, key_name: str) -> None:
    from ..config import save as _save_config
    if key_name == "volume":
        app.audio.set_volume(app.audio.volume + 5)
    elif key_name == "sleep_timer_minutes":
        val = app.config.get("sleep_timer_minutes", 30)
        app.config["sleep_timer_minutes"] = min(val + 1, 999)
    _save_config(app.config)


def _config_int_dec(app: PlayerApp, key_name: str) -> None:
    from ..config import save as _save_config
    if key_name == "volume":
        app.audio.set_volume(app.audio.volume - 5)
    elif key_name == "sleep_timer_minutes":
        val = app.config.get("sleep_timer_minutes", 30)
        app.config["sleep_timer_minutes"] = max(val - 1, 1)
    _save_config(app.config)


# ── Keybinding editor ──

def handle_keybindings(app: PlayerApp, key: int) -> None:
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
            if app.kb_capturing_action is not None:
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


def _open_keybindings(app: PlayerApp) -> None:
    app.kb_keybinding_view = True
    app.kb_cursor = 0
    app.kb_capturing = False
    app.kb_capturing_action = None
    app.kb_conflict_msg = ""
    app.kb_conflict_other = ""


def _toggle_keybinding_mode(app: PlayerApp) -> None:
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


def _assign_key(app: PlayerApp, action: str, keycode: int) -> None:
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


def _get_current_key(app: PlayerApp, action: str) -> int:
    if app.keybinding_mode == "custom":
        return int(app.config.get("keybindings", {}).get(action, kb.DEFAULT_BINDINGS[action]))
    return int(kb.DEFAULT_BINDINGS[action])


def _build_bindings_from_current(app: PlayerApp) -> dict[str, int]:
    return {a: _get_current_key(app, a) for a in kb.BINDABLE_ACTIONS}


def _save_keybindings(app: PlayerApp) -> None:
    from ..config import save as _save_config
    app.config["keybinding_mode"] = app.keybinding_mode
    _save_config(app.config)
