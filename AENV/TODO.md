# TODO — tplay

## Pendiente para próxima sesión

### Security Fixes — Media Severity
- [ ] S3: yt-dlp `--no-warnings` flag
- [ ] S5-S8: Input validation en handlers
- [ ] S10-S11: Network timeout en yt-dlp subprocess
- [ ] S14: File size limits en downloads

### Features
- [ ] #6: Cache Management (limpiar cache yt-dlp)
- [ ] #7: Paginación continua de resultados (buscar N, si no satisface → buscar N+1...2N, append al mismo scroll)

## Completado

### v1.7.0 — Security Fixes High Severity ✅
- F1: `--js-runtime node` condicional (`_has_node()`)
- F2: VLC import graceful fallback (`_VLC_ERROR`)
- F3: Pin versions `python-vlc>=3.0.0,<4.0.0`, `yt-dlp==2026.07.04`
- F4: `--` end-of-options en subprocess yt-dlp
- F5: Path validation en `_do_mkdir`
- F6: Stack thread safety (`_stack_pending_adds`)
- F7: Atomic writes para 7 módulos de persistencia
- F8: Confirm dialogs antes de borrado

## Completado

### Etapa 5: UX + Visual ✅ (v1.6.7)
- U1: stack size indicator en listen title
- U2: help doc para directorios [+]/
- U3: radio hints bar
- U5: dialog multiline
- U8: toast compact mode position
- U9: goto overlay compact overlap
- U10: curs_set(0) en state transition
- U4/U6/U7: Skipped (correcto / complejo / feature nueva)

### Etapa 4: Performance ✅ (v1.6.6)
- P1,P3,P4,P5: Implementados
- P2,P6,P7,P9: Skipped (negligible)

### Etapa 3-5: DRY + Performance + Visual ✅ (v1.6.4-v1.6.5)
- R1,R2,R15: DRY refactoring
- P8: Audio time/length cache
- V1-V5: Visual fixes

### Etapa 2: Audit Bugs Menores + Dead Code ✅ (v1.6.3)
- A1-A10: 10 bugs menores
- D1-D12: 10 dead code items

### Etapa 1: Audit Critical Bugs ✅ (v1.6.0-v1.6.2)
- C1-C8: 7 critical bugs

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
