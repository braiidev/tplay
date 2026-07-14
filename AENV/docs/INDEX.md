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
| `docs/BRAINSTORM.md` | Investigación features futuros | Al planificar features |
| `docs/EQ_PLAN.md` | Plan de implementación del Equalizer | Al implementar F2 |
| `docs/ONLINE.md` | Features online (yt-dlp) | Al implementar F10 |
| `docs/WEB_EXPLORER_PLAN.md` | Plan paso a paso Web Explorer | Al implementar F10 |

## Relación con código

```
Código fuente → Documentación
─────────────────────────────
player/       → docs/ARCH.md
*.json        → docs/MODELS.md
handlers/     → docs/BUSINESS.md
config.py     → docs/MODELS.md (config schema)
state.py      → docs/MODELS.md (state schema)
web.py        → docs/ONLINE.md
```
