# CHANGELOG — tplay

## v1.7.0
- fix: F1 — `_has_node()` cached helper, `--js-runtime node` condicional en `_build_stream_cmd`/`_build_download_cmd`
- fix: F2 — VLC import wrapped en try/except con `_VLC_ERROR` fallback, `AudioEngine.__init__` check `vlc is None`
- fix: F3 — `requirements.txt` pinned: `python-vlc>=3.0.0,<4.0.0`, `yt-dlp==2026.07.04`
- fix: F4 — `--` end-of-options en `_build_search_cmd`, `_build_stream_cmd`, `_build_download_cmd`
- fix: F5 — `_do_mkdir` validates `os.path.realpath(result).startswith(root + os.sep)`
- fix: F6 — Stack thread safety via `_stack_pending_adds` pending-flag pattern en `app.py` + `webexplorer.py`
- fix: F7 — `atomic_write()` en `file_utils.py`, aplicado a config/state/downloads/playlist/platforms/favorites/radios
- fix: F8 — `_confirm` dialogs antes de `_clear_tab` y `_remove_and_delete` en `download_history.py`

## v1.6.7
- feat: U1 — `draw_listen` muestra stack size `(N)` en el título cuando hay items
- feat: U2 — help tab "Explorador" documenta indicador `[+]/` para directorios con subdirs
- feat: U3 — `draw_radio` muestra hints bar (Enter, a/A, e, d, f, x)
- feat: U5 — `draw_dialog` soporta multiline text (separado por `\n`), ajusta altura automáticamente
- fix: U8 — toast en compact mode ahora se dibuja en `h-2` en vez de row 1 (no sobreescribe contenido)
- fix: U9 — goto overlay en compact mode respeta `h-3` para no superponerse con controls bar
- refactor: U10 — `curses.curs_set(0)` movido de `draw_dialog` a `_prompt()` y `_confirm()` (state transition)
- docs: Security audit completo (`AUDIT_v1.6.7_SECURITY.md`) — 27 hallazgos, 2 critical, 11 high
- skip: U4 (nav bar correcto), U6 (complejo), U7 (feature nueva)

## v1.6.6
- perf: P1 — `config.load()` cachea con mtime invalidation (evita re-leer JSON en cada llamada)
- perf: P4 — `_add_history` usa `next()` + `remove()` en vez de scan + rebuild O(n)
- perf: P5 — `_snapshot_state` usa shallow copy (list comprehension) en vez de `copy.deepcopy`
- refactor: elimina `import copy` de app.py (ya no se usa)
- skip: P2 — items property copy es necesaria para thread safety (max 3 items)
- skip: P3 — ya usa `time.sleep(0.5)`, no `threading.Event().wait()`
- skip: P6 — `time.sleep(0.05)` es frame rate limiter, no busy-wait
- skip: P7 — labels dict trivial, no vale cachear
- skip: P9 — save_history es infrequent, debounce añade complejidad innecesaria

## v1.6.5
- refactor: R1 — `FilterState` dataclass + `_handle_filter_text()` genérico en shared.py
- perf: P8 — `audio.refresh_time_cache()` cachea time/length una vez por frame (reduce VLC locks)
- fix: V1 — download history titles ahora usan ellipsis al truncar
- fix: V2 — `draw_radio` usa constante `LIST_H` en vez de `app.LIST_H`
- fix: V3 — help tab "Historial" duplicado renombrado a "Descargas"
- fix: V4 — theme `calido` nav cambiado de RED a GREEN (diferente de destacar)
- fix: V5 — theme `custom` defaults a CYAN/WHITE/YELLOW/GREEN/MAGENTA en vez de todo BLACK
- skip: R4-R6 — `draw_item_row` ya existe como helper, no vale duplicar
- skip: R13 — keybindings y meta editor son estructuralmente diferentes
- skip: P10 — `exists` property I/O es rápido (stat syscall), no vale cachear
- skip: V6 — fallback a WHITE ya es seguro, no necesita toast

