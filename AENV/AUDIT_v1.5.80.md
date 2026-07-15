# AUDIT v1.5.80 — Roadmap a v1.6.x

Audit completo del código fuente. Organizado por severidad para planificar etapas.

---

## 🔴 CRÍTICOS (deben resolverse antes de features nuevas)

### BUGS SILENCIOSOS

| # | Archivo:Línea | Descripción | Estado |
|---|---------------|-------------|--------|
| C1 | `app.py:1190+1249` | **Toast double-decrement en compact mode.** `toast_ticks` se decrementa 2x por frame, toasts desaparecen a la mitad de tiempo. | ✅ v1.6.0 |
| C2 | `app.py:285-306` | **Data race en `_on_download_change`.** Callback de DownloadManager muta `entries`, `download_history`, `dl_history_filtered` desde thread worker sin locks. Main thread lee sin locks. Puede corromper estado. | ✅ v1.6.1 |
| C3 | `history.py:84-93` | **DATA LOSS: historial de reproducción no persiste.** `_do_history_remove` y `_do_history_clear` nunca llaman `save_history()`. Eliminaciones se pierden al reiniciar. | ✅ v1.6.0 |
| C4 | `web.py:329-337` | **stderr读后wait.** `proc.communicate()` se llama después de `proc.wait()`. Stderr puede estar cerrado. Leer stderr antes de wait. | ⏭️ Dead code (D1) |
| C5 | `web.py:523-526` | **TOCTOU race en `_active_count`.** Lectura sin lock permite exceder límite de concurrencia. | ✅ v1.6.1 |
| C6 | `web.py:386-387` | **`_callbacks` list race.** `add_callback` (main thread) hace append mientras `_notify` (worker) itera. `RuntimeError` posible. | ✅ v1.6.1 |
| C7 | `webexplorer.py:370-389` | **RACE CONDITION: threads mutan `app.web_results`, `web_cursor`, `web_scroll`, `web_loading` sin locks.** Also `_toast` llama curses desde thread no-main (curses no es thread-safe). | ✅ v1.6.2 |
| C8 | `webexplorer.py:541-542` | **URL incorrecta en stack.** `_add_to_queue` usa `result.url` (stream URL temporal) en vez de `result.webpage_url` (URL estable). Stack items quedan inválidos cuando expira el stream. | ✅ v1.6.0 |

---

## 🟠 ALTA PRIORIDAD

### BUGS MENORES

| # | Archivo:Línea | Descripción |
|---|---------------|-------------|
| A1 | `config.py:89-98` | **Shallow copy de nested dict.** `dict(DEFAULT_CONFIG)` comparte `custom_colors` dict entre fallback y original. Mutar uno muta ambos. | ✅ v1.6.3 |
| A2 | `config.py:70-71` | **Theme `mono` destruye jerarquía visual.** Todos los 5 color pairs quedan iguales (WHITE on default). Cursor, hints, status = mismo color. | ✅ v1.6.3 |
| A3 | `audio.py:89-91` | **Rate se pierde en `play_file`.** `set_rate()` guarda `self.rate` pero `play_file()` no lo re-aplica. Siguiente reproduceción resetea a default VLC. | ✅ v1.6.3 |
| A4 | `audio.py:187-191` | **VLC resources nunca se liberan.** `close()` solo restaura stderr. `player` y `instance` (libvlc C allocations) nunca se liberan. | ✅ v1.6.3 |
| A5 | `explorer.py:104-112` | **Playlist open sin undo.** Abrir .m3u/.pls reemplaza stack completo sin `_push_snapshot()`. | ✅ v1.6.3 |
| A6 | `radio.py:106,110,124` | **Index out of bounds.** `app.radios[app.radio_cursor]` sin bounds check. Si se borró un radio, cursor puede estar fuera de rango. | ✅ v1.6.3 |
| A7 | `config_view.py:134,211` | **Cursor = -1.** Si `config_items` queda vacío después de rebuild, cursor se pone en -1. Crash al acceder array. | ✅ v1.6.3 |
| A8 | `favorites.py:17-20` | **Vista stuck.** Early return en lista vacía puede bloquear ESC. Verificar si ESC se maneja en main dispatch. | ✅ v1.6.3 |
| A9 | `platforms.py:135-140` | **`increment_downloads` nunca persiste.** Counter se resetea a 0 en cada restart. | ✅ v1.6.3 |
| A10 | `ui.py:238` | **Dialog usa PAIR_OVERLAY para texto.** Si overlay es de bajo contraste, dialog completo ilegible. | ✅ v1.6.3 |

