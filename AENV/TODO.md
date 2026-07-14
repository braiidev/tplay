# TODO — tplay

## F10: yt-dlp Web Explorer (ACTIVO)

### Fase 1: Streaming MVP
- [ ] 1.1 Wrapper `player/web.py` — WebResult dataclass, search(), is_available()
- [ ] 1.2 Handler `player/handlers/webexplorer.py` — handle_web, search input, playback
- [ ] 1.3 Drawer `draw_web()` en `player/views.py`
- [ ] 1.4 Integración `app.py` — V_WEB=7, register handler/drawer, view switch
- [ ] 1.5 Nav bar + Help tab en `ui.py`
- [ ] 1.6 Config defaults en `config.py` — online_max_results, online_audio_quality, online_search_history
- [ ] 1.7 Historial de búsquedas (últimas 10)
- [ ] 1.8 requirements.txt — agregar yt-dlp

### Fase 2: Descarga
- [ ] 2.1 Key `D` en Listen para descargar
- [ ] 2.2 Prompt de opciones (formato, calidad)
- [ ] 2.3 Progress bar curses
- [ ] 2.4 Pestaña Config "Online"
- [ ] 2.5 Guardar en music_dir

### Fase 3: Multi-plataforma
- [ ] 3.1 Detectar plataforma desde URL
- [ ] 3.2 Soporte Dailymotion, SoundCloud
- [ ] 3.3 Platform registry lazy
- [ ] 3.4 UI indicador de plataforma

## Completado
- [x] v1.5.59 — EQ custom bands, configuración, hints, help, radio
- [x] v1.5.58 — Help EQ hints (e/E), radio hints (g/G)
- [x] v1.5.57 — Config bands always visible, history g/G
- [x] v1.5.56 — draw_tab_carousel(), clamp_scroll(), draw_list_indicators()
- [x] v1.5.55 — Config/Audio bands solo lectura, hints contextuales
- [x] v1.5.54 — Listen metadata centrada, volume bar visual
