# TODO — tplay

## Pendiente para próxima sesión

### #6: Cache Management
- **Tecla**: `C` en Web Explorer → limpiar cache
- **Funciones**: Limpiar cache yt-dlp, mostrar tamaño, auto-limpieza opcional

## Completado

### #4+#5: Historial Unificado ✅
- Unificado downloads + streams en una sola vista `H`
- Tabs: [Descargas] [Streams] con `[/]`
- Streams se auto-descargan a `~/.config/tplay/data/tmp/`
- `is_temp` flag en DownloadEntry
- `X` limpia tab activo (borra archivos + entradas)
- `d` re-busca (stream) / re-descarga (download)
- Auto-save en `_play_web_result()`
- Help tab "Historial" actualizado

### F10: yt-dlp Web Explorer v2 ✅
- Phase 1-7 completados (v1.5.60 → v1.5.79)
- B22-B60 resueltos
- DownloadManager integrado con cola, pausa/resume por-item, cookies config
