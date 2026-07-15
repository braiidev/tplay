# TODO — tplay

## Pendiente para próxima sesión

### Features
- [ ] #6: Cache Management (limpiar cache yt-dlp)

## Completado

### Etapa 4: Performance ✅ (v1.6.6)
- P1: Config load cache (mtime-based)
- P3: Already fixed (time.sleep)
- P4: _add_history O(1) lookup
- P5: undo shallow copy (no deepcopy)
- P2/P6/P7/P9: Skipped (negligible or adds complexity)

### Etapa 3-5: DRY + Performance + Visual ✅ (v1.6.4-v1.6.5)
- R1: FilterState + handle_filter_text
- R2: navigate_cursor helper
- R15: import save a nivel módulo
- P8: Audio time/length cache
- V1-V5: Visual fixes

### Etapa 2: Audit Bugs Menores + Dead Code ✅ (v1.6.3)
- A1-A10: 10 bugs menores corregidos
- D1-D12: 10 dead code items eliminados

### Etapa 1: Audit Critical Bugs ✅ (v1.6.0-v1.6.2)
- C1-C8: 7 critical bugs corregidos

### #4+#5: Historial Unificado ✅ (v1.5.80)
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
