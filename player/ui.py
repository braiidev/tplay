from __future__ import annotations

import os
import curses
from typing import Any, TypedDict

from .config import PAIR_MARCO, PAIR_TEXTO, PAIR_DESTACAR, PAIR_NAV, PAIR_OVERLAY

LIST_H = 4
STATUS_ROW = 3
NAV_ROW = 1
EXPLORER_MARGIN = 2
PLAYLIST_MARGIN = 2

HINT_FULL_W: int = 70
HINT_MID_W: int = 45
HINT_MIN_W: int = 25
NAV_FULL_W: int = 65
NAV_MID_W: int = 45
NAV_MIN_W: int = 25


def _build_hints(segments: list[tuple[str, str]], w: int, prefix: str = "  ") -> str:
    sep = "│"
    avail = w - 4
    if avail < 5:
        return ""

    # Tier 1: full — [key] label
    if w >= HINT_FULL_W:
        full = sep.join(f" [{k}] {v}" for k, v in segments)
        if len(prefix) + len(full) <= avail:
            return prefix + full

    # Tier 2: mid — [key]label
    if w >= HINT_MID_W:
        mid = sep.join(f" [{k}]{v}" for k, v in segments)
        if len(prefix) + len(mid) <= avail:
            return prefix + mid

    # Tier 3: min — key only
    if w >= HINT_MIN_W:
        keys_only = sep.join(k for k, _ in segments)
        if len(prefix) + len(keys_only) <= avail:
            return prefix + keys_only

    # Fallback: drop segments from right until it fits
    for n in range(len(segments), 0, -1):
        keys_part = sep.join(k for k, _ in segments[:n])
        candidate = prefix + keys_part
        if len(candidate) <= avail:
            if n < len(segments):
                candidate += "…"
            return candidate

    return ""


def _build_nav(w: int) -> str:
    full = " 0:Config │ 1:Listen │ 2:Expl │ 3:Playlist │ 4:Hist │ 5:Radio │ 6:Fav │ q:Salir "
    mid = " 0:Cfg│1:Lis│2:Exp│3:PL│4:His│5:Rad│6:Fav│q:Salir"
    mn = " 0│1│2│3│4│5│6│q"
    if w >= NAV_FULL_W:
        return full
    if w >= NAV_MID_W:
        return mid
    if w >= NAV_MIN_W:
        return mn
    return ""


def safe_addstr(win: curses.window, y: int, x: int, text: str, attr: int | None = None, h: int = 0, w: int = 0) -> None:
    if y < 0 or y >= h or x < 0 or x >= w:
        return
    try:
        if attr is not None:
            win.addstr(y, x, text[:w - x], attr)
        else:
            win.addstr(y, x, text[:w - x])
    except curses.error:
        pass


