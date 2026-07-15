# STATE — tplay

## Estado actual
- **Version**: v1.6.7
- **Plan activo**: Audit completo + Security audit generado (AUDIT_v1.6.7_SECURITY.md)
- **Bugs abiertos**: 0
- **Docs**: Sincronizados con v1.6.7

## Último commit
- `docs: v1.6.7 — audit completo (todas las etapas 1-5)`

## Resumen v1.5.75→v1.6.7
| Versión | Cambio |
|---------|--------|
| 1.5.75 | Migración Python API → subprocess |
| 1.5.76 | B55-B58: pause/resume fix, temp .part cleanup |
| 1.5.77 | B59: `--continue` flag |
| 1.5.78 | DownloadManager class |
| 1.5.79 | B60-B61: Integración + .part cleanup |
| 1.5.80 | #4+#5: Historial unificado |
| 1.6.0 | C1,C3,C8 audit fixes |
| 1.6.1 | C2,C5,C6 audit fixes |
| 1.6.2 | C7 thread safety |
| 1.6.3 | A1-A10 + D1-D12 audit |
| 1.6.4 | R2 navigate_cursor + R15 import save |
| 1.6.5 | R1 FilterState, P8 audio cache, V1-V5 visual |
| 1.6.6 | P1 config cache, P4 history lookup, P5 undo shallow copy |
| 1.6.7 | U1-U10 UX improvements + Security audit completo |

## Pendiente para próxima sesión
- [ ] Security fixes: D1 (js-runtime condicional), D8 (VLC import graceful), D2+D9 (pin versions)
- [ ] Security fixes: S1+S2 (-- end-of-options), S12-S13 (atomic writes), S9 (stack thread safety)
- [ ] #6: Cache management
- [ ] Features nuevas según necesidad
