# DEVLOG — tplay

## Entrada 1 — 2025-07-14 — Setup AENV

**Tarea**: Migrar tracking del proyecto a sistema AENV

**Archivos creados**:
- AENV/STATE.md
- AENV/DEVLOG.md
- AENV/BUGS.md
- AENV/TODO.md
- AENV/CHANGELOG.md
- AENV/TEST.md
- AENV/docs/INDEX.md
- AENV/docs/MODELS.md
- AENV/docs/BUSINESS.md
- AENV/docs/ARCH.md
- AGENTS.md (reescribido como índice)

**Decisión**: Migración completa — el proyecto ya tiene documentación extensa en AGENTS.md y TODO.md, se reorganiza en estructura AENV estándar.

**Estado**: v1.5.45, 128+ items completados, pendiente F2 (ecualizador).

---

## Entrada 2 — 2025-07-14 — Explorer read-only fuera del root

**Tarea**: Implementar modo solo-lectura en el Explorer para directorios fuera del music_dir configurado

**Archivos modificados**:
- `player/handlers/explorer.py` — `_is_inside_root()`, bloqueo de ops de escritura
- `player/views.py` — indicador `[RO]` en título del Explorer

**Decisión**: Solo lectura (no bloqueo total) — el usuario puede navegar libremente pero no modificar archivos fuera del directorio raíz. Operaciones bloqueadas: delete, mkdir, rename, copy, move, tag edit.

**Estado**: v1.5.46, mypy strict pasa.

---

## Entrada 3 — 2025-07-14 — 9 extensiones nuevas

**Tarea**: Agregar soporte para .m4a .aac .opus .weba .wma .aiff .aif .flv .wmv

**Archivos modificados**:
- `player/file_utils.py` — AUDIO_EXT, VIDEO_EXT, EXT_LABEL

**Decisión**: Solo alta + media (9 ext). No se agregan nicho audiophile (.wv .ape .tak .tta) ni video legacy (.3gp .mpg .mpeg .ts .m4v .ogv).

**Estado**: v1.5.47, mypy strict pasa.

---

## Entrada 4 — 2025-07-14 — Fix symlinks en Explorer

**Tarea**: Corregir bug donde Explorer no ve directorios que son symlinks

**Causa raíz**: refactor P1 (os.listdir → os.scandir) usó `follow_symlinks=False`, que ignora symlinks-to-dirs. `os.listdir` + `os.path.isdir()` los seguía.

**Fix**: `entry.is_dir(follow_symlinks=True)` en file_utils.py

**Estado**: v1.5.48, mypy strict pasa.

---

## Entrada 5 — 2026-07-14 — F2 Ecualizador gráfico

**Tarea**: Implementar ecualizador gráfico de 10 bandas con presets y modo Custom

**Archivos modificados**:
- `player/audio.py` — +6 métodos EQ (set_equalizer, apply_preset, disable_equalizer, get_equalizer_info, reapply_equalizer), reapply en play_file
- `player/config.py` — defaults EQ + 16 presets (Flat..Custom) + EQ_PRESET_NAMES
- `player/app.py` — config tab Audio, persistencia session (save/resume), eq_edit_mode + _handle_eq_edit
- `player/handlers/listen.py` — tecla E toggle EQ
- `player/handlers/config_view.py` — _cycle_eq_preset, _toggle_bool con EQ, abre overlay Custom
- `player/views.py` — [EQ] indicator, hint E, draw_eq_overlay (10 bandas + preamp), compact EQ indicator
- `player/state.py` — save_state con eq_enabled/eq_bands/eq_preamp/eq_preset

**Decisión**: 
- VLC API: `set_amp_at_index`/`get_amp_at_index` (no `set_band_value`)
- 16 presets propios (no nativos de VLC) — más control sobre los valores
- Custom mode: overlay con j/k/h/l/r/s/Esc
- Re-aplicar EQ después de play_file por seguridad

**Estado**: v1.5.49, mypy strict pasa.

---

## Entrada 6 — 2026-07-14 — F2 refinamiento EQ

**Tarea**: Refinar ecualizador — eliminar overlay, integrar Custom en Config, preamp configurable, fix volumen

