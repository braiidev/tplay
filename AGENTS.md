# tplay — Guía del proyecto

## Stack
- Python 3.12 + curses + python-vlc + mutagen
- Sin frameworks web, es TUI pura

## Arquitectura

```
player/
├── app.py          # Clase PlayerApp — loop principal, diálogos, dibujo
├── audio.py        # AudioEngine — wrapper de vlc
├── config.py       # Colores, temas, constantes de UI
├── file_utils.py   # list_dir, time_str, ext_label, is_url, is_video_file
├── handlers.py     # Manejadores de teclas por vista (~55 funciones)
├── keybindings.py  # Mapa de teclas, resolución de conflictos
├── metadata.py     # MetadataCache — cache LRU de mutagen
├── playlist.py     # Carga/guarda playlists JSON
├── stack.py        # Stack, StackItem — cola de reproducción
├── state.py        # Snapshot/restore para undo/redo
├── ui.py           # safe_addstr, draw_box, draw_dialog, draw_nav, draw_status, draw_help
└── views.py        # draw_listen, draw_explorer, draw_playlist, draw_history, draw_config, draw_meta_editor
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

## Estado actual (v1.5.2)

### Completado
- L1-L4 (crashes, bugs visuales, UX, sugerencias) — ✅ en AUDIT_SPEC.md
- L2.7 (update notification tapa borde) — ✅ resuelto con margen `w - len(msg) - 1`
- E1-E5 — ✅ bugs corregidos
- M1 — ✅ draw_item_row() unificada
- M2 — ✅ 9 vars de diálogo unificadas en self.dialog dict
- M3 — ✅ mypy strict, 0 errores en 13 archivos

### Pendiente
- L5 (covers/metadata errors) — pendiente discusión
- F2 (ecualizador), F4 (exportar M3U), F8 (cover art), F28 (streaming/radio)

## Dialog system

Un solo `self.dialog: dict | None` con tipos:
- `{"type": "confirm", "label": str, "callback": Callable}`
- `{"type": "prompt", "label": str, "buf": str, "callback": Callable, "scroll": int}`
- `{"type": "dest", "path": str, "mode": str}`

Se maneja desde `_handle_dialog_key()` en app.py y se dibuja unificado en `_draw()`.
