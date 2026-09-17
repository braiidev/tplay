# tplay — Reproductor multimedia TUI

Reproductor multimedia de terminal con `curses` + `python-vlc`. Navega archivos de audio/video, arma playlists, reproduce con metadatos ID3, sleep timer, cola temporal (stack), keybindings personalizables, filtro en vivo, radios streaming y 6 temas editables.

## Requisitos

- Python 3.12+
- VLC instalado (`libvlc`)
- ffmpeg (requerido por yt-dlp para descargas de audio/video)
- Linux (terminal 256 colores recomendada, ej: kmscon)

`install.sh` instala VLC y ffmpeg automáticamente (con sudo) si faltan; esto es
válido también para las descargas: sin ffmpeg, yt-dlp no puede extraer audio ni
mergear video y la descarga falla al final.

### Instalar VLC (`libvlc`) y ffmpeg

| Distro          | Comando                              |
|-----------------|--------------------------------------|
| Debian / Ubuntu | `sudo apt install vlc ffmpeg`        |
| Alpine          | `sudo apk add vlc ffmpeg`            |
| Arch            | `sudo pacman -S vlc ffmpeg`          |
| Fedora          | `sudo dnf install vlc ffmpeg`        |

> Si usás **PipeWire** (default en distros modernas) y VLC se queda mudo tras
> un crash/reinicio del servicio, instalá el puente ALSA→PipeWire:
> `sudo apt install pipewire-alsa` (o `apk add` / `pacman -S` / `dnf install`
> `pipewire-alsa`). tplay detecta el backend al arrancar y loguea
> `aout`/`libvlc` en `data/error.log`.

## Instalación

```bash
git clone https://github.com/braiidev/tplay ~/.config/tplay
cd ~/.config/tplay
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Uso

```bash
python3 -m player
```

## Teclas principales

| Tecla       | Acción                      |
|-------------|-----------------------------|
| `1`         | Listen (reproducción)       |
| `2`         | Explorador                  |
| `3`         | Playlist                    |
| `4`         | Historial                   |
| `5`         | Radios                      |
| `6`         | Favoritos                   |
| `0`         | Config                      |
| `Space`     | Play / Pause                |
| `s`         | Stop                        |
| `n` / `b`   | Siguiente / Anterior        |
| `+` / `-`   | Volumen                     |
| `q`         | Salir                       |
| `?` / `F1`  | Ayuda completa              |
| `X`         | Exportar M3U                |
| `O`         | Importar M3U/PLS (Explorer) |

## Vista Radios

- `a` — agregar radio (nombre → URL)
- `Enter` — reproducir
- `d` — eliminar
- `e` / `E` — editar nombre / URL
- `s` — guardar persistencia
- `X` — exportar a radios.m3u

## Personalización

Config persistente en `~/.config/tplay/data/config.json`:

- Directorio de música
- Volumen
- Tema: clasico, mono, calido, alto_contraste, flatline, custom (portados de Clock)
- Sleep timer
- Keybindings personalizables
- `ui_minimal` / `ui_navbar` toggles de apariencia

## Estructura

```
~/.config/tplay/
├── player/
│   ├── __init__.py        # main() + CLI args
│   ├── app.py             # Orquestación, loop, diálogos
│   ├── audio.py           # VLC wrapper, sleep timer
│   ├── config.py          # Config y temas (6 themes)
│   ├── file_utils.py      # Helpers (M3U/PLS detection)
│   ├── keybindings.py     # Bindings
│   ├── metadata.py        # ID3 (mutagen) cache LRU
│   ├── playlist.py        # Playlists JSON
│   ├── radios.py          # Radios JSON
│   ├── stack.py           # Stack de reproducción
│   ├── state.py           # Persistencia sesión (undo/redo)
│   ├── ui.py              # Primitivas UI (safe_addstr, boxes)
│   ├── views.py           # Dibujado por vista
│   └── handlers/          # Input por vista (package)
│       ├── __init__.py
│       ├── shared.py
│       ├── listen.py
│       ├── explorer.py
│       ├── playlist.py
│       ├── history.py
│       ├── config_view.py
│       └── radio.py
├── requirements.txt
└── README.md
```
