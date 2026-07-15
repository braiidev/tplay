# TODO — tplay

## Pendiente para próxima sesión

### B60: DownloadManager Integration (ALTA PRIORIDAD)
**Problema**: Cola de descargas no funciona — items comparten estado, [Q] nunca se ejecuta
**Estado**: DownloadManager class implementada en web.py, pendiente integración
**Archivos a modificar**:
1. `player/handlers/webexplorer.py` — reemplazar lógica vieja por DownloadManager
2. `player/app.py` — remover variables viejas, agregar `download_manager`
3. `player/views.py` — leer estado de `get_download_manager().get_items()`
**Testing**: Cola con 3+ descargas, pause/resume/cancel por-item

### #4: Download History
**Archivo propuesto**: `~/.config/tplay/data/downloads.json`
**Tecla**: `H` en Web Explorer → lista de descargas
**Funciones**: Lista de descargas, re-descargar, eliminar de historial

### #5: Stream Replay
**Archivo propuesto**: `~/.config/tplay/data/streams.json`
**Tecla**: `S` en Web Explorer → historial de streams
**Funciones**: Guardar stream al reproducir, re-buscar, eliminar entradas

### #6: Cache Management
**Tecla**: `C` en Web Explorer → limpiar cache
**Funciones**: Limpiar cache yt-dlp, mostrar tamaño, auto-limpieza opcional

## F10: yt-dlp Web Explorer v2 (COMPLETADO)

### Fase 1: Platform Registry ✅
### Fase 2: Wrapper yt-dlp ✅
### Fase 3: Handler V7 ✅
### Fase 4: Views V7 ✅
### Fase 5: App & Config ✅
### Fase 6: Polish ✅
### Fase 7: Bugs post-implementación ✅ (B22-B31)
