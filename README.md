# tplay — Reproductor multimedia TUI

Reproductor multimedia de terminal con `curses` + `python-vlc`. Navega archivos de audio/video, arma playlists, reproduce con metadatos ID3, sleep timer, cola temporal, keybindings personalizables, filtro en vivo y temas editables.

## Requisitos

- Python 3.10+
- VLC instalado (`libvlc`)
- `git`
- Linux (terminal 256 colores recomendada)

## Instalación

```bash
curl -fsSL https://raw.githubusercontent.com/braiidev/tplay/main/install.sh | bash
```

Esto:
1. Clona el repo en `~/.config/tplay/`
2. Instala dependencias con `pip install --break-system-packages`
3. Crea el ejecutable `/usr/local/bin/tplay`

### Uso

```bash
tplay
```

## Teclas principales

| Tecla       | Acción                |
|-------------|-----------------------|
| `0`         | Config                |
| `1`         | Listen (reproducción) |
| `2`         | Explorador            |
| `3`         | Playlist              |
| `4`         | Historial             |
| `Space`     | Play / Pause          |
| `s`         | Stop                  |
| `n` / `b`   | Siguiente / Anterior  |
| `+` / `-`   | Volumen               |
| `q`         | Salir                |
| `?` / `F1`  | Ayuda completa        |

> Ver todas las teclas en `COMPACT_SPEC.md`.

## Personalización

Config persistente: `~/.config/tplay/data/config.json`

- Directorio de música
- Volumen
- Tema (clásico, mono, cálido, alto_contraste, custom)
- Sleep timer
- Keybindings personalizables

## Estructura

```
~/.config/tplay/
├── app.py
├── install.sh
├── requirements.txt
├── player/
│   ├── __init__.py        # main() + CLI args
│   ├── app.py             # Orquestación
│   ├── audio.py           # VLC wrapper
│   ├── config.py          # Config y temas
│   ├── file_utils.py      # Helpers
│   ├── handlers.py        # Input por vista
│   ├── keybindings.py     # Bindings
│   ├── metadata.py        # ID3 (mutagen)
│   ├── playlist.py        # Playlists
│   ├── stack.py           # Stack de reproducción
│   ├── state.py           # Persistencia sesión
│   ├── ui.py              # Primitivas UI
│   └── views.py           # Dibujado por vista
└── COMPACT_SPEC.md        # Documentación completa
```
