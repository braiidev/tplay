# MODELS — tplay

## Esquemas de persistencia

### config.json
```json
{
  "music_dir": "~/Music",
  "volume": 50,
  "theme": "clasico",
  "custom_colors": {
    "marco": "Cian",
    "texto": "Blanco",
    "destacar": "Amarillo",
    "nav": "Verde",
    "overlay": "Magenta"
  },
  "sleep_timer_minutes": 30,
  "keybinding_mode": "default",
  "keybindings": {},
  "ui_navbar": true,
  "ui_minimal": false
}
```

### state.json
```json
{
  "playing": false,
  "file": "",
  "position": 0,
  "stack_items": [
    {"path": "/path/to/file.mp3", "name": "file.mp3", "mode": "normal"}
  ],
  "playhead": 0,
  "shuffle": false,
  "repeat": false,
  "volume": 75,
  "rate": 1.0
}
```

### favorites.json
```json
[
  {"path": "/path/to/favorite.mp3", "name": "favorite.mp3"}
]
```

### history.json
```json
[
  {
    "path": "/path/to/file.mp3",
    "name": "file.mp3",
    "count": 5,
    "last_played": "2025-07-14T12:00:00"
  }
]
```

### playlist.json
```json
{
  "active": "default",
  "playlists": [
    {
      "name": "default",
      "songs": ["/path/to/song1.mp3", "/path/to/song2.mp3"]
    }
  ]
}
```

### radios.json
```json
[
  {
    "name": "Radio Stream",
    "url": "http://stream.example.com/radio.mp3"
  }
]
```

## Modelos en código

### StackItem (dataclass)
```python
@dataclass
class StackItem:
    path: str
    name: str
    mode: Literal["normal", "repeat_once", "repeat_inf"] = "normal"
```

### Stack
```python
class Stack:
    _items: list[StackItem]
    playhead: int  # -1 = vacío, >=0 = índice actual
    shuffle: bool
    repeat: bool
```

### Theme colors (5 pares)
```python
PAIR_MARCO: int = 1      # Bordes, frames
PAIR_TEXTO: int = 2      # Texto general
PAIR_DESTACAR: int = 3   # Cursor, items seleccionados
PAIR_NAV: int = 4        # Navegación, hints
PAIR_OVERLAY: int = 5    # Status bar, dialogs, filters
```

### Paleta de colores
```python
COLORS = {
    "Negro": 0, "Rojo": 1, "Verde": 2, "Amarillo": 3,
    "Azul": 4, "Magenta": 5, "Cian": 6, "Blanco": 7
}
```

### Themes predefinidos
- `clasico` — Cyan/Marco, Blanco/Texto, Amarillo/Destacar, Verde/Nav, Magenta/Overlay
- `mono` — Todo blanco
- `calido` — Amarillo/Marco, Blanco/Texto, Rojo/Destacar+Nav, Amarillo/Overlay
- `contraste` — Magenta/Marco, Blanco/Texto, Verde/Destacar+Overlay, Magenta/Nav
- `flatline` — Cyan/Marco, Blanco/Texto, Rojo/Destacar+Overlay, Cyan/Nav
- `custom` — Colores personalizados por el usuario

## Extensiones soportadas
```python
AUDIO_EXT = (".mp3", ".flac", ".wav", ".ogg", ".m4a", ".aac", ".opus", ".weba", ".wma", ".aiff", ".aif")
VIDEO_EXT = (".mp4", ".mkv", ".avi", ".mov", ".flv", ".wmv")
PLAYLIST_EXT = (".m3u", ".pls")
ALLOWED_EXT = AUDIO_EXT + VIDEO_EXT + PLAYLIST_EXT
```
