# SPEC_PLAYER.md — Reproductor multimedia TUI (OBSOLETO)

> **⚠️ Este documento está obsoleto.** La fuente de verdad es `COMPACT_SPEC.md`.
> Se mantiene solo como referencia histórica. No refleja el estado actual del código.

## Visión general

Reproductor multimedia de terminal con curses + python-vlc. Navega archivos de
audio/video, arma playlists, reproduce con metadatos ID3, sleep timer, cola
temporal con items consumibles y permanentes, keybindings customizables, filtro
en vivo y temas editables.

## Stack

- **TUI:** Python `curses` (stdlib), NO textual
- **Motor de audio:** `python-vlc` con `--no-video`
- **Metadatos:** `mutagen` (ID3 cacheado)
- **Persistencia:** `~/.config/player/` (JSON)

## Estructura del proyecto

```
Dev/Player/
├── app.py                    # Entry point: from player import main(); main()
├── SPEC_PLAYER.md
├── TODO.md
└── player/
    ├── __init__.py           # main()
    ├── app.py                # PlayerApp: init, run(), orquestación (1103 LOCs)
    ├── audio.py              # AudioEngine: wrapper VLC (play/pause/stop/…)
    ├── config.py             # Config persistente, temas, colores
    ├── file_utils.py         # list_dir, human_size, time_str, ext_label, is_media
    ├── keybindings.py        # Constantes, validación, lookup de bindings
    ├── metadata.py           # MetadataCache con mutagen
    ├── playlist.py           # Carga/guarda multi-playlist
    ├── ui.py                 # safe_addstr, draw_box, draw_nav, draw_status, draw_prompt, draw_help
    └── views.py              # draw_explorer, draw_playlist, draw_now_playing, draw_search, draw_config, draw_keybindings
```

## Vistas (6)

| Tecla | Vista       | ID  |
|-------|-------------|-----|
| `0`   | Config      | 0   |
| `1`   | Explorador  | 1   |
| `2`   | Playlist    | 2   |
| `3`   | Now Playing | 3   |
| `4`   | Búsqueda    | 4   |
| (Enter en Config) | Keybindings | 5 |

## Directorios

| Concepto                | Ruta                           |
| ----------------------- | ------------------------------ |
| Inicio explorador       | `~/Music`                      |
| Directorio del proyecto | `Dev/Player/`                  |
| Config persistente      | `~/.config/player/config.json` |
| Playlist persistente    | `~/.config/player/playlist.json` |

## Formatos soportados

- **Audio:** `.mp3`, `.flac`, `.wav`, `.ogg`
- **Video:** `.mp4`, `.mkv`, `.avi`, `.mov` — VLC con `--no-video`, solo audio

Se definen en `player/file_utils.py`: `AUDIO_EXT`, `VIDEO_EXT`, `ALLOWED_EXT`,
`EXT_LABEL`.

## Barra de navegación (fila h-1)

```
 0:Config │ 1:Expl │ 2:Playlist │ 3:Playing │ q:Salir
```

## Barra de estado (fila h-3)

Visible en vistas 0, 1, 2, 4 (oculta en 3 y 5).

```
 ► nombre_del_archi…  [00:42-03:15] [Vol: 75%] [S] [R] [MUTE] [▶NEXT×3] [◴ 5:00]
```

- `►` = reproduciendo, `⏸` = pausa
- `[MM:SS-MM:SS]` = tiempo actual - duración
- `[Vol: XX%]`
- `[S]` = shuffle activo
- `[R]` = repeat activo
- `[▶NEXT×N]` = N archivos consumibles en cola (tecla `N`)
- `[MUTE]` = mute activo (tecla `m`)
- `[◴ M:SS]` = sleep timer activo; `[◴ FIN]` = expirado. `t` togglea on/off.

## Controles globales

