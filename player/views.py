import os
import curses

from .config import PAIR_MARCO, PAIR_TEXTO, PAIR_DESTACAR
from .file_utils import time_str, ext_label
from .ui import safe_addstr, draw_box, LIST_H, STATUS_ROW, EXPLORER_MARGIN, PLAYLIST_MARGIN
from . import keybindings as kb
from .handlers import _get_current_key


def draw_explorer(app, h: int, w: int) -> None:
    extra = " [Filtro]" if app.explorer_filter_mode else ""
    draw_box(app.stdscr, h, w, f"Explorador: {app.current_dir}{extra}")
    texto = curses.color_pair(PAIR_TEXTO)
    destacar = curses.color_pair(PAIR_DESTACAR)

    offset = 0
    if app.file_op_mode:
        mode_label = "Copiar a" if app.file_op_mode == "copy" else "Mover a"
        app.stdscr.addstr(2, 2, f"  {mode_label}: Enter confirma  Esc cancela", destacar)
        offset = 1

    if app.explorer_filter_mode:
        app.stdscr.addstr(2 + offset, 2, f"> {app.explorer_filter}", destacar)
        offset += 1

    list_h = h - LIST_H - offset
    indices = app.explorer_filtered if app.explorer_filter_mode else list(range(len(app.entries)))
    visible = indices[app.scroll:app.scroll + list_h]

    for i, abs_idx in enumerate(visible):
        y = 2 + offset + i
        name, is_dir, full = app.entries[abs_idx]
        label = ext_label(name)
        if is_dir:
            line = f"  [+]/ {name}"
            attr = destacar
        else:
            base = name.rsplit('.', 1)[0] if '.' in name else name
            line = f"  ♪ {base}  [{label}]"
            attr = texto
        max_w = w - EXPLORER_MARGIN
        if len(line) > max_w:
            line = line[:max_w - 1] + "…"
        cur = app.cursor
        is_cursor = (cur < len(indices) and abs_idx == indices[cur])
        if is_cursor:
            app.stdscr.addstr(y, 2, line, attr | curses.A_REVERSE)
        else:
            app.stdscr.addstr(y, 2, line, attr)
        if not is_dir:
            meta = app.meta_cache.get(full)
            dur = meta.get('length', 0) if meta else 0
            dur_str = time_str(dur) if dur > 0 else ""
            if dur_str:
                app.stdscr.addstr(y, w - len(dur_str) - 2, dur_str, texto)


