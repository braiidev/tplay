# ARCH — tplay

## Arquitectura general

```
tplay/
├── app.py                  # Entry point, ejecuta PlayerApp.run()
├── player/
│   ├── __init__.py         # Package marker
│   ├── app.py              # PlayerApp — loop principal, diálogos, draw
│   ├── audio.py            # AudioEngine — wrapper VLC, sleep timer
│   ├── config.py           # Colores, temas, constantes UI
│   ├── favorites.py        # Persistencia de favoritos (JSON)
│   ├── file_utils.py       # Utilidades de archivos (list_dir, time_str, etc.)
│   ├── handlers/           # Manejadores de teclas por vista
│   │   ├── __init__.py     # Re-exporta 65 símbolos
│   │   ├── shared.py       # Helpers compartidos (_prompt, _toast, _confirm, etc.)
│   │   ├── listen.py       # handle_listen, handle_stack_view, handle_goto
│   │   ├── explorer.py     # handle_explorer, file ops, filter, multi-select
│   │   ├── playlist.py     # handle_playlist, playlist filter, CRUD
│   │   ├── history.py      # handle_history, history ops
│   │   ├── config_view.py  # handle_config, keybinding editor, cycling
│   │   ├── radio.py        # handle_radio, add/edit/delete/export
│   │   └── favorites.py    # handle_favorites (d=remove, Enter=play, a/A=stack)
│   ├── keybindings.py      # Mapa de teclas, resolución de conflictos
│   ├── metadata.py         # MetadataCache — cache LRU de mutagen
│   ├── playlist.py         # Carga/guarda playlists JSON
│   ├── radios.py           # Carga/guarda radios JSON
│   ├── stack.py            # Stack, StackItem — cola de reproducción
│   ├── state.py            # Snapshot/restore + state.json
│   ├── ui.py               # safe_addstr, draw_box, draw_dialog, draw_nav, etc.
│   └── views.py            # draw_listen, draw_explorer, draw_playlist, etc.
├── pyproject.toml          # mypy strict config
├── requirements.txt        # python-vlc, mutagen
├── install.sh              # Script de instalación
├── AGENTS.md               # Índice AENV (este archivo)
├── KEYBINDINGS.md          # Documentación de teclas
├── COLOR_SPEC.md           # especificación de colores
├── COMPACT_SPEC.md         # especificación de modo compacto
└── TODO.md                 # Lista de tareas (legacy)
```

## Flujo principal

```
app.py main()
  └─> PlayerApp(cwd).run()
        ├─> AudioEngine()          # Inicializa VLC
        ├─> config.load()          # Carga config.json
        ├─> state.load_state()     # Carga state.json
        ├─> stack.load_items()     # Restaura stack
        └─> mainloop
              ├─> _handle_key(key)  # Dispatch a handler según vista
              │     └─> handle_xxx(app, key)  # Handler específico
              ├─> _draw()           # Renderiza UI
              │     └─> draw_xxx(app, ...)  # Vista específica
              └─> _tick()           # Monitorea sleep timer, estado VLC
```

## Vistas (índices)
| Índice | Vista | Handler | Draw |
|--------|-------|---------|------|
| 0 | Listen | handle_listen | draw_listen |
| 1 | Stack View | handle_stack_view | draw_listen (variación) |
| 2 | Explorer | handle_explorer | draw_explorer |
| 3 | Playlist | handle_playlist | draw_playlist |
| 4 | History | handle_history | draw_history |
| 5 | Config | handle_config | draw_config |
| 6 | Favorites | handle_favorites | draw_favorites |
| 7 | Radio | handle_radio | draw_radio |
| 8 | Meta Editor | (desde handle_listen) | draw_meta_editor |
| 9 | Help | (navegación) | draw_help |

## Dependencias externas
- **python-vlc**: wrapper de libVLC para reproducción de audio/video
- **mutagen**: lectura de metadata de archivos de audio
- **curses**: stdlib de Python para TUI

## Patrones de diseño
1. **Handler pattern**: cada vista tiene su función handler que recibe (app, key)
2. **Dialog system**: dict unificado para confirm/prompt/dest
3. **State snapshot**: undo/redo con copias del stack
4. **Lazy mkdir**: `os.makedirs(exist_ok=True)` al guardar
5. **stderr redirect**: VLC/mutagen errors → error.log
6. **TYPE_CHECKING guard**: imports circulares evitados con `if TYPE_CHECKING`
