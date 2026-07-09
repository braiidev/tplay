import os
import curses

from .config import PAIR_MARCO, PAIR_TEXTO, PAIR_DESTACAR, PAIR_NAV

LIST_H = 4
FILTER_LIST_H = 5
STATUS_ROW = 3
NAV_ROW = 1
EXPLORER_MARGIN = 8
PLAYLIST_MARGIN = 6


def safe_addstr(win, y: int, x: int, text: str, attr=None, h: int = 0, w: int = 0) -> None:
    if y < 0 or y >= h or x < 0 or x >= w:
        return
    try:
        if attr is not None:
            win.addstr(y, x, text[:w - x], attr)
        else:
            win.addstr(y, x, text[:w - x])
    except curses.error:
        pass


def draw_box(win, h: int, w: int, title: str) -> None:
    marco = curses.color_pair(PAIR_MARCO)
    top = min(w - 2, 2)
    bot = max(0, h - 1) if h < 16 else max(0, h - 2)
    try:
        win.addstr(0, 0, "┌" + "─" * max(0, w - 2) + "┐", marco)
        if title:
            title_str = f" {title} "
            tx = max(2, (w - len(title_str)) // 2)
            max_tw = max(0, w - tx - 1)
            if len(title_str) > max_tw and max_tw >= 2:
                title_str = title_str[:max_tw - 1] + "…"
            elif len(title_str) > max_tw:
                title_str = title_str[:max_tw]
            win.addstr(0, tx, title_str, marco)
        for y in range(1, min(bot, h - 1)):
            win.addstr(y, 0, "│", marco)
            win.addstr(y, max(0, w - 1), "│", marco)
        if h > 1:
            win.addstr(bot, 0, "└" + "─" * max(0, w - 2) + "┘", marco)
    except curses.error:
        pass


def draw_nav(win, h: int, w: int) -> None:
    nav = curses.color_pair(PAIR_NAV)
    tabs = " 0:Config │ 1:Listen │ 2:Expl │ 3:Playlist │ 4:Hist │ q:Salir "
    win.move(h - NAV_ROW, 0)
    win.clrtoeol()
    win.addstr(h - NAV_ROW, max(0, (w - len(tabs)) // 2), tabs, nav)


def draw_status(win, h: int, w: int, audio, playing: bool, current_file, volume: int,
                shuffle: bool, repeat: bool, active_name: str, current_view: int,
                stack=None) -> None:
    if current_view in (1, 5, 6):
        return
    status = curses.color_pair(PAIR_DESTACAR)
    if playing:
        name = os.path.basename(current_file) if current_file else ""
        estado = "►" if not audio.paused else "||"
        cur = audio.get_time()
        dur = audio.get_length()
        cur_s = f"{cur // 60000:02d}:{(cur // 1000) % 60:02d}" if cur >= 0 else "--:--"
        dur_s = f"{dur // 60000:02d}:{(dur // 1000) % 60:02d}" if dur > 0 else "--:--"
        max_name = max(5, w // 3)
        name_s = (name[:max_name - 1] + "…") if len(name) > max_name else name
        txt = f" {estado} {name_s}  [{cur_s}-{dur_s}] [Vol: {volume}%]"
        if shuffle:
            txt += " [S]"
        if repeat:
            txt += " [R]"
        if audio.muted:
            txt += " [MUTE]"
        timer_str = audio.sleep_timer_str()
        if timer_str:
            txt += f" {timer_str}"
        safe_addstr(win, h - STATUS_ROW, 1, txt[:w - 3], status, h, w)
    elif audio.sleep_timer_active or audio.sleep_timer_expired:
        txt = audio.sleep_timer_str()
        safe_addstr(win, h - STATUS_ROW, 1, txt[:w - 3], status, h, w)


def draw_prompt(win, h: int, w: int, label: str, buf: str) -> None:
    texto = curses.color_pair(PAIR_TEXTO)
    dest = curses.color_pair(PAIR_DESTACAR)
    prompt = f" {label}: {buf} "
    max_pw = max(10, w - 8)
    if len(prompt) > max_pw:
        prompt = prompt[:max_pw - 1] + "…"
    tw = len(prompt) + 4
    ox = max(2, (w - tw) // 2)
    oy = max(1, h // 2 - 1)
    try:
        win.addstr(oy, ox, "╔" + "═" * (tw - 2) + "╗", dest)
        win.addstr(oy + 1, ox, "║" + " " * (tw - 2) + "║", dest)
        win.addstr(oy + 1, ox + 2, prompt, texto)
        win.addstr(oy + 2, ox, "╚" + "═" * (tw - 2) + "╝", dest)
        cx = ox + 2 + len(f" {label}: ") + len(buf)
        win.move(oy + 1, min(cx, w - 2))
    except curses.error:
        pass


def draw_dialog(win, h: int, w: int, title: str, text: str,
                is_confirm: bool = False, compact: bool = False,
                prompt_buf: str = "", prompt_scroll: int = 0) -> None:
    texto = curses.color_pair(PAIR_TEXTO)
    dest = curses.color_pair(PAIR_DESTACAR)

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
        win.addstr(oy, ox, tl[0] + hz * ih + tl[1], dest)
        ttl = f" {title} "
        if len(ttl) > ih:
            ttl = ttl[:ih - 1] + "…"
        win.addstr(oy, ox + 2, ttl, dest)

        def rline(body: str = "") -> None:
            s = body[:ih] if body else ""
            l = len(s)
            if l < ih:
                s += " " * (ih - l)
            win.addstr(oy, ox, vb + s + vb, dest)

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
            visible = prompt_buf[prompt_scroll:prompt_scroll + field_w]
            if len(prompt_buf) > prompt_scroll + field_w:
                visible += "…"
            rline(f"  {text}: {visible}")
            vlen = len(visible)
            if visible.endswith("…"):
                vlen -= 1
            cx = ox + 1 + len(f"  {text}: ") + vlen
            win.move(oy, min(cx, w - 2))
            curses.curs_set(1)

        # Row 3: buttons or empty
        oy += 1
        if is_confirm:
            btns = "  [S]í    [N]o  "
            pad_l = max(0, (ih - len(btns)) // 2)
            rline(" " * pad_l + btns)
        else:
            rline()

        # Row 4: bottom border
        oy += 1
        win.addstr(oy, ox, bl[0] + hz * ih + bl[1], dest)

    except curses.error:
        pass


HELP_TABS = [
    {
        "name": "General",
        "lines": [
            ("", None),
            ("  GENERAL", 3),
            ("", None),
            ("    0-4       Cambiar vista", 2),
            ("    ? / F1    Abrir ayuda", 2),
            ("    /         Filtrar lista", 2),
            ("    q         Salir (guarda todo)", 2),
            ("    Esc       Cancelar / cerrar", 2),
            ("", None),
            ("  NAVEGACION", 3),
            ("", None),
            ("    j / ↓     Abajo", 2),
            ("    k / ↑     Arriba", 2),
            ("    h / ←     Retroceder / subir", 2),
            ("    l / →     Avanzar / bajar", 2),
            ("    Enter     Reproducir / abrir", 2),
            ("    g / G     Inicio / Fin lista", 2),
            ("    ~         Ir al home", 2),
            ("", None),
            ("  EN AYUDA", 3),
            ("", None),
            ("    j / k     Scroll vertical", 2),
            ("    h / l     Cambiar pestaña", 2),
            ("    Esc / ?   Cerrar ayuda", 2),
        ]
    },
    {
        "name": "Listen",
        "lines": [
            ("", None),
            ("  REPRODUCCION", 3),
            ("", None),
            ("    Space     ▶ / || pausa", 2),
            ("    s         ◼ Stop", 2),
            ("    n / b     ►► siguiente / ◄◄ anterior", 2),
            ("    h / l     Seek -5s / +5s", 2),
            ("", None),
            ("  VOLUMEN", 3),
            ("", None),
            ("    + / -     Subir / bajar volumen", 2),
            ("    m         Mute", 2),
            ("", None),
            ("  MODO", 3),
            ("", None),
            ("    r / R     Shuffle / Repeat global", 2),
            ("", None),
            ("  TIEMPO", 3),
            ("", None),
            ("    g         Ir a tiempo (Goto)", 2),
            ("    t / T     Sleep timer toggle / configurar", 2),
            ("", None),
            ("  STACK / URL", 3),
            ("", None),
            ("    Tab       Ver stack de reproducción", 2),
            ("    o         Agregar URL de stream", 2),
            ("", None),
            ("  GOTO (ir a tiempo)", 3),
            ("", None),
            ("    ↑ / ↓     Valor min/seg", 2),
            ("    ← / →     Campo min/seg", 2),
            ("    Enter     Saltar a tiempo", 2),
            ("    Esc       Cancelar", 2),
            ("", None),
            ("  STACK (vista)", 3),
            ("", None),
            ("    Enter     Mover playhead al item", 2),
            ("    d / x     Eliminar item / limpiar", 2),
            ("    J / K     Reordenar item", 2),
            ("    s         Guardar stack como playlist", 2),
            ("    r / R     Modo item (normal/1x/∞)", 2),
            ("    Tab/Esc   Volver", 2),
        ]
    },
    {
        "name": "Explorer",
        "lines": [
            ("", None),
            ("  ARCHIVOS", 3),
            ("", None),
            ("    Enter     Abrir dir / reproducir", 2),
            ("    a / A     Añadir a stack (final/tras)", 2),
            ("    ~         Ir al home", 2),
            ("    g / G     Ir al inicio / fin", 2),
            ("    ← / →     Subir / entrar directorio", 2),
            ("    R         Refrescar vista", 2),
            ("    /         Filtrar archivos", 2),
            ("", None),
            ("  OPERACIONES", 3),
            ("", None),
            ("    C / V     Copiar / Mover archivo", 2),
            ("    E         Renombrar archivo", 2),
            ("    I         Editar tags ID3", 2),
            ("    d         Eliminar archivo (confirma)", 2),
            ("    M         Crear directorio", 2),
            ("    u         Undo file op", 2),
            ("", None),
            ("  COPIAR/MOVER", 3),
            ("", None),
            ("    Enter/C/V  Pegar en directorio", 2),
            ("    u          Undo última op", 2),
            ("    Esc        Cancelar", 2),
            ("", None),
            ("  METADATA", 3),
            ("", None),
            ("    ↑ / ↓     Navegar campos", 2),
            ("    Enter     Editar campo", 2),
            ("    s         Guardar cambios", 2),
            ("    q / Esc   Cancelar", 2),
        ]
    },
    {
        "name": "Playlist",
        "lines": [
            ("", None),
            ("  PLAYLIST", 3),
            ("", None),
            ("    c         Crear nueva playlist", 2),
            ("    D         Eliminar playlist", 2),
            ("    e         Renombrar playlist", 2),
            ("    [ / ]     Playlist ant / sig", 2),
            ("    s         Guardar playlist", 2),
            ("", None),
            ("  ITEMS", 3),
            ("", None),
            ("    Enter     Reproducir item", 2),
            ("    d         Quitar item", 2),
            ("    x         Limpiar playlist", 2),
            ("    a / A     Añadir a stack (final/tras)", 2),
            ("    J / K     Reordenar items", 2),
            ("    /         Filtrar items", 2),
        ]
    },
    {
        "name": "History",
        "lines": [
            ("", None),
            ("  HISTORIAL", 3),
            ("", None),
            ("    Enter     Reproducir archivo", 2),
            ("    d         Eliminar entrada", 2),
            ("    x         Limpiar todo", 2),
            ("    a / A     Añadir a stack (final/tras)", 2),
        ]
    },
    {
        "name": "Config",
        "lines": [
            ("", None),
            ("  CONFIGURACION", 3),
            ("", None),
            ("    [ / ]     Cambiar pestaña", 2),
            ("    ← / →     Cambiar valor", 2),
            ("    Enter     Activar item", 2),
            ("", None),
            ("  KEYBINDINGS", 3),
            ("", None),
            ("    ← / →     Cambiar default/custom", 2),
            ("    Enter     Asignar tecla", 2),
            ("    ↑ / ↓     Navegar acciones", 2),
            ("    Esc       Volver", 2),
        ]
    },
]

VIEW_TO_HELP_TAB = {1: 1, 2: 2, 3: 3, 4: 4, 0: 5}


def draw_help(win, h: int, w: int, scroll: int = 0, tab: int = 0) -> None:
    marco = curses.color_pair(PAIR_MARCO)
    texto = curses.color_pair(PAIR_TEXTO)
    dest = curses.color_pair(PAIR_DESTACAR)
    nav = curses.color_pair(PAIR_NAV)

    box_w = min(56, w - 4)
    ox = max(1, (w - box_w) // 2)
    tab_data = HELP_TABS[tab]
    lines = tab_data["lines"]
    total = len(lines)
    compact = h < 12

    if compact:
        list_h = max(2, h - 2)  # rows 1 to h-2 (no tab bar)
    else:
        list_h = max(2, h - 4)  # rows 2 to h-3 (tab bar at 1, footer at h-2)

    max_scroll = max(0, total - list_h)
    scroll = max(0, min(scroll, max_scroll))
    visible = lines[scroll:scroll + list_h]

    try:
        # Top border
        win.addstr(0, ox, "┌" + "─" * (box_w - 2) + "┐", marco)
        max_tw = box_w - 4

        if compact:
            # Tab name as title in top border
            title = f" {tab_data['name']} "
            if len(title) <= box_w - 4:
                tx = 2 + (box_w - 2 - len(title)) // 2
                win.addstr(0, ox + tx, title, dest)

            # Vertical bars
            for y in range(1, h - 1):
                win.addstr(y, ox, "│", marco)
                win.addstr(y, ox + box_w - 1, "│", marco)

            # Content with scroll indicator on last line
            for i, (text, attr) in enumerate(visible):
                y = 1 + i
                if attr is not None:
                    display = text[:max_tw]
                    if i == list_h - 1 and scroll + list_h < total:
                        ind = "▼"
                        if scroll > 0:
                            ind = "▲▼"
                        display = display[:max_tw - len(ind)] + ind
                    win.addstr(y, ox + 2, display, curses.color_pair(attr))
        else:
            # Tab bar at row 1
            tab_names = [t["name"] for t in HELP_TABS]
            x = ox + 1
            ti = 0
            while ti < len(tab_names) and x < ox + box_w - 2:
                name = tab_names[ti]
                remaining = ox + box_w - 2 - x
                attr = dest | curses.A_REVERSE if ti == tab else texto
                if len(name) > remaining:
                    name = name[:max(1, remaining - 1)] + "…"
                win.addstr(1, x, name, attr)
                x += len(name)
                ti += 1
                if ti < len(tab_names) and x + 1 < ox + box_w - 2:
                    win.addstr(1, x, "│", nav)
                    x += 1

            if x < ox + box_w - 1:
                win.addstr(1, x, "─" * (ox + box_w - 1 - x), marco)

            # Vertical bars
            for y in range(2, h - 1):
                win.addstr(y, ox, "│", marco)
                win.addstr(y, ox + box_w - 1, "│", marco)

            # Content
            for i, (text, attr) in enumerate(visible):
                y = 2 + i
                if attr is not None:
                    clipped = text[:max_tw] if len(text) <= max_tw else text[:max_tw - 1] + "…"
                    win.addstr(y, ox + 2, clipped, curses.color_pair(attr))

            # Footer (scroll indicators)
            footer = ""
            if scroll > 0:
                footer += "▲ "
            if scroll + list_h < total:
                footer += "▼"
            if footer:
                win.addstr(h - 2, ox + 2, footer, texto)

        # Bottom border
        win.addstr(h - 1, ox, "└" + "─" * (box_w - 2) + "┘", marco)

    except curses.error:
        pass
