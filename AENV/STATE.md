# STATE — tplay

## Estado actual
- **Version**: v1.6.4
- **Plan activo**: Etapa 3 — DRY Refactoring (parcial)
- **Bugs abiertos**: 0
- **Docs**: Sincronizados con v1.6.4

## Último commit
- `refactor - 1.6.4 - R2: navigate_cursor helper, R15: import save a nivel módulo`

## Resumen v1.5.75→v1.6.4
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
| 1.6.3 | Audit: A1-A10 bugs menores + D1-D12 dead code cleanup |
| 1.6.4 | Audit: R2 navigate_cursor helper + R15 import save a nivel módulo |

## Pendiente para próxima sesión
- [ ] R1: FilterState + handle_filter_input genérico
- [ ] R4-R6: Drawing helpers (_draw_row, _draw_item_with_duration, _draw_empty)
- [ ] R7-R10: Handler pattern helpers
- [ ] R13-R14: Motor/Meta editor shared + color pair caching
- [ ] P1-P10: Performance
- [ ] U1-U10: UX improvements
- [ ] V1-V6: Visual fixes
- [ ] #6: Cache management
