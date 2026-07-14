# STATE — tplay

## Estado actual
- **Version**: v1.5.60
- **Plan activo**: F10 yt-dlp Web Explorer (Fase 1 Streaming — search roto, pendiente fix)
- **Bugs abiertos**: B22 (search siempre "Sin resultados")
- **Docs**: Sincronizados con v1.5.60 + plan B22

## Último commit
- `fix - 1.5.60 - B20: web_search_mode interceptado en _handle_key_mode_specific + reset en view switch`

## Cambios desde última sesión
- B20 y B21 fixeados (web_search_mode intercept + reset)
- B22 documentado: search() roto por extract_flat=False
- Plan completo reescrito en WEB_EXPLORER_PLAN.md:
  - Nuevo: `player/platforms.py` (registry de plataformas)
  - Rediseñado: `player/web.py` (extract_flat=True + extracción individual)
  - Nuevo: `~/.config/tplay/data/platforms.json`
  - Platforms: YouTube (MVP), expandible a Dailymotion, SoundCloud, etc.

## Pendiente para mañana
- [ ] Crear `player/platforms.py` (registry + load/save + increment_downloads)
- [ ] Reescribir `player/web.py` (search con extract_flat=True + por-entry extraction)
- [ ] Modificar `player/handlers/webexplorer.py` (usar prefix + incrementar downloads)
- [ ] Agregar `online_platform` a `player/config.py`
- [ ] Actualizar `AENV/docs/ONLINE.md` con docs de platforms
- [ ] mypy --strict
- [ ] Commit code + docs
- [ ] Probar: `tplay → 7 → / → "beethoven" → Enter` → resultados reales