### CÓDIGO MUERTO

| # | Archivo:Línea | Descripción |
|---|---------------|-------------|
| D1 | `web.py:256-344` | **88 líneas: función `download()` standalone.** Nunca se llama. Todo usa `DownloadManager._download_worker`. | ✅ v1.6.3 |
| D2 | `webexplorer.py:504-517` | **Función `_do_download_direct`.** Definida pero nunca referenciada. | ✅ v1.6.3 |
| D3 | `app.py:5,7` | **Imports `shutil` y `subprocess`.** Solo usados localmente, nunca a nivel módulo. | ⏭️ Incorrecto — SÍ se usan |
| D4 | `app.py:12-14` | **Bloque `TYPE_CHECKING`.** Importa `AudioEngine`, `Stack`, `StackItem` pero también se importan incondicionalmente. | ✅ v1.6.3 |
| D5 | `app.py:80` | **`self.playlist_filter`.** Declarada pero nunca leída ni escrita. | ⏭️ Incorrecto — SÍ se usa |
| D6 | `file_utils.py:47-57` | **Función `human_size`.** Definida pero nunca llamada. | ✅ v1.6.3 |
| D7 | `audio.py:53-55` | **Propiedad `is_playing`.** Nunca se llama en el codebase. | ✅ v1.6.3 |
| D8 | `web.py:489-491` | **`get_items()`.** Duplicado exacto de propiedad `items` (línea 389-392). | ✅ v1.6.3 |
| D9 | `app.py:1164` | **`needs_cursor = False`.** Asignado pero nunca leído. | ✅ v1.6.3 |
| D10 | `app.py:292` | **Re-import `_list_dir`.** Ya importado arriba, redundante dentro del closure. | ✅ v1.6.3 |
| D11 | `ui.py:197-199` | **Parámetros `active_name` y `stack` en `draw_status`.** Nunca usados en el cuerpo. | ✅ v1.6.3 |
| D12 | `views.py:12` | **`draw_scroll_indicators` import.** Nunca se llama directamente (solo `draw_list_indicators`). | ✅ v1.6.3 |

---

## 🟡 MEDIA PRIORIDAD

### CÓDIGO REPETIDO (se puede abstraer)

| # | Patrón | Archivos | Sugerencia |
|---|--------|----------|------------|
| R1 | **Modo filtro** (init/cancel/backspace/char) | `explorer.py`, `playlist.py`, `download_history.py` | `FilterState` + `handle_filter_input()` genérico en `shared.py` | ✅ v1.6.5 |
| R2 | **Navegación de cursor** (down/up/pgup/pgdn/g/G) | 6 handlers | `navigate_cursor(cursor, key, total, page_size) -> int` | ✅ v1.6.4 |
| R3 | **Scroll clamping** | Todos los handlers | Unificar offset compact/no-compact en helper |
| R4 | **Cursor row con REVERSE highlight** | 14+ ubicaciones en `views.py` | `_draw_row(win, y, x, text, attr, is_cursor, h, w)` |
| R5 | **Duration string en borde derecho** | 4 ubicaciones en `views.py` | `_draw_item_with_duration(...)` |
| R6 | **Empty state messages** | 14 ubicaciones en `views.py` | `_draw_empty(win, msg, attr, h, w)` |
| R7 | **"No file for editing" toast** | `listen.py`, `playlist.py`, `explorer.py` | Helper compartido |
| R8 | **Add-to-stack** (append vs after_current) | `history.py`, `favorites.py`, `explorer.py` | `add_to_stack(app, items, mode)` |
| R9 | **_on_rename** callback updating refs | `explorer.py`, `playlist.py`, `shared.py` | 3 implementaciones, consolidar a 1 |
| R10 | **EQ preset cycling** | `listen.py`, `config_view.py` | Lógica duplicada, extraer a helper |
| R11 | **`clamp_scroll` duplicado** | `ui.py:180` vs `handlers/shared.py:33` | Firmas diferentes, unificar | ⏭️ Skip (diferentes firmas) |
| R12 | **`format_duration` duplicado** | `web.py:347` vs `downloads.py:173` | Comportamiento distinto para ≤0, unificar | ⏭️ Skip (deps circulares) |
| R13 | **Motor/Meta editor** | `views.py:856-915` vs `views.py:1141-1206` | Estructuralmente idénticos, share `_draw_field_editor` |
| R14 | **Color pair init por frame** | Todos los `draw_*` | Cachear referencias o namedtuple `Colors` |
| R15 | **`from ..config import save`** | `config_view.py` 12+ veces | Import a nivel módulo | ✅ v1.6.4 |

