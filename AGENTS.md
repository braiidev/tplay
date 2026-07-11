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

## Estado actual (v1.5.45)

### Completado (session actual)
- **B1** — History `count` siempre es 1 → preserva/incrementa
- **B2** — Playlist Enter usa `playlist_cursor`
- **B3** — Favorites usa `stack.append`/`insert_after_current`
- **B4** — `_play_folder`/`_play_marked` llaman `_push_snapshot()`
- **B5** — `_safe_tag()` helper en metadata.py
- **B6** — `playlist` property simplificada (sin validación per-access)
- **B7** — Confirm dialog: keys `s/S/y/Y` instant + Enter con pausa 150ms
- **B8** — ~~`_apply_updates` hard reset~~ REVERTIDO (end users no tienen local changes)
- **B9** — Config scroll clamp = `h-5 if h<16 else h-6` consistente
- **B10** — Explorer back-nav en directorios vacíos (before `if not entries`)
- **B11** — Status bar row descontada en todos los handlers
- **A1** — stderr redirigido a error.log
- **A2** — KEY_RESIZE handling
- **A3** — os.makedirs lazy
- **A4** — handlers.py → package (8 archivos)
- **A5** — playlist property valida entries inválidas
- **A6** — deferred imports sin riesgo circular
- **U1** — PgDn/PgUp/g/G en Playlist
- **U2** — update check async
- **U3** — toast en shuffle/repeat toggle
- **U4** — confirm acepta 's' y 'y'
- **U5** — sleep timer resetea al stop manual
- **U6** — toast 40 ticks, dismiss con Enter/Space/Esc
- **U7** — undo/redo archivos toast con razón de error
- **U8** — metadata save toast + permanencia en editor
- **P1** — `os.scandir()` reemplaza `os.listdir`+stat
- **P2** — scroll clamping redundante eliminado
- **P3** — playlist.py importa CONFIG_DIR de config
- **E1** — Radio emoji → `[R]`
- **E2** — Controles Listen responsive (cw dinámico)
- **E3** — Time separator `-` → `/`
- **N1-N5** — limpieza numbers, magic, compact shadow
- **C4** — _restart_app ruta con `app._repo_dir`
- **L1-L4**, **L2.7**, **E1-E5** — auditorías previas
- **M1-M3** — draw_item_row unificada, dialog system, mypy strict
- **F5** — Multi-select Explorer
- **F6** — Favoritos vista 6, f/F, d, persistencia JSON
- **F7** — f toggle global en todas las vistas

### Nuevos (última sesión v1.5.38-v1.5.45)
- **S5** — 5to par de colores OVERLAY (config.py, themes, apply_theme)
- **S6** — Redistribución UI: status/dialog→OVERLAY, filter→OVERLAY, config active tab→OVERLAY
- **S7** — Help section headers → NAV (antes ACCENT)
- **S8** — Radio REVERSE gap corregido (fill entre name y URL)
- **S9** — Pila hints → NAV (antes TEXTO)
- **S10** — Keybindings [Esc] Volver → NAV
- **S11** — Playlist carousel: `◀ [name] ▶` cyclic, sin arrows si 1 sola
- **S12** — Config carousel: `[prev | current | next]` cyclic
- **S13** — Help carousel: `[prev | current | next]` cyclic + footer hints
- **S14** — `[]` navegan pestañas en todas las vistas (Playlist, Config, Help)
- **S15** — Playlist: `h/l` ya no cambian playlist (solo `[]`)
- **S16** — Help: `[]` agregado para tabs (antes solo `h/l`)
- **S17** — Help scroll clamp corregido: `total - list_h` (antes `total - 1`)
- **S18** — Full-row cursor highlight: fill con REVERSE entre text y duration
- **S19** — Help tab bar dentro del marco (reemplaza borde superior `┌─┐` → `│ tab │`)
- **S20** — Meta edit editing: `h/l` insertan chars en vez de mover cursor

### Pendiente
- ~~**L5** — covers/metadata errors~~ ❌ sin acción
- **F2** — Ecualizador gráfico (VLC API)
- **F4** — Exportar/Importar M3U/PLS ← ✅ hecho
- **F8** — Cover art (chafa/viu) ← descartado
- **F28** — Streaming/Radio ← ✅ hecho

### Últimos tags de versión
- v1.5.45 — fix: meta_edit editing — h/l insertan chars en vez de mover cursor
- v1.5.44 — feat: full-row cursor highlight + Help tab bar inside marco
- v1.5.43 — fix: Playlist carousel simplificado ◀[name]▶ + Help scroll clamp corregido
- v1.5.42 — fix: [] navegan pestañas en todas las vistas — playlist ya no usa h/l para tabs
- v1.5.41 — feat: Playlist + Config carousel tabs — cyclic, ◀[name]▶ / [prev|current|next]
- v1.5.40 — feat: Help carousel tabs + hints NAV consistentes en todas las vistas
- v1.5.39 — fix: Radio REVERSE gap, Pila hints con NAV color
- v1.5.38 — feat: 5to par de colores OVERLAY — redistribución UI + COLOR_SPEC.md
- v1.5.37 — refactor: estandarización de rows — margenes, metadata, duración, Radio [R]
- v1.5.36 — style: E1-E3 — [R] icon para streams, controles Listen responsive, time separator '/'
- v1.5.35 — refactor: P1-P3 — os.scandir(), scroll clamping redundante, playlist CONFIG_DIR import
- v1.5.34 — fix: U2-U3 — undo/redo archivos toast + metadata save toast y permanencia en editor
- v1.5.33 — fix: B10-B11 — explorer back-nav en directorios vacíos + status bar row descontada en handlers
- v1.5.27 — feat: f toggle favoritos global (Listen, Stack, Explorer, Playlist, History, Radio, Favoritos)
- v1.5.26 — feat: F5 multi-select Explorer + F6 Favoritos (vista 6, f/F, d, persistencia JSON)
- v1.5.25 — feat: F2 speed control (w/W ±0.25x, 0.25x–4.0x, persistente en state.json)
- v1.5.23 — fix: Stack d con confirmación, audio para al último item, eliminar helper [o] obsoleto
- v1.5.22 — feat: ←/→ para mover cursor en Explorer filter, Playlist filter y Meta editor
- v1.5.21 — feat: filtros con cursor visual, hjk global→Listen, s/S consistente, radio e/E cyclic, dir picker, KEYBINDINGS.md
- v1.5.12 — feat: F4 import M3U/PLS desde Explorer
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
