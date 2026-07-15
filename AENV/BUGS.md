# BUGS — tplay

## Activos
_(ninguno)_

## Resueltos recientes

### B60 — Cola de descargas no funciona correctamente
- **Archivo**: `player/handlers/webexplorer.py`, `player/app.py`
- **Descripción**: Todos los items mostraban estado del primero; [Q] nunca se ejecutaba; cancel/pause afectaba todos; q no contaba solo activos.
- **Causa**: Sistema viejo usaba `web_download_queue` + `threading.Event` por-item sin aislamiento real.
- **Fix**: DownloadManager completo (v1.5.78-79): worker loop, cola, concurrencia, SIGSTOP/SIGCONT, `find_by_url()`. `q` solo cuenta items activos + reset counter tras 5s.
- **Estado**: Resuelto en v1.5.79

### B59 — Pause/resume reinicia desde 0%
- **Archivo**: `player/web.py`
- **Descripción**: Al reanudar descarga pausada, yt-dlp reiniciaba desde 0%.
- **Causa**: Falta flag `--continue` en comando yt-dlp.
- **Fix**: Agregado `--continue` a `_build_download_cmd`.
- **Estado**: Resuelto en v1.5.77

### B55-B58 — Descarga: slowness, estado inconsistente, temp files
- **Archivo**: `player/web.py`, `player/handlers/webexplorer.py`
- **Descripción**: Vista7 slowness (is_available spawneaba subprocess), estado inconsistente al cancelar, archivos .part no se limpiaban.
- **Fix**: `is_available()` cached; `_cleanup_part_files()` solo en cancel explícito.
- **Estado**: Resuelto en v1.5.76

### B54 — YouTube bot detection bloquea todas las operaciones
- **Archivo**: `player/web.py`
- **Descripción**: La API de Python (`yt_dlp.YoutubeDL`) es detectada por YouTube y bloqueada.
- **Fix**: Migrado a subprocess (v1.5.75) + `--js-runtime node` + config `online_cookies` (v1.5.79).
- **Estado**: Resuelto en v1.5.75 + v1.5.79

## Resueltos (legacy)
Ver historial de versiones anteriores.
