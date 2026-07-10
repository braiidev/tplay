# TODO.md — Player TUI

## 🔴 CRASH (pérdida de datos / cierre forzado)

| ID  | Descripción | Archivo | Estado |
| --- | ----------- | ------- | ------ |
| C1  | Renombrar con overwrite: callback lambda aridad incorrecta + mensaje pobre | handlers.py:672 | ✅ |
| C2  | `next()` sin default + `del` sin pop al borrar playlist activa | handlers.py:893 | ✅ |
| C3  | `list.index()` sin try/except al cambiar de playlist con `[`/`]` | handlers.py:332,338 | ✅ |
| C4  | `_restart_app` usa `__file__` con ruta incorrecta tras split A4 — `execv` ejecuta `player/app.py` en vez de `app.py` raíz | handlers/shared.py:157 | ✅ |

## 🟠 BUG (comportamiento incorrecto)

| ID  | Descripción | Archivo | Estado |
| --- | ----------- | ------- | ------ |
| B1  | Copiar/mover archivos sobreescribe sin confirmar (renombrar sí pregunta) | handlers.py:929 | ✅ |
| B2  | Dos sistemas de undo desconectados: file_op_undo vs snapshot_redo | app.py:709-737 | ✅ |
| B3  | Al salir/entrar se pierde el [Stack] de reproducción (E6) | app.py | ✅ |
| B4  | El [Stack] debería persistir entre sesiones o no (E7) | — | ✅ |

## 🟡 ARCH (arquitectura / mantenibilidad)

| ID  | Descripción | Archivo | Estado |
| --- | ----------- | ------- | ------ |
| A1  | stderr redirigido a log (~/.config/tplay/data/error.log) — VLC/mutagen errores capturados | audio.py | ✅ |
| A2  | Sin manejo de KEY_RESIZE → UI corrupta al redimensionar terminal | app.py | ✅ |
| A3  | `os.makedirs` lazy — solo en save(), no al importar | config.py | ✅ |
| A4  | handlers.py monolítico → handlers/ package con 7 archivos por vista | handlers.py | ✅ |
| A5  | Playlist property valida entries inválidas (log a stderr) | app.py:160 | ✅ |
| A6  | Deferred imports se dejan diferidos (sin riesgo de circulares) | handlers/*.py | ✅ |

## 🔵 UX (experiencia de usuario)

| ID  | Descripción | Archivo | Estado |
| --- | ----------- | ------- | ------ |
| U1  | Sin PgDn/PgUp ni g/G en vista Playlist | handlers/playlist.py | ✅ |
| U2  | Update check bloquea UI al inicio → async thread | app.py:156 | ✅ |
| U3  | Toast al toggle shuffle/repeat agregado | app.py:663-664 | ✅ |
| U4  | Confirm acepta 's' y 'y' (ambos) | app.py:478 | ✅ |
| U5  | Sleep timer resetea al hacer stop manual | app.py:643-644 | ✅ |

## ⚪ CLEANUP (deuda técnica menor)

| ID  | Descripción | Archivo | Estado |
| --- | ----------- | ------- | ------ |
| N1  | `min(w-2, w-2)` redundante | app.py | ✅ |
| N2  | `ord("\n")`/`10`/`13` unificado a `(10, 13)` en todos lados | varios | ✅ |
| N3  | Scroll-clamping duplicado → `_clamp_scroll()` helper | handlers/shared.py | ✅ |
| N4  | Magic numbers `(1, 5, 6)` → `== 1` + comentario | ui.py | ✅ |
| N5  | `compact` shadow → `meta_cpt` | app.py | ✅ |

## 🟣 L5 — Metadata / Covers (pendiente discusión)

| ID  | Descripción | Estado |
| --- | ----------- | ------ |
| L5  | Covers/metadata errors — discutir enfoque | ❌ sin acción |

## 🟢 FEATURES

| ID  | Feature | Prioridad | Estado |
| --- | ------- | --------- | ------ |
| F2  | Ecualizador gráfico (VLC API) | Alta | [ ] |
| F4  | Exportar playlist a M3U/PLS | Baja | [ ] |
| F8  | Cover art (chafa/viu) | Media | [ ] |
| F28 | Streaming/Radio (URL, M3U, radios guardadas) | Media | △ |

## ✅ Completado

- **E1-E5** — bugs de explorador/playlist/historial corregidos
- **L1-L4** — crashes, bugs visuales, UX, sugerencias (AUDIT_SPEC.md)
- **M1** — draw_item_row() unificada
- **M2** — 9 vars de diálogo unificadas en self.dialog dict
- **M3** — mypy strict, 0 errores en 13 archivos
- **B3/B4** — stack persistente entre sesiones (state.json + stack_items, shuffle, repeat, playhead, volumen)
- **A2** — KEY_RESIZE handling, resize sin corrupción de UI
- **A1** — stderr redirigido a error.log (data/) en vez de /dev/null
- **A3** — os.makedirs lazy, solo dentro de save()
- **A4** — handlers.py partido en handlers/ package por vista (7 archivos)
- **A5** — playlist property con validación de entries inválidas (log)
- **A6** — deferred imports se mantienen diferidos
- **U1** — PgDn, PgUp, g, G en vista Playlist
- **U2** — update check async (threading.Thread), UI sin bloqueo
- **U3** — toast en shuffle/repeat toggle
- **U4** — confirm acepta 's' y 'y'
- **U5** — sleep timer resetea al hacer stop manual
- **N1** — min(w-2, w-2) → w-2
- **N2** — ord("\n")/10/13 unificado a (10, 13)
- **N3** — scroll-clamping → _clamp_scroll() helper
- **N4** — magic numbers (1,5,6) limpiado
- **N5** — compact shadow → meta_cpt
- **C4** — _restart_app ruta incorrecta tras A4 → usa `app._repo_dir`
- **L5** — descartado: tags faltantes → "desconocido" (ok), covers no interesan