## v1.6.4
- refactor: R2 — `_navigate_cursor()` helper en shared.py (down/up/pgup/pgdn/g/G)
- refactor: R2 — explorer, playlist, download_history, favorites, radio usan `_navigate_cursor()`
- refactor: R15 — `config_view.py` import `save as _save_config` a nivel módulo (eliminados 15 imports locales)
- skip: R11 — clamp_scroll unificado (diferentes firmas, no vale el churn)
- skip: R12 — format_duration unificado (dependencias circulares, no vale el churn)

## v1.6.3
- fix: A1 — shallow copy de nested dict en config fallback (copy.deepcopy)
- fix: A2 — theme mono ahora usa MONO_BOLD flag para diferenciar visual hierarchy
- fix: A3 — rate se re-aplica en play_file() después de cada reproducción
- fix: A4 — VLC resources (player/instance) ahora se liberan en close()
- fix: A5 — playlist open (.m3u/.pls) ahora push snapshot antes de reemplazar stack
- fix: A6 — radio.py bounds check antes de acceder app.radios[radio_cursor]
- fix: A7 — config_view cursor se clamp a max(0, len-1) después de rebuild
- fix: A8 — favorites ESC siempre funciona, incluso con lista vacía
- fix: A9 — increment_downloads ahora persiste con save_platforms()
- fix: A10 — dialog text usa PAIR_TEXTO en vez de PAIR_OVERLAY (mejor contraste)
- refactor: D1-D12 dead code eliminado (D3,D5 skipped — audit incorrecto)

## v1.6.2
- fix: C7 — thread safety en webexplorer: search y play usan pending flags (main loop procesa)

## v1.6.1
- fix: C2 — data race en _on_download_change: callback setea flag, main loop procesa
- fix: C5 — TOCTOU race en _active_count: lectura bajo _active_lock
- fix: C6 — _callbacks list race: copia lista antes de iterar en _notify
- fix: P3 — reemplazado threading.Event().wait() por time.sleep() en worker loop

## v1.6.0
- fix: C1 — toast double-decrement en compact mode (app.py)
- fix: C3 — history data loss: _do_history_remove/_clear ahora persisten con save_history()
- fix: C8 — _add_to_queue resuelve stream URL async en vez de usar URL temporal

## v1.5.80
- feat: #4+#5 Historial unificado (descargas+streams) con tabs [Descargas] [Streams]
- feat: DownloadEntry campos `is_temp`, `duration`, `channel`, `play_count`
- feat: `get_downloads()`, `get_streams()`, `clean_old_temps()`, `format_duration()`
- feat: DownloadItem.output_dir + add_download(output_dir=) para streams temporales
- feat: Tabs con `[/]`, `X` limpia tab activo, `d` re-busca stream / re-descarga download
- feat: Auto-save stream en `_play_web_result()` → historial + DownloadManager a TMP_DIR
- feat: Help tab "Historial" unificado
- fix: View switch 0-8 range + dl_history_tab reset

## v1.5.79
- feat: #4 Download History — downloads.py (CRUD), handlers/download_history.py, views.py
- feat: DownloadItem + campo `platform`, add_download acepta platform param
- feat: Help tab "Descargas" + H key hint en Web tab
- feat: View switch 0-8 range + H key en Web Explorer → V_DL_HISTORY
- fix: B60 — DownloadManager integrado completamente en handler/views/app
- fix: B60 — Eliminadas variables viejas (web_download_queue, web_download_cancel, web_download_paused, web_result_status)
- fix: B60 — Views leen de get_result_status() (combina playing + download state)
- feat: Config online_cookies (none/firefox/chromium) + --js-runtime node
- feat: Auto-refresh explorer al completar descarga (callback en DownloadManager)
- fix: B60 — q exit: solo cuenta items activos (QUEUED/DOWNLOADING/PAUSED) + reset counter tras 5s
- fix: YouTube bot detection: --js-runtime node para resolver signatures
- fix: B61 — .part cleanup on exit: shutdown() fix deadlock + finally block en run()

