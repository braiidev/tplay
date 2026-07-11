from __future__ import annotations

import os
import curses
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from player.app import PlayerApp

from .config import PAIR_MARCO, PAIR_TEXTO, PAIR_DESTACAR, PAIR_NAV
from .file_utils import time_str, ext_label, is_url as _is_url, is_video_file as _is_video_file
from .ui import safe_addstr, draw_box, _build_hints, LIST_H, EXPLORER_MARGIN, PLAYLIST_MARGIN
from . import keybindings as kb
from .handlers import _get_current_key


def draw_item_row(win: curses.window, y: int, name: str, path: str, meta: dict[str, Any] | None, *,
                  is_cursor: bool = False, is_playing: bool = False, is_stream: bool = False,
                  exists: bool = True, suffix: str = "", mode_tag: str = "",
                  left_margin: int = 6, attr: int | None = None, cursor_attr: int | None = None,
                  dur_attr: int | None = None, fallback_icon: str = "♪",
                  fallback_label: str = "<Inexistente>", h: int = 0, w: int = 0) -> None:
    if attr is None:
        attr = curses.color_pair(PAIR_TEXTO)
    if cursor_attr is None:
        cursor_attr = attr
    if dur_attr is None:
        dur_attr = attr

    if not exists:
        line = f"  {fallback_icon} {fallback_label}{suffix}"
        display_attr = (cursor_attr | curses.A_REVERSE) if is_cursor else attr
        safe_addstr(win, y, 2, line, display_attr, h, w)
        return

    if is_stream:
        display = f"[R] {name}"
    elif meta and meta.get('title'):
        display = f"{meta.get('artist', '?')} - {meta.get('title', name)}"
    else:
        display = name

    icon = "►" if is_playing else ("◉" if _is_video_file(path) else "♪")
    line = f"  {icon} {display}{mode_tag}{suffix}"

    dur = meta.get('length', 0) if meta else 0
    dur_str = time_str(dur) if dur > 0 else ""
    dur_w = len(dur_str) + 3 if dur_str else 0
    max_w = w - left_margin - dur_w
    if len(line) > max_w:
        line = line[:max_w - 1] + "…"

    display_attr = (cursor_attr | curses.A_REVERSE) if is_cursor else attr
    safe_addstr(win, y, 2, line, display_attr, h, w)
    if dur_str:
        safe_addstr(win, y, w - len(dur_str) - 2, dur_str, dur_attr, h, w)


def _center(s: str, w: int) -> str:
    s = s.strip()
    if len(s) >= w:
        return s[:w]
    left = (w - len(s)) // 2
    return " " * left + s + " " * (w - len(s) - left)


