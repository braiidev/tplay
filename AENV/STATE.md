# STATE — tplay

## Estado actual
- **Version**: v1.9.0
- **Security audit**: COMPLETO (todos los items resueltos o mitigados)
- **Bugs abiertos**: 0
- **Tests**: 45 passed (12 ytdlp_update + 33 ipc)
- **Docs**: Sincronizados con v1.9.0

## Último commit
- `v1.8.0 docs — changelog, devlog, state, todo, bugs, test` (v1.9.0 sin commitear aún)

## Resumen v1.5.75→v1.9.0
| Versión | Cambio |
|---------|--------|
| 1.5.75 | Migración Python API → subprocess |
| 1.5.76-79 | DownloadManager + fixes |
| 1.5.80 | Historial unificado |
| 1.6.0-62 | Audit critical bugs (C1-C8) |
| 1.6.3 | Audit minor bugs + dead code (A1-A10, D1-D12) |
| 1.6.4-65 | DRY refactoring + visual fixes |
| 1.6.6 | Performance (config cache, history lookup) |
| 1.6.7 | UX improvements + Security audit |
| 1.7.0 | Security fixes high severity (F1-F8) |
| 1.7.1 | yt-dlp fixes + config cycling |
| 1.7.2 | Security fixes medium severity (S3-S14, D12-D16) |
| 1.8.0 | Fix 403 YouTube + auto-update yt-dlp al inicio |
| 1.9.0 | API control externo (IPC socket + tplay --ctl) |

## Pendiente para próxima sesión
- [ ] #6: Cache Management (limpiar cache yt-dlp)
- [ ] #7: Paginación continua de resultados
- [ ] Commit v1.9.0 (code + docs) — pendiente autorización