## v1.5.78
- feat: DownloadManager class (worker loop, cola, concurrencia limitada)
- feat: DownloadState enum (QUEUED, DOWNLOADING, PAUSED, COMPLETED, FAILED, STOPPED)
- feat: DownloadItem dataclass con estado independiente por item
- feat: pause_item() usa SIGSTOP/SIGCONT (Linux)
- feat: stop_item() mata proceso y limpia .part
- feat: get_download_manager() singleton

## v1.5.77
- fix: B59 — Pause/resume: agregado --continue al cmd de descarga, _cleanup_part_files solo en cancel explícito

## v1.5.76
- fix: B55 — Pause/Resume: _run() verifica web_download_paused antes de sobreescribir estado
- fix: B56 — Cancel: web.py retorna "Cancelado por usuario" (consistente con handler)
- fix: B57 — Vista 7 lenta: is_available() cacheada con variable global (1 sola ejecución)
- fix: B58 — Temp files: _cleanup_part_files() elimina *.part al cancelar
- feat: _play_web_result() async (get_stream_url en thread, no bloquea UI)

## v1.5.75
- feat: B54 — web.py migrado de Python API (yt_dlp.YoutubeDL) a subprocess (evita bot detection YouTube)
- feat: search() usa subprocess + --flat-playlist --dump-json (parse JSON lines)
- feat: get_stream_url() usa subprocess + --get-url -f bestaudio/best
- feat: download() usa subprocess con cancel_event para cancelación
- refactor: eliminada dependencia de yt_dlp.utils.DownloadCancelled en webexplorer.py
- fix: is_available() verifica yt-dlp via subprocess --version (no import)

## v1.5.74
- fix: B44 — ESC en download/motor config vuelve a V7 (excepciones en _handle_key_global)
- fix: B45 — Enter descarga desde Calidad (web_download_idx guarda cursor al abrir config)
- fix: B46 — d/D pausa/reanuda con Event por-ítem (dict[int, Event] en vez de Event único)
- fix: B47 — c cancela y limpia estado (web_download_paused.pop, status → [-])
- fix: B48 — q global verifica queue + paused antes de cerrar
- refactor: B49 — Motor cíclico hl sin vista exclusiva, a/e/d gestión inline, eliminar _handle_motor_mode/_draw_motor_list
- fix: B50 — Motor editor: solo Esc para cancelar (q cierra app)
- fix: B51 — Motor indicator formato ← [MOTOR] →
- fix: B52 — Búsqueda Sin Resultados: eliminada 2da extracción, stream URL on-demand con get_stream_url()
- fix: B53 — Errores de descarga/play: _classify_error() traduce yt-dlp errors a mensajes amigables, get_stream_url() retorna None en error

## v1.5.73
- fix: B40 — d/D toggle pause/resume: verifica queue + status, no solo status
- fix: B41 — ESC en download config vuelve a Web Explorer (V_WEB)
- fix: B42 — q global confirma si hay descargas activas (doble q para salir)
- fix: B43 — cancel real: status queda [C], error status [!], no [−]