| Acción                | Tecla                 |
|-----------------------|-----------------------|
| Cambiar vista         | `0`-`4`               |
| Play / Pause          | `Space`               |
| Stop                  | `s`                   |
| Siguiente             | `n`                   |
| Anterior              | `p`                   |
| Seek -5s / +5s        | `h` / `l`             | (en Now Playing)
| Volumen + / -         | `+` / `-`             |
| Shuffle toggle        | `r`                   |
| Repeat toggle         | `R`                   |
| Queue consumible      | `N`                   | (inserta al frente)
| Queue permanente      | `A`                   | (append al final)
| Sleep timer toggle    | `t`                   |
| Mute                  | `m`                   |
| Ir a tiempo           | `g`                   | (en Now Playing)
| Búsqueda global       | `/`                   |
| Ayuda                 | `?` / `F1`            |
| Salir (guarda todo)   | `q`                   |
| Esc                   | Cancela               |

## Controles por vista

### Explorador (vista 1)

| Acción                            | Tecla                  |
|-----------------------------------|------------------------|
| Moverse                           | `↑↓` / `jk`           |
| Página arriba/abajo               | `PgUp` / `PgDn`       |
| Ir al inicio/fin                  | `g` / `G`             |
| Reproducir directo (sin playlist) | `Enter`                |
| Añadir a playlist + reproducir    | `a`                    |
| Cola consumible (N)               | `N`                    |
| Cola permanente (A)               | `A`                    |
| Volver                            | `←` / `h` / `Bksp`    |
| Ir al home                        | `~`                    |

### Playlist (vista 2)

| Acción                    | Tecla                  |
|---------------------------|------------------------|
| Moverse                   | `↑↓`                  |
| Reproducir / saltar       | `Enter`                |
| Quitar canción            | `d`                    |
| Limpiar playlist          | `x`                    |
| Reordenar (abajo/arriba)  | `J` / `K`              |
| Crear nueva               | `C`                    |
| Renombrar                 | `E`                    |
| Eliminar                  | `D` (confirma)         |
| Anterior / sig. playlist  | `[` / `]`              |
| Filtro en vivo            | `/` → query → `Enter` reproduce, `Esc` sale |
| Cola consumible (N)       | `N`                    |
| Cola permanente (A)       | `A`                    |

### Now Playing (vista 3)

Muestra: `► PLAY` / `⏸ PAUSE`, título, artista — álbum, barra de progreso,
duración, volumen + toggles S/R/MUTE + sleep timer.

| Acción                       | Tecla                                         |
|------------------------------|-----------------------------------------------|
| Seek -5s / +5s               | `h` / `l`                                     |
| Ir a tiempo                  | `g` → `← →` campo, `↑ ↓` valor, `Enter` salta, `Esc` sale |
| Ver/ocultar Lista            | `Tab`                                         |

Footer: `[Space] ▶||  [s] ◼  [n] ►►  [p] ◄◄  [h/l] ±5s  [g] Ir a  [Tab] Lista`

### Lista (Tab en vista 3)

La "compactera"/slot de reproducción. Misma interfaz que Playlist (vista 2):
metadatos, íconos, navegación idéntica.

| Acción                       | Tecla                  |
|------------------------------|------------------------|
| Moverse                      | `↑↓` / `jk`           |
| Reproducir item              | `Enter`                |
| Poner como next (consumir)   | `N`                    | (mueve item al frente, se borra al reproducir)
| Quitar item                  | `d`                    |
| Limpiar toda la Lista        | `x`                    |
| Reordenar                    | `J` / `K`              |
| Guardar como playlist persistente | `s`               |
| Ir al inicio / fin           | `g` / `G`              |
| Página arriba / abajo        | `PgUp` / `PgDn`        |
| Siguiente / anterior pista   | `n` / `p`              |
| Volumen + / -                | `+` / `-`              |
| Cerrar Lista                 | `Tab` / `Esc`          |

- `♪` = item permanente (queda al reproducir)
- `♪ [N]` = item consumible (se borra al reproducir)
- `►` = item actual en reproducción

Las teclas `N` y `A` en Explorador/Playlist:
- `N` → inserta al frente como consumible (`[N]`)
- `A` → agrega al final como permanente

Desde Now Playing (sin Lista) también funcionan para agregar lo que esté bajo
el cursor en Explorador/Playlist.

### Búsqueda (vista 4)

| Acción    | Tecla                |
|-----------|----------------------|
| Escribir  | cualquier imprimible |
| Borrar    | `Backspace`          |
| Reproducir directo | `Enter`    |
| Cancelar  | `Esc`                |

