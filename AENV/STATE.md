# STATE — tplay

## Estado actual
- **Version**: v1.6.3
- **Plan activo**: Etapa 2 — High Priority Bugs + Dead Code COMPLETOS ✅
- **Bugs abiertos**: 0
- **Docs**: Sincronizados con v1.6.3

## Último commit
- `fix - 1.6.3 - A1-A10 bugs menores + D1-D12 dead code cleanup`

## Resumen v1.5.75→v1.6.3
| Versión | Cambio |
|---------|--------|
| 1.5.75 | Migración Python API → subprocess (yt-dlp bot detection fix) |
| 1.5.76 | B55-B58: pause/resume fix, vista7 slowness, temp .part cleanup |
| 1.5.77 | B59: pause/resume restart — `--continue` flag |
| 1.5.78 | `DownloadManager` class: worker loop, cola, concurrencia, SIGSTOP/SIGCONT |
| 1.5.79 | B60-B61: Integración completa + .part cleanup + download history (parcial) |
| 1.5.80 | #4+#5: Historial unificado (descargas+streams), tabs, auto-download streams |
| 1.6.0 | Audit: C1 toast fix, C3 history data loss fix, C8 queue URL fix |
| 1.6.1 | Audit: C2 download callback race, C5 TOCTOU active_count, C6 callbacks race |
| 1.6.2 | Audit: C7 thread safety en webexplorer (search + play async pending) |
| 1.6.3 | Audit: A1-A10 bugs menores + D1-D12 dead code cleanup (10 items each) |

## Pendiente para próxima sesión
- [ ] R1-R15: DRY refactoring (FilterState, navigate_cursor, drawing helpers)
- [ ] P1-P10: Performance (config cache, DownloadManager opts, app state opts)
- [ ] U1-U10: UX improvements
- [ ] V1-V6: Visual fixes
- [ ] #6: Cache management