## v1.5.72
- fix: B36 — Explorer refresca siempre al completar descarga
- fix: B37 — redirect fd 2 (stderr) a /dev/null, suprime output yt-dlp sin cortar curses
- fix: B38 — d/D toggle inicia/pausa/reanuda, c cancela con [C], d/D reinicia despues de cancel
- fix: B39 — Estados validados: [-][D][##%][PP][P][C][✓][!][Q][►]

## v1.5.71
- fix: yt-dlp progress=False → noprogress=True (param correcto, progress no existía)
- fix: eliminado os.dup2 redirect (cortaba stdout de curses, por eso no se veía [%])
- feat: cancel descarga con c — DownloadCancelled + threading.Event
- feat: pause descarga con P — cancel +保存 config para resume con continuedl
- fix: estado [PP] post-processing (100% → [PP] → [✓])
- fix: estado [P] pausa (doc一致)

## v1.5.70
- fix: B33 — yt-dlp progress=False + eliminadas opciones falsas stdout/stddev (corrompía curses)
- fix: B34 — _get_download_url quality_map: worst/144p/240p
- fix: B35 — _config_int_inc/dec: online_download_max ahora funcional
- fix: thread safety — bounds check en progress callback + completion handler

## v1.5.69
- fix: B32 — toast reposicionado a h-2 (borde inferior del box)

## v1.5.68
- fix: B31 — yt-dlp output redirect a /dev/null (no corrompe curses)
- fix: B30 — download config: Esc cancela, aesthetic `[val] ←→`
- fix: B29 — quality options: worst,144p,240p,480p,720p,1080p,best
- feat: config tab "Sistema" — settings de descarga (formato, calidad, máx)

## v1.5.67
- fix: B26 — download config cíclico (←→/hl para format y quality)
- fix: B27 — estado play preciso con web_playing_idx
- fix: B28 — toast reposicionado arriba de status bar

## v1.5.66
- fix: B25 — download no bloqueante (thread + progress % en lista)
- fix: B25 — nombre archivo usa título (page URL en vez de stream URL)
- fix: B25 — Explorer refresca post-descarga
- fix: B24 — feedback visual de carga en búsqueda ("Buscando..." blink)
- fix: B23 — prompt persiste query post-búsqueda

## v1.5.65
- feat: config.py — defaults downloads (platform, format, quality, stream, max)
- feat: ui.py — help tab Web actualizado con todas las teclas nuevas

## v1.5.64
- feat: views.py — draw_web() reescrito con motor+prompt+divider+lista
- feat: views.py — draw_motor_editor() y draw_download_config()
- feat: views.py — estados en lista: [-] [►] [D] [P] [Q] [✓] [X] [!]

## v1.5.63
- feat: webexplorer.py — 3 modos (normal/search/motor)
- feat: webexplorer.py — gestión de plataformas (add/edit/delete)
- feat: webexplorer.py — descarga directa (D) y con config (d)
- feat: webexplorer.py — cola de descarga (max 3)
- feat: app.py — nuevos estados web

## v1.5.62
- fix: B22 — search() con extract_flat=True retorna resultados reales
- feat: web.py — download() para audio (mp3) / video (mp4)
- feat: web.py — WebResult.download_url

## v1.5.61
- feat: platforms.py — Platform dataclass + 6 defaults
- feat: platforms.py — load/save/get_search_prefix/increment_downloads

## v1.5.59
- fix: Custom EQ — key `custom_bands` guarda estado independiente
- refactor: eliminado `r` reset de Config/Audio
- feat: Listen hints toggle con `;`

## v1.5.57
- fix: Config/Audio bands siempre visibles
- fix: History g/G implementados

## v1.5.56
- refactor: draw_tab_carousel() helper
- refactor: clamp_scroll() + draw_list_indicators() helpers

## v1.5.55
- feat: Config/Audio — bandas EQ en modo solo lectura
- feat: Config/Audio — hints contextuales

## v1.5.54
- feat: Listen view — metadata centrada
- feat: Listen view — indicador de volumen visual

## v1.5.53
- feat: draw_box_inline() — box inline para sub-views
- feat: Scroll indicators — ▲/▼ en vistas con scroll

## v1.5.52
- feat: COMPACT_THRESHOLD — vista compacta
- feat: Icono pausa ❚❚ en listen view
- feat: Separadores en Config/Audio

## v1.5.50
- feat: EQ refinado — preamp configurable, Custom en Config

## v1.5.49
- feat: Ecualizador gráfico — VLC API, 10 bandas, presets

## v1.5.48
- fix: symlinks-to-dirs en Explorer

## v1.5.47
- feat: 9 extensiones nuevas

## v1.5.46
- feat: Explorer read-only fuera del root

## v1.5.45
- feat: AENV setup
