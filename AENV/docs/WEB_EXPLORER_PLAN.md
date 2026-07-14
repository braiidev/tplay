# WEB_EXPLORER_PLAN — tplay

> Plan detallado de implementación del yt-dlp Web Explorer (Fase 1: Streaming MVP).

## Resumen
Nueva vista V7 "Web" que permite buscar en YouTube via `yt-dlp`, navegar resultados y reproducir streaming directo (audio-only, sin descargar).

## Stack nuevo
- `yt-dlp` (pip) — librería Python, no subprocess
- Sin dependencias de sistema

---

## Paso 1.0: Auto-install en `--update`

### Archivo: `player/__init__.py` (modificar `_cli_update`)

### Lógica
1. Antes de `git pull`, leer contenido actual de `requirements.txt`
2. Después del pull, leer nuevo `requirements.txt`
3. Comparar líneas (ignorando espacios y comentarios)
4. Si hay paquetes nuevos → `pip install --user <paquetes>`
5. Si falla → mostrar toast con instrucciones manuales (`pip install --break-system-packages yt-dlp`)

### Código aproximado
```python
def _cli_update() -> bool:
    repo = ...
    # Guardar requirements viejo
    req_path = os.path.join(repo, "requirements.txt")
    old_reqs = set()
    if os.path.isfile(req_path):
        with open(req_path) as f:
            old_reqs = {l.strip() for l in f if l.strip() and not l.startswith("#")}
    
    # git pull...
    
    # Detectar paquetes nuevos
    if os.path.isfile(req_path):
        with open(req_path) as f:
            new_reqs = {l.strip() for l in f if l.strip() and not l.startswith("#")}
        added = new_reqs - old_reqs
        if added:
            pkgs = [p.split(">=")[0].split("==")[0] for p in added]
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--user"] + pkgs,
                capture_output=True, text=True, timeout=120
            )
            if result.returncode != 0:
                print(f"  ⚠ Instalá manualmente: pip install --break-system-packages {' '.join(pkgs)}")
```

---

## Paso 1.1: Wrapper `player/web.py`

### Archivo: `player/web.py` (nuevo)

### Contenido
```python
"""yt-dlp wrapper para Web Explorer."""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Any

try:
    import yt_dlp
except ImportError:
    yt_dlp = None  # type: ignore[import-untyped]


@dataclass
class WebResult:
    title: str
    url: str           # stream URL (para VLC)
    duration: int      # segundos
    channel: str
    webpage_url: str   # URL original
    platform: str      # "youtube", etc.


def is_available() -> bool:
    """Retorna True si yt-dlp está instalado."""
    return yt_dlp is not None


def search(query: str, max_results: int = 5) -> list[WebResult]:
    """
    Busca en YouTube (u otra plataforma).
    Retorna lista de WebResult o lista vacía.
    Lanza RuntimeError si yt-dlp no está instalado.
    """
    if not is_available():
        raise RuntimeError("yt-dlp no instalado: pip install yt-dlp")
    results: list[WebResult] = []
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "default_search": "ytsearch",
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:  # type: ignore[union-attr]
            info = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
            if not info or "entries" not in info:
                return results
            for entry in info["entries"]:
                if entry is None:
                    continue
                stream_url = entry.get("url", "")
                if not stream_url and entry.get("formats"):
                    audio_fmts = [f for f in entry["formats"]
                                  if f.get("acodec") != "none"]
                    if audio_fmts:
                        best = max(audio_fmts, key=lambda f: f.get("abr", 0))
                        stream_url = best.get("url", "")
                if not stream_url:
                    continue
                duration = entry.get("duration") or 0
                results.append(WebResult(
                    title=entry.get("title", "Sin título"),
                    url=stream_url,
                    duration=int(duration),
                    channel=entry.get("channel", entry.get("uploader", "")),
                    webpage_url=entry.get("webpage_url", ""),
                    platform=entry.get("extractor", "unknown"),
                ))
    except Exception:
        return results
    return results


def format_duration(seconds: int) -> str:
    """Formatea segundos a MM:SS o HH:MM:SS."""
    if seconds <= 0:
        return "--:--"
    h, remainder = divmod(seconds, 3600)
    m, s = divmod(remainder, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"
```

### Notas
- `extract_flat=False` porque necesitamos la `url` de streaming
- `default_search="ytsearch"` permite que yt-dlp use su búsqueda nativa
- Si `formats` no tiene `url` directa, buscamos el mejor formato de audio
- `format_duration` helper para UI

---

## Paso 1.2: Handler `player/handlers/webexplorer.py`

### Archivo: `player/handlers/webexplorer.py` (nuevo)

### Contenido
```python
"""Handler para la vista Web Explorer (V7)."""
from __future__ import annotations
import curses
from typing import TYPE_CHECKING

from .. import web
from .shared import _toast, _clamp_scroll

if TYPE_CHECKING:
    from player.app import PlayerApp


def handle_web(app: PlayerApp, key: int) -> None:
    """Handler principal de la vista Web."""
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
    """Maneja input del prompt de búsqueda."""
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
    """Ejecuta la búsqueda y carga resultados."""
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
    """Reproduce un resultado web via streaming."""
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
    """Agrega query al historial (máx 10)."""
    history = app.config.get("online_search_history", [])
    history = [h for h in history if h != query]
    history.insert(0, query)
    app.config["online_search_history"] = history[:10]
    from ..config import save as _save_config
    _save_config(app.config)
```

### Notas
- `web_search_mode` controla si estamos en modo input vs navegación
- `_handle_search_input` maneja buffer de texto con Backspace y Enter
- `_do_search` lee max_results de config
- `_play_web_result` crea StackItem con URL de streaming
- `_add_to_history` guarda historial (max 10)

