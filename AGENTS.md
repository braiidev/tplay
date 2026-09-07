# tplay — Agent Workspace

## Startup (leer en este orden, siempre)
1. Este archivo
2. `TODO.md` → sección "Doing" (si vacía, primera de "Next")
3. `git log --oneline -5`

## Stack
- Python 3.12 + curses + python-vlc + mutagen
- Sin frameworks web, es TUI pura
- mypy strict

## Tracking
| Evento | Acción |
|--------|--------|
| Task completada | `TODO.md` → mover a "Done", tirar la próxima a "Doing" |
| Commit versionado | tag `v0.N` + mensaje `v0.N <tipo>: descripción` |
| `pytest` corrido | resultado en el commit/devlog de la task |
| Bug encontrado | git issue o task en `TODO.md` |

## Versión actual
- **v1.9.1**

## Regla de oro
> Loop atómico: una task por vez, commit chico y verificado. `TODO.md` dice qué sigue, `git log` dice qué pasó. Nada más que cargar.