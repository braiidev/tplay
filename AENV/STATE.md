# STATE — tplay

## Estado actual
- **Version**: v1.5.62
- **Plan activo**: F10 yt-dlp Web Explorer v2 (multi-plataforma + descarga)
- **Bugs abiertos**: B22 (search siempre "Sin resultados") — **EN PROCESO**
- **Docs**: Sincronizados con v1.5.62

## Último commit
- `Fase 2 - code - 1.5.62 - F10: reescribir player/web.py (extract_flat=True + download)`

## Cambios desde última sesión
- **Fase 2 completada**: `player/web.py` reescrito
  - WebResult: nuevo campo `download_url`
  - search(): usa `extract_flat=True` para listar + extracción individual por entry
  - download(): nueva función para descargar con yt-dlp (audio mp3 / video mp4)
  - _get_download_url(): helper para obtener mejor URL según config
  - Fix B22: search() ahora retorna resultados reales
  - mypy strict pasa

## Pendiente para mañana
- [x] Crear `player/platforms.py` (registry + load/save + defaults 6) ✅
- [x] Reescribir `player/web.py` (search con extract_flat=True + download()) ✅
- [ ] Reescribir `player/handlers/webexplorer.py` (3 modos + gestión + descarga)
- [ ] Modificar `player/views.py` (UI motor+prompt+estados + motor_editor + download_config)
- [ ] Modificar `player/app.py` (nuevos estados web)
- [ ] Modificar `player/config.py` (defaults downloads)
- [ ] mypy --strict
- [ ] Commit code + docs
- [ ] Probar: `tplay → 7 → Tab → YouTube → Tab → "beethoven" → Enter` → resultados
