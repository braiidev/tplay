# BUGS — tplay

## Activos

_(ninguno)_

## Resueltos

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
