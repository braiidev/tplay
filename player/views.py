import os
import curses

from .config import PAIR_MARCO, PAIR_TEXTO, PAIR_DESTACAR, PAIR_NAV
from .file_utils import time_str, ext_label, is_url as _is_url
from .ui import safe_addstr, draw_box, LIST_H, STATUS_ROW, EXPLORER_MARGIN, PLAYLIST_MARGIN
from . import keybindings as kb
from .handlers import _get_current_key


def _center(s: str, w: int) -> str:
    s = s.strip()
    if len(s) >= w:
        return s[:w]
    left = (w - len(s)) // 2
    return " " * left + s + " " * (w - len(s) - left)


def draw_listen(app, h: int, w: int) -> None:
    texto = curses.color_pair(PAIR_TEXTO)
    dest = curses.color_pair(PAIR_DESTACAR)
    nav = curses.color_pair(PAIR_NAV)

    if app.show_stack_view:
        total = len(app.stack.items)
        pos = f" ({app.stack_cursor + 1}/{total})" if total > 0 else ""
        draw_box(app.stdscr, h, w, f"Stack{pos} ({total})")
        if not app.stack.items:
            safe_addstr(app.stdscr, h // 2, 2, "  Stack vacío — usá [2] Explorer para añadir", texto, h, w)
        else:
            list_h = h - 8
            visible = app.stack.items[app.stack_scroll:app.stack_scroll + list_h]
            for row, item in enumerate(visible):
                y = 2 + row
                idx = app.stack_scroll + row
                meta = app.meta_cache.get(item.path) if not _is_url(item.path) else None
                is_stream = _is_url(item.path)
                if is_stream:
                    display_name = f"[R] {item.name}"
                elif meta and meta.get('title'):
                    display_name = f"{meta.get('artist', '?')} - {meta.get('title', item.name)}"
                else:
                    display_name = item.name
                is_playing = (app.stack.playhead == idx) and app.audio.playing
                icon = "►" if is_playing else "♪"
                mode_tag = ""
                if item.mode == "repeat_once":
                    mode_tag = " [1x]"
                elif item.mode == "repeat_inf":
                    mode_tag = " [∞]"
                line = f"  {icon} {display_name}{mode_tag}"
                dur = meta.get('length', 0) if meta else 0
                dur_str = time_str(dur) if dur > 0 else ""
                dur_w = len(dur_str) + 3 if dur_str else 0
                max_w = w - 8 - dur_w
                if len(line) > max_w:
                    line = line[:max_w - 1] + "…"
                attr = dest if is_playing else texto
                if idx == app.stack_cursor:
                    safe_addstr(app.stdscr, y, 2, line, attr | curses.A_REVERSE, h, w)
                else:
                    safe_addstr(app.stdscr, y, 2, line, attr, h, w)
                if dur_str:
                    safe_addstr(app.stdscr, y, w - len(dur_str) - 2, dur_str, attr, h, w)
            safe_addstr(app.stdscr, h - 4, 2,
                        "  [Enter]►  [Tab] Volver  [d]el  [x]clear  [J/K]orden  [s]guardar", texto, h, w)
            safe_addstr(app.stdscr, h - 3, 2,
                        "  [r/R]modo item  [g]Inicio  [G]Fin  [o]URL", texto, h, w)
        return

    draw_box(app.stdscr, h, w, "Listen")
    mid = max(3, (h - 8) // 2)

    if not app.stack.items or not app.audio.playing:
        safe_addstr(app.stdscr, mid - 1, 2, "  Nada sonando.", dest, h, w)
        safe_addstr(app.stdscr, mid + 1, 2, "  Abrí [2] Explorer y seleccioná un archivo", texto, h, w)
        return

    cur_item = app.stack.current
    if not cur_item:
        return

    is_stream = _is_url(cur_item.path)
    meta = app.meta_cache.get(cur_item.path) if not is_stream else None
    estado = "► PLAY" if not app.paused else "|| PAUSE"

    if is_stream:
        safe_addstr(app.stdscr, mid - 3, 2, f"  {estado}  [STREAM]", dest, h, w)
        safe_addstr(app.stdscr, mid - 1, 2, f"  {cur_item.name}", texto, h, w)
        safe_addstr(app.stdscr, mid, 2, f"  {cur_item.path}", texto, h, w)
    else:
        artist = (meta.get('artist') if meta else None) or "Artista desconocido"
        album = (meta.get('album') if meta else None) or "Álbum desconocido"
        title = (meta.get('title') if meta else None) or cur_item.name
        safe_addstr(app.stdscr, mid - 3, 2, f"  {estado}", dest, h, w)
        tw = w - 6
        title_s = title[:tw - 1] + "…" if len(title) > tw else title
        safe_addstr(app.stdscr, mid - 1, 2, f"    {title_s}", texto, h, w)
        artist_album = f"{artist}  —  {album}"
        aa_s = artist_album[:tw - 1] + "…" if len(artist_album) > tw else artist_album
        safe_addstr(app.stdscr, mid, 2, f"    {aa_s}", texto, h, w)

    length = app.audio.get_length()
    pos = app.audio.get_time()

    if length > 0:
        progress = min(pos / length, 1.0)
        cur_s = time_str(pos // 1000)
        dur_s = time_str(length // 1000)
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
        gm = f"{app.goto_mins:02d}"
        gs = f"{app.goto_secs:02d}"
        am = texto | curses.A_REVERSE if app.goto_field == 0 else texto
        as_ = texto | curses.A_REVERSE if app.goto_field == 1 else texto
        safe_addstr(app.stdscr, mid + 6, 2, "  Ir a: [", texto, h, w)
        safe_addstr(app.stdscr, mid + 6, 11, gm, am, h, w)
        safe_addstr(app.stdscr, mid + 6, 13, ":", texto, h, w)
        safe_addstr(app.stdscr, mid + 6, 14, gs, as_, h, w)
        safe_addstr(app.stdscr, mid + 6, 16, "]", texto, h, w)
        safe_addstr(app.stdscr, mid + 7, 2, "  ← → campo  ↑ ↓ valor  Enter saltar", texto, h, w)

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

    extra = "  [Tab] Stack │ [o] URL │ [g] Goto │ [t/T] Tmr │ [h/l] Seek │ [r]Sfl [R]Rpt [m]Mute"

    safe_addstr(app.stdscr, h - 5, 2, line1[:w - 4], dest, h, w)
    safe_addstr(app.stdscr, h - 4, 2, line2[:w - 4], texto, h, w)
    safe_addstr(app.stdscr, h - 3, 2, extra[:w - 4], nav, h, w)


def draw_mini_stack(app, win, h: int, w: int) -> None:
    texto = curses.color_pair(PAIR_TEXTO)
    dest = curses.color_pair(PAIR_DESTACAR)

    try:
        app.stdscr.addstr(0, 0, "┌" + "─" * max(0, w - 2) + "┐", dest)
    except curses.error:
        pass
    try:
        app.stdscr.addstr(h - 1, 0, "└" + "─" * max(0, w - 2) + "┘", dest)
    except curses.error:
        pass
    for y in range(1, h - 1):
        try:
            app.stdscr.addstr(y, 0, "│", dest)
            app.stdscr.addstr(y, max(0, w - 1), "│", dest)
        except curses.error:
            pass

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
        icon = "►" if is_playing else "♪"
        line = f" {icon} {item.name}"
        max_w = w - 3
        if len(line) > max_w:
            line = line[:max_w - 1] + "…"
        attr = dest if is_playing else texto
        if idx == app.stack_cursor:
            safe_addstr(win, y, 1, line, attr | curses.A_REVERSE, h, w)
        else:
            safe_addstr(win, y, 1, line, attr, h, w)


def draw_listen_compact(app, h: int, w: int) -> None:
    if app.show_stack_view:
        draw_mini_stack(app, app.stdscr, h, w)
        return
    marco = curses.color_pair(PAIR_MARCO)
    texto = curses.color_pair(PAIR_TEXTO)
    dest = curses.color_pair(PAIR_DESTACAR)

    status = ""
    if app.audio.playing:
        status = "❚❚" if app.paused else "▶"
    title = f" {status} Listen " if status else " Listen "
    try:
        app.stdscr.addstr(0, 0, "┌" + "─" * max(0, w - 2) + "┐", marco)
        if w > len(title) + 2:
            tx = max(2, (w - len(title)) // 2)
            app.stdscr.addstr(0, tx, title[:w - tx - 1], marco)
    except curses.error:
        pass
    try:
        app.stdscr.addstr(h - 1, 0, "└" + "─" * max(0, w - 2) + "┘", marco)
    except curses.error:
        pass
    for y in range(1, h - 1):
        try:
            app.stdscr.addstr(y, 0, "│", marco)
            app.stdscr.addstr(y, max(0, w - 1), "│", marco)
        except curses.error:
            pass

    if not app.stack.items or not app.audio.playing:
        msg = "Nada sonando."
        safe_addstr(app.stdscr, h // 2, (w - len(msg)) // 2, msg, dest, h, w)
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
    safe_addstr(app.stdscr, 2, 2, t, dest, h, w)

    if not is_stream:
        artist = (meta.get('artist') if meta else None) or "?"
        album = (meta.get('album') if meta else None) or "?"
        aa = f"{artist} — {album}"
        a = aa[:max_w - 1] + "…" if len(aa) > max_w else aa
        safe_addstr(app.stdscr, 3, 2, a, texto, h, w)

    length = app.audio.get_length()
    pos = app.audio.get_time()
    if length > 0:
        progress = min(pos / length, 1.0)
        cur_s = time_str(pos // 1000)
        dur_s = time_str(length // 1000)
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
    full = controls + vol_str + states
    if len(full) <= max_w:
        display = full
    else:
        no_states = controls + vol_str
        if len(no_states) <= max_w:
            display = no_states
        else:
            display = controls[:max_w]
    safe_addstr(app.stdscr, h - 2, 2, display, dest, h, w)


def draw_explorer(app, h: int, w: int) -> None:
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
        safe_addstr(app.stdscr, 2 + offset, 2, f"> {app.explorer_filter}", destacar, h, w)
        offset += 1

    list_h = h - LIST_H - offset
    indices = app.explorer_filtered if app.explorer_filter_mode else list(range(len(app.entries)))
    total = len(indices)
    pos = f" ({app.cursor + 1}/{total})" if total > 0 else ""
    title_p = "Explorador: "
    title_s = extra + pos
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
        label = ext_label(name)
        if is_dir:
            line = f"  [+]/ {name}"
            attr = destacar
            dur_str = ""
        else:
            base = name.rsplit('.', 1)[0] if '.' in name else name
            line = f"  ♪ {base}  [{label}]"
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


def draw_playlist(app, h: int, w: int) -> None:
    extra = " [Filtro]" if app.playlist_filter_mode else ""
    total_items = len(app.playlist)
    texto = curses.color_pair(PAIR_TEXTO)
    destacar = curses.color_pair(PAIR_DESTACAR)

    list_h = h - LIST_H - (1 if app.playlist_filter_mode else 0)
    if total_items > list_h and total_items > 0:
        pos = f" ({app.playlist_cursor + 1}/{total_items})"
    elif total_items > 0:
        pos = f" ({total_items})"
    else:
        pos = ""
    draw_box(app.stdscr, h, w, f"Playlist [{app.active_name}]{pos}{extra}")

    if app.playlist_filter_mode:
        safe_addstr(app.stdscr, 2, 2, f"> {app.playlist_filter}", destacar, h, w)

    if not app.playlist:
        if not app.playlist_data:
            safe_addstr(app.stdscr, h // 2, 2,
                              "  No hay playlists. [c] crear una.", texto, h, w)
        else:
            safe_addstr(app.stdscr, h // 2, 2,
                              "  Añadí items desde Explorer con a/A.", texto, h, w)
        return

    indices = app.playlist_filtered if app.playlist_filter_mode else list(range(len(app.playlist)))
    visible = indices[app.playlist_scroll:app.playlist_scroll + list_h]

    if app.playlist_filter_mode and not indices:
        safe_addstr(app.stdscr, 4, 2, "  Sin resultados", texto, h, w)
        return

    for row, abs_idx in enumerate(visible):
        y = (3 if app.playlist_filter_mode else 2) + row
        name, path = app.playlist[abs_idx]
        meta = app.meta_cache.get(path)
        display_name = f"{meta.get('artist', '?')} - {meta.get('title', name)}" if (meta and meta.get('title')) else name
        icon = "►" if app.stack.current and app.stack.current.path == path and app.audio.playing else "♪"
        line = f"  {icon} {display_name}"
        dur = meta.get('length', 0) if meta else 0
        dur_str = time_str(dur) if dur > 0 else ""
        dur_w = len(dur_str) + 3 if dur_str else 0
        max_w = w - PLAYLIST_MARGIN - dur_w
        if len(line) > max_w:
            line = line[:max_w - 1] + "…"
        attr = texto
        cur = app.playlist_cursor
        is_cursor = (cur < len(indices) and abs_idx == indices[cur])
        if is_cursor:
            safe_addstr(app.stdscr, y, 2, line, attr | curses.A_REVERSE, h, w)
        else:
            safe_addstr(app.stdscr, y, 2, line, attr, h, w)
        if dur_str:
            safe_addstr(app.stdscr, y, w - len(dur_str) - 2, dur_str, attr, h, w)


def draw_history(app, h: int, w: int) -> None:
    total = len(app.history)
    pos = f" ({app.history_cursor + 1}/{total})" if total > 0 else ""
    draw_box(app.stdscr, h, w, f"Historial{pos}")
    texto = curses.color_pair(PAIR_TEXTO)
    destacar = curses.color_pair(PAIR_DESTACAR)
    if not app.history:
        safe_addstr(app.stdscr, h // 2, 2, "  Sin historial", texto, h, w)
        return
    list_h = h - LIST_H
    start = max(0, min(app.history_scroll, len(app.history) - list_h))
    visible = app.history[start:start + list_h]
    for i, entry in enumerate(visible):
        y = 2 + i
        idx = start + i
        name = entry.get("name", "?")
        path = entry.get("path", "")
        count = entry.get("count", 0)
        exists = os.path.isfile(path)
        dur_str = ""
        if exists:
            meta = app.meta_cache.get(path)
            dur = meta.get('length', 0) if meta else 0
            dur_str = time_str(dur) if dur > 0 else ""
        dur_w = len(dur_str) + 3 if dur_str else 0
        if exists:
            base = name.rsplit('.', 1)[0] if '.' in name else name
            line = f"  ♪ {base}  ({count}x)"
        else:
            line = f"  ~ Archivo Inexistente  ({count}x)"
        max_w = w - 4 - dur_w
        if len(line) > max_w:
            line = line[:max_w - 1] + "…"
        attr = destacar if idx == app.history_cursor else texto
        if idx == app.history_cursor:
            safe_addstr(app.stdscr, y, 2, line, attr | curses.A_REVERSE, h, w)
        else:
            safe_addstr(app.stdscr, y, 2, line, attr, h, w)
        if dur_str:
            safe_addstr(app.stdscr, y, w - len(dur_str) - 2, dur_str, texto, h, w)


def draw_config(app, h: int, w: int) -> None:
    draw_box(app.stdscr, h, w, "Configuración")
    texto = curses.color_pair(PAIR_TEXTO)
    dest = curses.color_pair(PAIR_DESTACAR)
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
    safe_addstr(app.stdscr, 1, x, "<", nav, h, w)
    x += 1
    for ti, name in enumerate(tab_names):
        if ti > 0:
            safe_addstr(app.stdscr, 1, x, " │ ", nav, h, w)
            x += 3
        attr = dest | curses.A_REVERSE if ti == app.config_tab_idx else texto
        # Truncate name if needed
        display_name = name
        max_name_w = (w - 6) // max(len(tab_names), 1) - 3
        if len(display_name) > max_name_w > 0:
            display_name = display_name[:max_name_w - 1] + "…"
        safe_addstr(app.stdscr, 1, x, display_name, attr, h, w)
        x += len(display_name)
    safe_addstr(app.stdscr, 1, x, ">", nav, h, w)

    # --- Items with scroll ---
    items = app.config_items
    total = len(items)
    cur = app.config_cursor
    list_h = h - 5

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
        elif key == "keybindings":
            mode_label = "Default" if app.keybinding_mode == "default" else "Custom"
            line = f"  {label}  [{mode_label}]"
        elif key == "update":
            line = f"  {label}  [Comprobar]"
            if app.update_available:
                line += "  !"
        else:
            line = f"  {labels.get(key, key)}"
        if ctype in ("choice", "color", "int"):
            line += "  ← →"
        max_w = w - 4
        if len(line) > max_w:
            line = line[:max_w - 1] + "…"
        if idx == cur:
            safe_addstr(app.stdscr, y, 2, line, dest | curses.A_REVERSE, h, w)
        else:
            safe_addstr(app.stdscr, y, 2, line, texto, h, w)


def draw_keybindings(app, h: int, w: int) -> None:
    draw_box(app.stdscr, h, w, "Keybindings")
    texto = curses.color_pair(PAIR_TEXTO)
    destacar = curses.color_pair(PAIR_DESTACAR)

    compact = h < 16
    is_custom = app.keybinding_mode == "custom"
    mode = "CUSTOM" if is_custom else "DEFAULT"

    if compact:
        safe_addstr(app.stdscr, 2, 2, f"Modo:{mode}  ←→cambiar  Esc:volver", destacar, h, w)
        if not is_custom:
            safe_addstr(app.stdscr, 3, 2, "Pasá a Custom para editar", texto, h, w)
            return
        safe_addstr(app.stdscr, 3, 2, "Enter:asignar tecla", texto, h, w)
        list_h = max(1, h - 5)
        y0 = 4
    else:
        safe_addstr(app.stdscr, 2, 2, f"  Modo: {mode}  ← → cambiar", destacar, h, w)
        if not is_custom:
            safe_addstr(app.stdscr, 4, 2, "  Cambiá a modo Custom para personalizar las teclas", texto, h, w)
            safe_addstr(app.stdscr, h - 3, 2, "  [Esc] Volver", texto, h, w)
            return
        safe_addstr(app.stdscr, 3, 2, "  Enter para cambiar una tecla, Esc para volver", texto, h, w)
        list_h = h - 7
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
        if app.kb_conflict_msg:
            safe_addstr(app.stdscr, h - 3, 2, f"  {app.kb_conflict_msg}", texto, h, w)
        safe_addstr(app.stdscr, h - 4, 2, "  [Esc] Volver", texto, h, w)


def draw_meta_editor(app, win, h: int, w: int) -> None:
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
            safe_addstr(win, row, cx, display, attr | curses.A_REVERSE, h, w)

    # Status line only if room
    status_row = y0 + len(visible)
    if not compact and status_row < h - 1:
        row = status_row + 1
        if not app.meta_edit_changed:
            safe_addstr(win, row, pad_x, "  Sin cambios", texto, h, w)
