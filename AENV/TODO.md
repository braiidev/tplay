# TODO — tplay

## Pendiente para próxima sesión

### Security Fixes (prioritarios)
- [ ] S1+S2: Agregar `--` end-of-options a subprocess de yt-dlp
- [ ] S4: Path validation en `_do_mkdir`
- [ ] S9: Thread safety en `Stack._items` (pending-flag pattern)
- [ ] S12-S13: Atomic writes para config/persistence (temp + os.replace)
- [ ] D1: Hacer `--js-runtime node` condicional (detectar `node` en PATH)
- [ ] D8: Wrap VLC import con graceful fallback antes de curses
- [ ] D2+D9: Pin `yt-dlp==<tested>` y `python-vlc>=3.0.0,<4.0.0`
- [ ] S15+S16: Agregar `_confirm` antes de borrado de download history

### Features
- [ ] #6: Cache Management (limpiar cache yt-dlp)

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
