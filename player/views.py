from __future__ import annotations

import os
import curses
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from player.app import PlayerApp

from .config import PAIR_MARCO, PAIR_TEXTO, PAIR_DESTACAR, PAIR_NAV, PAIR_OVERLAY
from .file_utils import time_str, ext_label, is_url as _is_url, is_video_file as _is_video_file
from .ui import safe_addstr, draw_box, draw_box_inline, draw_tab_carousel, clamp_scroll, draw_list_indicators, _build_hints, LIST_H, EXPLORER_MARGIN, PLAYLIST_MARGIN, COMPACT_THRESHOLD
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
        dur_x = w - len(dur_str) - 2
        safe_addstr(win, y, dur_x, dur_str, dur_attr, h, w)
        if is_cursor:
            fill_start = 2 + len(line)
            fill_len = dur_x - fill_start
            if fill_len > 0:
                safe_addstr(win, y, fill_start, " " * fill_len, display_attr, h, w)
    elif is_cursor:
        fill_start = 2 + len(line)
        fill_len = w - 2 - fill_start
        if fill_len > 0:
            safe_addstr(win, y, fill_start, " " * fill_len, display_attr, h, w)


def _center(s: str, w: int) -> str:
    s = s.strip()
    if len(s) >= w:
        return s[:w]
    left = (w - len(s)) // 2
    return " " * left + s + " " * (w - len(s) - left)


def _eq_bar(value: float, bar_w: int) -> str:
    pos = int((value + 20.0) / 40.0 * bar_w)
    pos = max(0, min(bar_w, pos))
    return "█" * pos + "░" * (bar_w - pos)


def _vol_bar(vol: int, bar_w: int) -> str:
    filled = int(bar_w * vol / 100)
    return "█" * filled + "░" * (bar_w - filled)


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
                              mode_tag=mode_tag, left_margin=2, attr=attr,
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
                safe_addstr(app.stdscr, h - 4, 2, hints1, nav, h, w)
            if hints2:
                safe_addstr(app.stdscr, h - 3, 2, hints2, nav, h, w)
        return

    stack_n = len(app.stack.items)
    title = f"Listen ({stack_n})" if stack_n > 0 else "Listen"
    draw_box(app.stdscr, h, w, title)
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
    estado = "► PLAY" if not app.paused else "❚❚ PAUSE"
    inner_w = w - 4

    if is_stream:
        safe_addstr(app.stdscr, mid - 3, 2, _center(f"{estado}  [STREAM]", inner_w), destacar, h, w)
        safe_addstr(app.stdscr, mid - 1, 2, _center(cur_item.name, inner_w), texto, h, w)
        safe_addstr(app.stdscr, mid, 2, _center(cur_item.path, inner_w), texto, h, w)
    else:
        artist = (meta.get('artist') if meta else None) or "Artista desconocido"
        album = (meta.get('album') if meta else None) or "Álbum desconocido"
        title = (meta.get('title') if meta else None) or cur_item.name
        safe_addstr(app.stdscr, mid - 3, 2, _center(estado, inner_w), destacar, h, w)
        tw = inner_w - 3
        title_s = title[:tw - 1] + "…" if len(title) > tw else title
        safe_addstr(app.stdscr, mid - 1, 2, _center(f"♪ {title_s}", inner_w), destacar, h, w)
        artist_album = f"{artist}  —  {album}"
        aa_s = artist_album[:tw - 1] + "…" if len(artist_album) > tw else artist_album
        safe_addstr(app.stdscr, mid, 2, _center(aa_s, inner_w), texto, h, w)

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
    avail = w - 4
    min_cw = [3, 5, 3, 2, 7, 6]
    separators = 3 * (len(min_cw) - 1)
    min_total = sum(min_cw) + separators
    if avail >= min_total:
        pad = avail - min_total
        cw = list(min_cw)
        cw[4] += pad // 2
        cw[5] += pad - pad // 2
    else:
        cw = min_cw

    prev_i = _center("◀◀", cw[0])
    play_i = _center("▶||", cw[1])
    next_i = _center("▶▶", cw[2])
    stop_i = _center("◼", cw[3])
    vol_bar_w = cw[4] - 8
    if vol_bar_w >= 4:
        vol_bar = _vol_bar(app.volume, vol_bar_w)
        vol_i = _center(f"Vol:{vol_bar} {app.volume}%", cw[4])
    else:
        vol_i = _center(f"Vol:{app.volume:>3}%", cw[4])

    st_parts = [
        "[S]" if app.stack.shuffle else "   ",
        "[R]" if app.stack.repeat  else "   ",
        "[M]" if app.audio.muted   else "   ",
        "[EQ]" if app.audio._eq_enabled else "    ",
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
        ("E", "Preset"), ("e", "EQ"), (";", "Hints"),
    ], w) if app.config.get("show_listen_hints", True) else ""

    safe_addstr(app.stdscr, h - 5, 2, line1[:w - 4], destacar, h, w)
    safe_addstr(app.stdscr, h - 4, 2, line2[:w - 4], texto, h, w)
    if extra:
        safe_addstr(app.stdscr, h - 3, 2, extra, nav, h, w)