def draw_box(win: curses.window, h: int, w: int, title: str) -> None:
    marco = curses.color_pair(PAIR_MARCO)
    bot = max(0, h - 1) if h < 16 else max(0, h - 2)
    safe_addstr(win, 0, 0, "┌" + "─" * max(0, w - 2) + "┐", marco, h, w)
    if title:
        title_str = f" {title} "
        tx = max(2, (w - len(title_str)) // 2)
        max_tw = max(0, w - tx - 1)
        if len(title_str) > max_tw and max_tw >= 2:
            title_str = title_str[:max_tw - 1] + "…"
        elif len(title_str) > max_tw:
            title_str = title_str[:max_tw]
        safe_addstr(win, 0, tx, title_str, marco, h, w)
    for y in range(1, min(bot, h - 1)):
        safe_addstr(win, y, 0, "│", marco, h, w)
        safe_addstr(win, y, max(0, w - 1), "│", marco, h, w)
    if h > 1:
        safe_addstr(win, bot, 0, "└" + "─" * max(0, w - 2) + "┘", marco, h, w)


def draw_nav(win: curses.window, h: int, w: int) -> None:
    nav = curses.color_pair(PAIR_NAV)
    tabs = _build_nav(w)
    if not tabs:
        return
    win.move(h - NAV_ROW, 0)
    win.clrtoeol()
    safe_addstr(win, h - NAV_ROW, max(0, (w - len(tabs)) // 2), tabs, nav, h, w)


def draw_status(win: curses.window, h: int, w: int, audio: Any, playing: bool, current_file: str | None, volume: int,
                shuffle: bool, repeat: bool, active_name: str, current_view: int,
                stack: Any = None) -> None:
    if current_view == 1:  # V_LISTEN — status en su propio layout
        return
    status = curses.color_pair(PAIR_OVERLAY)
    if playing:
        name = os.path.basename(current_file) if current_file else ""
        estado = "►" if not audio.paused else "||"
        cur = audio.get_time()
        dur = audio.get_length()
        cur_s = f"{cur // 60000:02d}:{(cur // 1000) % 60:02d}" if cur >= 0 else "--:--"
        dur_s = f"{dur // 60000:02d}:{(dur // 1000) % 60:02d}" if dur > 0 else "--:--"
        max_name = max(5, w // 3)
        name_s = (name[:max_name - 1] + "…") if len(name) > max_name else name
        txt = f" {estado} {name_s}  [{cur_s} / {dur_s}] [Vol: {volume}%]"
        if shuffle:
            txt += " [S]"
        if repeat:
            txt += " [R]"
        if audio.muted:
            txt += " [M]"
        if audio.rate != 1.0:
            txt += f" [{audio.rate:.2f}x]"
        timer_str = audio.sleep_timer_str()
        if timer_str:
            txt += f" {timer_str}"
        safe_addstr(win, h - STATUS_ROW, 1, txt[:w - 3], status, h, w)
    elif audio.sleep_timer_active or audio.sleep_timer_expired:
        txt = audio.sleep_timer_str()
        safe_addstr(win, h - STATUS_ROW, 1, txt[:w - 3], status, h, w)




def draw_dialog(win: curses.window, h: int, w: int, title: str, text: str,
                is_confirm: bool = False, compact: bool = False,
                prompt_buf: str = "", prompt_scroll: int = 0,
                prompt_cursor_pos: int = -1,
                buttons: str = "") -> None:
    texto = curses.color_pair(PAIR_TEXTO)
    dest = curses.color_pair(PAIR_OVERLAY)

    DH = 5
    oy = max(1, (h - DH) // 2)

    if compact:
        box_w = w - 4
        ox = 2
        tl, bl, vb = "┌┐", "└┘", "│"
    else:
        box_w = min(60, w - 10)
        ox = max(1, (w - box_w) // 2)
        tl, bl, vb = "╔╗", "╚╝", "║"

    ih = box_w - 2  # inner width (between vertical bars)

    try:
        # Row 0: top border + title
        hz = "─" if compact else "═"
        safe_addstr(win, oy, ox, tl[0] + hz * ih + tl[1], dest, h, w)
        ttl = f" {title} "
        if len(ttl) > ih:
            ttl = ttl[:ih - 1] + "…"
        safe_addstr(win, oy, ox + 2, ttl, dest, h, w)

        def rline(body: str = "") -> None:
            s = body[:ih] if body else ""
            l = len(s)
            if l < ih:
                s += " " * (ih - l)
            safe_addstr(win, oy, ox, vb + s + vb, dest, h, w)

        # Row 1: empty
        oy += 1
        rline()

        # Row 2: content (message or input)
        oy += 1
        if is_confirm:
            content = f"  {text}  "
            pad_l = max(0, (ih - len(content)) // 2)
            rline(" " * pad_l + content)
        else:
            field_w = max(1, ih - len(text) - 6)
            if prompt_cursor_pos < 0:
                prompt_cursor_pos = len(prompt_buf)
            visible = prompt_buf[prompt_scroll:prompt_scroll + field_w]
            has_ellipsis = len(prompt_buf) > prompt_scroll + field_w
            if has_ellipsis:
                visible += "…"
            body = f"  {text}: {visible}"
            s = body[:ih]
            if len(s) < ih:
                s += " " * (ih - len(s))
            try:
                win.addstr(oy, ox, vb + s + vb, dest)
            except curses.error:
                pass
            cur_in_visible = max(0, min(prompt_cursor_pos - prompt_scroll, len(prompt_buf) - prompt_scroll))
            if has_ellipsis and cur_in_visible >= field_w:
                cur_in_visible = field_w - 1
            cx = len(f"  {text}: ") + cur_in_visible
            if cx < ih:
                try:
                    win.chgat(oy, ox + 1 + cx, 1, dest | curses.A_REVERSE)
                except curses.error:
                    pass
            curses.curs_set(0)

        # Row 3: buttons or empty
        oy += 1
        if is_confirm or buttons:
            btns = buttons if buttons else "  [S]í    [N]o  "
            pad_l = max(0, (ih - len(btns)) // 2)
            rline(" " * pad_l + btns)
        else:
            rline()

        # Row 4: bottom border
        oy += 1
        safe_addstr(win, oy, ox, bl[0] + hz * ih + bl[1], dest, h, w)

    except curses.error:
        pass


HelpLine = tuple[str, int | None]


class HelpTab(TypedDict):
    name: str
    lines: list[HelpLine]


HELP_TABS: list[HelpTab] = [
    {
        "name": "General",
        "lines": [
            ("", None),
            ("  GENERAL", PAIR_NAV),
            ("", None),
            ("    0-5       Cambiar vista", PAIR_TEXTO),
            ("    ? / F1    Abrir ayuda", PAIR_TEXTO),
            ("    q         Salir (guarda todo)", PAIR_TEXTO),
            ("    Esc       Cancelar / cerrar", PAIR_TEXTO),
            ("", None),
            ("  REPRODUCCIÓN", PAIR_NAV),
            ("", None),
            ("    Space     ▶ / || pausa", PAIR_TEXTO),
            ("    S         ◼ Detener (global)", PAIR_TEXTO),
            ("    n / b     ►► siguiente / ◄◄ anterior", PAIR_TEXTO),
            ("    + / -     Subir / bajar volumen", PAIR_TEXTO),
            ("", None),
            ("  EN AYUDA", PAIR_NAV),
            ("", None),
            ("    j / k     Desplazar vertical", PAIR_TEXTO),
            ("    h / l / [ / ]  Cambiar pestaña", PAIR_TEXTO),
            ("    Esc / ?   Cerrar ayuda", PAIR_TEXTO),
        ]
    },
    {
        "name": "Escucha",
        "lines": [
            ("", None),
            ("  REPRODUCCIÓN", PAIR_NAV),
            ("", None),
            ("    h / ←     Buscar -5s", PAIR_TEXTO),
            ("    l / →     Buscar +5s", PAIR_TEXTO),
            ("    s / S     ◼ Detener", PAIR_TEXTO),
            ("    I         Editar tags ID3", PAIR_TEXTO),
            ("", None),
            ("  VOLUMEN", PAIR_NAV),
            ("", None),
            ("    k         Subir volumen", PAIR_TEXTO),
            ("    j         Bajar volumen", PAIR_TEXTO),
            ("    m         Silenciar", PAIR_TEXTO),
            ("", None),
            ("  MODO", PAIR_NAV),
            ("", None),
            ("    r         Aleatorio ON/OFF", PAIR_TEXTO),
            ("    R         Repetir ON/OFF", PAIR_TEXTO),
            ("", None),
            ("  VELOCIDAD", PAIR_NAV),
            ("", None),
            ("    w         Aumentar velocidad (+0.25x)", PAIR_TEXTO),
            ("    W         Disminuir velocidad (-0.25x)", PAIR_TEXTO),
            ("", None),
            ("  FAVORITOS", PAIR_NAV),
            ("", None),
            ("    f         Añadir/quitar de favoritos", PAIR_TEXTO),
            ("", None),
            ("  TIEMPO", PAIR_NAV),
            ("", None),
            ("    g         Ir a tiempo", PAIR_TEXTO),
            ("    t         Activar temporizador", PAIR_TEXTO),
            ("    T         Configurar temporizador", PAIR_TEXTO),
            ("", None),
            ("  PILA", PAIR_NAV),
            ("", None),
            ("    Tab       Ver pila de reproducción", PAIR_TEXTO),
            ("", None),
            ("  IR A TIEMPO", PAIR_NAV),
            ("", None),
            ("    ↑ / ↓     Valor min/seg", PAIR_TEXTO),
            ("    ← / →     Campo min/seg", PAIR_TEXTO),
            ("    Enter     Saltar a tiempo", PAIR_TEXTO),
            ("    Esc       Cancelar", PAIR_TEXTO),
            ("", None),
            ("  PILA (vista)", PAIR_NAV),
            ("", None),
            ("    j / k     Cursor abajo / arriba", PAIR_TEXTO),
            ("    Enter     Reproducir elemento", PAIR_TEXTO),
            ("    d / x     Eliminar / limpiar (confirma)", PAIR_TEXTO),
            ("    J / K     Reordenar elemento", PAIR_TEXTO),
            ("    s         Guardar pila como lista", PAIR_TEXTO),
            ("    r / R     Modo elemento (normal/1x/∞)", PAIR_TEXTO),
            ("    f         Añadir/quitar de favoritos", PAIR_TEXTO),
            ("    X         Exportar como M3U", PAIR_TEXTO),
            ("    u / U     Deshacer / Rehacer", PAIR_TEXTO),
            ("    Tab/Esc   Volver", PAIR_TEXTO),
        ]
    },
    {
        "name": "Explorador",
        "lines": [
            ("", None),
            ("  ARCHIVOS", PAIR_NAV),
            ("", None),
            ("    Enter     Abrir dir / reproducir", PAIR_TEXTO),
            ("    Tab       Marcar/desmarcar archivo", PAIR_TEXTO),
            ("    a / A     Añadir a pila (final/tras)", PAIR_TEXTO),
            ("    f         Añadir/quitar de favoritos", PAIR_TEXTO),
            ("    F         Abrir vista Favoritos", PAIR_TEXTO),
            ("    ~         Ir al inicio", PAIR_TEXTO),
            ("    g / G     Ir al inicio / fin", PAIR_TEXTO),
            ("    ← / →     Subir / entrar directorio", PAIR_TEXTO),
            ("    F5        Refrescar vista", PAIR_TEXTO),
            ("    P         Reproducir directorio", PAIR_TEXTO),
            ("    /         Filtrar archivos", PAIR_TEXTO),
            ("", None),
            ("  OPERACIONES", PAIR_NAV),
            ("", None),
            ("    C / V     Copiar / Mover archivo", PAIR_TEXTO),
            ("    E         Renombrar archivo", PAIR_TEXTO),
            ("    I         Editar tags ID3", PAIR_TEXTO),
            ("    d         Eliminar archivo (confirma)", PAIR_TEXTO),
            ("    M         Crear directorio", PAIR_TEXTO),
            ("    u / U     Deshacer / Rehacer", PAIR_TEXTO),
            ("", None),
            ("  COPIAR / MOVER", PAIR_NAV),
            ("", None),
            ("    Enter/C/V  Pegar en directorio", PAIR_TEXTO),
            ("    u          Deshacer última op", PAIR_TEXTO),
            ("    Esc        Cancelar", PAIR_TEXTO),
            ("", None),
            ("  METADATOS", PAIR_NAV),
            ("", None),
            ("    ↑ / ↓     Navegar campos", PAIR_TEXTO),
            ("    Enter     Editar campo", PAIR_TEXTO),
            ("    ← / →     Mover cursor en campo", PAIR_TEXTO),
            ("    s         Guardar cambios", PAIR_TEXTO),
            ("    Esc       Cancelar", PAIR_TEXTO),
            ("", None),
            ("  FILTRO (/)", PAIR_NAV),
            ("", None),
            ("    ← / →     Mover cursor", PAIR_TEXTO),
            ("    ↑ / ↓     Navegar resultados", PAIR_TEXTO),
            ("    Enter     Seleccionar", PAIR_TEXTO),
            ("    Esc       Cancelar filtro", PAIR_TEXTO),
        ]
    },
    {
        "name": "Lista",
        "lines": [
            ("", None),
            ("  LISTA DE REPRODUCCIÓN", PAIR_NAV),
            ("", None),
            ("    c         Crear nueva lista", PAIR_TEXTO),
            ("    D         Eliminar lista", PAIR_TEXTO),
            ("    R         Renombrar lista", PAIR_TEXTO),
            ("    [ / ]     Lista ant / sig", PAIR_TEXTO),
            ("    s         Guardar lista", PAIR_TEXTO),
            ("    X         Exportar como M3U", PAIR_TEXTO),
            ("", None),
            ("  ELEMENTOS", PAIR_NAV),
            ("", None),
            ("    Enter     Reproducir elemento", PAIR_TEXTO),
            ("    d         Quitar elemento", PAIR_TEXTO),
            ("    x         Limpiar lista", PAIR_TEXTO),
            ("    E         Renombrar elemento", PAIR_TEXTO),
            ("    J / K     Reordenar elementos", PAIR_TEXTO),
            ("    f         Añadir/quitar de favoritos", PAIR_TEXTO),
            ("    /         Filtrar elementos", PAIR_TEXTO),
            ("", None),
            ("  FILTRO (/)", PAIR_NAV),
            ("", None),
            ("    ← / →     Mover cursor", PAIR_TEXTO),
            ("    ↑ / ↓     Navegar resultados", PAIR_TEXTO),
            ("    Enter     Seleccionar", PAIR_TEXTO),
            ("    Esc       Cancelar filtro", PAIR_TEXTO),
        ]
    },
    {
        "name": "Historial",
        "lines": [
            ("", None),
            ("  HISTORIAL", PAIR_NAV),
            ("", None),
            ("    Enter     Reproducir archivo / radio", PAIR_TEXTO),
            ("    d         Eliminar entrada", PAIR_TEXTO),
            ("    x         Limpiar todo", PAIR_TEXTO),
            ("    a / A     Añadir a pila (final/tras)", PAIR_TEXTO),
            ("    I         Editar tags ID3", PAIR_TEXTO),
            ("    f         Añadir/quitar de favoritos", PAIR_TEXTO),
            ("    Esc       Volver a Escucha", PAIR_TEXTO),
        ]
    },
    {
        "name": "Config",
        "lines": [
            ("", None),
            ("  CONFIGURACIÓN", PAIR_NAV),
            ("", None),
            ("    j / k     Cursor abajo / arriba", PAIR_TEXTO),
            ("    [ / ]     Pestaña anterior / siguiente", PAIR_TEXTO),
            ("    → / Enter Activar / cambiar valor", PAIR_TEXTO),
            ("    ← / h/l   Cambiar valor", PAIR_TEXTO),
            ("", None),
            ("  TECLAS", PAIR_NAV),
            ("", None),
            ("    ← / →     Cambiar default / custom", PAIR_TEXTO),
            ("    Enter     Asignar tecla", PAIR_TEXTO),
            ("    ↑ / ↓     Navegar acciones", PAIR_TEXTO),
            ("    Esc       Volver", PAIR_TEXTO),
            ("", None),
            ("  DIRECTORIO", PAIR_NAV),
            ("", None),
            ("    j / k     Cursor abajo / arriba", PAIR_TEXTO),
            ("    h / ←     Directorio padre", PAIR_TEXTO),
            ("    l / →     Entrar directorio", PAIR_TEXTO),
            ("    Enter     Seleccionar directorio", PAIR_TEXTO),
            ("    ~         Ir a home", PAIR_TEXTO),
            ("    g / G     Inicio / Fin", PAIR_TEXTO),
            ("    Esc       Cancelar", PAIR_TEXTO),
        ]
    },
    {
        "name": "Radio",
        "lines": [
            ("", None),
            ("  RADIOS", PAIR_NAV),
            ("", None),
            ("    Enter     Reproducir radio", PAIR_TEXTO),
            ("    a         Agregar radio", PAIR_TEXTO),
            ("    d         Eliminar radio", PAIR_TEXTO),
            ("    E         Editar nombre → URL", PAIR_TEXTO),
            ("    f         Añadir/quitar de favoritos", PAIR_TEXTO),
            ("    s         Guardar radios", PAIR_TEXTO),
            ("    X         Exportar M3U", PAIR_TEXTO),
        ]
    },
    {
        "name": "Favoritos",
        "lines": [
            ("", None),
            ("  FAVORITOS", PAIR_NAV),
            ("", None),
            ("    Enter     Reproducir", PAIR_TEXTO),
            ("    d         Eliminar de favoritos", PAIR_TEXTO),
            ("    f         Añadir/quitar de favoritos", PAIR_TEXTO),
            ("    a / A     Añadir a pila (final/tras)", PAIR_TEXTO),
            ("    g / G     Inicio / Fin", PAIR_TEXTO),
            ("", None),
            ("  DESDE CUALQUIER VISTA", PAIR_NAV),
            ("", None),
            ("    f         Añadir/quitar archivo actual", PAIR_TEXTO),
            ("    F         Abrir vista Favoritos (Expl)", PAIR_TEXTO),
        ]
    },
]

VIEW_TO_HELP_TAB: dict[int, int] = {1: 1, 2: 2, 3: 3, 4: 4, 0: 5, 5: 6, 6: 7}


def draw_help(win: curses.window, h: int, w: int, scroll: int = 0, tab: int = 0) -> None:
    marco = curses.color_pair(PAIR_MARCO)
    texto = curses.color_pair(PAIR_TEXTO)
    dest = curses.color_pair(PAIR_DESTACAR)
    nav = curses.color_pair(PAIR_NAV)
    overlay = curses.color_pair(PAIR_OVERLAY)

    box_w = min(56, w - 4)
    ox = max(1, (w - box_w) // 2)
    tab_data = HELP_TABS[tab]
    lines = tab_data["lines"]
    total = len(lines)
    compact = h < 12

    if compact:
        list_h = max(2, h - 2)  # rows 1 to h-2 (no tab bar)
    else:
        list_h = max(2, h - 3)  # rows 1 to h-3 (tab bar at row 0, footer at h-2)

    max_scroll = max(0, total - list_h)
    scroll = max(0, min(scroll, max_scroll))
    visible = lines[scroll:scroll + list_h]

    try:
        # Top border
        safe_addstr(win, 0, ox, "┌" + "─" * (box_w - 2) + "┐", marco, h, w)
        max_tw = box_w - 4

        # Fill interior to hide underlying content
        for y in range(1, h - 1):
            safe_addstr(win, y, ox + 1, " " * (box_w - 2), texto, h, w)

        if compact:
            # Tab name as title in top border
            title = f" {tab_data['name']} "
            if len(title) <= box_w - 4:
                tx = 2 + (box_w - 2 - len(title)) // 2
                safe_addstr(win, 0, ox + tx, title, dest, h, w)

            # Vertical bars
            for y in range(1, h - 1):
                safe_addstr(win, y, ox, "│", marco, h, w)
                safe_addstr(win, y, ox + box_w - 1, "│", marco, h, w)

            # Content
            for i, (text, attr) in enumerate(visible):
                y = 1 + i
                if attr is not None:
                    safe_addstr(win, y, ox + 2, text[:max_tw], curses.color_pair(attr), h, w)

            # Scroll indicators at right edge
            if scroll > 0:
                safe_addstr(win, 1, ox + box_w - 2, "▲", nav, h, w)
            if scroll + list_h < total:
                safe_addstr(win, h - 2, ox + box_w - 2, "▼", nav, h, w)
        else:
            # Tab bar carousel at row 0 (replaces top border)
            tab_names = [t["name"] for t in HELP_TABS]
            n = len(tab_names)
            prev_idx = (tab - 1) % n
            next_idx = (tab + 1) % n
            prev_name = tab_names[prev_idx]
            curr_name = tab_names[tab]
            next_name = tab_names[next_idx]
            inner_w = box_w - 2
            sep = " │ "
            carousel_parts = [
                (prev_name, nav),
                (curr_name, overlay | curses.A_REVERSE),
                (next_name, nav),
            ]
            parts_w = sum(len(name) for name, _ in carousel_parts) + len(sep) * 2
            start_x = ox + 1 + max(0, (inner_w - parts_w) // 2)
            # Draw left vertical bar + fill
            left_fill = start_x - (ox + 1)
            safe_addstr(win, 0, ox, "│", marco, h, w)
            if left_fill > 0:
                safe_addstr(win, 0, ox + 1, "─" * left_fill, marco, h, w)
            # Draw carousel
            x = start_x
            for i, (name, attr) in enumerate(carousel_parts):
                if i > 0:
                    safe_addstr(win, 0, x, sep, nav, h, w)
                    x += len(sep)
                safe_addstr(win, 0, x, name, attr, h, w)
                x += len(name)
            # Fill right + right vertical bar
            right_start = ox + 1 + inner_w
            if x < right_start:
                safe_addstr(win, 0, x, "─" * (right_start - x), marco, h, w)
            safe_addstr(win, 0, ox + box_w - 1, "│", marco, h, w)

            # Vertical bars (content starts at row 1)
            for y in range(1, h - 1):
                safe_addstr(win, y, ox, "│", marco, h, w)
                safe_addstr(win, y, ox + box_w - 1, "│", marco, h, w)

            # Content (row 1 to h-2)
            for i, (text, attr) in enumerate(visible):
                y = 1 + i
                if attr is not None:
                    clipped = text[:max_tw] if len(text) <= max_tw else text[:max_tw - 1] + "…"
                    safe_addstr(win, y, ox + 2, clipped, curses.color_pair(attr), h, w)

            # Scroll indicators at right edge
            if scroll > 0:
                safe_addstr(win, 1, ox + box_w - 2, "▲", nav, h, w)
            if scroll + list_h < total:
                safe_addstr(win, h - 2, ox + box_w - 2, "▼", nav, h, w)
            # Footer hints
            hint = "  h/l: pestañas  j/k: scroll"
            safe_addstr(win, h - 2, ox + 2, hint[:inner_w - 2], nav, h, w)

        # Bottom border
        safe_addstr(win, h - 1, ox, "└" + "─" * (box_w - 2) + "┘", marco, h, w)

    except curses.error:
        pass