def draw_listen(app: PlayerApp, h: int, w: int) -> None:
    texto = curses.color_pair(PAIR_TEXTO)
    destacar = curses.color_pair(PAIR_DESTACAR)
    nav = curses.color_pair(PAIR_NAV)

    if app.show_stack_view:
        total = len(app.stack.items)
        pos = f" ({app.stack_cursor + 1}/{total})" if total > 0 else ""
        draw_box(app.stdscr, h, w, f"Pila{pos} ({total})")
        if not app.stack.items:
            safe_addstr(app.stdscr, h // 2, 2, "  Pila vacía — usá [2] Explorador para añadir", texto, h, w)
        else:
            list_h = h - 8
            visible = app.stack.items[app.stack_scroll:app.stack_scroll + list_h]
            for row, item in enumerate(visible):
                y = 2 + row
                idx = app.stack_scroll + row
                is_stream = _is_url(item.path)
                meta = app.meta_cache.get(item.path) if not is_stream else None
                is_playing = (app.stack.playhead == idx) and app.audio.playing
                mode_tag = ""
                if item.mode == "repeat_once":
                    mode_tag = " [1x]"
                elif item.mode == "repeat_inf":
                    mode_tag = " [∞]"
                attr = destacar if is_playing else texto
                draw_item_row(app.stdscr, y, item.name, item.path, meta,
                              is_cursor=(idx == app.stack_cursor),
                              is_playing=is_playing, is_stream=is_stream,
                              mode_tag=mode_tag, left_margin=8, attr=attr,
                              h=h, w=w)
            hints1 = _build_hints([
                ("Enter", "►"), ("Tab", "Volver"), ("d", "el"),
                ("x", "clear"), ("J/K", "orden"), ("s", "guardar"),
            ], w)
            hints2 = _build_hints([
                ("r/R", "modo"), ("g/G", "Inicio/Fin"),
                ("X", "export"), ("u/U", "deshacer"),
            ], w)
            if hints1:
                safe_addstr(app.stdscr, h - 4, 2, hints1, texto, h, w)
            if hints2:
                safe_addstr(app.stdscr, h - 3, 2, hints2, texto, h, w)
        return

    draw_box(app.stdscr, h, w, "Listen")
    mid = max(3, (h - 8) // 2)

    if not app.stack.items or not app.audio.playing:
        safe_addstr(app.stdscr, mid - 1, 2, "  Nada sonando.", destacar, h, w)
        safe_addstr(app.stdscr, mid + 1, 2, "  Abrí [2] Explorador y seleccioná un archivo", texto, h, w)
        return

    cur_item = app.stack.current
    if not cur_item:
        return

    is_stream = _is_url(cur_item.path)
    meta = app.meta_cache.get(cur_item.path) if not is_stream else None
    estado = "► PLAY" if not app.paused else "|| PAUSE"

    if is_stream:
        safe_addstr(app.stdscr, mid - 3, 2, f"  {estado}  [STREAM]", destacar, h, w)
        safe_addstr(app.stdscr, mid - 1, 2, f"  {cur_item.name}", texto, h, w)
        safe_addstr(app.stdscr, mid, 2, f"  {cur_item.path}", texto, h, w)
    else:
        artist = (meta.get('artist') if meta else None) or "Artista desconocido"
        album = (meta.get('album') if meta else None) or "Álbum desconocido"
        title = (meta.get('title') if meta else None) or cur_item.name
        safe_addstr(app.stdscr, mid - 3, 2, f"  {estado}", destacar, h, w)
        tw = w - 6
        title_s = title[:tw - 1] + "…" if len(title) > tw else title
        safe_addstr(app.stdscr, mid - 1, 2, f"    {title_s}", texto, h, w)
        artist_album = f"{artist}  —  {album}"
        aa_s = artist_album[:tw - 1] + "…" if len(artist_album) > tw else artist_album
        safe_addstr(app.stdscr, mid, 2, f"    {aa_s}", texto, h, w)

    length_ms = int(app.audio.get_length())
    pos_ms = int(app.audio.get_time())

    if length_ms > 0:
        progress = min(pos_ms / length_ms, 1.0)
        cur_s = time_str(pos_ms // 1000)
        dur_s = time_str(length_ms // 1000)
        bar_w = max(8, w - 18)
        filled = int(bar_w * progress)
        bar = "█" * filled + "░" * (bar_w - filled)
        safe_addstr(app.stdscr, mid + 2, 2, f"  {cur_s} {bar} {dur_s}", texto, h, w)
    else:
        safe_addstr(app.stdscr, mid + 2, 2, "  --:--", texto, h, w)

    timer_str = app.audio.sleep_timer_str()
    if timer_str:
        safe_addstr(app.stdscr, mid + 4, 2, f"  {timer_str}", texto, h, w)

    if app.goto_mode:
        goto_y = min(mid + 6, h - 7)
        gm = f"{app.goto_mins:02d}"
        gs = f"{app.goto_secs:02d}"
        am = texto | curses.A_REVERSE if app.goto_field == 0 else texto
        as_ = texto | curses.A_REVERSE if app.goto_field == 1 else texto
        safe_addstr(app.stdscr, goto_y, 2, "  Ir a: [", texto, h, w)
        safe_addstr(app.stdscr, goto_y, 11, gm, am, h, w)
        safe_addstr(app.stdscr, goto_y, 13, ":", texto, h, w)
        safe_addstr(app.stdscr, goto_y, 14, gs, as_, h, w)
        safe_addstr(app.stdscr, goto_y, 16, "]", texto, h, w)
        safe_addstr(app.stdscr, goto_y + 1, 2, "  ← → campo  ↑ ↓ valor  Enter saltar", texto, h, w)

    # ── Bottom grid: controls ──
    cw = [5, 7, 5, 4, 9, 11]

    prev_i = _center("◀◀", cw[0])
    play_i = _center("▶||", cw[1])
    next_i = _center("▶▶", cw[2])
    stop_i = _center("◼", cw[3])
    vol_i = _center(f"Vol:{app.volume:>3}%", cw[4])

    st_parts = [
        "[S]" if app.stack.shuffle else "   ",
        "[R]" if app.stack.repeat  else "   ",
        "[M]" if app.audio.muted   else "   ",
    ]
    if app.audio.rate != 1.0:
        st_parts.append(f"[{app.audio.rate:.2f}x]")
    states_i = _center(" ".join(st_parts), cw[5])

    icons = [prev_i, play_i, next_i, stop_i, vol_i, states_i]
    keys = [
        _center("b", cw[0]),
        _center("space", cw[1]),
        _center("n", cw[2]),
        _center("s", cw[3]),
        _center("j  k", cw[4]),
        _center("", cw[5]),
    ]

    line1 = " " + "   ".join(icons)
    line2 = " " + "   ".join(keys)

    extra = _build_hints([
        ("Tab", "Pila"), ("g", "Ir a"), ("t/T", "Tmp"),
        ("h/l", "Buscar"), ("r", "Azar"), ("R", "Rep"), ("m", "Sil"),
    ], w)

    safe_addstr(app.stdscr, h - 5, 2, line1[:w - 4], destacar, h, w)
    safe_addstr(app.stdscr, h - 4, 2, line2[:w - 4], texto, h, w)
    if extra:
        safe_addstr(app.stdscr, h - 3, 2, extra, nav, h, w)


def draw_mini_stack(app: PlayerApp, win: curses.window, h: int, w: int) -> None:
    marco = curses.color_pair(PAIR_MARCO)
    texto = curses.color_pair(PAIR_TEXTO)
    destacar = curses.color_pair(PAIR_DESTACAR)

    safe_addstr(win, 0, 0, "┌" + "─" * max(0, w - 2) + "┐", marco, h, w)
    safe_addstr(win, h - 1, 0, "└" + "─" * max(0, w - 2) + "┘", marco, h, w)
    for y in range(1, h - 1):
        safe_addstr(win, y, 0, "│", marco, h, w)
        safe_addstr(win, y, max(0, w - 1), "│", marco, h, w)

    items = app.stack.items
    total = len(items)
    if total == 0:
        safe_addstr(win, h // 2, 2, "  (vacío)", texto, h, w)
        return

    list_h = h - 2
    visible = items[app.stack_scroll:app.stack_scroll + list_h]
    for i, item in enumerate(visible):
        y = 1 + i
        idx = app.stack_scroll + i
        is_playing = (app.stack.playhead == idx) and app.audio.playing
        icon = "►" if is_playing else ("◉" if _is_video_file(item.path) else "♪")
        line = f" {icon} {item.name}"
        max_w = w - 3
        if len(line) > max_w:
            line = line[:max_w - 1] + "…"
        attr = destacar if is_playing else texto
        if idx == app.stack_cursor:
            safe_addstr(win, y, 1, line, attr | curses.A_REVERSE, h, w)
        else:
            safe_addstr(win, y, 1, line, attr, h, w)


def draw_listen_compact(app: PlayerApp, h: int, w: int) -> None:
    if app.show_stack_view:
        draw_mini_stack(app, app.stdscr, h, w)
        return
    marco = curses.color_pair(PAIR_MARCO)
    texto = curses.color_pair(PAIR_TEXTO)
    destacar = curses.color_pair(PAIR_DESTACAR)

    status = ""
    if app.audio.playing:
        status = "❚❚" if app.paused else "▶"
    title = f" {status} Listen " if status else " Listen "
    safe_addstr(app.stdscr, 0, 0, "┌" + "─" * max(0, w - 2) + "┐", marco, h, w)
    if w > len(title) + 2:
        tx = max(2, (w - len(title)) // 2)
        safe_addstr(app.stdscr, 0, tx, title[:w - tx - 1], marco, h, w)
    safe_addstr(app.stdscr, h - 1, 0, "└" + "─" * max(0, w - 2) + "┘", marco, h, w)
    for y in range(1, h - 1):
        safe_addstr(app.stdscr, y, 0, "│", marco, h, w)
        safe_addstr(app.stdscr, y, max(0, w - 1), "│", marco, h, w)

    if not app.stack.items or not app.audio.playing:
        msg = "Nada sonando."
        safe_addstr(app.stdscr, h // 2, (w - len(msg)) // 2, msg, destacar, h, w)
        return

    cur_item = app.stack.current
    if not cur_item:
        return

    is_stream = _is_url(cur_item.path)
    meta = app.meta_cache.get(cur_item.path) if not is_stream else None
    max_w = w - 4

    if is_stream:
        title_text = cur_item.name
    else:
        title_text = (meta.get('title') if meta else None) or cur_item.name
    t = title_text[:max_w - 1] + "…" if len(title_text) > max_w else title_text
    safe_addstr(app.stdscr, 2, 2, t, destacar, h, w)

    if not is_stream:
        artist = (meta.get('artist') if meta else None) or "?"
        album = (meta.get('album') if meta else None) or "?"
        aa = f"{artist} — {album}"
        a = aa[:max_w - 1] + "…" if len(aa) > max_w else aa
        safe_addstr(app.stdscr, 3, 2, a, texto, h, w)

    length_ms = int(app.audio.get_length())
    pos_ms = int(app.audio.get_time())
    if length_ms > 0:
        progress = min(pos_ms / length_ms, 1.0)
        cur_s = time_str(pos_ms // 1000)
        dur_s = time_str(length_ms // 1000)
        bar_w = max(4, w - 16)
        filled = int(bar_w * progress)
        bar = "█" * filled + "░" * (bar_w - filled)
        safe_addstr(app.stdscr, 4, 2, f"{cur_s} {bar} {dur_s}", texto, h, w)
    else:
        safe_addstr(app.stdscr, 4, 2, "--:--", texto, h, w)

    controls = " ◀◀  ▶||  ▶▶  ◼"
    vol_str = f" V:{app.volume}%"
    states = ""
    if app.stack.shuffle:
        states += " S"
    if app.stack.repeat:
        states += " R"
    if app.audio.muted:
        states += " M"
    if app.audio.rate != 1.0:
        states += f" {app.audio.rate:.2f}x"
    if app.audio.sleep_timer_active:
        states += " ◴"
    elif app.audio.sleep_timer_expired:
        states += " ◴FIN"
    full = controls + vol_str + states
    if len(full) <= max_w:
        display = full
    else:
        no_states = controls + vol_str
        if len(no_states) <= max_w:
            display = no_states
        else:
            display = controls[:max_w]
    safe_addstr(app.stdscr, h - 2, 2, display, destacar, h, w)

    # ── Goto overlay for compact ──
    if app.goto_mode:
        goto_h = 5
        oy = max(0, (h - goto_h) // 2)
        bw = min(22, w - 4)
        ox = (w - bw) // 2
        safe_addstr(app.stdscr, oy, ox, "┌" + "─" * (bw - 2) + "┐", marco, h, w)
        title = " Ir a "
        tx = ox + 1 + (bw - 2 - len(title)) // 2
        safe_addstr(app.stdscr, oy, tx, title, destacar, h, w)
        for yy in range(1, goto_h - 1):
            safe_addstr(app.stdscr, oy + yy, ox, "│", marco, h, w)
            safe_addstr(app.stdscr, oy + yy, ox + bw - 1, "│", marco, h, w)
            safe_addstr(app.stdscr, oy + yy, ox + 1, " " * (bw - 2), texto, h, w)
        safe_addstr(app.stdscr, oy + goto_h - 1, ox, "└" + "─" * (bw - 2) + "┘", marco, h, w)
        gm = f"{app.goto_mins:02d}"
        gs = f"{app.goto_secs:02d}"
        am = texto | curses.A_REVERSE if app.goto_field == 0 else texto
        as_ = texto | curses.A_REVERSE if app.goto_field == 1 else texto
        tmp = f"{gm}:{gs}"
        tx2 = ox + 1 + (bw - 2 - len(tmp)) // 2
        safe_addstr(app.stdscr, oy + 1, tx2, gm, am, h, w)
        safe_addstr(app.stdscr, oy + 1, tx2 + 2, ":", texto, h, w)
        safe_addstr(app.stdscr, oy + 1, tx2 + 3, gs, as_, h, w)
        ax = ox + 1 + (bw - 2 - 7) // 2
        safe_addstr(app.stdscr, oy + 2, ax, "← → ↑ ↓", texto, h, w)
        ex = ox + 1 + (bw - 2 - 5) // 2
        safe_addstr(app.stdscr, oy + 3, ex, "Enter", destacar, h, w)


def draw_explorer(app: PlayerApp, h: int, w: int) -> None:
    extra = " [Filtro]" if app.explorer_filter_mode else ""
    texto = curses.color_pair(PAIR_TEXTO)
    destacar = curses.color_pair(PAIR_DESTACAR)

    offset = 0
    if app.file_op_mode:
        mode_label = "Copiar" if app.file_op_mode == "copy" else "Mover"
        src_name = os.path.basename(app.file_op_source) if app.file_op_source else ""
        safe_addstr(app.stdscr, 2, 2, f"  {mode_label}: {src_name}  Enter/C/V=pegar bajo directorio  Esc=cancelar  u=deshacer", destacar, h, w)
        offset = 1

    if app.explorer_filter_mode:
        y = 2 + offset
        prefix = "> "
        body = prefix + app.explorer_filter
        try:
            app.stdscr.addstr(y, 2, body[:w - 4], destacar)
        except curses.error:
            pass
        cx = 2 + len(prefix) + app.explorer_filter_cursor
        if cx < w - 1:
            try:
                app.stdscr.chgat(y, cx, 1, destacar | curses.A_REVERSE)
            except curses.error:
                pass
        offset += 1

    list_h = h - LIST_H - offset - (0 if h < 16 else 1)
    indices = app.explorer_filtered if app.explorer_filter_mode else list(range(len(app.entries)))
    total = len(indices)
    mark_s = f" [{len(app.explorer_marked)}✓]" if app.explorer_marked else ""
    pos = f" ({app.cursor + 1}/{total})" if total > 0 else ""
    title_p = "Explorador: "
    title_s = extra + pos + mark_s
    max_pw = w - 4 - len(title_p) - len(title_s)
    pd = app.current_dir
    if len(pd) > max_pw and max_pw > 4:
        pd = "…" + pd[-(max_pw - 1):]
    draw_box(app.stdscr, h, w, f"{title_p}{pd}{title_s}")

    if app.explorer_filter_mode and not indices:
        safe_addstr(app.stdscr, 3 + offset, 2, "  Sin resultados", texto, h, w)
        return
    if not app.entries and not app.explorer_filter_mode:
        safe_addstr(app.stdscr, h // 2, 2, "  Sin archivos multimedia en este directorio", texto, h, w)
        return
    visible = indices[app.scroll:app.scroll + list_h]

    for i, abs_idx in enumerate(visible):
        y = 2 + offset + i
        name, is_dir, full = app.entries[abs_idx]
        mark = "✓ " if abs_idx in app.explorer_marked else "  "
        label = ext_label(name)
        if is_dir:
            line = f"  {mark}[+]/ {name}"
            attr = destacar
            dur_str = ""
        else:
            base = name.rsplit('.', 1)[0] if '.' in name else name
            icon = "◉" if _is_video_file(full) else "♪"
            line = f"  {mark}{icon} {base}  [{label}]"
            attr = texto
            meta = app.meta_cache.get(full)
            dur = meta.get('length', 0) if meta else 0
            dur_str = time_str(dur) if dur > 0 else ""
        dur_w = len(dur_str) + 3 if dur_str else 0
        max_w = w - EXPLORER_MARGIN - dur_w
        if len(line) > max_w:
            line = line[:max_w - 1] + "…"
        cur = app.cursor
        is_cursor = (cur < len(indices) and abs_idx == indices[cur])
        if is_cursor:
            safe_addstr(app.stdscr, y, 2, line, attr | curses.A_REVERSE, h, w)
        else:
            safe_addstr(app.stdscr, y, 2, line, attr, h, w)
        if dur_str:
            safe_addstr(app.stdscr, y, w - len(dur_str) - 2, dur_str, texto, h, w)


def draw_playlist(app: PlayerApp, h: int, w: int) -> None:
    extra = " [Filtro]" if app.playlist_filter_mode else ""
    total_items = len(app.playlist)
    texto = curses.color_pair(PAIR_TEXTO)
    destacar = curses.color_pair(PAIR_DESTACAR)

    list_h = h - LIST_H - (1 if app.playlist_filter_mode else 0) - (0 if h < 16 else 1)
    if total_items > list_h and total_items > 0:
        pos = f" ({app.playlist_cursor + 1}/{total_items})"
    elif total_items > 0:
        pos = f" ({total_items})"
    else:
        pos = ""
    draw_box(app.stdscr, h, w, f"Playlist [{app.active_name}]{pos}{extra}")

    if app.playlist_filter_mode:
        prefix = "> "
        body = prefix + app.playlist_filter
        try:
            app.stdscr.addstr(2, 2, body[:w - 4], destacar)
        except curses.error:
            pass
        cx = 2 + len(prefix) + app.playlist_filter_cursor
        if cx < w - 1:
            try:
                app.stdscr.chgat(2, cx, 1, destacar | curses.A_REVERSE)
            except curses.error:
                pass

    if not app.playlist:
        if not app.playlist_data:
            safe_addstr(app.stdscr, h // 2, 2,
                              "  No hay listas. [c] crear una.", texto, h, w)
        else:
            safe_addstr(app.stdscr, h // 2, 2,
                              "  Añadí elementos desde Explorador con a/A.", texto, h, w)
        return

    indices = app.playlist_filtered if app.playlist_filter_mode else list(range(len(app.playlist)))
    visible = indices[app.playlist_scroll:app.playlist_scroll + list_h]

    if app.playlist_filter_mode and not indices:
        safe_addstr(app.stdscr, 4, 2, "  Sin resultados", texto, h, w)
        return

    for row, abs_idx in enumerate(visible):
        y = (3 if app.playlist_filter_mode else 2) + row
        name, path = app.playlist[abs_idx]
        exists = os.path.isfile(path)
        meta = app.meta_cache.get(path) if exists else None
        is_playing = bool(app.stack.current and app.stack.current.path == path and app.audio.playing)
        cur = app.playlist_cursor
        is_cursor = (cur < len(indices) and abs_idx == indices[cur])
        draw_item_row(app.stdscr, y, name, path, meta,
                      is_cursor=is_cursor, is_playing=is_playing,
                      exists=exists, left_margin=PLAYLIST_MARGIN,
                      attr=texto, dur_attr=texto, h=h, w=w)


def draw_history(app: PlayerApp, h: int, w: int) -> None:
    total = len(app.history)
    pos = f" ({app.history_cursor + 1}/{total})" if total > 0 else ""
    draw_box(app.stdscr, h, w, f"Historial{pos}")
    texto = curses.color_pair(PAIR_TEXTO)
    destacar = curses.color_pair(PAIR_DESTACAR)
    if not app.history:
        safe_addstr(app.stdscr, h // 2, 2, "  Sin historial", texto, h, w)
        return
    _compact_history = h < 16
    list_h = h - LIST_H - (0 if _compact_history else 1)
    start = max(0, min(app.history_scroll, len(app.history) - list_h))
    visible = app.history[start:start + list_h]
    for i, entry in enumerate(visible):
        y = 2 + i
        idx = start + i
        name = entry.get("name", "?")
        path = entry.get("path", "")
        count = entry.get("count", 0)
        is_stream = _is_url(path)
        exists = is_stream or os.path.isfile(path)
        meta = app.meta_cache.get(path) if exists and not is_stream else None
        draw_item_row(app.stdscr, y, name, path, meta,
                      is_cursor=(idx == app.history_cursor),
                      is_stream=is_stream,
                      exists=exists, suffix=f" ({count}x)",
                      left_margin=4, attr=texto, cursor_attr=destacar,
                      dur_attr=texto, fallback_icon="~",
                      fallback_label="Archivo Inexistente", h=h, w=w)


def draw_config(app: PlayerApp, h: int, w: int) -> None:
    draw_box(app.stdscr, h, w, "Configuración")
    texto = curses.color_pair(PAIR_TEXTO)
    destacar = curses.color_pair(PAIR_DESTACAR)
    nav = curses.color_pair(PAIR_NAV)

    labels = {
        "music_dir": f"Directorio música: {app.config.get('music_dir', '~/Music')}",
        "volume": f"Volumen: {app.volume}%",
        "theme": f"Tema: {app.config.get('theme', 'clasico')}",
        "sleep_timer_minutes": f"Sleep timer: {app.config.get('sleep_timer_minutes', 30)} min",
    }
    cc = app.config.get("custom_colors", {})

    # --- Tab bar at line 1 ---
    tab_names = [t["name"] for t in app.config_tabs]
    x = 2
    safe_addstr(app.stdscr, 1, x, "◀ ", nav, h, w)
    x += 2
    for ti, name in enumerate(tab_names):
        if ti > 0:
            safe_addstr(app.stdscr, 1, x, " │ ", nav, h, w)
            x += 3
        max_name_w = (w - 6) // max(len(tab_names), 1) - 3
        display_name = name
        if len(display_name) > max_name_w > 0:
            display_name = display_name[:max_name_w - 1] + "…"
        if ti == app.config_tab_idx:
            safe_addstr(app.stdscr, 1, x, "[", nav, h, w)
            x += 1
            safe_addstr(app.stdscr, 1, x, display_name, destacar, h, w)
            x += len(display_name)
            safe_addstr(app.stdscr, 1, x, "]", nav, h, w)
            x += 1
        else:
            safe_addstr(app.stdscr, 1, x, display_name, texto, h, w)
            x += len(display_name)
    safe_addstr(app.stdscr, 1, x, " ▶", nav, h, w)

    # --- Items with scroll ---
    items = app.config_items
    total = len(items)
    cur = app.config_cursor
    list_h = h - 5 if h < 16 else h - 6

    # Clamp scroll
    if cur < app.config_scroll:
        app.config_scroll = cur
    elif cur >= app.config_scroll + list_h:
        app.config_scroll = cur - list_h + 1
    app.config_scroll = max(0, app.config_scroll)

    visible = items[app.config_scroll:app.config_scroll + list_h]
    for i, (key, label, ctype) in enumerate(visible):
        y = 3 + i
        idx = app.config_scroll + i
        if ctype == "color":
            line = f"  {label}: {cc.get(key, 'Blanco')}"
        elif ctype == "bool":
            line = f"  {label}: {'Sí' if app.config.get(key, True) else 'No'}"
        elif key == "keybindings":
            mode_label = "Default" if app.keybinding_mode == "default" else "Custom"
            line = f"  {label}  [{mode_label}]"
        elif key == "update":
            line = f"  {label}  [Comprobar]"
            if app.update_available:
                line += "  !"
        else:
            line = f"  {labels.get(key, key)}"
        if ctype in ("choice", "color", "int", "bool"):
            line += "  ← →"
        elif ctype == "path":
            line += "  Enter"
        max_w = w - 4
        if len(line) > max_w:
            line = line[:max_w - 1] + "…"
        if idx == cur:
            safe_addstr(app.stdscr, y, 2, line, destacar | curses.A_REVERSE, h, w)
        else:
            safe_addstr(app.stdscr, y, 2, line, texto, h, w)


def draw_keybindings(app: PlayerApp, h: int, w: int) -> None:
    draw_box(app.stdscr, h, w, "Keybindings")
    texto = curses.color_pair(PAIR_TEXTO)
    destacar = curses.color_pair(PAIR_DESTACAR)

    compact = h < 16
    is_custom = app.keybinding_mode == "custom"
    mode = "PERSONALIZADO" if is_custom else "POR DEFECTO"

    if compact:
        safe_addstr(app.stdscr, 2, 2, f"Modo:{mode}  ←→cambiar  Esc:volver", destacar, h, w)
        if not is_custom:
            safe_addstr(app.stdscr, 3, 2, "Pasá a Personalizado para editar", texto, h, w)
            return
        safe_addstr(app.stdscr, 3, 2, "Enter:asignar tecla", texto, h, w)
        list_h = max(1, h - 5)
        y0 = 4
    else:
        safe_addstr(app.stdscr, 2, 2, f"  Modo: {mode}  ← → cambiar", destacar, h, w)
        if not is_custom:
            safe_addstr(app.stdscr, 4, 2, "  Cambiá a modo Personalizado para editar las teclas", texto, h, w)
            safe_addstr(app.stdscr, h - 3, 2, "  [Esc] Volver", texto, h, w)
            return
        safe_addstr(app.stdscr, 3, 2, "  Enter para cambiar una tecla, Esc para volver", texto, h, w)
        list_h = h - 8
        y0 = 5

    actions = kb.BINDABLE_ACTIONS
    start = max(0, min(app.kb_cursor, len(actions) - list_h))
    visible = actions[start:start + list_h]

    for i, action in enumerate(visible):
        y = y0 + i
        idx = start + i
        keycode = _get_current_key(app, action)
        kname = kb.key_name(keycode)
        line = f"  {action:<15}  {kname}"
        if app.kb_capturing and app.kb_capturing_action == action:
            line += "  ⏎ esperando tecla..."
        attr = destacar if idx == app.kb_cursor else texto
        if idx == app.kb_cursor:
            safe_addstr(app.stdscr, y, 2, line, attr | curses.A_REVERSE, h, w)
        else:
            safe_addstr(app.stdscr, y, 2, line, attr, h, w)

    if not compact:
        footer = "  [Esc] Volver"
        if app.kb_conflict_msg:
            footer = f"  {app.kb_conflict_msg}  |  [Esc] Volver"
        safe_addstr(app.stdscr, h - 3, 2, footer, texto, h, w)


def draw_meta_editor(app: PlayerApp, win: curses.window, h: int, w: int) -> None:
    texto = curses.color_pair(PAIR_TEXTO)
    destacar = curses.color_pair(PAIR_DESTACAR)
    compact = h < 16

    pad_x = 2
    draw_box(win, h, w, "Editar metadata")

    if compact:
        safe_addstr(win, 2, pad_x, "↑↓ Naveg  Enter Ed  s:Guardar  q:Salir", texto, h, w)
        y0 = 3
    else:
        safe_addstr(win, 2, pad_x,
                    "↑/↓: navegar  Enter: editar  [s] guardar  [q] cancelar",
                    texto, h, w)
        y0 = 4

    fields = app.meta_edit_fields
    total = len(fields)
    cur = app.meta_edit_cursor
    list_h = total if not compact else max(2, h - y0 - 1)

    # Auto-scroll so cursor is always visible
    scroll = max(0, min(cur, total - list_h)) if total > list_h else 0
    visible = fields[scroll:scroll + list_h]

    for i, (label, key, orig) in enumerate(visible):
        actual_idx = scroll + i
        row = y0 + i
        current = app.meta_edit_changed.get(key, orig)
        val = current if current else "(vacío)"
        marker = " *" if key in app.meta_edit_changed else "  "
        line = f"  {label}: {val}{marker}"
        attr = destacar if actual_idx == cur else texto
        if actual_idx == cur and not app.meta_edit_editing:
            safe_addstr(win, row, pad_x, line, attr | curses.A_REVERSE, h, w)
        else:
            safe_addstr(win, row, pad_x, line, attr, h, w)
        if actual_idx == cur and app.meta_edit_editing:
            buf = app.meta_edit_buf
            cx = pad_x + len(f"  {label}: ")
            display = buf if buf else ""
            try:
                win.addstr(row, cx, display[:w - cx - 2], attr)
            except curses.error:
                pass
            cur_in_buf = app.meta_edit_cursor_pos
            if cx + cur_in_buf < w - 1:
                try:
                    win.chgat(row, cx + cur_in_buf, 1, attr | curses.A_REVERSE)
                except curses.error:
                    pass

    # Status line only if room
    status_row = y0 + len(visible)
    if not compact and status_row < h - 1:
        row = status_row + 1
        if not app.meta_edit_changed:
            safe_addstr(win, row, pad_x, "  Sin cambios", texto, h, w)


def draw_radio(app: PlayerApp, h: int, w: int) -> None:
    win = app.stdscr
    texto = curses.color_pair(PAIR_TEXTO)
    destacar = curses.color_pair(PAIR_DESTACAR)
    draw_box(win, h, w, "Radios")
    radios = app.radios
    y0 = 3
    list_h = h - app.LIST_H - 1
    scroll = app.radio_scroll
    cursor = app.radio_cursor
    visible = radios[scroll:scroll + list_h] if radios else []
    for i, r in enumerate(visible):
        y = y0 + i
        idx = scroll + i
        is_cursor = idx == cursor
        attr = destacar if is_cursor else texto
        if is_cursor:
            attr |= curses.A_REVERSE
        line = f"  {r['name']}"
        safe_addstr(win, y, 2, line[:w - 4], attr, h, w)
        url_start = len(line) + 3
        url_display = r['url'][:w - url_start - 2]
        safe_addstr(win, y, url_start, url_display, attr, h, w)
    if not radios:
        safe_addstr(win, y0, 2, "  Sin radios guardadas", texto, h, w)


def draw_dir_picker(app: PlayerApp, win: curses.window, h: int, w: int) -> None:
    texto = curses.color_pair(PAIR_TEXTO)
    destacar = curses.color_pair(PAIR_DESTACAR)
    nav = curses.color_pair(PAIR_NAV)

    title = app.dir_picker_path
    max_tw = w - 20
    if len(title) > max_tw and max_tw > 4:
        title = "…" + title[-(max_tw - 1):]
    draw_box(win, h, w, f"Dir: {title}")

    entries = app.dir_picker_entries
    list_h = h - 5
    visible = entries[app.dir_picker_scroll:app.dir_picker_scroll + list_h]

    if not entries:
        safe_addstr(win, h // 2, 2, "  (sin subdirectorios)", texto, h, w)
    else:
        for i, (name, _, full) in enumerate(visible):
            y = 2 + i
            idx = app.dir_picker_scroll + i
            line = f"  [+]/ {name}"
            max_w = w - 4
            if len(line) > max_w:
                line = line[:max_w - 1] + "…"
            if idx == app.dir_picker_cursor:
                safe_addstr(win, y, 2, line, destacar | curses.A_REVERSE, h, w)
            else:
                safe_addstr(win, y, 2, line, destacar, h, w)

    hints = _build_hints([
        ("Enter", "seleccionar"), ("h/l", "subir/bajar"), ("Esc", "cancelar"),
    ], w)
    if hints:
        safe_addstr(win, h - 4, 2, hints, nav, h, w)


def draw_favorites(app: PlayerApp, h: int, w: int) -> None:
    win = app.stdscr

    texto = curses.color_pair(PAIR_TEXTO)

    title = f"Favoritos ({len(app.favorites)})"
    draw_box(win, h, w, title)

    if not app.favorites:
        safe_addstr(win, h // 2, 2, "  Sin favoritos — usa 'f' en el Explorador", texto, h, w)
        return

    list_h = h - 5 if h >= 16 else h - 4
    visible = app.favorites[app.favorites_scroll:app.favorites_scroll + list_h]

    for i, entry in enumerate(visible):
        y = 2 + i
        idx = app.favorites_scroll + i
        name = entry.get("name", os.path.basename(entry.get("path", "?")))
        path = entry.get("path", "")
        is_stream = "://" in path
        icon = "📻" if is_stream else "♪"
        line = f"  {icon} {name}"
        max_w = w - 4
        if len(line) > max_w:
            line = line[:max_w - 1] + "…"

        is_cursor = (idx == app.favorites_cursor)
        if is_cursor:
            safe_addstr(win, y, 2, line, texto | curses.A_REVERSE, h, w)
        else:
            safe_addstr(win, y, 2, line, texto, h, w)
