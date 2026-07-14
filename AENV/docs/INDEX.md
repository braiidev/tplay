# INDEX — Documentación tplay

## Mapa de la documentación

| Archivo | Contenido | Cuándo leer |
|---------|-----------|-------------|
| `STATE.md` | Estado actual, versión, módulos | Siempre al inicio |
| `DEVLOG.md` | Bitácora operacional (última entrada) | Siempre al inicio |
| `BUGS.md` | Bugs activos y resueltos | Al investigar problemas |
| `TODO.md` | Pendientes y features planificadas | Al planificar trabajo |
| `CHANGELOG.md` | Historial de versiones | Al verificar qué cambió |
| `TEST.md` | Guía de testing manual | Al verificar funcionalidad |
| `docs/MODELS.md` | Modelos de datos, schemas | Al modificar persistencia |
| `docs/BUSINESS.md` | Reglas de negocio | Al implementar features |
| `docs/ARCH.md` | Arquitectura detallada | Al refactorizar o agregar módulos |

## Relación con código

```
Código fuente → Documentación
─────────────────────────────
player/       → docs/ARCH.md
*.json        → docs/MODELS.md
handlers/     → docs/BUSINESS.md
config.py     → docs/MODELS.md (config schema)
state.py      → docs/MODELS.md (state schema)
```
