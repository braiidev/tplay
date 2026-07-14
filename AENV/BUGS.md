# BUGS — tplay

## Activos

### B22 — search() siempre devuelve "Sin resultados"
- **Archivo**: `player/web.py`
- **Descripción**: `search()` con `extract_flat=False` retorna entries pero `entry.get("url")` es siempre string vacío. yt-dlp search solo retorna metadata básica sin stream URLs.
- **Causa**: `extract_flat=False` con search query no extrae URLs de streaming de cada entry.
- **Fix**: Usar `extract_flat=True` para listar (rápido), luego `extract_info()` por cada entry para obtener stream URL.
- **Estado**: Pendiente — requiere reescribir `search()` + crear `player/platforms.py`
- **Fecha**: v1.5.60

## Resueltos

### B20 — Global keys atrapan search mode en Web Explorer
- **Archivo**: `player/app.py`
- **Descripción**: `_handle_key_global` interceptaba teclas (`S`, `Space`, `n`, `b`, `+`, `-`, `1-7`) antes de que `handle_web` las procesara como texto de búsqueda.
- **Causa**: `web_search_mode` no estaba en `_handle_key_mode_specific`, así que las teclas llegaban a `_handle_key_global`.
- **Fix**: Agregado check `web_search_mode` en `_handle_key_mode_specific` (como `explorer_filter_mode`).
- **Fecha**: v1.5.60
- **Commit**: `dbc0b52`

### B21 — web_search_mode no se resetea al cambiar de vista
- **Archivo**: `player/app.py`
- **Descripción**: Al cambiar de vista (ej: 7→3), `web_search_mode` y `web_search_buf` no se limpiaban. Al volver a V7, el usuario quedaba atrapado en modo búsqueda con buffer viejo.
- **Causa**: Faltaban resets en `_handle_key_view_switch`.
- **Fix**: Agregado `web_search_mode = False` y `web_search_buf = ""` en `_handle_key_view_switch`.
- **Fecha**: v1.5.60
- **Commit**: `dbc0b52`

### B1-B19
Ver historial de versiones anteriores.
