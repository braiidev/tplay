# tplay — Guía del proyecto

## Stack
- Python 3.12 + curses + python-vlc + mutagen
- Sin frameworks web, es TUI pura
- mypy strict

## Arquitectura

```
player/
├── app.py             # Clase PlayerApp — loop, diálogos, draw
├── audio.py           # AudioEngine — wrapper vlc, sleep timer, stderr→error.log
├── config.py          # Colores, temas, constantes UI (lazy mkdir)
├── file_utils.py      # list_dir, time_str, ext_label, is_url, is_video_file
├── handlers/          # Manejadores de teclas por vista (package)
│   ├── __init__.py    # Re-exporta todo (60 símbolos)
│   ├── shared.py      # _prompt, _toast, _confirm, _clamp_scroll, _play_file_direct, _rename, _open_tag_editor, update/restart
│   ├── listen.py      # handle_listen, handle_stack_view, handle_goto, _add_url_cb
│   ├── explorer.py    # handle_explorer, file ops (delete, mkdir, rename, copy/move), explorer filter
│   ├── playlist.py    # handle_playlist, playlist filter, playlist CRUD (save/switch/create/delete/rename)
│   ├── history.py     # handle_history, history ops (add/remove/clear)
│   └── config_view.py # handle_config, keybinding editor (handle_keybindings), theme/color/int cycling
├── keybindings.py     # Mapa de teclas, resolución de conflictos
├── metadata.py        # MetadataCache — cache LRU de mutagen
├── playlist.py        # Carga/guarda playlists JSON
├── stack.py           # Stack, StackItem — cola de reproducción
├── state.py           # Snapshot/restore para undo/redo + state.json (stack persistente)
├── ui.py              # safe_addstr, draw_box, draw_dialog, draw_nav, draw_status, draw_help
└── views.py           # draw_listen, draw_explorer, draw_playlist, draw_history, draw_config, draw_meta_editor
```

## Convenciones de tipado (mypy strict)

- **strict = true** en `pyproject.toml`
- `from __future__ import annotations` en todos los archivos
- TYPE_CHECKING guard para imports cíclicos: `if TYPE_CHECKING: from player.app import PlayerApp`
- Todos los `__init__` tienen `-> None`
- Todos los métodos tienen parámetros y return tipados
- Tipos genéricos siempre con argumentos: `list[int]`, `dict[str, Any]`, `tuple[str, bool, str]`
- `explorer_filtered` y `playlist_filtered` son `list[int]` (índices, no datos)
- `self.dialog` es `dict[str, Any] | None`
- Para `mutagen.File` usar `# type: ignore[attr-defined]`
- `# type: ignore` solo como último recurso

## Estado actual (v1.5.9)

### Completado (session actual)
- **B2** — undo unificado (file_undo integrado en snapshots)
- **B3/B4** — stack persistente entre sesiones (state.json: stack_items, playhead, shuffle, repeat, volumen)
- **A2** — KEY_RESIZE handling (resizeterm + clear + refresh)
- **A1** — stderr redirigido a `~/.config/tplay/data/error.log` (append)
- **A3** — os.makedirs lazy, solo en save()
- **A4** — handlers.py partido en handlers/ package (7 archivos por vista)
- **A5** — playlist property valida entries inválidas (log a stderr)
- **A6** — deferred imports mantenidos (sin riesgo circular)
- **U1** — PgDn, PgUp, g, G en vista Playlist
- **U2** — update check async (threading.Thread), UI sin bloqueo
- **U3** — toast en shuffle/repeat toggle
- **U4** — confirm acepta 's' y 'y'
- **U5** — sleep timer resetea al hacer stop manual
- **N1** — min(w-2, w-2) → w-2
- **N2** — ord("\n")/10/13 unificado a (10, 13)
- **N3** — scroll-clamping → _clamp_scroll() helper en shared
- **N4** — magic numbers (1,5,6) limpiado en ui.py
- **N5** — compact shadow → meta_cpt en _draw()
- **L1-L4**, **L2.7**, **E1-E5** — auditorías previas
- **M1-M3** — draw_item_row unificada, dialog system unificado, mypy strict

### Pendiente
- **L5** — covers/metadata errors (pendiente discusión)
- **F2** — Ecualizador gráfico (VLC API)
- **F4** — Exportar playlist a M3U/PLS
- **F8** — Cover art (chafa/viu)
- **F28** — Streaming/Radio (URL, M3U, radios guardadas)

### Últimos tags de versión
- v1.5.9 — cleanup N1-N5
- v1.5.8 — feat: U2-U5 (update async, toast, s/y confirm, sleep timer reset)
- v1.5.7 — feat: U1 PgDn/PgUp g/G en Playlist
- v1.5.6 — refactor: A4 handlers.py → package + A5/A6
- v1.5.5 — fix: A1 stderr→error.log + A3 lazy mkdir
- v1.5.4 — fix: A2 KEY_RESIZE resize handling
- v1.5.3 — feat: B3/B4 stack persistente
- v1.5.2 — fix: B2 undo unificado

## Dialog system

Un solo `self.dialog: dict | None` con tipos:
- `{"type": "confirm", "label": str, "callback": Callable}`
- `{"type": "prompt", "label": str, "buf": str, "callback": Callable, "scroll": int}`
- `{"type": "dest", "path": str, "mode": str}`

Se maneja desde `_handle_dialog_key()` en app.py y se dibuja unificado en `_draw()`.

## Bundle de configuración

```
~/.config/tplay/
└── data/
    ├── config.json     # Configuración (volumen, tema, etc.)
    ├── state.json      # Estado de sesión (stack, playhead, shuffle, repeat, posición)
    ├── history.json    # Historial de reproducción (últimos 100)
    ├── error.log       # Stderr de VLC/mutagen (append)
    └── playlists/      # Playlists guardadas