**Cambios**:
- Eliminado: eq_edit_mode, draw_eq_overlay, _handle_eq_edit (overlay system)
- Tecla E ahora cicla presets, e toggle ON/OFF
- Preamp configurable para TODOS los presets (no solo Custom)
- Custom bandas integradas en Config/Audio tab (items dinámicos con tipo eq_band)
- Default preamp +12dB para compensar reducción de volumen de VLC
- Helper _reapply_eq en config_view.py

**Archivos modificados**:
- `player/app.py` — _build_config_tabs dinámico, eliminado overlay
- `player/config.py` — eq_preamp default 12.0
- `player/handlers/listen.py` — E=ciclar, e=toggle
- `player/handlers/config_view.py` — _eq_preamp_inc/dec, _eq_band_inc/dec, _reapply_eq
- `player/views.py` — draw_config muestra preamp/bands, eliminado draw_eq_overlay

**Estado**: v1.5.50, mypy strict pasa.

---

## Entrada 7 — 2026-07-14 — EQ barras visuales + r reset

**Tarea**: Agregar barras visuales en Config/Audio + fix r reset

**Cambios**:
- Helper `_eq_bar(value, bar_w)` genera string de barras (█/░)
- Config/Audio tab muestra barras para preamp y bandas
  - Full mode (≥61 cols): 40 chars, 1 dB por char
  - Compact mode (<61 cols): 4 chars, 10 dB por char
- Hints line "← → cambiar" en tab Audio
- `r` en config resetea: banda → 0.0, preamp → 0.0, preset → Flat
- Fix cursor: se guarda/restaura después de _build_config_tabs

**Archivos modificados**:
- `player/views.py` — _eq_bar(), draw_config con barras y hints Audio
- `player/handlers/config_view.py` — handler `r` para EQ items

**Estado**: v1.5.50, mypy strict pasa.

---

## Entrada 8 — 2026-07-14 — Fix alineación visual EQ bands

**Tarea**: Alinear labels de bandas custom en Config/Audio

**Problema**: Labels con longitudes distintas ("60 Hz" vs "1k" vs "Preamp") causaban desfase visual en colon, valores y barras.

**Solución**: Padear labels a 6 chars con `{label:<6}`, unificar branches `eq_preamp`/`eq_band` en uno solo.

**Archivos modificados**:
- `player/views.py` — draw_config, branch unificado eq_preamp/eq_band con label padeado

**Estado**: v1.5.51, mypy strict pasa.

---

## Entrada 9 — 2026-07-14 — Rediseño visual Fase 1+2

**Tarea**: Consistencia visual + jerarquía en Listen y Config

**Cambios**:
- `COMPACT_THRESHOLD = 16` en `ui.py` — reemplaza 19 hardcoded `h < 16` / `h < 12` en todo el codebase
- Icono de pausa unificado a `❚❚` (antes: `||` en status, `❚❚` en compact, `||` en help)
- Separador visual `───` entre preamp y bandas en Config/Audio (Custom mode)
  - Item virtual `("separator")` en lista de items, cursor lo salta automáticamente
- Listen view: título con icono `♪` y color `destacar` (antes: sin icono, color `texto`)

**Archivos modificados**:
- `player/ui.py` — COMPACT_THRESHOLD, pausa ❚❚, help text
- `player/views.py` — COMPACT_THRESHOLD import, separador Config, Listen title
- `player/app.py` — COMPACT_THRESHOLD import, separator item en _build_config_tabs
- `player/handlers/config_view.py` — _skip_separator(), COMPACT_THRESHOLD import
- `player/handlers/explorer.py` — COMPACT_THRESHOLD import
- `player/handlers/history.py` — COMPACT_THRESHOLD import
- `player/handlers/playlist.py` — COMPACT_THRESHOLD import
- `player/handlers/radio.py` — COMPACT_THRESHOLD import

**Estado**: v1.5.52, mypy strict pasa.

---

## Entrada 10 — 2026-07-14 — draw_box_inline + scroll indicators

**Tarea**: Fase 1.1 (unificar box drawing) + Fase 3.2 (scroll indicators)

