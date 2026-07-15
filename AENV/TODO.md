# TODO — tplay

## Pendiente para próxima sesión

### Etapa 1: Critical Bugs (restante)
- [ ] C7: Thread safety en webexplorer (curses not thread-safe, queue para main↔worker)

### Etapa 2: Bugs menores + Dead Code
- [ ] A1-A10: Bugs menores del audit (config shallow copy, mono theme, audio rate, etc.)
- [ ] D1-D12: Dead code cleanup (download() 88 líneas, _do_download_direct, imports muertos)

### Etapa 3: Features
- [ ] #6: Cache Management (limpiar cache yt-dlp)

## Completado

### Audit Critical Bugs ✅ (v1.6.0-v1.6.1)
- C1: Toast double-decrement fix
- C2: Data race en download callback fix
- C3: History data loss fix
- C5: TOCTOU race en active_count fix
- C6: _callbacks list race fix
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