### RENDIMIENTO

| # | Archivo:Línea | Descripción |
|---|---------------|-------------|
| P1 | `config.py:load()` | Lee JSON de disco en cada llamada. Usado por `_build_stream_cmd`, `_build_download_cmd`, `_download_worker`. Cachear. |
| P2 | `web.py:390-392` | `items` property crea copia completa del list en cada acceso. Múltiples veces por frame. |
| P3 | `web.py:526` | `threading.Event().wait(0.5)` alloca Event nuevo en cada iteración del spin loop. Usar `time.sleep(0.5)`. |
| P4 | `app.py:577-588` | `_add_history` triple O(n): scan + rebuild + `insert(0)`. |
| P5 | `app.py:997` | `copy.deepcopy(self.playlist_data)` en cada undo snapshot. Playlists grandes = copies grandes. |
| P6 | `app.py:622` | `time.sleep(0.05)` busy-wait loop. Wastes CPU cuando idle. |
| P7 | `views.py:701-799` | `draw_config` reconstruye `labels` dict en cada frame. Cachear. |
| P8 | `views.py:89-119` | `draw_listen` llama `audio.get_length()` y `audio.get_time()` en cada frame. VLC API calls con locks. Cachear al inicio del render cycle. | ✅ v1.6.5 |
| P9 | `downloads.py:49-56` | `save_history` reescribe JSON completo en cada llamada. Batch o debounce. |
| P10 | `downloads.py:35-36` | `exists` property hace I/O de filesystem por acceso. Cachear o invalidar manualmente. |

---

## 🔵 BAJA PRIORIDAD

### MEJORAS DE UX

| # | Descripción |
|---|-------------|
| U1 | `draw_listen` no muestra stack size fuera del stack view. Mostrar `(N items)` indicador. |
| U2 | Explorer: directorios muestran `[+]/ ` pero no está documentado en help. |
| U3 | `draw_radio` no tiene hints/keyboard reference en la parte inferior. |
| U4 | Nav bar muestra keybindings hardcodeados, no respeta custom keybindings. |
| U5 | `draw_dialog` no soporta multi-line text. Mensajes largos se truncan. |
| U6 | No hay preview de theme antes de aplicar. Cambios son instantáneos. |
| U7 | Help system no tiene búsqueda dentro del contenido. |
| U8 | Compact mode: toast se dibuja en row 1, sobre-escribe título del box. |
| U9 | Compact listen: goto overlay puede superponerse con controls bar. |
| U10 | `curses.curs_set(0)` se llama cada frame dentro de `draw_dialog`. Mover a transición de estado. |

### ARQUITECTURA

| # | Descripción |
|---|-------------|
| X1 | **God class `PlayerApp`.** ~190 instance variables. Separar en `AudioState`, `WebState`, `UIState`, etc. |
| X2 | **`AudioEngine` mezcla 4 concerns.** VLC lifecycle + volume/rate + sleep timer + equalizer + OS stderr redirect. Descomponer. |
| X3 | **`DownloadManager` mezcla 4 concerns.** Queue + worker + SIGSTOP/SIGCONT + callback notify. Separar. |
| X4 | **`_handle_key_view_switch` resetea ~20 vars manualmente.** Agregar nueva vista requiere recordar este método. Usar pattern o dataclass de estado. |
| X5 | **Stack encapsulation undermined.** `app.stack.items = [...]` bypass setter. Callers usan `.append()`, `.insert()`, direct index. |
| X6 | **2 `save_history`/`load_history` functions.** `state.py` (playback) vs `downloads.py` (download). Import shadowing en `app.py`. Renombrar para claridad. |
| X7 | **`format_duration` duplicado con comportamiento distinto.** `web.py` retorna `"--:--"` para ≤0, `downloads.py` retorna `""`. |
| X8 | **Hardcoded config path.** `~/.config/tplay/` en múltiples archivos. Centralizar. |

### VISUAL / TRUNCATION