def draw_playlist(app, h: int, w: int) -> None:
    extra = " [Filtro]" if app.playlist_filter_mode else ""
    draw_box(app.stdscr, h, w, f"Playlist [{app.active_name}] ({len(app.playlist)}){extra}")
    texto = curses.color_pair(PAIR_TEXTO)
    destacar = curses.color_pair(PAIR_DESTACAR)

    if app.playlist_filter_mode:
        app.stdscr.addstr(2, 2, f"> {app.playlist_filter}", destacar)

    if not app.playlist:
        app.stdscr.addstr(h // 2, 2, "Playlist vacía — agregá canciones desde el Explorador", texto)
        return

    list_h = h - LIST_H - (1 if app.playlist_filter_mode else 0)
    indices = app.playlist_filtered if app.playlist_filter_mode else list(range(len(app.playlist)))
    visible = indices[app.playlist_scroll:app.playlist_scroll + list_h]

    if app.playlist_filter_mode and not indices:
        app.stdscr.addstr(4, 2, "  Sin resultados", texto)
        return

    for row, abs_idx in enumerate(visible):
        y = (3 if app.playlist_filter_mode else 2) + row
        name, path = app.playlist[abs_idx]
        meta = app.meta_cache.get(path)
        display_name = f"{meta.get('artist', '?')} - {meta.get('title', name)}" if (meta and meta.get('title')) else name
        icon = "►" if abs_idx == app.playlist_idx and app.playing else "♪"
        tag = " [NEXT]" if any(p == path for p, _ in app.temp_queue) else ""
        line = f"  {icon} {display_name}{tag}"
        max_w = w - PLAYLIST_MARGIN
        if len(line) > max_w:
            line = line[:max_w - 1] + "…"
        attr = destacar if abs_idx == app.playlist_idx else texto
        cur = app.playlist_cursor
        is_cursor = (cur < len(indices) and abs_idx == indices[cur])
        if is_cursor:
            app.stdscr.addstr(y, 2, line, attr | curses.A_REVERSE)
        else:
            app.stdscr.addstr(y, 2, line, attr)
        dur = meta.get('length', 0) if meta else 0
        dur_str = time_str(dur) if dur > 0 else ""
        if dur_str:
            app.stdscr.addstr(y, w - len(dur_str) - 2, dur_str, attr)


def draw_now_playing(app, h: int, w: int) -> None:
    texto = curses.color_pair(PAIR_TEXTO)
    dest = curses.color_pair(PAIR_DESTACAR)

    if app.show_temp_queue:
        draw_box(app.stdscr, h, w, f"Lista ({len(app.temp_queue)})")
        if not app.temp_queue:
            app.stdscr.addstr(h // 2, 2, "  Lista vacía — usá N/A en Explorador para añadir", texto)
        else:
            list_h = h - 8
            visible = app.temp_queue[app.tq_scroll:app.tq_scroll + list_h]
            for row, item in enumerate(visible):
                y = 2 + row
                path, consumable = item
                meta = app.meta_cache.get(path)
                name = os.path.basename(path)
                display_name = f"{meta.get('artist', '?')} - {meta.get('title', name)}" if (meta and meta.get('title')) else name
                is_playing = (app.tq_playhead == app.tq_scroll + row) and app.audio.playing
                icon = "►" if is_playing else "♪"
                tag = " [N]" if consumable else ""
                line = f"  {icon} {display_name}{tag}"
                max_w = w - 8
                if len(line) > max_w:
                    line = line[:max_w - 1] + "…"
                idx = app.tq_scroll + row
                attr = dest if is_playing else texto
                if idx == app.tq_cursor:
                    app.stdscr.addstr(y, 2, line, attr | curses.A_REVERSE)
                else:
                    app.stdscr.addstr(y, 2, line, attr)
                dur = meta.get('length', 0) if meta else 0
                dur_str = time_str(dur) if dur > 0 else ""
                if dur_str:
                    app.stdscr.addstr(y, w - len(dur_str) - 2, dur_str, attr)
            safe_addstr(app.stdscr, h - 4, 2, "  [Enter]►  [Tab] Volver  [N] Next  [d]el  [x]clear", texto, h, w)
            safe_addstr(app.stdscr, h - 3, 2, "  [J/K]ordenar  [s]guardar  [g]Inicio  [G]Fin", texto, h, w)
        return

    draw_box(app.stdscr, h, w, "Now Playing")

    mid = max(2, (h - 2) // 2)
    if app.current_file and app.playing:
        meta = app.meta_cache.get(app.current_file)
        name = os.path.basename(app.current_file)
        estado = "► PLAY" if not app.paused else "⏸ PAUSE"
        artist = (meta.get('artist') if meta else None) or "Artista desconocido"
        album = (meta.get('album') if meta else None) or "Álbum desconocido"
        title = (meta.get('title') if meta else None) or name
        safe_addstr(app.stdscr, mid - 3, 2, f"  {estado}", dest, h, w)
        safe_addstr(app.stdscr, mid - 1, 2, f"  {title}", texto, h, w)
        safe_addstr(app.stdscr, mid, 2, f"  {artist}  —  {album}", texto, h, w)

        length = app.audio.get_length()
        pos = app.audio.get_time()

        if length > 0:
            progress = min(pos / length, 1.0)
            dur_str = f"{time_str(pos // 1000)} / {time_str(length // 1000)}"
            bar_w = max(10, w - 12)
            filled = int(bar_w * progress)
            bar = "█" * filled + "░" * (bar_w - filled)
            safe_addstr(app.stdscr, mid + 2, 2, f"  {bar} ", texto, h, w)
            safe_addstr(app.stdscr, mid + 3, 2, f"  {dur_str}", texto, h, w)
        else:
            safe_addstr(app.stdscr, mid + 3, 2, "  Duración: --:--", texto, h, w)

        toggles = ""
        toggles += " [S]" if app.shuffle else ""
        toggles += " [R]" if app.repeat else ""
        toggles += " [MUTE]" if app.audio.muted else ""
        info = f"  Vol: {app.volume}%{toggles}"
        safe_addstr(app.stdscr, mid + 5, 2, info, texto, h, w)

        timer_str = app.audio.sleep_timer_str()
        if timer_str:
            safe_addstr(app.stdscr, mid + 6, 2, f"  {timer_str}", texto, h, w)

        if app.goto_mode:
            gm = f"{app.goto_mins:02d}"
            gs = f"{app.goto_secs:02d}"
            am = texto | curses.A_REVERSE if app.goto_field == 0 else texto
            as_ = texto | curses.A_REVERSE if app.goto_field == 1 else texto
            safe_addstr(app.stdscr, mid + 8, 2, "  Ir a: [", texto, h, w)
            safe_addstr(app.stdscr, mid + 8, 11, gm, am, h, w)
            safe_addstr(app.stdscr, mid + 8, 13, ":", texto, h, w)
            safe_addstr(app.stdscr, mid + 8, 14, gs, as_, h, w)
            safe_addstr(app.stdscr, mid + 8, 16, "]", texto, h, w)
            safe_addstr(app.stdscr, mid + 9, 2, "  \u2190\u2192 campo  \u2191\u2193 valor  Enter saltar", texto, h, w)
    else:
        safe_addstr(app.stdscr, mid - 1, 2, "  Nada en reproducción", texto, h, w)
        safe_addstr(app.stdscr, mid + 1, 2, "  Explorá música en [1] y presioná Enter", texto, h, w)

    hint = "  [Space] ▶||  [s] ◼  [n] ►►  [p] ◄◄  [h/l] ±5s  [g] Ir a"
    if app.temp_queue:
        hint += "  [Tab] Lista"
    safe_addstr(app.stdscr, h - STATUS_ROW, 2, hint, texto, h, w)


def draw_config(app, h: int, w: int) -> None:
    draw_box(app.stdscr, h, w, "Configuración")
    texto = curses.color_pair(PAIR_TEXTO)
    destacar = curses.color_pair(PAIR_DESTACAR)

    labels = {
        "music_dir": f"Directorio música: {app.config.get('music_dir', '~/Music')}",
        "volume": f"Volumen: {app.volume}%",
        "theme": f"Tema: {app.config.get('theme', 'clasico')}",
        "sleep_timer_minutes": f"Sleep timer: {app.config.get('sleep_timer_minutes', 30)} min",
    }
    cc = app.config.get("custom_colors", {})

    for i, (key, label, ctype) in enumerate(app.config_items):
        y = 2 + i
        if ctype == "color":
            line = f"  {label}: {cc.get(key, 'Blanco')}"
        elif key == "keybindings":
            mode_label = "Default" if app.keybinding_mode == "default" else "Custom"
            line = f"  {label}  [{mode_label}]"
        elif key == "update":
            line = f"  {label}  [Comprobar]"
            if app.update_available:
                line += "  ⚡"
        else:
            line = f"  {labels.get(key, key)}"
        attr = texto
        if ctype in ("choice", "color", "int"):
            line += "  ← →"
        if i == app.config_cursor:
            app.stdscr.addstr(y, 2, line, destacar | curses.A_REVERSE)
        else:
            app.stdscr.addstr(y, 2, line, attr)


def draw_history(app, h: int, w: int) -> None:
    draw_box(app.stdscr, h, w, "Historial")
    texto = curses.color_pair(PAIR_TEXTO)
    destacar = curses.color_pair(PAIR_DESTACAR)
    if not app.history:
        app.stdscr.addstr(3, 2, "  Sin historial", texto)
        return
    list_h = h - 5
    start = max(0, min(app.history_scroll, len(app.history) - list_h))
    visible = app.history[start:start + list_h]
    for i, (name, path) in enumerate(visible):
        y = 3 + i
        idx = start + i
        base = name.rsplit('.', 1)[0] if '.' in name else name
        line = f"  {base}"
        attr = destacar if idx == app.history_cursor else texto
        if idx == app.history_cursor:
            app.stdscr.addstr(y, 2, line, attr | curses.A_REVERSE)
        else:
            app.stdscr.addstr(y, 2, line, attr)
        meta = app.meta_cache.get(path)
        dur = meta.get('length', 0) if meta else 0
        dur_str = time_str(dur) if dur > 0 else ""
        if dur_str:
            app.stdscr.addstr(y, w - len(dur_str) - 2, dur_str, texto)


def draw_keybindings(app, h: int, w: int) -> None:
    draw_box(app.stdscr, h, w, "Keybindings")
    texto = curses.color_pair(PAIR_TEXTO)
    destacar = curses.color_pair(PAIR_DESTACAR)

    is_custom = app.keybinding_mode == "custom"
    mode = "CUSTOM" if is_custom else "DEFAULT"
    app.stdscr.addstr(2, 2, f"  Modo: {mode}  ← → cambiar", destacar)

    if not is_custom:
        app.stdscr.addstr(4, 2, "  Cambiá a modo Custom para personalizar las teclas", texto)
        app.stdscr.addstr(h - 3, 2, "  [Esc] Volver", texto)
        return

    app.stdscr.addstr(3, 2, "  Enter para cambiar una tecla, Esc para volver", texto)

    actions = kb.BINDABLE_ACTIONS
    list_h = h - 7
    start = max(0, min(app.kb_cursor, len(actions) - list_h))
    visible = actions[start:start + list_h]

    for i, action in enumerate(visible):
        y = 5 + i
        idx = start + i
        keycode = _get_current_key(app, action)
        kname = kb.key_name(keycode)
        line = f"  {action:<15}  {kname}"
        if app.kb_capturing and app.kb_capturing_action == action:
            line += "  ⏎ esperando tecla..."
        attr = destacar if idx == app.kb_cursor else texto
        if idx == app.kb_cursor:
            app.stdscr.addstr(y, 2, line, attr | curses.A_REVERSE)
        else:
            app.stdscr.addstr(y, 2, line, attr)

    if app.kb_conflict_msg:
        app.stdscr.addstr(h - 3, 2, f"  {app.kb_conflict_msg}", texto)
    app.stdscr.addstr(h - 4, 2, "  [Esc] Volver", texto)
