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
