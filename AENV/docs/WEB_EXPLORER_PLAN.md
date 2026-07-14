# WEB_EXPLORER_PLAN — tplay

> Plan detallado de implementación del yt-dlp Web Explorer (Fase 1: Streaming MVP).

## Resumen
Nueva vista V7 "Web" que permite buscar en YouTube via `yt-dlp`, navegar resultados y reproducir streaming directo (audio-only, sin descargar).

## Stack nuevo
- `yt-dlp` (pip) — librería Python, no subprocess
- Sin dependencias de sistema

---

## Estado actual (v1.5.60)

### Lo que ya está implementado
- `player/web.py` — wrapper yt-dlp (search, WebResult, format_duration)
- `player/handlers/webexplorer.py` — handler V7 (search input, nav, playback)
- `player/views.py` — draw_web()
- `player/app.py` — V_WEB=7, handler/drawer, dispatch, web_search_mode intercept
- `player/ui.py` — nav bar 7:Web, help tab Web
- `player/config.py` — defaults online
- `player/__init__.py` — auto-install deps en --update
- `requirements.txt` — yt-dlp

### Bugs fixeados
- B20: web_search_mode interceptado en _handle_key_mode_specific
- B21: web_search_mode reset en view switch

### Bug pendiente: B22 — search() siempre devuelve "Sin resultados"

**Causa raíz**: `extract_flat=False` con yt-dlp search retorna entries pero `entry.get("url", "")` es string vacío. yt-dlp search solo retorna metadata básica (title, id, webpage_url) sin extraer stream URL.

**Test que confirma**:
```python
import yt_dlp
with yt_dlp.YoutubeDL(opts) as ydl:
    info = ydl.extract_info("ytsearch3:beethoven", download=False)
    for e in info["entries"]:
        print(e.get("url"))  # → "" (vacío siempre)
```

**Solución**: Usar `extract_flat=True` para obtener la lista (rápido), luego extraer stream URL de cada entry individualmente con `extract_info(entry["url"], download=False)`.

---

## Cambio de diseño: Registry de plataformas

### Problema
El approach actual usa `ytsearch5:query` hardcodeado. No soporta otras plataformas ni tiene tracking de uso.

### Solución: Base de datos de plataformas
Estructura JSON en `~/.config/tplay/data/platforms.json`:

```json
[
  {
    "name": "YouTube",
    "url": "https://www.youtube.com",
    "download_pattern": "/watch?v={id}",
    "search_pattern": "/results?search_query={query}",
    "search_prefix": "ytsearch",
    "downloads": 0
  },
  {
    "name": "Dailymotion",
    "url": "https://www.dailymotion.com",
    "download_pattern": "/video/{id}",
    "search_pattern": "/search/{query}/videos",
    "search_prefix": "dmsearch",
    "downloads": 0
  }
]
```

### Campos
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `name` | str | Nombre legible (YouTube, Dailymotion) |
| `url` | str | URL base del sitio |
| `download_pattern` | str | Patrón de URL de video, `{id}` se reemplaza |
| `search_pattern` | str | Patrón de URL de búsqueda, `{query}` se reemplaza |
| `search_prefix` | str | Prefijo yt-dlp para búsqueda nativa (`ytsearch`, `dmsearch`) |
| `downloads` | int | Contador de descargas realizadas |

### Por qué `search_prefix` es clave
yt-dlp soporta búsqueda nativa en muchas plataformas:
- `ytsearch5:query` → YouTube
- `dmsearch5:query` → Dailymotion
- `scsearch5:query` → SoundCloud
- `vpsearch5:query` → Vimeo

El `search_prefix` permite construir la query de búsqueda sin parsear URLs.

---

## Plan de implementación

### Paso 2.1: Crear `player/platforms.py` (nuevo)

Módulo que maneja el registry de plataformas.

