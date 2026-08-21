# TODO — tplay

## Pendiente para próxima sesión

### Features
- [ ] #6: Cache Management (limpiar cache yt-dlp)
- [ ] #7: Paginación continua de resultados
- [ ] Commit v1.9.0 (code + docs) — pendiente autorización

## Completado

### v1.9.0 ✅
- API control externo: Unix socket (`player/ipc.py`) + `tplay --ctl <cmd>` + toggle/play/pause/stop/next/prev/vol/status
- 33 tests IPC (suite total 45) + E2E real verificado en tmux

### v1.8.0 ✅
- Fix 403 YouTube (yt-dlp 2026.7.4 → 2026.8.19 + cache clear)
- Auto-update yt-dlp al inicio (`player/ytdlp_update.py`, cache 24h, toggle en Sistema, 12 tests)

### Security Fixes (v1.7.0-1.7.2) ✅
- v1.7.0: F1-F8 (critical + high) — js-runtime, VLC import, pin versions, end-of-options, path validation, stack thread safety, atomic writes, confirm dialogs
- v1.7.1: yt-dlp fixes — eliminate --js-runtime node, search cookies, quality map, config cycling
- v1.7.2: S3-S14, D12-D16 (medium) — cookie validation, toast pending, git reset hard, isatty, log rotation, history limit, max_concurrent

### Audit + Refactoring (v1.6.0-1.6.7) ✅
- C1-C8: Critical bugs (toast, data races, TOCTOU, thread safety)
- A1-A10: Minor bugs + D1-D12 dead code cleanup
- R1-R2-R15: DRY refactoring
- P1-P8: Performance (config cache, history lookup, audio cache)
- V1-V5: Visual fixes
- U1-U10: UX improvements

### Core Features (v1.5.60-1.5.80) ✅
- yt-dlp Web Explorer v2 (subprocess approach)
- DownloadManager (queue, pause/resume, per-item state)
- Historial unificado (downloads + streams)
- Equalizer 10 bandas + 16 presets
