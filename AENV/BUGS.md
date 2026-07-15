# BUGS — tplay

## Activos

_(ninguno)_

## Resueltos

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
