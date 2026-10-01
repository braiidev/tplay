# tplay — Reproductor multimedia TUI

Reproductor multimedia de terminal con `curses` + `python-vlc`. Navega archivos de audio/video, arma playlists, reproduce con metadatos ID3, sleep timer, cola temporal (stack), keybindings personalizables, filtro en vivo, radios streaming y 6 temas editables.

## Requisitos

- Linux
- VLC (`libvlc`)
- ffmpeg (lo requiere yt-dlp para descargas de audio/video)
- Python 3.10–3.14 — lo elige y lo pinnea el instalador; no tenés que instalar nada a mano

`install.sh` intenta instalar las deps del sistema si faltan, con sudo. Si no puede (sin tty, sin sudo, distro sin gestor conocido), sigue y te dice qué instalar a mano. Sin ffmpeg, yt-dlp no puede extraer audio ni mergear video y la descarga falla al final.

| Distro          | Comando                              |
|-----------------|--------------------------------------|
| Debian / Ubuntu | `sudo apt install vlc ffmpeg`        |
| Alpine          | `sudo apk add vlc ffmpeg`            |
| Arch            | `sudo pacman -S vlc ffmpeg`          |
| Fedora          | `sudo dnf install vlc ffmpeg`        |

> Si usás **PipeWire** (default en distros modernas) y VLC se queda mudo tras
> un crash/reinicio del servicio, instalá el puente ALSA→PipeWire:
> `sudo apt install pipewire-alsa` (o `apk add` / `pacman -S` / `dnf install`).
> tplay detecta el backend al arrancar y loguea `aout`/`libvlc` en
> `data/error.log`.

## Instalación

```bash
curl -fsSL https://raw.githubusercontent.com/braiidev/tplay/main/install.sh | bash
```

Usá `bash`, no `sh`: el instalador genera un wrapper en Bash que se autorepara.

Qué hace, en orden: elige un Python **versionado** (3.10–3.14, con preferencia
por el más nuevo disponible), crea un **venv propio** en
`~/.local/share/tplay/.venv`, instala el proyecto con `pip install -e .`, y deja
el comando en `~/.local/bin/tplay`.

Tres cosas que el diseño garantiza:

- **No toca el Python del sistema.** Todo va al venv. Nunca hace
  `pip install --user` ni `--break-system-packages`.
- **Es idempotente.** Volver a correrlo reutiliza el venv si está sano; no
  golpea la red de más.
- **Sobrevive una actualización de SO.** El pin es un rango, no una versión fija:
  si el sistema pasa de Python 3.12 a 3.14, el instalador re-resuelve y recrea el
  venv. También detecta el venv "colgado" del alias flotante `/usr/bin/python3` y
  lo rehace.

Si ya tenías tplay con el método viejo (repo en `~/.config/tplay`), no hace falta
que hagas nada: los datos se migran solos, **por copia**, al primer arranque. El
original queda intacto hasta que confirmes que todo está bien.

### Uso

```bash
tplay
```

Opciones:

| Opción           | Qué hace                                                       |
|------------------|----------------------------------------------------------------|
| (sin flags)      | abre el reproductor (requiere terminal interactivo)            |
| `--update`       | trae la última versión y reconcilia las deps del venv          |
| `--reinstall`    | re-corre el `install.sh` de este repo                          |
| `--uninstall`    | desinstala; **pide confirmación antes de borrar los datos**    |
| `--ctl <cmd>`    | control externo: `play`/`pause`/`next`/`prev`/`status`/`vol`   |
| `--version`      | imprime la versión                                             |
| `--help`         | ayuda                                                          |

`--uninstall` muestra qué va a borrar (con cantidad y tamaño) y no borra los
datos sin un "sí" explícito. Sin terminal interactiva conserva los datos: no hay
a quién preguntarle, y asumir "sí" desde un script es cómo se pierden favoritos.

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

## Dónde vive cada cosa

| Qué                | Dónde                                                    | Por qué                                             |
|--------------------|----------------------------------------------------------|-----------------------------------------------------|
| Código             | `~/.local/share/tplay/`                                  | datos de app: no es caché ni config a mano         |
| Estado (JSON)      | `~/.local/share/tplay/data/`                             | XDG: `~/.config` es para lo que editás con un editor |
| Comando            | `~/.local/bin/tplay`                                     | no requiere sudo                                    |
| Intérprete         | `~/.local/share/tplay/.venv/`                            | aislado del Python del sistema                      |
| Versión pineada    | `~/.local/share/tplay/.pinned-python`                    | qué intérprete se usó, para poder detectar drift    |

Antes el código y los datos vivían juntos en `~/.config/tplay`, y por eso el
`--uninstall` anterior podía llevarse favoritos e historial en un `rm -rf`.

### Estado persistente

`~/.local/share/tplay/data/config.json` guarda:

- Directorio de música
- Volumen
- Tema: clasico, mono, calido, alto_contraste, flatline, custom (portados de Clock)
- Sleep timer
- Keybindings personalizables
- `ui_minimal` / `ui_navbar` toggles de apariencia

El resto del estado (`favorites.json`, `history.json`, `downloads.json`,
`playlist.json`, `radios.json`, `state.json`, `platforms.json`,
`ytdlp_check.json`, `error.log`) vive en el mismo directorio.

## Estructura del repo

```
tplay/
├── install.sh            # pin + venv, idempotente, genera el wrapper
├── pyproject.toml        # fuente única de deps y entry point
├── player/
│   ├── __init__.py       # main() + CLI (update/reinstall/uninstall/ctl)
│   ├── __main__.py       # habilita python -m player
│   ├── paths.py          # rutas + guard de arranque + migración de datos
│   ├── app.py            # Orquestación, loop, diálogos
│   ├── audio.py          # VLC wrapper, sleep timer
│   ├── config.py         # Config y temas (6 themes)
│   ├── file_utils.py     # Helpers (M3U/PLS detection)
│   ├── keybindings.py    # Bindings
│   ├── metadata.py       # ID3 (mutagen) cache LRU
│   ├── playlist.py       # Playlists JSON
│   ├── radios.py         # Radios JSON
│   ├── stack.py          # Stack de reproducción
│   ├── state.py          # Persistencia sesión (undo/redo)
│   ├── ui.py             # Primitivas UI (safe_addstr, boxes)
│   ├── views.py          # Dibujado por vista
│   └── handlers/         # Input por vista (package)
│       ├── __init__.py
│       ├── shared.py
│       ├── listen.py
│       ├── explorer.py
│       ├── playlist.py
│       ├── history.py
│       ├── config_view.py
│       └── radio.py
└── tests/
    ├── conftest.py       # sys.path para pytest pelado
    ├── test_paths.py     # guard de arranque + migración
    ├── test_lifecycle.py # update / reinstall / uninstall
    └── ...
```

## Desarrollo

```bash
python3 -m pytest        # 108 tests
python3 -m mypy player   # strict, 32 archivos
bash -n install.sh
```

`install.sh` acepta `TPLAY_DIR`, `TPLAY_BIN` y `TPLAY_RC` para testear en un
sandbox sin tocar la instalación real:

```bash
TPLAY_DIR=/tmp/t/share/tplay TPLAY_BIN=/tmp/t/bin/tplay TPLAY_RC=/tmp/t/rc \
  bash install.sh
```
