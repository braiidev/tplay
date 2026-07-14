# tplay — Agent Workspace

## Startup (leer en este orden, siempre)
1. Este archivo
2. `AENV/STATE.md`
3. `AENV/DEVLOG.md` → última entrada únicamente
4. `AENV/BUGS.md` → sección "Activos" únicamente
5. `git log --oneline -5`

## Reference (leer SOLO cuando el trabajo toque ese módulo)
| Contexto | Archivo |
|----------|---------|
| Modelos/DB | `AENV/docs/MODELS.md` |
| Persistencia/State | `AENV/docs/MODELS.md` |
| Reglas de negocio | `AENV/docs/BUSINESS.md` |
| Arquitectura | `AENV/docs/ARCH.md` |
| Test manual | `AENV/TEST.md` |

## Tracking (escritura, al ocurrir el evento)
| Evento | Archivo | Acción |
|--------|---------|--------|
| Bug encontrado | `AENV/BUGS.md` | entrada en "Activos" |
| Bug corregido | `AENV/BUGS.md` | mover a "Resueltos" |
| Task completada | `AENV/TODO.md` | marcar done |
| Cambio significativo | `AENV/DEVLOG.md` | entrada nueva |
| Commit versionado | `AENV/CHANGELOG.md` | entrada nueva |
| `pytest` corrido | `AENV/TEST.md` → Resultados | registrar |

## Stack
- Python 3.12 + curses + python-vlc + mutagen
- Sin frameworks web, es TUI pura
- mypy strict

## Versión actual
- **v1.5.50** — ver `AENV/STATE.md` para detalle completo

## Regla de oro
> Cargar solo lo necesario ahora (L0-L1). Leer L2 (docs/) solo cuando el trabajo lo exija. Nunca leer L2 "por las dudas".