def draw_mini_stack(app: PlayerApp, win: curses.window, h: int, w: int) -> None:
    texto = curses.color_pair(PAIR_TEXTO)
    destacar = curses.color_pair(PAIR_DESTACAR)

    draw_box_inline(win, h, w)

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
    title = f"{status} Listen" if status else "Listen"
    draw_box_inline(app.stdscr, h, w, title)

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
    safe_addstr(app.stdscr, 2, 2, _center(t, max_w), destacar, h, w)

    if not is_stream:
        artist = (meta.get('artist') if meta else None) or "?"
        album = (meta.get('album') if meta else None) or "?"
        aa = f"{artist} — {album}"
        a = aa[:max_w - 1] + "…" if len(aa) > max_w else aa
        safe_addstr(app.stdscr, 3, 2, _center(a, max_w), texto, h, w)

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
    vol_bar_w = 4
    vol_bar = _vol_bar(app.volume, vol_bar_w)
    vol_str = f" V:{vol_bar}{app.volume}%"
    states = ""
    if app.stack.shuffle:
        states += " S"
    if app.stack.repeat:
        states += " R"
    if app.audio.muted:
        states += " M"
    if app.audio._eq_enabled:
        states += " EQ"
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
        vol_str = f" V:{app.volume}%"
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
        oy = min(max(0, (h - goto_h) // 2), max(0, h - goto_h - 3))
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
    overlay = curses.color_pair(PAIR_OVERLAY)

    root = os.path.realpath(app.config.get("music_dir", os.path.expanduser("~/Music")))
    cur_dir = os.path.realpath(app.current_dir)
    read_only = not (cur_dir == root or cur_dir.startswith(root + os.sep))
    if read_only:
        extra += " [RO]"

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
            app.stdscr.addstr(y, 2, body[:w - 4], overlay)
        except curses.error:
            pass
        cx = 2 + len(prefix) + app.explorer_filter_cursor
        if cx < w - 1:
            try:
                app.stdscr.chgat(y, cx, 1, overlay | curses.A_REVERSE)
            except curses.error:
                pass
        offset += 1

    list_h = h - LIST_H - offset - (0 if h < COMPACT_THRESHOLD else 1)
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
            icon = "◉" if _is_video_file(full) else "♪"
            meta = app.meta_cache.get(full)
            if meta and meta.get('title'):
                display = f"{meta.get('artist', '?')} - {meta.get('title', name)}"
            else:
                display = name.rsplit('.', 1)[0] if '.' in name else name
            line = f"  {mark}{icon} {display}  [{label}]"
            attr = texto
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
            dur_x = w - len(dur_str) - 2
            safe_addstr(app.stdscr, y, dur_x, dur_str, texto, h, w)
            if is_cursor:
                fill_start = 2 + len(line)
                fill_len = dur_x - fill_start
                if fill_len > 0:
                    safe_addstr(app.stdscr, y, fill_start, " " * fill_len, attr | curses.A_REVERSE, h, w)
        elif is_cursor:
            fill_start = 2 + len(line)
            fill_len = w - 2 - fill_start
            if fill_len > 0:
                safe_addstr(app.stdscr, y, fill_start, " " * fill_len, attr | curses.A_REVERSE, h, w)

    draw_list_indicators(app.stdscr, h, w, app.scroll, total, list_h)


def draw_playlist(app: PlayerApp, h: int, w: int) -> None:
    extra = " [Filtro]" if app.playlist_filter_mode else ""
    total_items = len(app.playlist)
    texto = curses.color_pair(PAIR_TEXTO)
    destacar = curses.color_pair(PAIR_DESTACAR)
    overlay = curses.color_pair(PAIR_OVERLAY)
    nav = curses.color_pair(PAIR_NAV)
    marco = curses.color_pair(PAIR_MARCO)

    list_h = h - LIST_H - (1 if app.playlist_filter_mode else 0) - (0 if h < COMPACT_THRESHOLD else 1)
    if total_items > list_h and total_items > 0:
        pos = f" ({app.playlist_cursor + 1}/{total_items})"
    elif total_items > 0:
        pos = f" ({total_items})"
    else:
        pos = ""

    # Draw box with carousel title
    draw_box(app.stdscr, h, w, "")
    names = list(app.playlist_data.keys())
    n = len(names)
    if n > 1:
        title = f"Playlist ◀ [{app.active_name}] ▶{pos}{extra}"
    else:
        title = f"Playlist [{app.active_name}]{pos}{extra}"
    title_str = f" {title} "
    tx = max(2, (w - len(title_str)) // 2)
    max_tw = max(0, w - tx - 1)
    if len(title_str) > max_tw and max_tw >= 2:
        title_str = title_str[:max_tw - 1] + "…"
    elif len(title_str) > max_tw:
        title_str = title_str[:max_tw]
    safe_addstr(app.stdscr, 0, tx, title_str, marco, h, w)

    if app.playlist_filter_mode:
        prefix = "> "
        body = prefix + app.playlist_filter
        try:
            app.stdscr.addstr(2, 2, body[:w - 4], overlay)
        except curses.error:
            pass
        cx = 2 + len(prefix) + app.playlist_filter_cursor
        if cx < w - 1:
            try:
                app.stdscr.chgat(2, cx, 1, overlay | curses.A_REVERSE)
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

    draw_list_indicators(app.stdscr, h, w, app.playlist_scroll, len(indices), list_h)


def draw_history(app: PlayerApp, h: int, w: int) -> None:
    total = len(app.history)
    pos = f" ({app.history_cursor + 1}/{total})" if total > 0 else ""
    draw_box(app.stdscr, h, w, f"Historial{pos}")
    texto = curses.color_pair(PAIR_TEXTO)
    destacar = curses.color_pair(PAIR_DESTACAR)
    if not app.history:
        safe_addstr(app.stdscr, h // 2, 2, "  Sin historial", texto, h, w)
        return
    _compact_history = h < COMPACT_THRESHOLD
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
                      left_margin=2, attr=texto, cursor_attr=destacar,
                      dur_attr=texto, fallback_icon="~",
                      fallback_label="Archivo Inexistente", h=h, w=w)

    draw_list_indicators(app.stdscr, h, w, start, len(app.history), list_h)


def draw_download_history(app: PlayerApp, h: int, w: int) -> None:
    """Dibuja la vista de historial unificado (descargas + streams)."""
    from .downloads import format_size, format_duration
    history = app.download_history
    items = app.dl_history_filtered
    total = len(items)
    is_streams = app.dl_history_tab == 1
    tab_label = "Streams" if is_streams else "Descargas"
    pos = f" ({app.dl_history_cursor + 1}/{total})" if total > 0 else ""
    title = f"Historial — {tab_label}{pos}"
    if app.dl_history_filter_mode:
        title += f"  /{app.dl_history_filter}"
    draw_box(app.stdscr, h, w, title)
    texto = curses.color_pair(PAIR_TEXTO)
    destacar = curses.color_pair(PAIR_DESTACAR)
    nav = curses.color_pair(PAIR_NAV)

    # Tab bar
    tab_y = 1
    tab_x = 4
    for i, name in enumerate(["Descargas", "Streams"]):
        is_active = i == app.dl_history_tab
        label = f"[{name}]" if is_active else f" {name} "
        attr = (destacar | curses.A_REVERSE) if is_active else nav
        safe_addstr(app.stdscr, tab_y, tab_x, label, attr, h, w)
        tab_x += len(name) + 3

    if not history:
        msg = "Sin streams" if is_streams else "Sin historial de descargas"
        safe_addstr(app.stdscr, h // 2, 2, f"  {msg}", texto, h, w)
        return

    if not items:
        safe_addstr(app.stdscr, h // 2, 2, "  Sin resultados", texto, h, w)
        return

    list_h = h - 5
    start = max(0, min(app.dl_history_scroll, total - list_h))
    visible = items[start:start + list_h]

    for i, idx in enumerate(visible):
        y = 3 + i
        entry = history[idx]
        is_cur = idx == items[app.dl_history_cursor] if app.dl_history_cursor < len(items) else False
        exists = entry.exists

        if is_streams:
            icon = "♪" if exists else "✗"
            dur = format_duration(entry.duration)
            count = f"{entry.play_count}x" if entry.play_count > 1 else ""
            title_w = w - 30
            entry_title = entry.title[:title_w - 1] + "…" if len(entry.title) > title_w else entry.title
            line = f" {icon} {entry_title}"
            if dur:
                line += f"  {dur:>6}"
            if count:
                line += f"  {count:>4}"
            line += f"  {entry.platform[:8]:>8}"
        else:
            status = "✓" if exists else "✗"
            size = format_size(entry.file_size_bytes)
            title_w = w - 25
            entry_title = entry.title[:title_w - 1] + "…" if len(entry.title) > title_w else entry.title
            line = f" {status} {entry_title}"
            if size:
                line += f"  {size:>6}"
            line += f"  {entry.platform[:8]:>8}"

        attr = destacar | curses.A_REVERSE if is_cur else texto
        if not exists:
            attr = curses.color_pair(PAIR_NAV) if is_cur else curses.A_DIM
        safe_addstr(app.stdscr, y, 2, line[:w - 4], attr, h, w)

    draw_list_indicators(app.stdscr, h, w, start, total, list_h)

    hints = "[/]:tab  j/k:navegar  Enter:play  d:buscar/re-descargar  c:quitar  x:borrar  X:limpiar  /:filtrar  Esc:volver"
    safe_addstr(app.stdscr, h - 2, 2, hints[:w - 4], nav, h, w)


def draw_config(app: PlayerApp, h: int, w: int) -> None:
    draw_box(app.stdscr, h, w, "")
    texto = curses.color_pair(PAIR_TEXTO)
    destacar = curses.color_pair(PAIR_DESTACAR)
    nav = curses.color_pair(PAIR_NAV)
    overlay = curses.color_pair(PAIR_OVERLAY)
    marco = curses.color_pair(PAIR_MARCO)

    is_audio_tab = app.config_tabs[app.config_tab_idx]["name"] == "Audio"
    compact = h < COMPACT_THRESHOLD or w < 61
    eq_bar_w = 4 if compact else 40

    labels = {
        "music_dir": f"Directorio música: {app.config.get('music_dir', '~/Music')}",
        "volume": f"Volumen: {app.volume}%",
        "theme": f"Tema: {app.config.get('theme', 'clasico')}",
        "sleep_timer_minutes": f"Sleep timer: {app.config.get('sleep_timer_minutes', 30)} min",
        "eq_preset": f"Preset: {app.config.get('eq_preset', 'Flat')}",
        "online_download_format": f"Formato descarga: {app.config.get('online_download_format', 'audio')}",
        "online_download_quality": f"Calidad descarga: {app.config.get('online_download_quality', '480p')}",
        "online_download_max": f"Descargas máximas: {app.config.get('online_download_max', 3)}",
        "online_cookies": f"Cookies yt-dlp: {app.config.get('online_cookies', 'none')}",
    }
    cc = app.config.get("custom_colors", {})

    # --- Tab bar carousel at line 1 ---
    tab_names = [t["name"] for t in app.config_tabs]
    inner_w = w - 4
    draw_tab_carousel(app.stdscr, 1, tab_names, app.config_tab_idx, inner_w, 2,
                      nav, overlay | curses.A_REVERSE, marco, h=h, w=w)

    # --- Hints line for Audio tab ---
    y_offset = 0
    if is_audio_tab:
        cur_item_type = app.config_items[app.config_cursor][2] if app.config_cursor < len(app.config_items) else ""
        if cur_item_type in ("eq_preamp", "eq_band"):
            hints = _build_hints([("← →", "±0.5dB")], w - 4)
        elif cur_item_type == "choice":
            hints = _build_hints([("← →", "cambiar")], w - 4)
        else:
            hints = _build_hints([("← →", "cambiar")], w - 4)
        if hints:
            safe_addstr(app.stdscr, 2, 2, hints, nav, h, w)
            y_offset = 1

    # --- Items with scroll ---
    items = app.config_items
    total = len(items)
    cur = app.config_cursor
    list_h = h - 5 - y_offset if h < COMPACT_THRESHOLD else h - 6 - y_offset

    app.config_scroll = clamp_scroll(app.config_scroll, total, list_h, cur)

    visible = items[app.config_scroll:app.config_scroll + list_h]
    is_custom_eq = app.config.get("eq_preset", "Flat") == "Custom"
    for i, (key, label, ctype) in enumerate(visible):
        y = 3 + y_offset + i
        idx = app.config_scroll + i
        if ctype == "separator":
            sep_w = max(0, w - 4)
            safe_addstr(app.stdscr, y, 2, "─" * sep_w, marco, h, w)
            continue
        elif ctype == "color":
            line = f"  {label}: {cc.get(key, 'Blanco')}"
        elif ctype == "bool":
            line = f"  {label}: {'Sí' if app.config.get(key, True) else 'No'}"
        elif ctype in ("eq_preamp", "eq_band"):
            if ctype == "eq_preamp":
                val = app.config.get("eq_preamp", 0.0)
            else:
                band_idx = int(key.split("_")[-1])
                bands = app.config.get("eq_bands", [0.0] * 10)
                val = bands[band_idx] if band_idx < len(bands) else 0.0
            bar = _eq_bar(val, eq_bar_w)
            line = f"  {label:<6}: {val:+5.1f}  {bar}"
        elif key == "keybindings":
            mode_label = "Default" if app.keybinding_mode == "default" else "Custom"
            line = f"  {label}  [{mode_label}]"
        elif key == "update":
            line = f"  {label}  [Comprobar]"
            if app.update_available:
                line += "  !"
        else:
            line = f"  {labels.get(key, key)}"
        if ctype in ("choice", "color", "int", "bool") and ctype != "eq_preamp":
            line += "  ← →"
        elif ctype == "path":
            line += "  Enter"
        max_w = w - 4
        if len(line) > max_w:
            line = line[:max_w - 1] + "…"
        if ctype == "eq_band" and not is_custom_eq:
            safe_addstr(app.stdscr, y, 2, line, texto, h, w)
        elif idx == cur:
            safe_addstr(app.stdscr, y, 2, line, destacar | curses.A_REVERSE, h, w)
        else:
            safe_addstr(app.stdscr, y, 2, line, texto, h, w)

    draw_list_indicators(app.stdscr, h, w, app.config_scroll, total, list_h)


def draw_keybindings(app: PlayerApp, h: int, w: int) -> None:
    draw_box(app.stdscr, h, w, "Keybindings")
    texto = curses.color_pair(PAIR_TEXTO)
    destacar = curses.color_pair(PAIR_DESTACAR)
    overlay = curses.color_pair(PAIR_OVERLAY)
    nav = curses.color_pair(PAIR_NAV)

    compact = h < COMPACT_THRESHOLD
    is_custom = app.keybinding_mode == "custom"
    mode = "PERSONALIZADO" if is_custom else "POR DEFECTO"

    if compact:
        safe_addstr(app.stdscr, 2, 2, f"Modo:{mode}  ←→cambiar  Esc:volver", overlay, h, w)
        if not is_custom:
            safe_addstr(app.stdscr, 3, 2, "Pasá a Personalizado para editar", texto, h, w)
            return
        safe_addstr(app.stdscr, 3, 2, "Enter:asignar tecla", texto, h, w)
        list_h = max(1, h - 5)
        y0 = 4
    else:
        safe_addstr(app.stdscr, 2, 2, f"  Modo: {mode}  ← → cambiar", overlay, h, w)
        if not is_custom:
            safe_addstr(app.stdscr, 4, 2, "  Cambiá a modo Personalizado para editar las teclas", texto, h, w)
            safe_addstr(app.stdscr, h - 3, 2, "  [Esc] Volver", nav, h, w)
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
        safe_addstr(app.stdscr, h - 3, 2, footer, overlay, h, w)


def draw_meta_editor(app: PlayerApp, win: curses.window, h: int, w: int) -> None:
    texto = curses.color_pair(PAIR_TEXTO)
    destacar = curses.color_pair(PAIR_DESTACAR)
    compact = h < COMPACT_THRESHOLD

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
    y0 = 2
    list_h = h - LIST_H - 1
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
        dur_str = "STREAM"
        dur_w = len(dur_str) + 3
        line = f"  [R] {r['name']}"
        max_w = w - 2 - dur_w
        if len(line) > max_w:
            line = line[:max_w - 1] + "…"
        safe_addstr(win, y, 2, line, attr, h, w)
        gap_start = 2 + len(line)
        url_start = gap_start + 2
        gap_len = url_start - gap_start
        if gap_len > 0 and is_cursor:
            safe_addstr(win, y, gap_start, " " * gap_len, attr, h, w)
        url_display = r['url'][:w - url_start - dur_w - 2]
        safe_addstr(win, y, url_start, url_display, attr, h, w)
        dur_x = w - len(dur_str) - 2
        if is_cursor and url_start + len(url_display) < dur_x:
            fill = dur_x - (url_start + len(url_display))
            if fill > 0:
                safe_addstr(win, y, url_start + len(url_display), " " * fill, attr, h, w)
        safe_addstr(win, y, dur_x, dur_str, texto, h, w)
    if not radios:
        safe_addstr(win, y0, 2, "  Sin radios guardadas", texto, h, w)
        return
    draw_list_indicators(win, h, w, scroll, len(radios), list_h)
    nav = curses.color_pair(PAIR_NAV)
    hints = _build_hints([
        ("Enter", "►"), ("a/A", "agregar"), ("e", "editar"),
        ("d", "eliminar"), ("f", "fav"), ("x", "export"),
    ], w)
    if hints:
        safe_addstr(win, h - 2, 2, hints, nav, h, w)


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


def draw_web(app: PlayerApp, h: int, w: int) -> None:
    """V7 Web Explorer con motor + prompt + divider + lista."""
    from . import web as _web
    texto = curses.color_pair(PAIR_TEXTO)
    destacar = curses.color_pair(PAIR_DESTACAR)
    nav = curses.color_pair(PAIR_NAV)

    draw_box(app.stdscr, h, w, "Web")

    if not _web.is_available():
        safe_addstr(app.stdscr, 3, 2, "yt-dlp no está instalado.", destacar, h, w)
        safe_addstr(app.stdscr, 5, 2, "Ejecutá en tu terminal:", texto, h, w)
        safe_addstr(app.stdscr, 6, 2, "pip install --break-system-packages yt-dlp", nav, h, w)
        safe_addstr(app.stdscr, 8, 2, "Luego reiniciá tplay.", texto, h, w)
        return

    if app.web_motor_edit_mode:
        _draw_motor_editor(app, h, w)
        return

    if app.web_download_mode:
        _draw_download_config(app, h, w)
        return

    platforms = app.web_platforms
    p_name = platforms[app.web_active_platform].name if platforms else "Ninguna"

    _draw_web_main(app, h, w, p_name)


def _draw_web_main(app: PlayerApp, h: int, w: int, p_name: str) -> None:
    """Layout principal: motor + prompt + divider + lista."""
    from . import web as _web
    texto = curses.color_pair(PAIR_TEXTO)
    destacar = curses.color_pair(PAIR_DESTACAR)
    nav = curses.color_pair(PAIR_NAV)

    multi = len(app.web_platforms) > 1
    motor_str = f"← [{p_name}] →" if multi else f"[{p_name}]"
    if app.web_search_mode:
        prompt_str = f"buscar: {app.web_search_buf}"
        motor_attr = nav
        prompt_attr = texto | curses.A_UNDERLINE
    elif app.web_last_query:
        prompt_str = f"buscar: {app.web_last_query}"
        motor_attr = nav
        prompt_attr = texto
    else:
        prompt_str = "presiona / para buscar"
        motor_attr = nav
        prompt_attr = nav

    y_motor = 2
    motor_w = len(motor_str) + 2
    safe_addstr(app.stdscr, y_motor, 2, motor_str, motor_attr, h, w)
    prompt_x = motor_w + 2
    prompt_w = w - prompt_x - 2
    safe_addstr(app.stdscr, y_motor, prompt_x, prompt_str[:prompt_w], prompt_attr, h, w)

    y_divider = 3
    safe_addstr(app.stdscr, y_divider, 2, "─" * (w - 4), nav, h, w)

    if app.web_loading:
        safe_addstr(app.stdscr, (h - 4) // 2, 2, "  Buscando...", destacar | curses.A_BLINK, h, w)
        _draw_web_hints(app, h, w)
        return

    if not app.web_results:
        safe_addstr(app.stdscr, (h - 4) // 2, 2, "  Sin resultados", nav, h, w)
        _draw_web_hints(app, h, w)
        return

    list_h = h - 7
    start = app.web_scroll
    end = min(start + list_h, len(app.web_results))

    for i in range(start, end):
        y = 4 + i - start
        r = app.web_results[i]
        is_cur = i == app.web_cursor
        dur = _web.format_duration(r.duration)

        status = _web.get_result_status(app.web_results, i, app.web_playing_idx)

        title_w = w - 19
        title = r.title[:title_w]
        line = f" {status} {title:<{title_w}}{dur:>7}"
        attr = destacar | curses.A_REVERSE if is_cur else texto
        safe_addstr(app.stdscr, y, 2, line[:w - 4], attr, h, w)

    if app.web_cursor < len(app.web_results):
        dm = _web.get_download_manager()
        cur_result = app.web_results[app.web_cursor]
        dl_item = dm.find_by_url(cur_result.webpage_url)
        if dl_item and dl_item.state == _web.DownloadState.FAILED and dl_item.error:
            err_line = f" Error: {dl_item.error}"
            safe_addstr(app.stdscr, 3, 2, err_line[:w - 4], curses.color_pair(PAIR_NAV), h, w)

    draw_list_indicators(app.stdscr, h, w, app.web_scroll, len(app.web_results), list_h)
    _draw_web_hints(app, h, w)


def _draw_web_hints(app: PlayerApp, h: int, w: int) -> None:
    """Hints de la vista web."""
    from .ui import _build_hints
    nav = curses.color_pair(PAIR_NAV)

    if app.web_search_mode:
        hints = _build_hints([
            ("Enter", "buscar"), ("Tab", "buscar"), ("Esc", "cancelar"),
        ], w)
    elif app.web_download_mode:
        hints = _build_hints([
            ("h/l", "ciclar"), ("j/k", "campo"), ("Enter", "descargar"),
            ("Esc", "volver"),
        ], w)
    elif app.web_motor_edit_mode:
        hints = _build_hints([
            ("j/k", "campo"), ("Enter", "editar"), ("s", "guardar"),
            ("q/Esc", "cancelar"),
        ], w)
    else:
        has_results = len(app.web_results) > 0
        hints_list = [
            ("j/k", "navegar"), ("g/G", "inicio/fin"),
            ("h/l", "motor"),
        ]
        if has_results:
            hints_list.extend([
                ("Enter", "play"), ("D", "descargar"), ("d", "config"),
                ("a", "añadir"), ("A", "siguiente"),
                ("c", "cancelar"), ("x", "limpiar"),
            ])
        else:
            hints_list.extend([
                ("a", "nuevo motor"), ("e", "editar"), ("d", "eliminar"),
            ])
        hints_list.extend([("/", "buscar"), ("Esc", "volver")])
        hints = _build_hints(hints_list, w)
    if hints:
        safe_addstr(app.stdscr, h - 4, 2, hints, nav, h, w)


def _draw_motor_editor(app: PlayerApp, h: int, w: int) -> None:
    """Editor de plataformas (patrón draw_meta_editor)."""
    texto = curses.color_pair(PAIR_TEXTO)
    destacar = curses.color_pair(PAIR_DESTACAR)
    compact = h < COMPACT_THRESHOLD

    pad_x = 2
    title = "Nueva plataforma" if app.web_motor_edit_is_new else "Editar plataforma"
    draw_box(app.stdscr, h, w, title)

    if compact:
        safe_addstr(app.stdscr, 2, pad_x, "↑↓ Naveg  Enter Ed  s:Guardar  q:Salir", texto, h, w)
        y0 = 3
    else:
        safe_addstr(app.stdscr, 2, pad_x,
                    "↑/↓: navegar  Enter: editar  [s] guardar  [q] cancelar",
                    texto, h, w)
        y0 = 4

    fields_order = ["name", "url", "search_pattern", "download_pattern", "search_prefix"]
    labels = {
        "name": "Nombre",
        "url": "URL",
        "search_pattern": "Patrón búsqueda",
        "download_pattern": "Patrón descarga",
        "search_prefix": "Search prefix",
    }

    total = len(fields_order)
    cur = app.web_motor_edit_cursor
    list_h = total if not compact else max(2, h - y0 - 1)

    scroll = max(0, min(cur, total - list_h)) if total > list_h else 0
    visible = fields_order[scroll:scroll + list_h]

    for i, field in enumerate(visible):
        actual_idx = scroll + i
        row = y0 + i
        label = labels.get(field, field)
        current = app.web_motor_edit_fields.get(field, "")
        val = current if current else "(vacío)"
        line = f"  {label}: {val}"
        attr = destacar if actual_idx == cur else texto
        if actual_idx == cur and not app.web_motor_edit_editing:
            safe_addstr(app.stdscr, row, pad_x, line, attr | curses.A_REVERSE, h, w)
        else:
            safe_addstr(app.stdscr, row, pad_x, line, attr, h, w)
        if actual_idx == cur and app.web_motor_edit_editing:
            buf = app.web_motor_edit_buf
            cx = pad_x + len(f"  {label}: ")
            display = buf if buf else ""
            try:
                app.stdscr.addstr(row, cx, display[:w - cx - 2], attr)
            except curses.error:
                pass
            cur_in_buf = app.web_motor_edit_cursor_pos
            if cx + cur_in_buf < w - 1:
                try:
                    app.stdscr.chgat(row, cx + cur_in_buf, 1, attr | curses.A_REVERSE)
                except curses.error:
                    pass

    status_row = y0 + len(visible)
    if not compact and status_row < h - 1:
        safe_addstr(app.stdscr, status_row + 1, pad_x, "  s: guardar  q: cancelar", texto, h, w)


def _draw_download_config(app: PlayerApp, h: int, w: int) -> None:
    """Configuración de descarga cíclica."""
    texto = curses.color_pair(PAIR_TEXTO)
    destacar = curses.color_pair(PAIR_DESTACAR)
    nav = curses.color_pair(PAIR_NAV)
    compact = h < COMPACT_THRESHOLD

    pad_x = 2
    draw_box(app.stdscr, h, w, "Configurar descarga")

    if compact:
        safe_addstr(app.stdscr, 2, pad_x, "↑↓ Naveg  ←→ Cambiar  Enter Descargar", texto, h, w)
        y0 = 3
    else:
        safe_addstr(app.stdscr, 2, pad_x,
                    "↑/↓: navegar  ←/→: cambiar  Enter: descargar  Esc: cancelar",
                    texto, h, w)
        y0 = 4

    fields_order = ["format", "quality"]
    labels = {"format": "Formato", "quality": "Calidad"}

    total = len(fields_order)
    cur = app.web_download_cursor

    for i, field in enumerate(fields_order):
        row = y0 + i
        label = labels.get(field, field)
        val = app.web_download_fields.get(field, "")
        line = f"  {label}: [{val}] ←→"
        attr = destacar if i == cur else texto
        if i == cur:
            safe_addstr(app.stdscr, row, pad_x, line, attr | curses.A_REVERSE, h, w)
        else:
            safe_addstr(app.stdscr, row, pad_x, line, attr, h, w)

    status_row = y0 + total
    if not compact and status_row < h - 1:
        safe_addstr(app.stdscr, status_row + 1, pad_x, "  Enter: descargar  Esc: cancelar", nav, h, w)


def draw_favorites(app: PlayerApp, h: int, w: int) -> None:
    win = app.stdscr

    texto = curses.color_pair(PAIR_TEXTO)

    title = f"Favoritos ({len(app.favorites)})"
    draw_box(win, h, w, title)

    if not app.favorites:
        safe_addstr(win, h // 2, 2, "  Sin favoritos — usa 'f' en el Explorador", texto, h, w)
        return

    list_h = h - 5 if h >= COMPACT_THRESHOLD else h - 4
    visible = app.favorites[app.favorites_scroll:app.favorites_scroll + list_h]

    for i, entry in enumerate(visible):
        y = 2 + i
        idx = app.favorites_scroll + i
        name = entry.get("name", os.path.basename(entry.get("path", "?")))
        path = entry.get("path", "")
        is_stream = "://" in path
        icon = "[R]" if is_stream else "♪"
        if is_stream:
            display = name
            dur_str = "--:--"
        else:
            exists = os.path.isfile(path)
            meta = app.meta_cache.get(path) if exists else None
            if meta and meta.get('title'):
                display = f"{meta.get('artist', '?')} - {meta.get('title', name)}"
            else:
                display = name.rsplit('.', 1)[0] if '.' in name else name
            dur = meta.get('length', 0) if meta else 0
            dur_str = time_str(dur) if dur > 0 else ""
        dur_w = len(dur_str) + 3 if dur_str else 0
        line = f"  {icon} {display}"
        max_w = w - 2 - dur_w
        if len(line) > max_w:
            line = line[:max_w - 1] + "…"

        is_cursor = (idx == app.favorites_cursor)
        if is_cursor:
            safe_addstr(win, y, 2, line, texto | curses.A_REVERSE, h, w)
        else:
            safe_addstr(win, y, 2, line, texto, h, w)
        if dur_str:
            dur_x = w - len(dur_str) - 2
            safe_addstr(win, y, dur_x, dur_str, texto, h, w)
            if is_cursor:
                fill_start = 2 + len(line)
                fill_len = dur_x - fill_start
                if fill_len > 0:
                    safe_addstr(win, y, fill_start, " " * fill_len, texto | curses.A_REVERSE, h, w)
        elif is_cursor:
            fill_start = 2 + len(line)
            fill_len = w - 2 - fill_start
            if fill_len > 0:
                safe_addstr(win, y, fill_start, " " * fill_len, texto | curses.A_REVERSE, h, w)

    draw_list_indicators(win, h, w, app.favorites_scroll, len(app.favorites), list_h)
