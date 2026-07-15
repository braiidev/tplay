# TODO — tplay

## F10: yt-dlp Web Explorer v2 (COMPLETADO)

### Fase 1: Platform Registry ✅
- [x] 1.1 Crear `player/platforms.py`
- [x] 1.2 Crear `~/.config/tplay/data/platforms.json`
- [x] 1.3 Agregar `is_default` para proteger platforms

### Fase 2: Wrapper yt-dlp ✅
- [x] 2.1 Reescribir `player/web.py` — search() con extract_flat=True
- [x] 2.2 Agregar `download()` — audio (mp3) / video (mp4)
- [x] 2.3 Agregar `download_url` a WebResult
- [x] 2.4 Fix B22: search() retorna resultados reales

### Fase 3: Handler V7 ✅
- [x] 3.1 Reescribir `player/handlers/webexplorer.py` — 3 modos
- [x] 3.2 Implementar `web_motor_mode` — gestión de plataformas
- [x] 3.3 Implementar `web_motor_edit_mode` — editor de plataformas
- [x] 3.4 Implementar `web_download_mode` — configuración de descarga
- [x] 3.5 Agregar g/G navegación
- [x] 3.6 Agregar D (descarga directa) y d (con config)
- [x] 3.7 Agregar cola de descarga (max 3)
- [x] 3.8 Check de re-descarga
- [x] 3.9 Plataformas sin búsqueda: URL completa

### Fase 4: Views V7 ✅
- [x] 4.1 Reescribir `draw_web()` — layout motor+prompt+divider+lista
- [x] 4.2 Agregar estados en lista
- [x] 4.3 Crear `draw_motor_editor()`
- [x] 4.4 Crear `draw_download_config()`
- [x] 4.5 Truncado de texto

### Fase 5: App & Config ✅
- [x] 5.1 Agregar estados web en `player/app.py`
- [x] 5.2 Agregar defaults downloads en `player/config.py`
- [x] 5.3 Actualizar help tab en `player/ui.py`

### Fase 6: Polish ✅
- [x] 6.1 mypy --strict
- [ ] 6.2 Tests manuales (pendiente de probar en máquina)

## Pendiente (próxima sesión)
- [ ] Probar: `tplay → 7 → Tab → YouTube → Tab → "beethoven" → Enter`
- [ ] Fixear bugs que aparezcan en testing
