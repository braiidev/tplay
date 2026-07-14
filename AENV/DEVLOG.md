# DEVLOG — tplay

## Entrada 1 — 2025-07-14 — Setup AENV

**Tarea**: Migrar tracking del proyecto a sistema AENV

**Archivos creados**:
- AENV/STATE.md
- AENV/DEVLOG.md
- AENV/BUGS.md
- AENV/TODO.md
- AENV/CHANGELOG.md
- AENV/TEST.md
- AENV/docs/INDEX.md
- AENV/docs/MODELS.md
- AENV/docs/BUSINESS.md
- AENV/docs/ARCH.md
- AGENTS.md (reescribido como índice)

**Decisión**: Migración completa — el proyecto ya tiene documentación extensa en AGENTS.md y TODO.md, se reorganiza en estructura AENV estándar.

**Estado**: v1.5.45, 128+ items completados, pendiente F2 (ecualizador).

---

## Entrada 2 — 2025-07-14 — Explorer read-only fuera del root

**Tarea**: Implementar modo solo-lectura en el Explorer para directorios fuera del music_dir configurado

**Archivos modificados**:
- `player/handlers/explorer.py` — `_is_inside_root()`, bloqueo de ops de escritura
- `player/views.py` — indicador `[RO]` en título del Explorer

**Decisión**: Solo lectura (no bloqueo total) — el usuario puede navegar libremente pero no modificar archivos fuera del directorio raíz. Operaciones bloqueadas: delete, mkdir, rename, copy, move, tag edit.

**Estado**: v1.5.46, mypy strict pasa.
