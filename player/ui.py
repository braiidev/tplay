import os
import curses

from .config import PAIR_MARCO, PAIR_TEXTO, PAIR_DESTACAR, PAIR_NAV

LIST_H = 5
SEARCH_LIST_H = 7
FILTER_LIST_H = 6
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
    bot = max(0, h - 2)
    try:
        win.addstr(0, 0, "┌" + "─" * max(0, w - 2) + "┐", marco)
        if title:
            title_str = f" {title} "
            tx = max(2, (w - len(title_str)) // 2)
            win.addstr(0, tx, title_str[:max(0, w - tx - 1)], marco)
        for y in range(1, min(bot, h - 1)):
            win.addstr(y, 0, "│", marco)
            win.addstr(y, max(0, w - 1), "│", marco)
        if h > 1:
            win.addstr(bot, 0, "└" + "─" * max(0, w - 2) + "┘", marco)
    except curses.error:
        pass


def draw_nav(win, h: int, w: int) -> None:
    nav = curses.color_pair(PAIR_NAV)
    tabs = " 0:Config │ 1:Expl │ 2:Playlist │ 3:Playing │ H:Hist │ q:Salir "
    win.move(h - NAV_ROW, 0)
    win.clrtoeol()
    win.addstr(h - NAV_ROW, max(0, (w - len(tabs)) // 2), tabs, nav)


def draw_status(win, h: int, w: int, audio, playing: bool, current_file, volume: int,
                shuffle: bool, repeat: bool, active_name: str, current_view: int,
                temp_queue: list = None) -> None:
    if current_view in (3, 5, 6):
        return
    status = curses.color_pair(PAIR_DESTACAR)
    if playing:
        name = os.path.basename(current_file) if current_file else ""
        estado = "►" if not audio.paused else "⏸"
        cur = audio.get_time()
        dur = audio.get_length()
        cur_s = f"{cur // 60000:02d}:{(cur // 1000) % 60:02d}" if cur >= 0 else "--:--"
        dur_s = f"{dur // 60000:02d}:{(dur // 1000) % 60:02d}" if dur > 0 else "--:--"
        txt = f" {estado} {name[:w//3]}  [{cur_s}-{dur_s}] [Vol: {volume}%]"
        if shuffle:
            txt += " [S]"
        if repeat:
            txt += " [R]"
        if audio.muted:
            txt += " [MUTE]"
        if temp_queue:
            n = sum(1 for _, c in temp_queue if c)
            if n:
                txt += f" [▶NEXT×{n}]"
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
    tw = len(prompt) + 4
    ox = max(2, (w - tw) // 2)
    oy = max(1, h // 2 - 1)
    try:
        win.addstr(oy, ox, "╭" + "─" * (tw - 2) + "╮", dest)
        win.addstr(oy + 1, ox, "│" + " " * (tw - 2) + "│", dest)
        win.addstr(oy + 1, ox + 2, prompt[:tw - 4], texto)
        win.addstr(oy + 2, ox, "╰" + "─" * (tw - 2) + "╯", dest)
        cx = ox + 2 + len(f" {label}: ") + len(buf)
        win.move(oy + 1, min(cx, w - 2))
    except curses.error:
        pass


def draw_help(win, h: int, w: int) -> None:
    marco = curses.color_pair(PAIR_MARCO)
    texto = curses.color_pair(PAIR_TEXTO)
    nav = curses.color_pair(PAIR_NAV)
    dest = curses.color_pair(PAIR_DESTACAR)
    lines = [
        ("", None),
        ("  A Y U D A   D E   T E C L A S", dest),
        ("", None),
        ("  Navegacion", nav),
        ("    ^ v / j k    Desplazarse", texto),
        ("    < > / h l    Retroceder / Avanzar", texto),
        ("    Enter        Reproducir / entrar carpeta", texto),
        ("    ~            Ir al home", texto),
        ("", None),
        ("  Reproduccion", nav),
        ("    Space        ▶ / ⏸", texto),
        ("    s            ◼ Stop", texto),
        ("    n / p        ►► / ◄◄", texto),
        ("    h / l        Seek -5s / +5s", texto),
        ("    + / -        Subir / Bajar volumen", texto),
        ("    m            Mute", texto),
        ("    r / R        Shuffle / Repeat", texto),
        ("    g            Ir a tiempo (en Now Playing)", texto),
        ("", None),
        ("  Playlist", nav),
        ("    a            Anadir a playlist", texto),
        ("    d            Quitar de playlist", texto),
        ("    x            Limpiar playlist", texto),
        ("    J / K        Reordenar (mover abajo/arriba)", texto),
        ("    C            Crear nueva playlist", texto),
        ("    E            Renombrar playlist", texto),
        ("    D            Eliminar playlist", texto),
        ("    [ / ]        Playlist anterior / siguiente", texto),
        ("", None),
        ("  Vistas", nav),
        ("    0-4          Cambiar vista", texto),
        ("    /            Buscar canciones", texto),
        ("    ? / F1       Abrir esta ayuda", texto),
        ("  Cola Temporal", nav),
        ("    Tab          Ver/ocultar cola (en Now Playing)", texto),
        ("    d / x        Quitar / Limpiar cola", texto),
        ("    J / K        Reordenar cola", texto),
        ("    s            Guardar cola como playlist", texto),
        ("    Esc          Cerrar ayuda", texto),
        ("    q            Salir", texto),
        ("", None),
    ]
    inner_w = 35
    inner_h = len(lines)
    box_w = min(inner_w + 2, w - 2)
    box_h = min(inner_h + 2, h - 2)
    ox = max(0, (w - box_w) // 2)
    oy = max(0, (h - box_h) // 2)
    try:
        win.addstr(oy, ox, "\u250c" + "\u2500" * (box_w - 2) + "\u2510", marco)
        for y in range(1, box_h - 1):
            clear = "\u2502" + " " * (box_w - 2) + "\u2502"
            win.addstr(oy + y, ox, clear, marco)
        win.addstr(oy + box_h - 1, ox, "\u2514" + "\u2500" * (box_w - 2) + "\u2518", marco)
        for i, (text, attr) in enumerate(lines):
            if i >= box_h - 2:
                break
            y = oy + 1 + i
            win.addstr(y, ox + 2, " " * (box_w - 4), texto)
            if attr is not None:
                win.addstr(y, ox + 2, text[:box_w - 4], attr)
    except curses.error:
        pass
