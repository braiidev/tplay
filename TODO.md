# TODO.md — Player TUI

## 🔴 CRASH (pérdida de datos / cierre forzado)

| ID  | Descripción | Archivo | Estado |
| --- | ----------- | ------- | ------ |
| C1  | Renombrar con overwrite: callback lambda aridad incorrecta + mensaje pobre | handlers.py:672 | ✅ |
| C2  | `next()` sin default + `del` sin pop al borrar playlist activa | handlers.py:893 | ✅ |
| C3  | `list.index()` sin try/except al cambiar de playlist con `[`/`]` | handlers.py:332,338 | ✅ |

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
| A4  | handlers.py monolítico (1183 líneas, 60+ funciones) | handlers.py | [ ] |
| A5  | Playlist property retorna lista mutable interna | app.py:160 | [ ] |
| A6  | Deferred imports (from .config import save) dentro de funciones | handlers.py:867+ | [ ] |

## 🔵 UX (experiencia de usuario)

| ID  | Descripción | Archivo | Estado |
| --- | ----------- | ------- | ------ |
| U1  | Sin PgDn/PgUp ni g/G en vista Playlist | handlers.py:238 | [ ] |
| U2  | Update check bloquea UI al inicio (git fetch sync, hasta 10s) | app.py:198-226 | [ ] |
| U3  | Sin toast al toggle shuffle/repeat | app.py:615-622 | [ ] |
| U4  | Confirm dialog usa "s" para sí (vs "y" estándar) | app.py:431 | [ ] |
| U5  | Sleep timer muestra "FIN" tras stop manual | audio.py:62 | [ ] |

## ⚪ CLEANUP (deuda técnica menor)

| ID  | Descripción | Archivo | Estado |
| --- | ----------- | ------- | ------ |
| N1  | `min(w-2, w-2)` redundante | app.py:492 | [ ] |
| N2  | `ord("\n")`/`10`/`13` redundantes en múltiples sitios | varios | [ ] |
| N3  | Scroll-clamping duplicado en 6 handlers | handlers.py:140+ | [ ] |
| N4  | Magic numbers `(1, 5, 6)` para vistas inexistentes | ui.py:59 | [ ] |
| N5  | `compact` shadoweado dentro de `_draw()` | app.py:858 | [ ] |

## 🟣 L5 — Metadata / Covers (pendiente discusión)

| ID  | Descripción | Estado |
| --- | ----------- | ------ |
| L5  | Covers/metadata errors — discutir enfoque | [ ] |

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
