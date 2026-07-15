# STATE — tplay

## Estado actual
- **Version**: v1.5.63
- **Plan activo**: F10 yt-dlp Web Explorer v2 (multi-plataforma + descarga)
- **Bugs abiertos**: B22 (search siempre "Sin resultados") — **RESUELTO**
- **Docs**: Sincronizados con v1.5.63

## Último commit
- `Fase 3 - code - 1.5.63 - F10: reescribir player/handlers/webexplorer.py (3 modos + gestión + descarga)`

## Cambios desde última sesión
- **Fase 3 completada**: `player/handlers/webexplorer.py` reescrito
  - 3 modos: normal (lista), search (prompt), motor (gestión)
  - Motor mode: add/edit/delete plataformas (patrón meta_editor)
  - Download: D (directo), d (con config)
  - g/G: navegación primer/último resultado
  - A/a: add to queue
  - x: clear results
  - Cola de descarga: max 3 (configurable hasta 10)
  - Check re-descarga
  - Plataformas sin búsqueda: URL completa en prompt
  - mypy strict pasa

## Pendiente para mañana
- [x] Crear `player/platforms.py` (registry + load/save + defaults 6) ✅
- [x] Reescribir `player/web.py` (search con extract_flat=True + download()) ✅
- [x] Reescribir `player/handlers/webexplorer.py` (3 modos + gestión + descarga) ✅
- [x] Modificar `player/app.py` (nuevos estados web) ✅
- [ ] Modificar `player/views.py` (UI motor+prompt+estados + motor_editor + download_config)
- [ ] Modificar `player/config.py` (defaults downloads)
- [ ] mypy --strict
- [ ] Commit code + docs
- [ ] Probar: `tplay → 7 → Tab → YouTube → Tab → "beethoven" → Enter` → resultados