```python
"""Registry de plataformas soportadas para Web Explorer."""
from __future__ import annotations
import json
import os
from dataclasses import dataclass, field, asdict

PLATFORMS_FILE = os.path.expanduser("~/.config/tplay/data/platforms.json")

DEFAULT_PLATFORMS = [
    {
        "name": "YouTube",
        "url": "https://www.youtube.com",
        "download_pattern": "/watch?v={id}",
        "search_pattern": "/results?search_query={query}",
        "search_prefix": "ytsearch",
        "downloads": 0,
    },
]


@dataclass
class Platform:
    name: str
    url: str
    download_pattern: str
    search_pattern: str
    search_prefix: str
    downloads: int = 0


def load_platforms() -> list[Platform]:
    """Carga plataformas desde archivo o crea defaults."""
    try:
        with open(PLATFORMS_FILE) as f:
            data = json.load(f)
        return [Platform(**p) for p in data]
    except (FileNotFoundError, json.JSONDecodeError, TypeError):
        return [Platform(**p) for p in DEFAULT_PLATFORMS]


def save_platforms(platforms: list[Platform]) -> None:
    """Guarda plataformas a archivo."""
    try:
        os.makedirs(os.path.dirname(PLATFORMS_FILE), exist_ok=True)
        with open(PLATFORMS_FILE, "w") as f:
            json.dump([asdict(p) for p in platforms], f, indent=2)
    except OSError:
        pass


def get_search_prefix(platforms: list[Platform], name: str) -> str:
    """Retorna el search_prefix para una plataforma."""
    for p in platforms:
        if p.name.lower() == name.lower():
            return p.search_prefix
    return "ytsearch"  # fallback


def increment_downloads(platforms: list[Platform], name: str) -> None:
    """Incrementa el contador de descargas de una plataforma."""
    for p in platforms:
        if p.name.lower() == name.lower():
            p.downloads += 1
            break
```

### Archivos afectados
- **Nuevo**: `player/platforms.py`
- **Nuevo**: `~/.config/tplay/data/platforms.json` (se crea automáticamente)

---

### Paso 2.2: Rediseñar `player/web.py`

Cambios principales:
1. Usar `extract_flat=True` para listar resultados (rápido)
2. Extraer stream URL individualmente por cada entry
3. Recibir `search_prefix` como parámetro
4. Incrementar contador de descargas al hacer play

```python
def search(query: str, max_results: int = 5, 
           search_prefix: str = "ytsearch") -> list[WebResult]:
    """
    Busca en la plataforma indicada.
    1. extract_flat=True → obtiene lista de entries (rápido, sin stream URLs)
    2. Para cada entry → extract_info para obtener stream URL
    """
    if not is_available():
        raise RuntimeError("yt-dlp no instalado: pip install --break-system-packages yt-dlp")
    
    results: list[WebResult] = []
    try:
        import yt_dlp
    except ImportError:
        return results
    
    # Paso 1: listar resultados (rápido)
    list_opts: dict[str, object] = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,  # No extraer URLs aún
    }
    try:
        with yt_dlp.YoutubeDL(list_opts) as ydl:
            info = ydl.extract_info(f"{search_prefix}{max_results}:{query}", download=False)
            if not info or "entries" not in info:
                return results
            entries = list(info["entries"])
    except Exception:
        return results
    
    # Paso 2: extraer stream URL de cada entry
    extract_opts: dict[str, object] = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "skip_download": True,
    }
    for entry in entries:
        if entry is None:
            continue
        entry_url = entry.get("url") or entry.get("webpage_url", "")
        if not entry_url:
            continue
        try:
            with yt_dlp.YoutubeDL(extract_opts) as ydl:
                detail = ydl.extract_info(entry_url, download=False)
                if not detail:
                    continue
                stream_url = detail.get("url", "")
                if not stream_url and detail.get("formats"):
                    audio_fmts = [f for f in detail["formats"]
                                  if f.get("acodec") != "none"]
                    if audio_fmts:
                        best = max(audio_fmts, key=lambda f: f.get("abr", 0))
                        stream_url = best.get("url", "")
                if not stream_url:
                    continue
                results.append(WebResult(
                    title=detail.get("title", entry.get("title", "Sin título")),
                    url=stream_url,
                    duration=int(detail.get("duration") or 0),
                    channel=detail.get("channel", detail.get("uploader", "")),
                    webpage_url=detail.get("webpage_url", entry_url),
                    platform=detail.get("extractor", "unknown"),
                ))
        except Exception:
            continue
    
    return results
```