---

## Paso 1.3: Drawer `draw_web()` en `player/views.py`

### Ubicación: al final de `views.py` (antes del `draw_mini_stack`)

### Contenido
```python
def draw_web(app: PlayerApp, h: int, w: int) -> None:
    """Dibuja la vista Web Explorer."""
    texto = curses.color_pair(PAIR_TEXTO)
    destacar = curses.color_pair(PAIR_DESTACAR)
    nav = curses.color_pair(PAIR_NAV)

    draw_box(app.stdscr, h, w, "Web")

    if app.web_search_mode:
        prompt = f"  Buscar: {app.web_search_buf}"
        safe_addstr(app.stdscr, 3, 2, prompt[:w - 4], texto | curses.A_UNDERLINE, h, w)
        safe_addstr(app.stdscr, 5, 2, "  Escribe tu búsqueda y presiona Enter", nav, h, w)
        return

    if not app.web_results:
        safe_addstr(app.stdscr, (h - 4) // 2, 2,
                     "  Presiona / para buscar", nav, h, w)
        return

    list_h = h - 8
    start = app.web_scroll
    end = min(start + list_h, len(app.web_results))

    for i in range(start, end):
        y = 5 + i - start
        r = app.web_results[i]
        is_cur = i == app.web_cursor
        dur = web.format_duration(r.duration)
        title = r.title[:w - 16]
        line = f"  {title:<{w - 16}}{dur:>7}"
        attr = destacar | curses.A_REVERSE if is_cur else texto
        safe_addstr(app.stdscr, y, 2, line, attr, h, w)

    draw_list_indicators(app.stdscr, 5, list_h, len(app.web_results),
                         app.web_scroll, nav, h, w)

    hints = _build_hints([
        ("j/k", "navegar"), ("Enter", "play"), ("/", "buscar"), ("Esc", "volver"),
    ], w)
    if hints:
        safe_addstr(app.stdscr, h - 4, 2, hints, nav, h, w)
```

### Notas
- Misma estructura que `draw_explorer`
- Prompt de búsqueda con underline
- Lista de resultados con cursor highlight
- Indicadores de scroll
- Hints en la parte inferior

---

## Paso 1.4: Integración en `player/app.py`

### Cambios

#### 1. Agregar constante V_WEB (junto a las otras V_*)
```python
V_WEB: int = 7
```

#### 2. Agregar estado Web en `__init__`
```python
# Estado Web
self.web_results: list = []
self.web_cursor: int = 0
self.web_scroll: int = 0
self.web_search_mode: bool = False
self.web_search_buf: str = ""
```

#### 3. Registrar handler y drawer
```python
self._view_handlers[self.V_WEB] = handlers.handle_web
self._view_drawers[self.V_WEB] = views.draw_web
```

#### 4. Extender range de view switch (línea 767)
```python
# De:
if ord("0") <= key <= ord("6"):
# A:
if ord("0") <= key <= ord("7"):
```

---

## Paso 1.5: Nav bar y Help en `player/ui.py`

### Cambios

#### 1. En `draw_nav()`, agregar entrada para `7`
Buscar la línea con las entradas de nav y agregar:
```python
("7", "Web"),
```

#### 2. En `HELP_TABS`, agregar nueva pestaña
```python
{
    "name": "Web",
    "lines": [
        ("", None),
        ("  WEB EXPLORER", PAIR_NAV),
        ("", None),
        ("    7         Abrir Web Explorer", PAIR_TEXTO),
        ("    /         Nueva búsqueda", PAIR_TEXTO),
        ("    j/k       Navegar resultados", PAIR_TEXTO),
        ("    Enter     Reproducir resultado", PAIR_TEXTO),
        ("    Esc       Volver a Escucha", PAIR_TEXTO),
    ]
},
```

---

## Paso 1.6: Config defaults en `player/config.py`

### Cambios en `DEFAULT_CONFIG`
```python
"online_max_results": 5,
"online_audio_quality": "128",
"online_search_history": [],
```

---

## Paso 1.7: Export en `player/handlers/__init__.py`

### Cambios
```python
from .webexplorer import handle_web
```

---

## Paso 1.8: Requirements

### Archivo: `requirements.txt`
Agregar:
```
yt-dlp
```

---

## Verificación post-implementación

1. `python3 -m mypy --strict player/` → debe pasar sin errores
2. `python3 -m player.app` → iniciar tplay
3. Presionar `7` → debe abrir vista Web
4. Presionar `/` → prompt de búsqueda
5. Escribir "beethoven" + Enter → resultados
6. `j/k` navegar, `Enter` → streaming en Listen
7. `Esc` → volver a Listen
8. `/` de nuevo → historial de búsquedas visible

## Errores a testear
- `yt-dlp` no instalado → toast informativo
- Sin internet → toast "Error de red"
- Query sin resultados → toast "Sin resultados"
- URL stream inválida → VLC maneja (fallback)

## Archivos modificados (resumen)

| Archivo | Acción | Líneas approx |
|---------|--------|---------------|
| `player/web.py` | CREAR | ~70 |
| `player/handlers/webexplorer.py` | CREAR | ~100 |
| `player/views.py` | AGREGAR draw_web() | ~40 |
| `player/app.py` | MODIFICAR | ~15 |
| `player/ui.py` | MODIFICAR | ~15 |
| `player/config.py` | MODIFICAR | ~3 |
| `player/handlers/__init__.py` | MODIFICAR | ~1 |
| `requirements.txt` | MODIFICAR | ~1 |

**Total estimado**: ~245 líneas nuevas/modificadas
