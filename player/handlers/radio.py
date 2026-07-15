from __future__ import annotations

import curses
import os
from typing import TYPE_CHECKING

from ..stack import StackItem
from ..radios import save_radios
from .shared import _prompt, _toast, _confirm, _clamp_scroll, _toggle_favorite
from ..ui import COMPACT_THRESHOLD

if TYPE_CHECKING:
    from player.app import PlayerApp


def _add_radio_name_cb(app: PlayerApp, name: str) -> None:
    name = name.strip()
    if not name:
        return
    app._radio_pending_name = name
    _prompt(app, "URL de la radio", _add_radio_url_cb)


def _add_radio_url_cb(app: PlayerApp, url: str) -> None:
    url = url.strip()
    if not url:
        return
    name = app._radio_pending_name
    app.radios.append({"name": name, "url": url})
    save_radios(app.radios)
    _toast(app, f"Radio '{name}' agregada")


def _edit_radio_cb(app: PlayerApp, buf: str) -> None:
    idx = app.radio_edit_idx
    field = app.radio_edit_field
    if idx is None or field is None or not buf.strip():
        app.radio_edit_idx = None
        app.radio_edit_field = None
        return
    app.radios[idx][field] = buf.strip()
    save_radios(app.radios)
    if field == "name" and app.radio_edit_cycle:
        app.radio_edit_field = "url"
        _prompt(app, "Nueva URL", _edit_radio_cb, app.radios[idx]["url"])
        return
    app.radio_edit_idx = None
    app.radio_edit_field = None
    app.radio_edit_cycle = False
    _toast(app, "Radio actualizada")


def _do_play_radio(app: PlayerApp) -> None:
    if not app.radios or app.radio_cursor >= len(app.radios):
        return
    r = app.radios[app.radio_cursor]
    item = StackItem(path=r["url"], name=r["name"])
    app.stack.items = [item]
    app.audio.play_file(r["url"])
    app.current_view = app.V_LISTEN
    app._add_history(r["url"], name=r["name"])


def _do_delete_radio(app: PlayerApp) -> None:
    if not app.radios or app.radio_cursor >= len(app.radios):
        return
    name = app.radios[app.radio_cursor]["name"]
    app.radios.pop(app.radio_cursor)
    save_radios(app.radios)
    if app.radio_cursor >= len(app.radios) and app.radio_cursor > 0:
        app.radio_cursor -= 1
    _toast(app, f"Radio '{name}' eliminada")


def _do_export_radios_m3u(app: PlayerApp) -> None:
    if not app.radios:
        _toast(app, "No hay radios para exportar")
        return
    music_dir = app.config.get("music_dir", os.path.expanduser("~/Music"))
    dest = os.path.join(music_dir, "radios.m3u")
    try:
        lines: list[str] = ["#EXTM3U\n"]
        for r in app.radios:
            lines.append(f"#EXTINF:-1,{r['name']}\n")
            lines.append(f"{r['url']}\n")
        with open(dest, "w", encoding="utf-8") as f:
            f.writelines(lines)
        _toast(app, "Radios exportadas a radios.m3u")
    except Exception as e:
        _toast(app, f"Error al exportar: {e}")


def _get_radio_page(app: PlayerApp) -> int:
    h, _ = app.stdscr.getmaxyx()
    return int(max(1, h - app.LIST_H - (0 if h < COMPACT_THRESHOLD else 1)))


def handle_radio(app: PlayerApp, key: int) -> None:
    if key == ord("a"):
        _prompt(app, "Nombre de la radio", _add_radio_name_cb)
        return
    if key in (10, 13):
        _do_play_radio(app)
        return
    if key == ord("d") and app.radios and 0 <= app.radio_cursor < len(app.radios):
        name = app.radios[app.radio_cursor]["name"]
        _confirm(app, f"¿Eliminar radio '{name}'?", lambda: _do_delete_radio(app))
        return
    if key == ord("E") and app.radios and 0 <= app.radio_cursor < len(app.radios):
        r = app.radios[app.radio_cursor]
        app.radio_edit_idx = app.radio_cursor
        app.radio_edit_field = "name"
        app.radio_edit_cycle = True
        _prompt(app, "Nuevo nombre", _edit_radio_cb, r["name"])
        return
    if key == ord("s"):
        save_radios(app.radios)
        _toast(app, "Radios guardadas")
        return
    if key == ord("X"):
        _do_export_radios_m3u(app)
        return
    if key == ord("f") and app.radios and 0 <= app.radio_cursor < len(app.radios):
        r = app.radios[app.radio_cursor]
        _toggle_favorite(app, r["url"], r["name"])
        return
    if not app.radios:
        return
    if key == curses.KEY_DOWN:
        app.radio_cursor = min(app.radio_cursor + 1, len(app.radios) - 1)
    elif key == curses.KEY_UP:
        app.radio_cursor = max(app.radio_cursor - 1, 0)
    elif key == curses.KEY_NPAGE:
        app.radio_cursor = min(app.radio_cursor + _get_radio_page(app), len(app.radios) - 1)
    elif key == curses.KEY_PPAGE:
        app.radio_cursor = max(app.radio_cursor - _get_radio_page(app), 0)
    elif key == ord("g"):
        app.radio_cursor = 0
    elif key == ord("G"):
        app.radio_cursor = len(app.radios) - 1

    h, _ = app.stdscr.getmaxyx()
    app.radio_scroll = _clamp_scroll(app.radio_cursor, app.radio_scroll, h - app.LIST_H - (0 if h < COMPACT_THRESHOLD else 1))