Busca recursivamente desde `current_dir` con `os.scandir` (límite 200
resultados). `Enter` ejecuta `_play_file_direct` (no toca la playlist
persistente).

### Config (vista 0)

| Acción              | Tecla                |
|---------------------|----------------------|
| Moverse             | `↑↓`                |
| Cambiar valor       | `← →`               |
| Abrir keybindings   | `Enter` / `F2`      |
| Editar dir. música  | `/` (abre buscador) |

Items: music_dir, volume, theme, *(colores si theme=custom)*, sleep_timer,
keybinding_mode [Default/Custom].

### Keybindings (vista 5)

| Acción                   | Tecla           |
|--------------------------|-----------------|
| Moverse                  | `↑↓`           |
| Cambiar modo             | `← →` (Default / Custom) |
| Reasignar tecla          | `Enter` en una acción |
| Volver                   | `Esc`           |

## Lista / Slot de reproducción (`temp_queue`)

Atributo `PlayerApp.temp_queue: list[tuple[str, bool]]`.

Cada item es una tupla `(path: str, consumable: bool)`.

- `temp_queue` es el **slot activo** del reproductor (la "compactera")
- Idéntica interfaz a la playlist persistente
- Se vacía al elegir otra playlist (`Enter` en vista 2), al reproducir
  directo (`Enter` en explorador), o al limpiar (`x`)

| Tecla | Comportamiento                                       | Uso                   |
|-------|------------------------------------------------------|-----------------------|
| `N`   | `insert(0, (path, True))` — al frente, consumible    | "suena ya, una vez"   |
| `A`   | `append((path, False))` — al final, permanente        | "queda en la lista"   |

**`_auto_next_temp`** (en `PlayerApp`):
1. Si el primer item es **consumible** → `pop(0)`, reproduce, descarta
2. Si no, avanza `tq_playhead` al siguiente item **permanente**
3. Si `temp_queue` terminó → `tq_playhead = -1`, cae a `audio.auto_next(playlist)`
4. Con `Enter` en la Lista: consumible se popea y reproduce; permanente se
   reproduce y queda con `tq_playhead` apuntándolo

**Indicadores visuales:**
- Status bar: `[▶NEXT×N]` = solo items consumibles
- Vista Lista (Tab): `♪`=permanente, `♪ [N]`=consumible, `►`=reproduciendo
- Playlist (vista 2): tag `[NEXT]` si el path está en temp_queue

**Auto-play al añadir primero:** si `temp_queue` está vacía y no hay nada
sonando, tanto `N` como `A` arrancan el primer item automáticamente.

**s (guardar):** guarda toda la temp_queue como playlist persistente.

## AudioEngine (`player/audio.py`)

- `play_file(path)` — reproduce liberando media anterior
- `toggle_play_pause()` / `stop()`
- `next(playlist)` / `prev(playlist)` — shuffle-aware, repeat-aware
- `auto_next(playlist)` — solo playlist persistente (temp_queue se maneja en app.py)
- `is_ended()` — consulta si VLC.State.Ended
- `set_volume(vol)` — 0-100. Vol>0 resetea `muted=False`
- `mute`/`unmute`/`toggle_mute` — con `_prev_volume` para restore
- Sleep timer: `set_sleep_timer(min)`, check en loop principal, stop al expirar

## Metadatos ID3

`player/metadata.py` — `MetadataCache` con dict interno. Lee artista, álbum,
título vía `mutagen.File`. Cachea resultados por path. Fallo silencioso.

Mostrados en Now Playing y Playlist.

## Temas de color

Definidos en `player/config.py`:

| Tema            | Marco  | Texto  | Destacar | Nav     |
|-----------------|--------|--------|----------|---------|
| `clasico`       | CYAN   | WHITE  | YELLOW   | CYAN    |
| `mono`          | WHITE  | WHITE  | WHITE    | WHITE   |
| `calido`        | YELLOW | WHITE  | RED      | RED     |
| `alto_contraste`| MAGENTA| WHITE  | GREEN    | MAGENTA |
| `custom`        | (usuario) |       |          |         |

Pares: `PAIR_MARCO=1`, `PAIR_TEXTO=2`, `PAIR_DESTACAR=3`, `PAIR_NAV=4`.

