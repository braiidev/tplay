from __future__ import annotations

import curses
import os
from typing import TYPE_CHECKING, Any

from ..config import THEME_NAMES, COLORS, EQ_PRESETS, EQ_PRESET_NAMES
from .. import keybindings as kb
from .shared import _toast, _clamp_scroll
from ..ui import COMPACT_THRESHOLD

if TYPE_CHECKING:
    from player.app import PlayerApp


def _skip_disabled(app: PlayerApp, direction: int) -> None:
    """Move cursor in direction, skipping separators + non-Custom bands."""
    items = app.config_items
    total = len(items)
    is_custom = app.config.get("eq_preset", "Flat") == "Custom"
    last_valid = app.config_cursor
    app.config_cursor += direction
    while 0 <= app.config_cursor < total:
        _, _, ctype = items[app.config_cursor]
        if ctype != "separator" and not (ctype == "eq_band" and not is_custom):
            last_valid = app.config_cursor
        app.config_cursor += direction
    app.config_cursor = last_valid


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
        _skip_disabled(app, 1)
    elif key == curses.KEY_UP:
        _skip_disabled(app, -1)
    elif key in (curses.KEY_RIGHT, 10, 13):
        if total == 0:
            return
        key_name, _, ctype = app.config_items[app.config_cursor]
        if ctype == "choice":
            if key_name == "eq_preset":
                _cycle_eq_preset(app, 1)
            else:
                _cycle_theme(app, 1)
        elif ctype == "bool":
            _toggle_bool(app, key_name)
        elif ctype == "color":
            _cycle_color(app, key_name, 1)
        elif ctype == "int":
            _config_int_inc(app, key_name)
        elif ctype == "eq_preamp":
            _eq_preamp_inc(app)
        elif ctype == "eq_band":
            if app.config.get("eq_preset", "Flat") == "Custom":
                _eq_band_inc(app, key_name)
        elif ctype == "action" and key_name == "keybindings":
            _open_keybindings(app)
        elif ctype == "action" and key_name == "update":
            from .shared import _handle_update
            _handle_update(app)
        elif ctype == "path":
            _open_dir_picker(app, key_name)
    elif key == curses.KEY_LEFT:
        if total == 0:
            return
        key_name, _, ctype = app.config_items[app.config_cursor]
        if ctype == "choice":
            if key_name == "eq_preset":
                _cycle_eq_preset(app, -1)
            else:
                _cycle_theme(app, -1)
        elif ctype == "bool":
            _toggle_bool(app, key_name)
        elif ctype == "color":
            _cycle_color(app, key_name, -1)
        elif ctype == "int":
            _config_int_dec(app, key_name)
        elif ctype == "eq_preamp":
            _eq_preamp_dec(app)
        elif ctype == "eq_band":
            if app.config.get("eq_preset", "Flat") == "Custom":
                _eq_band_dec(app, key_name)
        elif ctype == "path":
            _open_dir_picker(app, key_name)

    elif key == ord("r"):
        if total == 0:
            return
        key_name, _, ctype = app.config_items[app.config_cursor]
        if ctype == "eq_band" and app.config.get("eq_preset", "Flat") == "Custom":
            idx = int(key_name.split("_")[-1])
            bands = list(app.config.get("eq_bands", [0.0] * 10))
            bands[idx] = 0.0
            app.config["eq_bands"] = bands
            if app.config.get("eq_enabled", False):
                _reapply_eq(app)
            from ..config import save as _save_config
            _save_config(app.config)
        elif ctype == "eq_preamp":
            app.config["eq_preamp"] = 0.0
            if app.config.get("eq_enabled", False):
                _reapply_eq(app)
            from ..config import save as _save_config
            _save_config(app.config)
        elif ctype == "choice" and key_name == "eq_preset":
            app.config["eq_bands"] = [0.0] * 10
            app.config["eq_preamp"] = 12.0
            app.config["eq_preset"] = "Flat"
            app._build_config_tabs()
            app.config_scroll = 0
            if app.config.get("eq_enabled", False):
                _reapply_eq(app)
            from ..config import save as _save_config
            _save_config(app.config)

    h, _ = app.stdscr.getmaxyx()
    list_h = h - 5 if h < COMPACT_THRESHOLD else h - 6
    app.config_scroll = _clamp_scroll(app.config_cursor, app.config_scroll, list_h)


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


def _toggle_bool(app: PlayerApp, key_name: str) -> None:
    app.config[key_name] = not app.config.get(key_name, True)
    if key_name == "eq_enabled":
        if app.config["eq_enabled"]:
            _reapply_eq(app)
        else:
            app.audio.disable_equalizer()
    from ..config import save as _save_config
    _save_config(app.config)


def _cycle_eq_preset(app: PlayerApp, direction: int) -> None:
    try:
        idx = EQ_PRESET_NAMES.index(app.config.get("eq_preset", "Flat"))
    except ValueError:
        idx = 0
    new_preset = EQ_PRESET_NAMES[(idx + direction) % len(EQ_PRESET_NAMES)]
    app.config["eq_preset"] = new_preset
    if new_preset != "Custom":
        bands = EQ_PRESETS.get(new_preset, [0.0] * 10)
        app.config["eq_bands"] = bands
    saved_cursor = app.config_cursor
    app._build_config_tabs()
    app.config_cursor = min(saved_cursor, len(app.config_items) - 1)
    app.config_scroll = 0
    if app.config.get("eq_enabled", False):
        preamp = app.config.get("eq_preamp", 0.0)
        app.audio.set_equalizer(app.config.get("eq_bands", [0.0] * 10), preamp)
    from ..config import save as _save_config
    _save_config(app.config)


