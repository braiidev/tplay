# TODO — tplay

## Pendiente para próxima sesión

### Etapa 3: DRY Refactoring
- [ ] R1-R3: FilterState + navigate_cursor + scroll clamping
- [ ] R4-R6: Drawing helpers (_draw_row, _draw_item_with_duration, _draw_empty)
- [ ] R7-R10: Handler pattern helpers
- [ ] R11-R15: Unificación de funciones duplicadas

### Etapa 4: Performance
- [ ] P1-P10: Config cache, DownloadManager opts, app state opts, view render opts

### Etapa 5: UX + Visual
- [ ] U1-U10: UX improvements
- [ ] V1-V6: Visual fixes

### Features
- [ ] #6: Cache Management (limpiar cache yt-dlp)

## Completado

### Etapa 2: Audit Bugs Menores + Dead Code ✅ (v1.6.3)
- A1-A10: 10 bugs menores corregidos
- D1-D12: 10 dead code items eliminados (D3,D5 skipped — audit incorrecto)

### Etapa 1: Audit Critical Bugs ✅ (v1.6.0-v1.6.2)
- C1: Toast double-decrement fix
- C2: Data race en download callback fix
- C3: History data loss fix
- C5: TOCTOU race en active_count fix
- C6: _callbacks list race fix
- C7: Thread safety en webexplorer fix
- C8: URL incorrecta en _add_to_queue fix

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