En Config, si theme=custom aparecen 4 ítems editables con `← →` para elegir
color de 8 colores ANSI. El orden en Config es: theme, marco, texto, destacar,
nav (inmediatamente después de theme).

## Keybindings personalizables

`player/keybindings.py`:

- `DEFAULT_BINDINGS` — dict `{accion: keycode}`
- `BINDABLE_ACTIONS` — lista ordenada
- `RESERVED_KEYS` — set de teclas no bindeables
- `resolve_conflicts(dict) -> dict`
- `build_lookup(dict) -> dict` — `{keycode: accion}` para dispatch O(1)
- `key_name(keycode) -> str` — nombre legible

Dos modos: `default` (hardcoded) y `custom` (desde config.json). UI en vista 5:
`← →` togglea modo, en custom se listan acciones y `Enter` captura nueva tecla.
El indicador de modo es `[Default]`/`[Custom]`.

Acciones bindeables: play_pause, stop, next, prev, volume_up, volume_down,
shuffle, repeat, help, play_next, queue_add, sleep_timer, mute.

## Persistencia

### `~/.config/player/config.json`
```json
{
  "music_dir": "~/Music",
  "volume": 50,
  "theme": "clasico",
  "custom_colors": {"marco": "Cian", ...},
  "sleep_timer_minutes": 30,
  "keybinding_mode": "default",
  "keybindings": {}
}
```

### `~/.config/player/playlist.json`
```json
{
  "active": "default",
  "playlists": [
    {"name": "default", "songs": [["name","/path"], ...]},
    {"name": "rock", "songs": [...]}
  ]
}
```

Se guarda en cada append, remove, clear, create, rename, delete y al salir.

## Prompt / diálogos

Overlay centrado con borde (`╭─╮││╰─╯`). Label + input de hasta 60 chars.
Enter confirma, Esc cancela.

## Arquitectura del código

### `PlayerApp` (`player/app.py`, ~1103 LOCs)

**Init:**
- Carga config, playlist, inicia VLC, arma dispatch dicts, colores

**Loop principal `run()`:**
- `check_playback_end(playlist, temp_queue)`
- `check_sleep_timer()`
- `getch()` → `_handle_key()` o `_handle_prompt()`
- `_draw()`
- `time.sleep(0.05)` — flat 50ms

**Manejo de teclas:**
1. `_handle_key_help` → toggle help
2. `_handle_key_mode_specific` → temp queue, goto, search, playlist filter
3. HJKL mapping
4. `_handle_key_view_switch` → `0`-`4` y `/` como global
5. vista 5 → `_handle_keybindings`
6. `_handle_key_global` → custom lookup + defaults hardcoded
7. `_view_handlers[id](key)` → dispatch por vista

**Dibujado:**
1. `erase()`
2. `_view_drawers[id](self, h, w)`
3. `_draw_status(h, w)`
4. `ui.draw_prompt()` si prompt_mode, sino `ui.draw_nav()`
5. `ui.draw_help()` si show_help
6. cursor positioning + `refresh()`

## Flujo de datos

```
run()
 ├── audio.check_playback_end(playlist, temp_queue)
 ├── audio.check_sleep_timer()
 ├── key = stdscr.getch()
 ├── if key: _handle_key(key)
 │    ├── _handle_key_help
 │    ├── _handle_key_mode_specific (temp_queue, goto, search, filter)
 │    ├── HJKL → curses keys
 │    ├── _handle_key_view_switch (0-4, /)
 │    ├── _handle_keybindings (vista 5)
 │    ├── _handle_key_global (bindings + defaults)
 │    └── _view_handlers[id](key)
 └── _draw()
      ├── _view_drawers[id](self, h, w)
      ├── _draw_status
      ├── draw_prompt / draw_nav
      └── draw_help (if active)
```

## Qué falta (pendientes)

| Feature | Complex. | Estado |
|---------|----------|--------|
| F2 — Ecualizador gráfico (VLC API) | Alta | ▢ |
| F4 — Exportar playlist a M3U/PLS | Baja | ▢ |
| F7 — Soporte mouse (curses clics) | Baja | ▢ |
| F8 — Cover art (chafa/viu) | Media | ▢ |
| F11 — Modo radio (URL/stream) | Media | ▢ |
