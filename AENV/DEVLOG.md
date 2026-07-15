# DEVLOG — tplay

## Entrada 1 — 2025-07-14 — Setup AENV
- Migrar tracking a sistema AENV
- Archivos: STATE.md, DEVLOG.md, BUGS.md, TODO.md, CHANGELOG.md, TEST.md, docs/
- Estado: v1.5.45

---

## Entrada 2 — 2025-07-14 — Explorer read-only fuera del root
- `_is_inside_root()` + bloqueo ops de escritura + indicador `[RO]`
- Estado: v1.5.46

---

## Entrada 3 — 2025-07-14 — 9 extensiones nuevas
- .m4a .aac .opus .weba .wma .aiff .aif .flv .wmv
- Estado: v1.5.47

---

## Entrada 4 — 2025-07-14 — Fix symlinks en Explorer
- `entry.is_dir(follow_symlinks=True)` en file_utils.py
- Estado: v1.5.48

---

## Entrada 5-9 — 2025-07-14 — F2 Ecualizador
- Ecualizador gráfico 10 bandas + 16 presets + Custom mode
- Preamp configurable, barras visuales, r reset, hints contextuales
- Estado: v1.5.55, mypy strict pasa

---

## Entrada 10-12 — 2025-07-14 — Rediseño visual
- draw_box_inline, scroll indicators, tab carousel helper
- Listen metadata centrada + volumen visual
- Config/Audio polish (solo lectura bands + hints)
- Estado: v1.5.55, mypy strict pasa

---

## Entrada 13-14 — 2025-07-14 — Bug fixes post-rediseño
- B14: Config/Audio bands siempre visibles
- B15: History g/G implementados
- Estado: v1.5.57

---

## Entrada 15-16 — 2025-07-14 — Bug fixes B13+B16+B17
- B13: Listen hints toggle con `;`
- B16: Custom EQ persistence (`custom_bands`)
- B17: Config/Audio cursor skip disabled bands
- Cleanup: eliminado r reset (conflicto con shuffle)
- Estado: v1.5.59, 0 bugs activos

---

## Entrada 17-21 — 2025-07-15 — F10: Web Explorer v2 (consolidado)

### Phase 1: Platform Registry (v1.5.61)
- `player/platforms.py` — Platform dataclass + load/save + 6 defaults

### Phase 2: Wrapper yt-dlp (v1.5.62)
- `player/web.py` — search(), get_stream_url(), download() con subprocess

### Phase 3: Handler V7 (v1.5.63)
- `player/handlers/webexplorer.py` — 3 modos (normal/search/motor) + descarga

### Phase 4: Views V7 (v1.5.64)
- `player/views.py` — draw_web + motor_list + motor_editor + download_config

### Phase 5: App & Config (v1.5.65)
- config.py defaults + ui.py help tab Web

### Phase 6: Polish (v1.5.66-v1.5.74)
- B22-B59: Search fix, motor editor, error handling, pause/resume, cancel
- Migración Python API → subprocess (bot detection fix)
- `--continue` flag para pause/resume

### Phase 7: DownloadManager (v1.5.78-v1.5.79)
- **v1.5.78**: `DownloadManager` class (worker loop, cola, concurrencia, SIGSTOP/SIGCONT)
- **v1.5.79**: Integración completa en handler/views/app
  - Eliminadas variables viejas (`web_download_queue`, `web_download_cancel`, `web_download_paused`)
  - Views leen de `get_result_status()` (combina playing + download state)
  - Config `online_cookies` (none/firefox/brave/chromium) + `--js-runtime node`
  - Auto-refresh explorer al completar descarga
  - Fix `q` exit bug (count only active + reset after 5s)

**Archivos tocados**: web.py, webexplorer.py, app.py, views.py, config.py, config_view.py

**Descubrimientos**:
- YouTube requiere `--js-runtime node` para resolver signatures (yt-dlp 2026.7.4+)
- Firefox cookies funciona; Brave no tiene DB de cookies instalada
- `--cookies-from-browser` es la única forma confiable de bypass bot detection
- `yt-dlp[default]` instala `yt-dlp-ejs` (challenge solver)

**Estado**: v1.5.79, mypy strict pasa, B60 resuelto, 0 bugs activos

---

