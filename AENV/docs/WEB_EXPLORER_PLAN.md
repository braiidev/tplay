# WEB_EXPLORER_PLAN — tplay

> Plan completo de implementación del yt-dlp Web Explorer v2.

## Resumen
Vista V7 "Web" con motor de búsqueda multi-plataforma, gestión de plataformas, descarga directa y estados de descarga en lista.

## Stack
- `yt-dlp` (pip) — librería Python, no subprocess
- Sin dependencias de sistema

---

## Arquitectura actual (v1.5.60)

### Lo que existe
- `player/web.py` — wrapper yt-dlp (WebResult, search, format_duration) — **ROTO** (B22)
- `player/handlers/webexplorer.py` — handler V7 (search input, nav, playback)
- `player/views.py` — draw_web() básico
- `player/app.py` — V_WEB=7, handler/drawer, dispatch
- `player/ui.py` — nav bar 7:Web, help tab Web
- `player/config.py` — defaults online básicos
- `player/__init__.py` — auto-install deps en --update
- `requirements.txt` — yt-dlp

### Bugs conocidos
- **B22**: `search()` siempre retorna "Sin resultados" (extract_flat=False no retorna stream URLs)

---

## Nueva arquitectura v2

### 1. `player/platforms.py` — NUEVO

Registry de plataformas soportadas.

```python
@dataclass
class Platform:
    name: str                    # "YouTube"
    url: str                     # "https://youtube.com"
    search_pattern: str          # "/results?search_query={query}" (vacío = sin búsqueda)
    download_pattern: str        # "/watch?v={id}"
    search_prefix: str           # "ytsearch" (vacío = sin búsqueda nativa)
    downloads: int = 0
    is_default: bool = False     # protege de eliminación
```

**DEFAULT_PLATFORMS (6):**
| Platform | search_prefix | Búsqueda nativa |
|----------|---------------|-----------------|
| YouTube | `ytsearch` | ✅ |
| SoundCloud | `scsearch` | ✅ |
| Vimeo | `vpsearch` | ✅ |
| Dailymotion | `dmsearch` | ✅ |
| Twitch | `twsearch` | ✅ |
| Niconico | `nicosearch` | ✅ |

**Funciones:**
- `load_platforms() → list[Platform]`
- `save_platforms(list[Platform])`
- `get_search_prefix(platforms, name) → str`
- `increment_downloads(platforms, name)`

**Almacenamiento:** `~/.config/tplay/data/platforms.json`

**Plataformas sin búsqueda nativa:** El usuario puede agregarlas manualmente. Si `search_prefix` está vacío, el prompt acepta URL completa.

---

### 2. `player/web.py` — REESCRIBIR

**WebResult (existente, modificar):**
```python
@dataclass
class WebResult:
    title: str
    url: str              # stream URL para playback
    duration: int
    channel: str
    webpage_url: str
    platform: str
    download_url: str     # NUEVO: URL para descarga
```

**Funciones:**
- `search(query, max_results, search_prefix) → list[WebResult]` — REESCRIBIR con extract_flat=True
- `download(url, output_path, fmt, quality) → bool` — NUEVO
- `is_available() → bool` — sin cambios
- `format_duration() → str` — sin cambios

**Formatos:**
- Audio: `.mp3` (mejor compatibilidad)
- Video: `.mp4` (mejor compatibilidad)

---

### 3. `player/handlers/webexplorer.py` — REESCRIBIR

**3 modos de operación:**

```
┌─ web_search_mode (prompt de búsqueda)
│    Tab → web_motor_mode
│    Enter → buscar (si search_prefix existe)
│           → URL directa (si search_prefix vacío)
│    Esc → volver a lista
│
├─ web_motor_mode (gestionar plataformas)
│    ← → → ciclar motores
│    a → _add_platform() → web_motor_edit_mode
│    e → _edit_platform() → web_motor_edit_mode
│    d → _delete_platform() (no-defaults)
│    Tab → web_search_mode
│    Enter → seleccionar motor activo
│
└─ Normal (navegar lista)
     / → web_search_mode
     j/k, g/G, PgUp/PgDn → navegar
     Enter → play (sin resetear lista)
     D → descarga directa (sin config)
     d → descarga con config
     A/a → add to queue (reproducción)
     x → clear list
     Esc → volver a Listen
```

**Funciones nuevas:**
- `_handle_motor_input(app, key)` — gestión de plataformas
- `_add_platform(app)` — agregar plataforma
- `_edit_platform(app)` — editar plataforma
- `_delete_platform(app)` — eliminar plataforma (no-defaults)
- `_download_web_result(app, with_config)` — descarga directa o con config

---

### 4. `player/views.py` — MODIFICAR

**Nuevo layout de draw_web():**

```
┌─ Web ─────────────────────────────────┐
│ [← YouTube →]  buscar: beethoven     │  ← Línea 1: Motor + Prompt
│──────────────────────────────────────│  ← Divider
│ [✓] Symphony No. 5 - 7:12           │
│ [►] Moonlight Sonata - 15:03         │  ← Lista con estados
│ [-] Für Elise - 3:02                 │
│ [Q] Hungarian Dances - 10:00         │
│ ...                                  │
└───────────────────────────────────────┘
```

