# BUSINESS — tplay

## Reglas de negocio

### Reproducción
1. **Stack como cola central**: toda reproducción pasa por `Stack`
2. **Playhead**: índice del item actual (-1 = vacío)
3. **Modos por item**: `normal`, `repeat_once`, `repeat_inf`
4. **Shuffle**: elige siguiente aleatorio excluyendo actual
5. **Repeat global**: al finalizar, vuelve al inicio (0)
6. **Sleep timer**: monitorea en cada tick, auto-stop al expirar

### Favoritos
1. **Toggle global**: tecla `f` en cualquier vista
2. **Persistencia**: favorites.json (path + name)
3. **Reproducción**: `Enter` reproduce, `a/A` agrega al stack
4. **Eliminación**: `d` con confirmación

### Playlists
1. **Multi-playlist**: dict[str, list[tuple[name, path]]]
2. **Actividad**: una playlist activa a la vez
3. **Importación**: soporta M3U y PLS
4. **Navegación**: `[]` cambia entre playlists

### Explorer
1. **Filtros**: búsqueda por nombre con cursor visual
2. **Multi-select**: modo `m` para selección múltiple
3. **Operaciones**: delete, mkdir, rename, copy, move
4. **Undo/Redo**: snapshots del estado antes de operaciones destructivas

### Historial
1. **Capacidad**: últimos 100 items
2. **Conteo**: preserva/incrementa `count`
3. **Persistencia**: history.json

### Undo/Redo
1. **Snapshots**: guarda estado del stack antes de operaciones
2. **Razón**: cada undo/redo muestra toast con razón del cambio
3. **Persistencia**: state.json (solo durante sesión)

### Configuración
1. **Temas**: 5 predefinidos + custom
2. **Keybindings**: default + custom por tecla
3. **Persistencia**: config.json
4. **Volumen**: 0-100, persistente entre sesiones
5. **Rate**: 0.25x-4.0x, persistente en state.json

### Radio/Streaming
1. **Almacenamiento**: radios.json (name + url)
2. **Reproducción**: VLC maneja streams HTTP/RTMP/etc.
3. **Exportación**: soporta exportar a archivo

### Diálogos
1. **Un solo diálogo activo**: `self.dialog: dict | None`
2. **Tipos**: confirm, prompt, dest
3. **Confirm**: acepta s/S/y/Y + Enter
4. **Prompt**: buffer de texto con scroll

### UI Rules
1. **Mínimo terminal**: 80x24
2. **Resize handling**: KEY_RESIZE re-calcula dimensiones
3. **Status bar**: siempre visible (1 row)
4. **Nav bar**: configurable (ui_navbar)
5. **Compact mode**: configuración alternativa