## Entrada 12 — 2025-07-15 — #4 Download History (parcial)
- `downloads.py`: DownloadEntry dataclass, load_history, save_history, add_entry, remove_entry, format_size
- `handlers/download_history.py`: handle_download_history con j/k/g/G/d/D/c/x// keys
- `views.py`: draw_download_history() con layout consistente con Historial/Playlist
- `web.py`: DownloadItem + campo `platform`, add_download acepta platform param
- `handlers/webexplorer.py`: 3 llamadas a add_download ahora pasan result.platform
- `app.py`: V_DL_HISTORY=8, state vars, handler/drawer mappings, callback auto-save completed downloads
- `handlers/__init__.py`: expose handle_download_history
- `ui.py`: Help tab "Descargas" + H key hint en Web tab
- `app.py`: View switch 0-8 range + H key en Web Explorer → V_DL_HISTORY

**Estado**: v1.5.79, mypy strict pasa (28 archivos), archivos compilan OK

---

## Entrada 13 — 2025-07-15 — #4+#5 Historial Unificado
- `downloads.py`: campos `is_temp`, `duration`, `channel`, `play_count` + `get_downloads()`, `get_streams()`, `clean_old_temps()`, `format_duration()`
- `web.py`: `DownloadItem.output_dir` + `add_download(output_dir=)` para streams temporales
- `handlers/download_history.py`: tabs `[`/`]`, `_switch_tab()`, `_get_current_items()`, `_play_entry()`, `_re_download()` (re-busca stream / re-descarga download), `_clear_tab()` (X key)
- `views.py`: `draw_download_history()` con tab bar, streams muestran `♪ duración Nx`, downloads muestran `✓ tamaño`
- `handlers/webexplorer.py`: `_play_web_result()` auto-save stream a historial + DownloadManager a TMP_DIR
- `app.py`: `dl_history_tab` state var, reset en view switch
- `ui.py`: Help tab "Historial" unificado

**Estado**: v1.5.80, mypy strict pasa (28 archivos), archivos compilan OK

---

## Entrada 14 — 2025-07-15 — v1.6.0 Audit: Critical Bugs
- C1: `app.py` — toast double-decrement en compact mode. Agregado guard `not compact` en toast no-compact.
- C3: `handlers/history.py` — data loss: `_do_history_remove` y `_do_history_clear` nunca persistían. Agregado `save_history()` después de mutaciones.
- C8: `handlers/webexplorer.py` — `_add_to_queue` usaba `result.url` (stream temporal). Cambiado a resolver stream URL async con `get_stream_url()` antes de agregar al stack.
- C4: `web.py` — skip (dead code, función `download()` nunca se llama).

**Estado**: v1.6.0, mypy strict pasa (28 archivos), archivos compilan OK

---

## Entrada 15 — 2025-07-15 — v1.6.1 Audit: Thread Safety
- C5: `web.py` — TOCTOU race en `_active_count`. Loop ahora lee bajo `_active_lock` antes de proceder. También reemplazado `threading.Event().wait(0.5)` por `time.sleep(0.5)` (P3).
- C6: `web.py` — `_callbacks` list race. `_notify()` ahora copia lista antes de iterar (`cbs = list(self._callbacks)`).
- C2: `app.py` — data race en `_on_download_change`. Callback ahora solo setea flag `_download_completed_pending`. Main loop procesa en `_process_download_completions()` (seguro, main thread).

**Estado**: v1.6.1, mypy strict pasa (28 archivos), archivos compilan OK

---

## Entrada 16 — 2025-07-15 — v1.6.2 Audit: Thread Safety (webexplorer)
- C7: `handlers/webexplorer.py` — `_do_search._run()` y `_play_web_result._run()` mutaban `app.web_results`, `web_cursor`, `web_scroll`, `web_loading`, `stack.items`, `current_view` y llamaban `_toast()` desde threads workers.
- Fix: Workers ahora solo setean `_web_search_pending`/`_web_search_error` y `_web_play_pending`/`_web_play_error`. Main loop procesa en `_process_web_search()` y `_process_web_play()` (seguro, main thread).
- Patrón idéntico al C2 (download callback).
- Etapa 1 Audit COMPLETADA ✅ (C1-C8, C4 skipped dead code).

**Estado**: v1.6.2, mypy strict pasa (28 archivos), archivos compilan OK
