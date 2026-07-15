# ONLINE — tplay

> Features de streaming y descarga online via yt-dlp.

## Dependencias
- **yt-dlp** (pip) — librería Python para extracción de audio/video
- **ffmpeg** (sistema) — para descarga con conversión (audio→mp3, video→mp4)

## Arquitectura actual (v1.5.65)

### Archivos
| Archivo | Función |
|---------|---------|
| `player/platforms.py` | Registry de plataformas (Platform dataclass) |
| `player/web.py` | Wrapper yt-dlp (search, download, WebResult) |
| `player/handlers/webexplorer.py` | Handler V7 (3 modos: normal/search/motor) |
| `player/views.py` | UI V7 (draw_web, motor_editor, download_config) |

### Platform Registry
```python
@dataclass
class Platform:
    name: str                    # "YouTube"
    url: str                     # "https://youtube.com"
    search_pattern: str          # "/results?search_query={query}"
    download_pattern: str        # "/watch?v={id}"
    search_prefix: str           # "ytsearch" (vacío = sin búsqueda nativa)
    downloads: int = 0
    is_default: bool = False     # protege de eliminación
```

### Plataformas default (6)
| Platform | search_prefix | Búsqueda nativa |
|----------|---------------|-----------------|
| YouTube | `ytsearch` | ✅ |
| SoundCloud | `scsearch` | ✅ |
| Vimeo | `vpsearch` | ✅ |
| Dailymotion | `dmsearch` | ✅ |
| Twitch | `twsearch` | ✅ |
| Niconico | `nicosearch` | ✅ |

### Funciones de platforms.py
- `load_platforms()` → carga desde archivo o crea defaults
- `save_platforms()` → guarda a archivo
- `get_search_prefix(platforms, name)` → retorna prefijo
- `increment_downloads(platforms, name)` → incrementa contador
- `can_delete(platforms, name)` → True si no es default

## UI V7 — Web Explorer

### Layout
```
┌─ Web ─────────────────────────────────┐
│ [← YouTube →]  buscar: beethoven     │  ← Motor + Prompt
│──────────────────────────────────────│  ← Divider
│ [✓] Symphony No. 5 - 7:12           │
│ [►] Moonlight Sonata - 15:03         │  ← Lista con estados
│ [-] Für Elise - 3:02                 │
│ ...                                  │
└───────────────────────────────────────┘
```

### Estados de resultado
| Símbolo | Estado |
|---------|--------|
| `[-]` | Sin acción |
| `[►]` | Reproduciendo |
| `[D]` | Descargando |
| `[P]` | Pausado |
| `[Q]` | En cola |
| `[✓]` | Descargado |
| `[X]` | Cancelado |
| `[!]` | Error |

### Teclas
| Tecla | Acción |
|-------|--------|
| `/` | Buscar |
| `Tab` | Cambiar motor/prompt |
| `j/k` | Navegar |
| `g/G` | Inicio/Fin |
| `Enter` | Reproducir |
| `D` | Descarga directa |
| `d` | Descarga con config |
| `A/a` | Añadir a pila |
| `x` | Limpiar resultados |
| `Esc` | Volver a Escucha |

### Motor mode (Tab)
| Tecla | Acción |
|-------|--------|
| `j/k` | Navegar plataformas |
| `a` | Agregar plataforma |
| `e` | Editar plataforma |
| `d` | Eliminar (no-default) |
| `Enter` | Seleccionar motor |

## Config
```python
"online_platform": "YouTube",
"online_download_format": "audio",    # "audio" | "video"
"online_download_quality": "480p",    # "480p" | "720p" | "1080p" | "best"
"online_download_stream": "fastest",
"online_download_max": 3,             # max descargas simultáneas (1-10)
"online_max_results": 5,
"online_search_history": [],
```

## Plataformas sin búsqueda nativa
Si `search_prefix` está vacío, el prompt acepta URL completa:
```
[← Custom →]  https://example.com/video/12345
```
