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
