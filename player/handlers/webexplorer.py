"""Handler para la vista Web Explorer (V7)."""
from __future__ import annotations

import curses
from typing import TYPE_CHECKING

from .shared import _toast, _clamp_scroll

if TYPE_CHECKING:
    from player.app import PlayerApp


def handle_web(app: PlayerApp, key: int) -> None:
    if app.web_search_mode:
        _handle_search_input(app, key)
        return

    total = len(app.web_results)

    if key == ord("/"):
        app.web_search_mode = True
        app.web_search_buf = ""
        app.web_cursor = 0
        app.web_scroll = 0
        curses.curs_set(1)
        curses.flushinp()
        return

    if key in (curses.KEY_DOWN, ord("j")):
        app.web_cursor = min(app.web_cursor + 1, max(0, total - 1))
    elif key in (curses.KEY_UP, ord("k")):
        app.web_cursor = max(app.web_cursor - 1, 0)
    elif key in (10, 13) and total > 0:
        _play_web_result(app)
        return
    elif key == 27:
        app.current_view = app.V_LISTEN
        curses.flushinp()
        return
    elif key in (curses.KEY_NPAGE,):
        h, _ = app.stdscr.getmaxyx()
        page = h - 8
        app.web_cursor = min(app.web_cursor + page, max(0, total - 1))
    elif key in (curses.KEY_PPAGE,):
        h, _ = app.stdscr.getmaxyx()
        page = h - 8
        app.web_cursor = max(app.web_cursor - page, 0)

    h, _ = app.stdscr.getmaxyx()
    list_h = h - 8
    app.web_scroll = _clamp_scroll(app.web_cursor, app.web_scroll, list_h)


def _handle_search_input(app: PlayerApp, key: int) -> None:
    if key == 27:
        app.web_search_mode = False
        curses.curs_set(0)
        return
    if key in (10, 13):
        app.web_search_mode = False
        curses.curs_set(0)
        query = app.web_search_buf.strip()
        if not query:
            return
        _add_to_history(app, query)
        _do_search(app, query)
        return
    if key in (curses.KEY_BACKSPACE, 127):
        app.web_search_buf = app.web_search_buf[:-1]
    elif 32 <= key <= 126:
        app.web_search_buf += chr(key)


def _do_search(app: PlayerApp, query: str) -> None:
    from .. import web
    from ..config import load as _load_config
    cfg = _load_config()
    max_results = cfg.get("online_max_results", 5)
    try:
        results = web.search(query, max_results)
    except RuntimeError as e:
        _toast(app, str(e))
        return
    app.web_results = results
    app.web_cursor = 0
    app.web_scroll = 0
    if not results:
        _toast(app, f"Sin resultados: {query}")


def _play_web_result(app: PlayerApp) -> None:
    if app.web_cursor >= len(app.web_results):
        return
    result = app.web_results[app.web_cursor]
    from ..stack import StackItem
    item = StackItem(path=result.url, name=result.title)
    app.stack.items = [item]
    app.stack.playhead = 0
    app.audio.play_file(result.url)
    app.current_view = app.V_LISTEN
    _toast(app, f"▶ {result.title}")


def _add_to_history(app: PlayerApp, query: str) -> None:
    history: list[str] = app.config.get("online_search_history", [])
    history = [h for h in history if h != query]
    history.insert(0, query)
    app.config["online_search_history"] = history[:10]
    from ..config import save as _save_config
    _save_config(app.config)