def _eq_preamp_inc(app: PlayerApp) -> None:
    val = app.config.get("eq_preamp", 0.0)
    app.config["eq_preamp"] = min(20.0, round(val + 0.5, 1))
    if app.config.get("eq_enabled", False):
        _reapply_eq(app)
    from ..config import save as _save_config
    _save_config(app.config)


def _eq_preamp_dec(app: PlayerApp) -> None:
    val = app.config.get("eq_preamp", 0.0)
    app.config["eq_preamp"] = max(-20.0, round(val - 0.5, 1))
    if app.config.get("eq_enabled", False):
        _reapply_eq(app)
    from ..config import save as _save_config
    _save_config(app.config)


def _eq_band_inc(app: PlayerApp, key_name: str) -> None:
    idx = int(key_name.split("_")[-1])
    bands = list(app.config.get("eq_bands", [0.0] * 10))
    bands[idx] = min(20.0, round(bands[idx] + 0.5, 1))
    app.config["eq_bands"] = bands
    if app.config.get("eq_enabled", False):
        _reapply_eq(app)
    from ..config import save as _save_config
    _save_config(app.config)


def _eq_band_dec(app: PlayerApp, key_name: str) -> None:
    idx = int(key_name.split("_")[-1])
    bands = list(app.config.get("eq_bands", [0.0] * 10))
    bands[idx] = max(-20.0, round(bands[idx] - 0.5, 1))
    app.config["eq_bands"] = bands
    if app.config.get("eq_enabled", False):
        _reapply_eq(app)
    from ..config import save as _save_config
    _save_config(app.config)


def _reapply_eq(app: PlayerApp) -> None:
    preset_name = app.config.get("eq_preset", "Flat")
    if preset_name == "Custom":
        bands = app.config.get("eq_bands", [0.0] * 10)
    else:
        bands = EQ_PRESETS.get(preset_name, [0.0] * 10)
    preamp = app.config.get("eq_preamp", 0.0)
    app.audio.set_equalizer(bands, preamp)


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
    elif key in (10, 13):
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


# ── Directory Picker ──

def _open_dir_picker(app: PlayerApp, key_name: str) -> None:
    current = app.config.get(key_name, os.path.expanduser("~/Music"))
    app.dir_picker_mode = True
    app.dir_picker_config_key = key_name
    app.dir_picker_path = os.path.abspath(current)
    _reload_dir_picker(app)
    app.dir_picker_cursor = 0
    app.dir_picker_scroll = 0
    curses.flushinp()


def _reload_dir_picker(app: PlayerApp) -> None:
    from ..file_utils import list_dir
    all_entries = list_dir(app.dir_picker_path)
    app.dir_picker_entries = [(n, d, f) for n, d, f in all_entries if d]


def handle_dir_picker(app: PlayerApp, key: int) -> None:
    total = len(app.dir_picker_entries)

    if key == 27:
        app.dir_picker_mode = False
        curses.flushinp()
        return

    if key in (10, 13):
        if total > 0 and app.dir_picker_cursor < total:
            _, _, full = app.dir_picker_entries[app.dir_picker_cursor]
            app.config[app.dir_picker_config_key] = full
            from ..config import save as _save_config
            _save_config(app.config)
            _toast(app, f"Directorio: {full}")
        app.dir_picker_mode = False
        curses.flushinp()
        return

    if key in (curses.KEY_DOWN, ord("j")):
        app.dir_picker_cursor = min(app.dir_picker_cursor + 1, max(0, total - 1))
    elif key in (curses.KEY_UP, ord("k")):
        app.dir_picker_cursor = max(app.dir_picker_cursor - 1, 0)
    elif key in (curses.KEY_RIGHT, ord("l")):
        if total > 0 and app.dir_picker_cursor < total:
            _, _, full = app.dir_picker_entries[app.dir_picker_cursor]
            app.dir_picker_path = full
            _reload_dir_picker(app)
            app.dir_picker_cursor = 0
            app.dir_picker_scroll = 0
    elif key in (curses.KEY_LEFT, ord("h"), 127, curses.KEY_BACKSPACE):
        parent = os.path.dirname(app.dir_picker_path.rstrip("/"))
        if parent and parent != app.dir_picker_path:
            app.dir_picker_path = parent
            _reload_dir_picker(app)
            app.dir_picker_cursor = 0
            app.dir_picker_scroll = 0
    elif key == ord("~"):
        app.dir_picker_path = os.path.expanduser("~")
        _reload_dir_picker(app)
        app.dir_picker_cursor = 0
        app.dir_picker_scroll = 0
    elif key == ord("g"):
        app.dir_picker_cursor = 0
    elif key == ord("G"):
        app.dir_picker_cursor = max(0, total - 1)

    h, _ = app.stdscr.getmaxyx()
    list_h = max(1, h - 5 if h >= 16 else h - 4)
    app.dir_picker_scroll = _clamp_scroll(app.dir_picker_cursor, app.dir_picker_scroll, list_h)