**Cambios**:
- `draw_box_inline(win, h, w, title, clear)` en `ui.py` — helper para box con título inline + limpieza interior
- Reemplaza implementación manual en `draw_mini_stack` y `draw_listen_compact` (~15 líneas eliminadas)
- `draw_scroll_indicators(win, h, w, has_above, has_below)` en `ui.py` — dibuja `▲`/`▼` en borde derecho
- Indicadores en: explorer, playlist, history, favorites, radio, config
- Fix: `favorites` list_h usa `COMPACT_THRESHOLD` (era hardcoded `16`)

**Archivos modificados**:
- `player/ui.py` — draw_box_inline, draw_scroll_indicators
- `player/views.py` — reemplazo manual boxes, scroll indicators en 6 vistas, fix favorites threshold

**Estado**: v1.5.53, mypy strict pasa.

---

## Entrada 11 — 2026-07-14 — Listen metadata centrada + volumen visual

**Tarea**: Fase 2.2 (metadata centrada) + Fase 2.3 (indicador volumen visual)

**Cambios**:
- Helper `_vol_bar(vol, bar_w)` genera barra de volumen (█/░)
- **2.2 Listen full**: estado, título ♪ y artista/álbum centrados con `_center(s, inner_w)`
- **2.2 Listen compact**: título y artista/álbum centrados (sin filas extra, misma densidad)
- **2.3 Listen full**: `Vol:████░░░░ 50%` en controles (8 chars bar, fallback a texto si w<50)
- **2.3 Listen compact**: `V:██░░ 50%` en controles (4 chars bar, fallback si no cabe)

**Archivos modificados**:
- `player/views.py` — _vol_bar(), draw_listen centrado + vol bar, draw_listen_compact centrado + vol bar

**Decisión**:
- Centrado dinámico con `_center(s, w-4)` — funciona en cualquier ancho
- Barra de volumen con fallback automático a texto si el espacio no alcanza
- Compact mode: sin filas extra, solo centrado horizontal (preserva densidad)

**Estado**: v1.5.54, mypy strict pasa.

---

## Entrada 12 — 2026-07-14 — Config/Audio polish (solo lectura + hints)

**Tarea**: Fase 4.1 (bands solo lectura) + Fase 4.2 (hints contextuales)

**Cambios**:
- **4.1** Config/Audio: bandas EQ muestran color `texto` cuando preset ≠ Custom (antes siempre `destacar` en cursor)
- **4.2** Config/Audio: hints dinámicos por tipo de item:
  - `eq_preamp` / `eq_band`: `← → ±0.5dB │ r reset`
  - `choice`: `← → cambiar │ r reset`
  - Otros: `← → cambiar` (genérico)
- Variable `is_custom_eq` calculada una vez por frame

**Archivos modificados**:
- `player/views.py` — draw_config: is_custom_eq, hints contextuales, eq_band color

**Decisión**:
- Solo `eq_band` usa color condicional — `eq_preamp` sigue siendo editable en todos los presets
- Hints se recalculan por frame (simple, sin caché)

**Estado**: v1.5.55, mypy strict pasa.

---

## Entrada 13 — 2026-07-14 — Refactor visual helpers (Fase 5)

**Tarea**: Fase 5.1 (tab carousel helper) + Fase 5.2 (list helpers)

**Cambios**:
- **5.1** `draw_tab_carousel(win, y, tab_names, current_idx, inner_w, ox, nav_attr, curr_attr, fill_attr, sep, h, w)` — helper unificado para carousel de pestañas
  - Reemplaza implementación manual en `draw_config` (~30 líneas → 4 líneas)
  - Reemplaza implementación manual en `draw_help` (~35 líneas → 5 líneas)
- **5.2** `clamp_scroll(scroll, total, list_h, cursor) → int` — normaliza scroll clamping
- **5.2** `draw_list_indicators(win, h, w, scroll, total, list_h)` — dibuja ▲/▼ basado en scroll/total
  - Reemplaza 3 líneas en 6 vistas (explorer, playlist, history, config, radio, favorites)

**Archivos modificados**:
- `player/ui.py` — draw_tab_carousel, clamp_scroll, draw_list_indicators
- `player/views.py` — refactored draw_config, draw_help, draw_explorer, draw_playlist, draw_history, draw_radio, draw_favorites

**Decisión**:
- 5.1: Helper dibuja carousel + fills, caller dibuja borders/bars si necesita
- 5.2: Helpers ligeros (no render genérico) — cada vista mantiene su lógica de render, pero scroll/indicators son consistentes

