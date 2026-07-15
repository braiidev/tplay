# BUGS — tplay

## Activos
_(ninguno)_

## Resueltos recientes

### Audit C1 — Toast double-decrement en compact mode
- **Archivo**: `player/app.py`
- **Descripción**: `toast_ticks` se decrementaba 2x por frame en compact mode (línea 1190 + 1249).
- **Fix**: Agregado guard `not compact` en toast no-compact (línea 1238).
- **Estado**: Resuelto en v1.6.0

### Audit C2 — Data race en _on_download_change
- **Archivo**: `player/app.py`
- **Descripción**: Callback de DownloadManager mutaba `entries`, `download_history`, `dl_history_filtered` desde thread worker sin locks.
- **Fix**: Callback ahora solo setea flag `_download_completed_pending`. Main loop procesa en `_process_download_completions()`.
- **Estado**: Resuelto en v1.6.1

### Audit C3 — History data loss
- **Archivo**: `player/handlers/history.py`
- **Descripción**: `_do_history_remove` y `_do_history_clear` nunca persistían cambios a disco.
- **Fix**: Agregado `save_history(app.history)` después de mutaciones.
- **Estado**: Resuelto en v1.6.0

### Audit C5 — TOCTOU race en _active_count
- **Archivo**: `player/web.py`
- **Descripción**: `_active_count` se leía sin lock en el while loop del worker, permitiendo exceder límite de concurrencia.
- **Fix**: Lectura bajo `_active_lock`. También reemplazado `threading.Event().wait()` por `time.sleep()`.
- **Estado**: Resuelto en v1.6.1

### Audit C6 — _callbacks list race
- **Archivo**: `player/web.py`
- **Descripción**: `add_callback` (main thread) hacía append mientras `_notify` (worker) iteraba la lista.
- **Fix**: `_notify()` ahora copia lista antes de iterar.
- **Estado**: Resuelto en v1.6.1

### Audit C8 — URL incorrecta en _add_to_queue
- **Archivo**: `player/handlers/webexplorer.py`
- **Descripción**: `_add_to_queue` usaba `result.url` (stream URL temporal) en vez de `result.webpage_url`.
- **Fix**: Ahora resuelve stream URL async con `get_stream_url()` antes de agregar al stack.
- **Estado**: Resuelto en v1.6.0

### B61 — .part files no se limpian al salir de la app
- **Archivo**: `player/web.py`, `player/app.py`
- **Descripción**: Al salir de la app con descargas en curso, los archivos `.part` quedaban en `~/Music` ocupando espacio. También `shutdown()` tenía deadlock (sostén `_lock` + llamada a `stop_item()` que también agarraba `_lock`).
- **Causa**: `app.py` no llamaba `dm.shutdown()` al salir. `shutdown()` intentaba llamar `stop_item()` mientras sostén el lock.
- **Fix**: `shutdown()` ahora recolecta IDs primero, suelta lock, luego llama `stop_item()`. `finally` block en `run()` llama `dm.shutdown()` en cualquier salida (q, Ctrl+C, error).
- **Estado**: Resuelto en v1.5.79

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
