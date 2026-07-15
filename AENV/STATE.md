# STATE — tplay

## Estado actual
- **Version**: v1.6.2
- **Plan activo**: Etapa 1 — Critical Bugs COMPLETOS ✅
- **Bugs abiertos**: 0
- **Docs**: Sincronizados con v1.6.2

## Último commit
- `fix - 1.6.2 - C7: thread safety en webexplorer (search + play async)`

## Resumen v1.5.75→v1.6.2
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

## Pendiente para próxima sesión
- [ ] A1-A10: Bugs menores del audit
- [ ] D1-D12: Dead code cleanup
- [ ] #6: Cache management
