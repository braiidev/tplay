# tplay — Agent Workspace

## Startup (leer en este orden, siempre)
1. Este archivo
2. `TODO.md` → sección "Doing" (si vacía, primera de "Next")
3. `git log --oneline -5`

## Stack
- Python 3.10–3.14 (lo pinnea `install.sh`, con preferencia por el más nuevo) + curses + python-vlc + mutagen
- Sin frameworks web, es TUI pura
- mypy strict
- **venv propio en `~/.local/share/tplay/.venv`. Nunca `pip install --user` ni
  `--break-system-packages`**: modifican el Python del sistema y es la causa raíz
  del FIX de abajo.

## Rutas (fuente única: `player/paths.py`)
| Qué | Dónde |
|-----|-------|
| Código | `~/.local/share/tplay/` |
| Estado (JSON) | `~/.local/share/tplay/data/` |
| Comando | `~/.local/bin/tplay` |
| Pin del intérprete | `~/.local/share/tplay/.pinned-python` |

El estado NO va en `~/.config`: según XDG, `~/.config` es para lo que el usuario
abre con un editor, y esto es estado interno de la app. Antes código y datos
compartían `~/.config/tplay`, y por eso `--uninstall` podía llevarse favoritos e
historial en un `rm -rf`.

**Nunca hardcodear rutas en un módulo.** Importar de `.paths`. La migración desde
`~/.config/tplay/data` es por COPIA y vive en `paths.migrar_datos_legacy()`.

## Verificación
| Qué | Comando |
|-----|---------|
| Tests | `python3 -m pytest` (108) |
| Tipos | `python3 -m mypy player` (strict) |
| Instalador | `bash -n install.sh` |
| E2E real | `bash tests/e2e_install.sh` (30 checks, sandbox) |

El e2e es el único que corre `install.sh` de verdad. Encontró dos bugs que ningún
test unitario veía: `grep -q` + `set -o pipefail` daba falso negativo de libvlc
(SIGPIPE), y un glob sin match abortaba el script. **Un check que pasa porque el
código murió antes de llegar al bug es un check que no prueba nada**: fijarse que
no haya traceback, no solo que el efecto observable sea el esperado.

## Tracking
| Evento | Acción |
|--------|--------|
| Task completada | `TODO.md` → mover a "Done", tirar la próxima a "Doing" |
| Commit versionado | tag `v0.N` + mensaje `v0.N <tipo>: descripción` |
| `pytest` corrido | resultado en el commit/devlog de la task |
| Bug encontrado | git issue o task en `TODO.md` |

## Versión actual
- **v0.22** (código `0.16.0` en pyproject — el tag y la versión interna corren
  distinto; unificar es una task abierta)

## Regla de oro
> Loop atómico: una task por vez, commit chico y verificado. `TODO.md` dice qué sigue, `git log` dice qué pasó. Nada más que cargar.