**Estado**: v1.5.56, mypy strict pasa.

---

## Entrada 14 — 2026-07-14 — Bug fixes post-rediseño

**Tarea**: Corregir bugs encontrados al probar el rediseño visual

**Bugs corregidos**:
- **B14** Config/Audio bands no visibles para presets non-Custom
  - Causa: `_build_config_tabs()` solo agregaba bands cuando `eq_preset == "Custom"`
  - Fix: siempre agregar separator + 10 bands, `views.py` ya usaba `texto` para non-Custom
- **B15** History g/G no implementados
  - Causa: handler no tenía cases para `g`/`G`
  - Fix: agregados `g→cursor=0`, `G→cursor=len-1`

**Pendiente**:
- **B13** Listen hints show/hide — requiere config option + tecla toggle (para próxima sesión)

**Archivos modificados**:
- `player/app.py` — _build_config_tabs: bands siempre visibles
- `player/handlers/history.py` — g/G handlers

**Estado**: v1.5.57, mypy strict pasa.

---

## Entrada 15 — 2026-07-14 — Bug fixes B13+B16+B17 + Custom EQ persistence

**Tarea**: Corregir bugs activos de UX en Config/Audio y Listen + persistencia de Custom EQ

**Bugs corregidos**:
- **B13** Listen hints no se pueden ocultar
  - Fix: config `show_listen_hints` + toggle con `;`
- **B17** Config/Audio cursor navega bands en non-Custom
  - Fix: `_skip_disabled` reemplaza `_skip_separator`; guarda `start` antes del `+1`; revierte si no hay item accesible
  - Iteraciones: last_valid (erróneo) → revert a start → primer válido (final)
- **B16** Custom EQ no se guarda
  - Fix: key `custom_bands` en config; guarda al salir de Custom, restaura al entrar

**Custom EQ persistence**:
- `custom_bands` key separada en config.json
- `_cycle_eq_preset` guarda custom_bands al salir de Custom, restaura al entrar
- `r` reset banda: actualiza solo esa banda en custom_bands
- `r` preset: limpia custom_bands a [0.0]*10
- Listen handler `E`:同步 lógica custom_bands

**Archivos modificados**:
- `player/config.py` — custom_bands default
- `player/handlers/config_view.py` — _cycle_eq_preset, _skip_disabled, r handlers
- `player/handlers/listen.py` — E handler, `;` handler
- `player/keybindings.py` — `;` reserved
- `player/views.py` — hints condicional
- `player/ui.py` — Help Listen hints

**Estado**: v1.5.59, mypy strict pasa, 0 bugs activos.

---

## Entrada 16 — 2026-07-14 — Cleanup: eliminar r reset de Config/Audio

**Tarea**: Eliminar `r` reset de Config/Audio (conflicto con shuffle global)

**Problema**: `r` es mapeado a "shuffle" en keybindings. `_handle_key_global` lo intercepta antes de `handle_config`.

**Decisión**: Eliminar funcionalidad de reset en Config/Audio. El usuario edita manualmente.

**Archivos modificados**:
- `player/handlers/config_view.py` — eliminado bloque `elif key == ord("r")`
- `player/views.py` — eliminado hint `(r, reset)` de Config/Audio

**Estado**: v1.5.59, mypy strict pasa, 0 bugs activos.

---

## Entrada 17 — 2026-07-15 — F10: crear player/platforms.py

**Tarea**: Fase 1 del Web Explorer v2 — crear registry de plataformas

**Archivos creados**:
- `player/platforms.py` — Platform dataclass + load/save + 6 defaults

**Cambios**:
- Platform dataclass: name, url, search_pattern, download_pattern, search_prefix, downloads, is_default
- 6 plataformas default con búsqueda nativa: YouTube, SoundCloud, Vimeo, Dailymotion, Twitch, Niconico
- Funciones: load_platforms, save_platforms, get_search_prefix, get_platform, increment_downloads, can_delete
- Helper _dict_to_platform para conversión segura de dicts
- Property has_search para verificar soporte de búsqueda

