# STATE — tplay

## Estado actual
- **Version**: v1.5.61
- **Plan activo**: F10 yt-dlp Web Explorer v2 (multi-plataforma + descarga)
- **Bugs abiertos**: B22 (search siempre "Sin resultados")
- **Docs**: Sincronizados con v1.5.61

## Último commit
- `Fase 1 - code - 1.5.61 - F10: crear player/platforms.py (registry 6 plataformas)`

## Cambios desde última sesión
- **Fase 1 completada**: `player/platforms.py` creado
  - Platform dataclass con 7 campos
  - 6 plataformas default: YouTube, SoundCloud, Vimeo, Dailymotion, Twitch, Niconico
  - Funciones: load_platforms, save_platforms, get_search_prefix, get_platform, increment_downloads, can_delete
  - mypy strict pasa

## Pendiente para mañana
- [x] Crear `player/platforms.py` (registry + load/save + defaults 6) ✅
- [ ] Reescribir `player/web.py` (search con extract_flat=True + download())
- [ ] Reescribir `player/handlers/webexplorer.py` (3 modos + gestión + descarga)
- [ ] Modificar `player/views.py` (UI motor+prompt+estados + motor_editor + download_config)
- [ ] Modificar `player/app.py` (nuevos estados web)
- [ ] Modificar `player/config.py` (defaults downloads)
- [ ] mypy --strict
- [ ] Commit code + docs
- [ ] Probar: `tplay → 7 → Tab → YouTube → Tab → "beethoven" → Enter` → resultados
