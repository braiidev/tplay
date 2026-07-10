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
├── favorites.py       # Persistencia de favoritos (favorites.json)
├── file_utils.py      # list_dir, time_str, ext_label, is_url, is_video_file
├── handlers/          # Manejadores de teclas por vista (package)
│   ├── __init__.py    # Re-exporta todo (65 símbolos)
│   ├── shared.py      # _prompt, _toast, _confirm, _clamp_scroll, _play_file_direct, _toggle_favorite, _rename, _open_tag_editor, update/restart
│   ├── listen.py      # handle_listen, handle_stack_view, handle_goto
│   ├── explorer.py    # handle_explorer, file ops (delete, mkdir, rename, copy/move), explorer filter, multi-select
│   ├── playlist.py    # handle_playlist, playlist filter, playlist CRUD (save/switch/create/delete/rename)
│   ├── history.py     # handle_history, history ops (add/remove/clear)
│   ├── config_view.py # handle_config, keybinding editor (handle_keybindings), theme/color/int cycling
│   ├── radio.py       # handle_radio, add/edit/delete/export radios
│   └── favorites.py   # handle_favorites (d=remove, Enter=play, a/A=stack, f=toggle)
├── keybindings.py     # Mapa de teclas, resolución de conflictos
├── metadata.py        # MetadataCache — cache LRU de mutagen
├── playlist.py        # Carga/guarda playlists JSON
├── radios.py          # Carga/guarda radios JSON
├── stack.py           # Stack, StackItem — cola de reproducción
├── state.py           # Snapshot/restore para undo/redo + state.json (stack persistente)
├── ui.py              # safe_addstr, draw_box, draw_dialog, draw_nav, draw_status, draw_help
└── views.py           # draw_listen, draw_explorer, draw_playlist, draw_history, draw_config, draw_meta_editor, draw_favorites
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

## Estado actual (v1.5.27)

### Completado (session actual)
- **B2** — undo unificado (file_undo integrado en snapshots)
- **B3/B4** — stack persistente entre sesiones (state.json: stack_items, playhead, shuffle, repeat, volumen)
- **A2** — KEY_RESIZE handling (resizeterm + clear + refresh)
- **A1** — stderr redirigido a `~/.config/tplay/data/error.log` (append)
- **A3** — os.makedirs lazy, solo en save()
- **A4** — handlers.py partido en handlers/ package (8 archivos por vista)
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
- **C4** — _restart_app ruta incorrecta tras split en handlers/ package → usa `app._repo_dir` en vez de `__file__`
- **U6** — toast: duración 3→40 ticks, dismiss con Enter/Space/Esc
- **L1-L4**, **L2.7**, **E1-E5** — auditorías previas
- **M1-M3** — draw_item_row unificada, dialog system unificado, mypy strict
- **F5** — Multi-select Explorer (Tab marca, Enter carga marcados, ✓ visual)
- **F6** — Favoritos: vista 6 (nueva), f/F desde Explorer, d desde Favoritos, persistencia JSON
- **F7** — f toggle global: `f` add/remove favoritos en todas las vistas (Listen, Stack, Explorer, Playlist, History, Radio, Favoritos)

### Pendiente
- ~~**L5** — covers/metadata errors~~ ❌ sin acción
- **F2** — Ecualizador gráfico (VLC API)
- **F4** — Exportar/Importar M3U/PLS ← ✅ hecho (M3U extendido, `X` export, `O` import)
- **F8** — Cover art (chafa/viu) ← descartado por ahora
- **F28** — Streaming/Radio (URL, M3U, radios guardadas) ← ✅ hecho (vista Radios con `5`, persistente, historial automático)

### Últimos tags de versión
- v1.5.27 — feat: f toggle favoritos global (Listen, Stack, Explorer, Playlist, History, Radio, Favoritos)
- v1.5.26 — feat: F5 multi-select Explorer + F6 Favoritos (vista 6, f/F, d, persistencia JSON)
- v1.5.25 — feat: F2 speed control (w/W ±0.25x, 0.25x–4.0x, persistente en state.json)
- v1.5.23 — fix: Stack d con confirmación, audio para al último item, eliminar helper [o] obsoleto
- v1.5.22 — feat: ←/→ para mover cursor en Explorer filter, Playlist filter y Meta editor
- v1.5.21 — feat: filtros con cursor visual, hjk global→Listen, s/S consistente, radio e/E cyclic, dir picker, KEYBINDINGS.md
- v1.5.12 — feat: F4 import M3U/PLS desde Explorer
- v1.5.11 — feat: F4 import M3U/PLS (tecla O) — revertido
- v1.5.10 — fix: C4 _restart_app ruta incorrecta tras A4 → app._repo_dir
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
    ├── favorites.json  # Favoritos (path + name, lista persistente)
    ├── error.log       # Stderr de VLC/mutagen (append)
    ├── playlists/      # Playlists guardadas
    └── radios.json     # Radios guardadas
```