**Decisión**:
- `is_default=True` protege de eliminación (can_delete retorna False)
- search_prefix vacío = plataforma sin búsqueda nativa (solo URL directa)
- Almacenamiento en `~/.config/tplay/data/platforms.json`

**Estado**: v1.5.61, mypy strict pasa.

---

## Entrada 18 — 2026-07-15 — F10: reescribir player/web.py

**Tarea**: Fase 2 del Web Explorer v2 — fix B22 + download

**Archivos modificados**:
- `player/web.py` — reescritura completa

**Cambios**:
- WebResult: nuevo campo `download_url`
- search(): `extract_flat=True` para listar + extracción individual por entry
- download(): nueva función para descargar con yt-dlp
  - Audio: mp3 (FFmpegExtractAudio)
  - Video: mp4 (merge_output_format)
  - Quality: configurable (480p/720p/1080p/best)
- _get_download_url(): helper para obtener mejor URL según config
- _get_download_url() selectora de calidad para audio y video

**Decisión**:
- Fix B22: `extract_flat=True` lista rápido, luego `extract_info()` por entry obtiene stream URL
- Audio download usa FFmpegExtractAudio para convertir a mp3
- Video download usa merge_output_format para mp4
- Quality map: 480p=480, 720p=720, 1080p=1080, best=9999

**Estado**: v1.5.62, mypy strict pasa.

---

## Entrada 19 — 2026-07-15 — F10: reescribir player/handlers/webexplorer.py

**Tarea**: Fase 3 del Web Explorer v2 — handler con 3 modos + gestión + descarga

**Archivos modificados**:
- `player/handlers/webexplorer.py` — reescritura completa (110→530 líneas)
- `player/app.py` — nuevos estados web + _load_web_platforms()

**Cambios**:
- 3 modos: normal (lista), search (prompt), motor (gestión)
- Motor mode: add/edit/delete plataformas (patrón meta_editor)
- Download: D (directo), d (con config)
- g/G: navegación primer/último resultado
- A/a: add to queue
- x: clear results
- Cola de descarga: max 3 (configurable hasta 10)
- Check re-descarga
- Plataformas sin búsqueda: URL completa en prompt

**Decisión**:
- Patrón meta_editor para motor edit y download config
- Estados en lista: [-] [►] [D] [P] [Q] [✓] [X] [!]
- Tab alterna entre motor y search
- _load_web_platforms() en __init__ para cargar plataformas al inicio

**Estado**: v1.5.63, mypy strict pasa.

---

## Entrada 20 — 2026-07-15 — F10: reescribir player/views.py

**Tarea**: Fase 4 del Web Explorer v2 — UI con motor+prompt+estados + editors

**Archivos modificados**:
- `player/views.py` — reescritura de draw_web() + 4 funciones nuevas

**Cambios**:
- draw_web(): dispatch a sub-funciones según modo
- _draw_web_main(): layout motor+prompt+divider+lista con estados
- _draw_motor_list(): lista de plataformas con stats
- _draw_motor_editor(): editor de plataformas (patrón meta_editor)
- _draw_download_config(): configuración de descarga
- _draw_web_hints(): hints contextuales por modo
- Estados en lista: [-] [►] [D] [P] [Q] [✓] [X] [!]
- Truncado de texto automático

**Decisión**:
- Patrón draw_meta_editor para motor_editor y download_config
- Layout: Línea 1 motor+prompt, línea 2 divider, línea 3+ lista
- Hints diferentes por modo (search/motor/normal)
- Status display: 3 chars fijos + título truncado + duración

**Estado**: v1.5.64, mypy strict pasa.

---

## Entrada 21 — 2026-07-15 — F10: actualizar config.py + ui.py

**Tarea**: Fase 5 del Web Explorer v2 — defaults downloads + help tab

**Archivos modificados**:
- `player/config.py` — defaults downloads
- `player/ui.py` — help tab Web actualizado

**Cambios**:
- config.py: online_platform, online_download_format, online_download_quality, online_download_stream, online_download_max
- ui.py: help tab Web con todas las teclas nuevas (Tab, g/G, D, d, A/a, x, motor keys)

**Decisión**:
- Defaults: audio, 480p, fastest, max 3
- Help tab: 3 secciones (Web Explorer, Búsqueda, Motor)

**Estado**: v1.5.65, mypy strict pasa.
