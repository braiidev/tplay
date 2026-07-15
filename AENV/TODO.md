# TODO — tplay

## Pendiente para próxima sesión

### #4: Download History
**Archivo propuesto**: `~/.config/tplay/data/downloads.json`
```json
[
  {
    "title": "Beethoven Symphony",
    "path": "/home/user/Music/Beethoven Symphony.mp3",
    "platform": "YouTube",
    "url": "https://youtube.com/watch?v=xxx",
    "date": "2026-07-15T12:00:00",
    "format": "audio",
    "quality": "192"
  }
]
```
**Tecla**: `H` en Web Explorer → lista de descargas
**Funciones**:
- Lista de descargas con fecha/título
- Re-descargar si existe
- Eliminar de historial

### #5: Stream Replay
**Archivo propuesto**: `~/.config/tplay/data/streams.json`
```json
[
  {
    "title": "Beethoven Symphony",
    "webpage_url": "https://youtube.com/watch?v=xxx",
    "platform": "YouTube",
    "date": "2026-07-15T12:00:00"
  }
]
```
**Tecla**: `S` en Web Explorer → historial de streams
**Funciones**:
- Guardar stream al reproducir
- Re-buscar automáticamente al seleccionar
- Eliminar entradas antiguas

### #6: Cache Management
**Ubicación cache**: `/tmp/yt-dlp/` o `~/.cache/yt-dlp/`
**Tecla**: `C` en Web Explorer → limpiar cache
**Opción Config**: auto-limpiar al salir
**Funciones**:
- Limpiar cache yt-dlp
- Mostrar tamaño del cache
- Auto-limpieza opcional

## F10: yt-dlp Web Explorer v2 (COMPLETADO)

### Fase 1: Platform Registry ✅
### Fase 2: Wrapper yt-dlp ✅
### Fase 3: Handler V7 ✅
### Fase 4: Views V7 ✅
### Fase 5: App & Config ✅
### Fase 6: Polish ✅
### Fase 7: Bugs post-implementación ✅ (B22-B31)