| # | Archivo:Línea | Descripción |
|---|---------------|-------------|
| V1 | `views.py:672,684` | Download history titles se truncan sin ellipsis. Todas las demás vistas usan `[:max-1] + "..."`. | ✅ v1.6.5 |
| V2 | `views.py:924` | `draw_radio` usa `app.LIST_H` en vez del constante importado `LIST_H`. Divergence hazard. | ✅ v1.6.5 |
| V3 | `ui.py:648` | Dos help tabs se llaman "Historial" (tab 4 = playback history, tab 9 = download history). Confuso. | ✅ v1.6.5 |
| V4 | `config.py:72-73` | Theme `calido` usa `COLOR_RED` para nav y destacar. Roles indistinguibles. | ✅ v1.6.5 |
| V5 | `config.py:78` | Theme `custom` inicializa todos los colores a 0 (COLOR_BLACK). Si falta `apply_theme`, texto invisible. | ✅ v1.6.5 |
| V6 | `config.py:115` | Color name inválido en custom_colors silenciosamente fallback a WHITE. Sin feedback al usuario. |

---

## 📋 PLAN DE ETAPAS v1.6.x

### Etapa 1: Critical Bugs (v1.6.0)
- [x] C1: Fix toast double-decrement ✅ v1.6.0
- [x] C2: Fix data race en download callback (agregar lock) ✅ v1.6.1
- [x] C3: Fix history data loss (agregar save_history) ✅ v1.6.0
- [x] C4: Fix stderr-after-wait en web.py ⏭️ Dead code (D1)
- [x] C5: Fix TOCTOU race en active_count ✅ v1.6.1
- [x] C6: Fix _callbacks list race ✅ v1.6.1
- [x] C7: Fix thread safety en webexplorer (usar queue para comunicación main↔worker) ✅ v1.6.2
- [x] C8: Fix URL incorrecta en _add_to_queue ✅ v1.6.0

### Etapa 2: High Priority Bugs + Dead Code (v1.6.3)
- [x] A1-A10: Bugs menores ✅ v1.6.3
- [x] D1-D12: Eliminar código muerto ✅ v1.6.3 (D3,D5 skipped — audit incorrecto)

### Etapa 3: Abstracciones + DRY (v1.6.5)
- [x] R1: FilterState + handle_filter_text genérico ✅ v1.6.5
- [x] R2: navigate_cursor helper ✅ v1.6.4
- [x] R4-R6: Drawing helpers ⏭️ draw_item_row ya existe
- [x] R11: clamp_scroll unificado ⏭️ Skip (diferentes firmas)
- [x] R12: format_duration unificado ⏭️ Skip (deps circulares)
- [x] R13: Motor/Meta editor shared ⏭️ Skip (diferentes estructuras)
- [x] R15: import save a nivel módulo ✅ v1.6.4

### Etapa 4: Performance (v1.6.5)
- [x] P8: Audio time/length cache ✅ v1.6.5
- [x] P10: exists property I/O ⏭️ Skip (stat rápido)
- [ ] P1-P7,P9: Performance restantes (config cache, items property, etc.)

### Etapa 5: UX + Visual (v1.6.5)
- [x] V1-V5: Visual fixes ✅ v1.6.5
- [x] V6: Color name fallback ⏭️ Skip (fallback seguro)
- [ ] U1-U10: UX improvements

### Etapa 4: Performance (v1.6.3)
- [ ] P1: Cache config load
- [ ] P2-P3: DownloadManager optimizations
- [ ] P4-P6: App state optimizations
- [ ] P7-P10: View render optimizations

### Etapa 5: UX + Visual (v1.6.4)
- [ ] U1-U10: UX improvements
- [ ] V1-V6: Visual fixes

### Etapa 6: Architecture (v1.7.0)
- [ ] X1-X8: Refactoring mayor (God class, AudioEngine, DownloadManager)

---

## 📊 ESTADÍSTICAS

| Categoría | Count |
|-----------|-------|
| 🔴 Críticos | 8 |
| 🟠 Alto (bugs) | 10 |
| 🟠 Alto (dead code) | 12 |
| 🟡 Medio (DRY) | 15 |
| 🟡 Medio (perf) | 10 |
| 🔵 Bajo (UX) | 10 |
| 🔵 Bajo (arquitectura) | 8 |
| 🔵 Bajo (visual) | 6 |
| **Total items** | **79** |
