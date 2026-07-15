# TODO — tplay

## F10: yt-dlp Web Explorer v2 (ACTIVO)

### Fase 1: Platform Registry
- [x] 1.1 Crear `player/platforms.py` — Platform dataclass, load/save, DEFAULT_PLATFORMS (6) ✅
- [x] 1.2 Crear `~/.config/tplay/data/platforms.json` — archivo de plataformas (se crea automáticamente)
- [x] 1.3 Agregar `is_default` para proteger platforms de eliminación ✅

### Fase 2: Wrapper yt-dlp
- [ ] 2.1 Reescribir `player/web.py` — search() con extract_flat=True + por-entry extraction
- [ ] 2.2 Agregar `download()` — descarga con yt-dlp (fmt: audio/video, quality, stream)
- [ ] 2.3 Agregar `download_url` a WebResult
- [ ] 2.4 Fix B22: search() retorna resultados reales

### Fase 3: Handler V7
- [ ] 3.1 Reescribir `player/handlers/webexplorer.py` — 3 modos (normal/search/motor)
- [ ] 3.2 Implementar `web_motor_mode` — gestión de plataformas (a/e/d)
- [ ] 3.3 Implementar `web_motor_edit_mode` — editor de plataformas (patrón meta_editor)
- [ ] 3.4 Implementar `web_download_mode` — configuración de descarga
- [ ] 3.5 Agregar g/G navegación (primer/último resultado)
- [ ] 3.6 Agregar D (descarga directa) y d (descarga con config)
- [ ] 3.7 Agregar cola de descarga (max 3, configurable hasta 10)
- [ ] 3.8 Check de re-descarga (mismo formato = no, otro formato = sí)
- [ ] 3.9 Plataformas sin búsqueda: aceptar URL completa en prompt

### Fase 4: Views V7
- [ ] 4.1 Reescribir `draw_web()` — layout motor+prompt+divider+lista
- [ ] 4.2 Agregar estados en lista: [-] [►] [D] [P] [Q] [✓] [X] [!]
- [ ] 4.3 Crear `draw_motor_editor()` — patrón draw_meta_editor()
- [ ] 4.4 Crear `draw_download_config()` — patrón draw_meta_editor()
- [ ] 4.5 Truncado de texto en lista

### Fase 5: App & Config
- [ ] 5.1 Agregar estados web en `player/app.py` (motor_mode, download_queue, etc.)
- [ ] 5.2 Agregar defaults downloads en `player/config.py`
- [ ] 5.3 Actualizar nav bar y help tab en `player/ui.py`

### Fase 6: Polish
- [ ] 6.1 mypy --strict
- [ ] 6.2 Tests manuales completos
- [ ] 6.3 Commit code + docs

## Completado
- [x] v1.5.59 — EQ custom bands, configuración, hints, help, radio
- [x] v1.5.58 — Help EQ hints (e/E), radio hints (g/G)
- [x] v1.5.57 — Config bands always visible, history g/G
- [x] v1.5.56 — draw_tab_carousel(), clamp_scroll(), draw_list_indicators()
- [x] v1.5.55 — Config/Audio bands solo lectura, hints contextuales
- [x] v1.5.54 — Listen metadata centrada, volume bar visual
