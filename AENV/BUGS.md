# BUGS — tplay

## Activos

_(ninguno)_

## Resueltos

### B35 — _config_int_inc/dec no maneja online_download_max
- **Archivo**: `player/handlers/config_view.py`
- **Descripción**: Cambiar "Descargas máximas" en Config/Sistema no hacía nada.
- **Causa**: `_config_int_inc/dec` solo manejaba `volume` y `sleep_timer_minutes`.
- **Fix**: Agregado caso `online_download_max` con sync a `app.web_download_max`.
- **Estado**: Resuelto en v1.5.70

### B34 — _get_download_url quality_map incompleto
- **Archivo**: `player/web.py`
- **Descripción**: Worst/144p/240p caían en fallback 480p al obtener URL de descarga.
- **Causa**: quality_map solo tenía 480p/720p/1080p/best.
- **Fix**: Agregado worst (min height), 144p, 240p al quality_map.
- **Estado**: Resuelto en v1.5.70

### B33 — yt-dlp corrompe curses (progreso visible + bordes destruidos)
- **Archivo**: `player/web.py`
- **Descripción**: `[download] 90.4%...` se dibuja fuera del box; al finalizar, helper bar y bordes `│` desaparecen.
- **Causa**: Opciones `"stdout"` y `"stderr"` en yt-dlp **no son válidas** — yt-dlp las ignora silenciosamente y escribe progreso a stdout real.
- **Fix**: Eliminadas opciones falsas; agregado `"progress": False` para suprimir barra de progreso. Progress hooks siguen funcionando (son API separada).
- **Estado**: Resuelto en v1.5.70

### B32 — Toast borra borde inferior del box
- **Archivo**: `player/app.py`
- **Descripción**: Toast en `h-4` sobreescribe `│` del borde; al desaparecer no se restaura.
- **Causa**: Posición `h - STATUS_ROW - 1` estaba dentro del área del box.
- **Fix**: Toast ahora en `h-2` (borde inferior) con color `PAIR_NAV`.
- **Estado**: Resuelto en v1.5.69

### B31 — yt-dlp corrompe curses (status bar desaparece)
- **Archivo**: `player/web.py`
- **Descripción**: Output de yt-dlp se dibuja encima de status bar, borra `│` de marcos.
- **Causa**: Opciones `"stdout"`/`"stderr"` no son válidas en yt-dlp.
- **Fix**: Resuelto definitivamente en B33 (progress=False).
- **Estado**: Superseded by B33

### B30 — Download config: q cierra app + aesthetic incorrecta
- **Archivo**: `player/handlers/webexplorer.py`, `player/views.py`
- **Descripción**: `q` cierra la app en vez de cancelar; aesthetic usa `◄ prev [val] next ►`.
- **Causa**: `q` no era interceptado; aesthetic no seguía convención `[val] ←→`.
- **Fix**: Solo `Esc` cancela; aesthetic `[selected] ←→`; quality options expandidas.
- **Estado**: Resuelto en v1.5.68

### B29 — Quality options incompletas
- **Archivo**: `player/web.py`, `player/handlers/config_view.py`
- **Descripción**: Solo 480p/720p/1080p/best; falta worst/144p/240p.
- **Causa**: quality_map limitada.
- **Fix**: Agregado worst, 144p, 240p; config tab "Sistema" con settings downloads.
- **Estado**: Resuelto en v1.5.68

### B28 — Toast tapa status bar en Web Explorer
- **Archivo**: `player/app.py`
- **Descripción**: Toast de descarga se dibuja en `h-3` (misma posición que status bar).
- **Causa**: Ambos usaban `h-3`.
- **Fix**: Toast ahora en `h - STATUS_ROW - 1` (arriba de status).
- **Estado**: Resuelto en v1.5.67

### B27 — Estado play persiste indebidamente en Web Explorer
- **Archivo**: `player/app.py`, `player/handlers/webexplorer.py`
- **Descripción**: Al play un resultado, [►] queda en el item aunque se cambie de vista.
- **Causa**: No había tracking de cuál item está reproduciendo.
- **Fix**: `web_playing_idx` + reset en `_check_playback_end`.
- **Estado**: Resuelto en v1.5.67

### B26 — Download config no permite cambiar valores
- **Archivo**: `player/handlers/webexplorer.py`, `player/views.py`
- **Descripción**: Editor de descarga pide Enter pero no hay opciones visibles para cambiar.
- **Causa**: Era un editor de texto, no selector cíclico.
- **Fix**: ←→/hl para ciclar opciones (format: audio/video, quality: 480p/720p/1080p/best).
- **Estado**: Resuelto en v1.5.67

### B25 — Descarga bloqueante + sin nombre correcto
- **Archivo**: `player/handlers/webexplorer.py`, `player/web.py`
- **Descripción**: Download bloquea UI, archivo se guarda como "videoplayback.ext", Explorer no refresca.
- **Causa**: `_start_download()` ejecuta yt-dlp sync; `result.download_url` es stream URL sin metadata.
- **Fix**: Thread daemon + progress hook; pasar `webpage_url` a yt-dlp; refresh entries post-download.
- **Estado**: Resuelto en v1.5.66
- **Commit**: pendiente

### B24 — Sin feedback visual de carga en búsqueda
- **Archivo**: `player/handlers/webexplorer.py`, `player/views.py`
- **Descripción**: No hay indicador de loading durante búsqueda web.
- **Causa**: `_do_search()` era sync sin estado visual.
- **Fix**: `web_loading` state + `threading.Thread` + "Buscando..." blink en vista.
- **Estado**: Resuelto en v1.5.66

### B23 — Prompt desaparece al buscar
- **Archivo**: `player/views.py`, `player/handlers/webexplorer.py`
- **Descripción**: Al presionar Enter en búsqueda, prompt vuelve a "presiona / para buscar".
- **Causa**: `web_search_mode = False` ocultaba query.
- **Fix**: `web_last_query` persiste la query post-búsqueda.
- **Estado**: Resuelto en v1.5.66

### B22 — search() siempre devuelve "Sin resultados"
- **Archivo**: `player/web.py`
- **Descripción**: `search()` con `extract_flat=False` retorna entries pero `entry.get("url")` es siempre string vacío.
- **Causa**: `extract_flat=False` con search query no extrae URLs de streaming de cada entry.
- **Fix**: Usar `extract_flat=True` para listar, luego `extract_info()` por cada entry.
- **Estado**: Resuelto en v1.5.62
- **Commit**: `afda09c`

### B20 — Global keys atrapan search mode en Web Explorer
- **Archivo**: `player/app.py`
- **Fix**: Agregado check `web_search_mode` en `_handle_key_mode_specific`.
- **Fecha**: v1.5.60
- **Commit**: `dbc0b52`

### B21 — web_search_mode no se resetea al cambiar de vista
- **Archivo**: `player/app.py`
- **Fix**: Agregado resets en `_handle_key_view_switch`.
- **Fecha**: v1.5.60
- **Commit**: `dbc0b52`

### B1-B19
Ver historial de versiones anteriores.