### Notas
- `extract_flat=True` → la búsqueda lista rápido (~1s)
- `extract_info(entry_url)` por cada resultado → extrae stream URL (~2-3s cada uno)
- Total para 5 resultados: ~10-15s (aceptable, con toast de progreso opcional)
- `skip_download=True` asegura que no descargue nada

### Archivos afectados
- **Modificar**: `player/web.py` (reemplazar search())

---

### Paso 2.3: Modificar `player/handlers/webexplorer.py`

Cambios:
1. `_do_search()` lee `search_prefix` de la plataforma activa
2. `_play_web_result()` incrementa contador de descargas

```python
def _do_search(app: PlayerApp, query: str) -> None:
    from .. import web
    from ..platforms import load_platforms, get_search_prefix
    from ..config import load as _load_config
    
    platforms = load_platforms()
    cfg = _load_config()
    max_results = cfg.get("online_max_results", 5)
    prefix = get_search_prefix(platforms, "YouTube")  # plataforma activa (futuro: configurable)
    
    try:
        results = web.search(query, max_results, search_prefix=prefix)
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
    
    # Incrementar contador de descargas
    from ..platforms import load_platforms, save_platforms, increment_downloads
    platforms = load_platforms()
    increment_downloads(platforms, result.platform)
    save_platforms(platforms)
    
    from ..stack import StackItem
    item = StackItem(path=result.url, name=result.title)
    app.stack.items = [item]
    app.stack.playhead = 0
    app.audio.play_file(result.url)
    app.current_view = app.V_LISTEN
    _toast(app, f"▶ {result.title}")
```

### Archivos afectados
- **Modificar**: `player/handlers/webexplorer.py`

---

### Paso 2.4: Actualizar `player/config.py`

Agregar plataforma activa:
```python
"online_platform": "YouTube",  # plataforma activa para búsqueda
```

### Archivos afectados
- **Modificar**: `player/config.py`

---

### Paso 2.5: Actualizar `AENV/docs/ONLINE.md`

Documentar:
- Estructura de `platforms.json`
- Cómo agregar nuevas plataformas
- Flujo de búsqueda con `extract_flat`

### Archivos afectados
- **Modificar**: `AENV/docs/ONLINE.md`

---

## Flujo completo de búsqueda (post-fix)

```
1. Usuario presiona 7 → V_WEB
2. Presiona / → prompt de búsqueda
3. Escribe "beethoven" + Enter
4. _do_search("beethoven")
   a. load_platforms() → obtiene prefix "ytsearch"
   b. web.search("beethoven", 5, "ytsearch")
      b1. extract_flat=True → lista de 5 entries (~1s)
      b2. Para cada entry → extract_info → stream URL (~2-3s c/u)
      b3. Retorna 5 WebResult con stream URLs
5. draw_web() muestra resultados con títulos y duración
6. Usuario presiona Enter → _play_web_result()
   a. Incrementa downloads en platforms.json
   b. Crea StackItem con URL de streaming
   c. VLC reproduce stream HTTP directamente
7. Cambia a V_LISTEN
```

## Archivos modificados (resumen total)

| Archivo | Acción | Estado |
|---------|--------|--------|
| `player/platforms.py` | CREAR | Pendiente |
| `player/web.py` | REESCRIBIR search() | Pendiente |
| `player/handlers/webexplorer.py` | MODIFICAR _do_search, _play_web_result | Pendiente |
| `player/config.py` | AGREGAR online_platform | Pendiente |
| `AENV/docs/ONLINE.md` | ACTUALIZAR | Pendiente |
| `player/__init__.py` | Ya hecho (auto-install) | ✅ |
| `player/app.py` | Ya hecho (V_WEB, dispatch) | ✅ |
| `player/ui.py` | Ya hecho (nav, help) | ✅ |
| `player/handlers/__init__.py` | Ya hecho (export) | ✅ |
| `requirements.txt` | Ya hecho (+yt-dlp) | ✅ |

## Verificación post-implementación

1. `python3 -m mypy --strict player/` → sin errores
2. `tplay → 7 → / → "beethoven" → Enter` → 5 resultados con títulos
3. `Enter` en resultado → streaming en Listen
4. `~/.config/tplay/data/platforms.json` → YouTube downloads incrementado
5. `tplay --update` → auto-install si hay deps nuevas