**Estados de cada resultado:**
| Símbolo | Estado |
|---------|--------|
| `[-]` | Sin acción asignada |
| `[►]` | Reproduciendo |
| `[D]` | Descargando |
| `[P]` | Pausado |
| `[Q]` | En cola de descarga |
| `[✓]` | Descargado |
| `[X]` | Cancelado |
| `[!]` | Error en descarga |

**Funciones nuevas:**
- `draw_motor_editor(app, win, h, w)` — patrón idéntico a draw_meta_editor()
- `draw_download_config(app, win, h, w)` — patrón idéntico a draw_meta_editor()

---

### 5. `player/app.py` — MODIFICAR

**Estados web (actuales + nuevos):**
```python
web_results: list[WebResult]          # existente
web_cursor: int                       # existente
web_scroll: int                       # existente
web_search_mode: bool                 # existente
web_search_buf: str                   # existente
web_motor_mode: bool                  # NUEVO
web_active_platform: int              # NUEVO (índice)
web_motor_edit_mode: bool             # NUEVO
web_download_mode: bool               # NUEVO
web_platforms: list[Platform]         # NUEVO
web_download_queue: list[WebResult]   # NUEVO (max 3)
web_download_max: int                 # NUEVO (configurable hasta 10)
```

---

### 6. `player/config.py` — MODIFICAR

**Defaults nuevos:**
```python
"online_platform": "YouTube",
"online_download_format": "audio",    # "audio" | "video"
"online_download_quality": "480p",    # "480p" | "720p" | "1080p" | "best"
"online_download_stream": "fastest",
"online_download_max": 3,             # max descargas simultáneas (1-10)
```

---

## Flujo completo

### Búsqueda
```
V7 → Tab motor → ← → YouTube → Tab prompt → "beethoven" → Enter
  → extract_flat=True → lista → Enter en resultado → Play en Listen
```

### Descarga directa (D)
```
V7 → Enter en resultado → estado [►] → D → descarga directa → estado [D]
  → completado → estado [✓] → toast "Descargado en music_dir/"
```

### Descarga con config (d)
```
V7 → d en resultado → draw_download_config → configurar → Enter → descarga → estado [D]
```

### Gestión de plataformas
```
V7 → Tab motor → a → draw_motor_editor →填写 campos → Enter → nueva plataforma guardada
V7 → Tab motor → e → draw_motor_editor → editar → Enter → plataforma actualizada
V7 → Tab motor → d → eliminar (no-defaults) → toast confirmación
```

### Plataforma sin búsqueda nativa
```
V7 → Tab motor → seleccionar plataforma sin search_prefix
  → Tab prompt → ingresar URL completa → Enter → resultado único
```

---

## Escenarios cubiertos

| Escenario | Comportamiento |
|-----------|----------------|
| `Enter` en resultado | Play en Listen, estado → `[►]` |
| `D` en resultado | Descarga directa, estado → `[D]` o `[Q]` si cola llena |
| `d` en resultado | Muestra config, luego descarga |
| Ya descargado mismo formato | Toast "Ya descargado en music_dir/" |
| Ya descargado otro formato | Re-descargar con nuevo formato |
| Cola llena (3) | Siguiente `D` → estado `[Q]`, espera |
| `A` en resultado | Add to queue (reproducción) |
| `x` limpia lista | Limpia resultados y estados |
| `g` / `G` | Primer / último resultado |
| Plataforma sin búsqueda | Prompt acepta URL completa |
| Error en descarga | Toast error, estado `[!]` |
| Descarga cancelada | Estado `[X]` |

---

## Archivos modificados (resumen total)

| Archivo | Acción | Estado |
|---------|--------|--------|
| `player/platforms.py` | CREAR | Pendiente |
| `player/web.py` | REESCRIBIR search() + download() | Pendiente |
| `player/handlers/webexplorer.py` | REESCRIBIR 3 modos + gestión | Pendiente |
| `player/views.py` | MODIFICAR draw_web() + nuevos draws | Pendiente |
| `player/app.py` | MODIFICAR nuevos estados | Pendiente |
| `player/config.py` | MODIFICAR defaults downloads | Pendiente |
| `player/__init__.py` | Ya hecho (auto-install) | ✅ |
| `player/ui.py` | Ya hecho (nav, help) | ✅ |
| `player/handlers/__init__.py` | Ya hecho (export) | ✅ |
| `requirements.txt` | Ya hecho (+yt-dlp) | ✅ |

---

## Verificación post-implementación

1. `python3 -m mypy --strict player/` → sin errores
2. `tplay → 7 → Tab motor → ← → YouTube → Tab prompt → "beethoven" → Enter` → 5 resultados
3. `Enter` en resultado → streaming en Listen
4. `D` en resultado → descarga directa → archivo en music_dir/
5. `g/G` → navega primer/último resultado
6. `Tab` alterna motor/prompt
7. `a` en motor → editor de plataformas
8. `~/.config/tplay/data/platforms.json` → plataformas guardadas
