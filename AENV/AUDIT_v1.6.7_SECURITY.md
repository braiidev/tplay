# AUDIT v1.6.7 — Re-escaneo Completo

Fecha: 2026-07-15
Versión auditada: v1.6.7
Alcance: Seguridad, Dependencias, Arquitectura, Escenarios de Rotura

---

## 🔴 ALTA PRIORIDAD — Seguridad y Robustez

### Inyección de argumentos en yt-dlp

| # | Severidad | Archivo:Línea | Descripción |
|---|-----------|---------------|-------------|
| S1 | 🔴 high | `web.py:105` | Search query se concatena directo al cmd de yt-dlp sin `--` end-of-options. Un query como `--exec "rm -rf ~"` se interpreta como flag de yt-dlp. |
| S2 | 🔴 high | `web.py:125,173` | `webpage_url` se pasa sin `--` end-of-options. Un platform config malicioso podría inyectar flags. |
| S3 | 🟡 medium | `web.py:120-121` | Cookie path (`file:`) se pasa sin validación. Podría apuntar a cualquier archivo del sistema. |

**Fix S1-S2**: Agregar `cmd.append("--")` antes de argumentos de usuario en `_build_search_cmd`, `_build_stream_cmd`, `_build_download_cmd`.

### Path Traversal

| # | Severidad | Archivo:Línea | Descripción |
|---|-----------|---------------|-------------|
| S4 | 🔴 high | `explorer.py:263-271` | `_do_mkdir` no valida que el resultado quede dentro de `current_dir`. `../../etc/cron.d/backdoor` crea directorios en cualquier lugar. |
| S5 | 🟡 medium | `shared.py:148-162` | `_parse_m3u`/`_parse_pls` aceptan paths absolutos sin validar que sean media files. |
| S6 | 🟡 medium | `shared.py:121-141` | `_export_as_m3u` escribe a path arbitrario via prompt input. |
| S7 | 🟡 medium | `app.py:1104-1130` | `_apply_file_undo`/`_apply_file_redo` usan paths del undo stack sin validar contra `music_dir`. |
| S8 | 🟡 medium | `app.py:416-459` | `_resume_session` carga paths de `state.json` sin validar contra `music_dir`. |

**Fix S4**: Después de `os.path.join`, verificar `os.path.realpath(result).startswith(root)`.

### Race Conditions en Threads

| # | Severidad | Archivo:Línea | Descripción |
|---|-----------|---------------|-------------|
| S9 | 🔴 high | `webexplorer.py:494,517` | `_add_to_queue` y `_add_to_queue_next` mutan `app.stack.items` desde threads background sin lock. Main thread lee/muta el mismo list. |
| S10 | 🟡 medium | `webexplorer.py:490,495,512,518` | `_toast()` se llama desde threads background. `toast_msg`/`toast_ticks` se escriben sin sync. |
| S11 | 🟡 medium | `web.py:428` | `_worker_loop` lee `item.state` sin lock. |

**Fix S9**: Usar pending-flag pattern (como `_download_completed_pending`) o lock en `Stack._items`.

### Pérdida de Datos

| # | Severidad | Archivo:Línea | Descripción |
|---|-----------|---------------|-------------|
| S12 | 🟡 medium | `config.py:127-134` | `save()` usa `open(f, "w")` que trunca inmediatamente. Crash mid-write = config corrupta = todos los settings perdidos. |
| S13 | 🟡 medium | `state.py`, `playlist.py`, `downloads.py`, `platforms.py` | Mismo patrón no-atómico en todas las persistencias. |
| S14 | 🔴 high | `app.py:373-379` | `_apply_updates` hace `git reset --hard origin/main` si pull falla. Destruye cambios locales sin confirmación extra. |
| S15 | 🟡 medium | `download_history.py:231-256` | `_clear_tab` borra archivos sin confirmación. `X` = eliminación irreversible. |
| S16 | 🟡 medium | `download_history.py:209-228` | `_remove_and_delete` borra sin confirmación. |

**Fix S12-S13**: Escribir a `.tmp` + `os.replace()` (atómico en POSIX).

---

## 🟡 DEPENDENCIAS — Riesgos de Rotura

### yt-dlp (CRÍTICO)

| # | Severidad | Riesgo | Descripción |
|---|-----------|--------|-------------|
| D1 | 🔴 critical | availability | `--js-runtime node` hardcodeado. Sin Node.js = crash total. |
| D2 | 🔴 high | version_conflict | yt-dlp sin pin en `requirements.txt`. Cualquier `pip install` puede romper la CLI. |
| D3 | 🔴 high | breaking_change | `--cookies-from-browser` depende de paths de browser que cambian con updates. |
| D4 | 🟡 medium | api_change | `--flat-playlist --dump-json` output format puede cambiar entre versiones. |
| D5 | 🟡 medium | api_change | Progress parsing (`[download]` lines) es frágil a cambios de formato. |
| D6 | 🟡 medium | api_change | `--get-url` retorna URLs que VLC no puede reproducir (DRM, PO tokens). |
| D7 | 🟡 medium | api_change | Filename parsing de stdout (`Destination:`, `has already`) depende de formato exacto. |

**Fix D1**: Detectar `node` en PATH, omitir `--js-runtime` si no existe.
**Fix D2**: Pin a versión testada: `yt-dlp==2026.x.x`.

### python-vlc

| # | Severidad | Riesgo | Descripción |
|---|-----------|--------|-------------|
| D8 | 🔴 critical | availability | VLC/libvlc no instalado = `ImportError` al inicio, sin fallback graceful. |
| D9 | 🔴 high | version_conflict | Sin upper bound: `python-vlc>=3.0.0` permite VLC 4.x que tiene API changes. |
| D10 | 🟡 medium | availability | `os.dup2(log_fd, 2)` sin try/except. Si falla, crash en init. |

**Fix D8**: Wrap `import vlc` en try/except con error message claro antes de curses.
**Fix D9**: Pin `python-vlc>=3.0.0,<4.0.0`.

### Otras

| # | Severidad | Riesgo | Descripción |
|---|-----------|--------|-------------|
| D11 | 🟡 medium | availability | `signal.SIGSTOP/SIGCONT` no existe en Windows. (Mitigado: target Linux-only) |
| D12 | 🟡 medium | availability | No check `sys.stdout.isatty()` antes de curses. |
| D13 | 🟡 medium | api_change | Config sin validación de tipos. `"volume": "loud"` pasa sin error. |
| D14 | 🟡 medium | dos | `error.log` sin rotación. VLC errors acumulan sin límite. |
| D15 | 🟡 medium | dos | Download history sin límite de tamaño. |
| D16 | 🟡 medium | dos | `max_concurrent` setter sin validación (acepta 0 o negativo). |

---

## 🟢 FORTALEZAS

| # | Categoría | Archivo | Descripción |
|---|-----------|---------|-------------|
| F1 | Arquitectura | `app.py:205-226` | Handler dispatch table pattern. Agregar vista = nuevo handler + 2 entries. |
| F2 | Thread Safety | `web.py:279-517` | DownloadManager usa Lock, Event, _active_lock correctamente. |
| F3 | Error Handling | `audio.py:30-214` | Toda interacción VLC envuelta en try/except. |
| F4 | Degradation | `web.py:65-78` | yt-dlp no instalado degrada graceful. |
| F5 | UI | `app.py:1219` | Compact/responsive system con COMPACT_THRESHOLD. |
| F6 | Reuse | `shared.py` | Utilidades compartidas eliminan duplicación masiva. |
| F7 | State | `app.py:1058-1131` | Undo/redo system con snapshot-based approach. |
| F8 | Performance | `config.py:94-124` | Config cache con mtime invalidation. |

---

## ⚡ ESCENARIOS DE ROTURA

| # | Severidad | Escenario | Impacto | Mitigación actual |
|---|-----------|-----------|---------|-------------------|
| B1 | 🔴 high | Teclas rápidas durante async ops (web search/play) | Stack mutation desde thread → crash | Ninguna |
| B2 | 🟡 medium | Archivos borrados externamente mientras app corre | UX confusa pero no crash | `os.path.isfile()` check |
| B3 | 🟡 medium | Red cae durante download | Worker thread stuck forever, slots llenos | `proc.kill()` on cancel |
| B4 | 🟡 medium | VLC crash mid-playback | Player muerto, UI muestra tiempo stale | Ninguna |
| B5 | 🔴 high | Crash durante config save | Config corrupta = settings perdidos | try/except on read |
| B6 | 🟡 medium | Disco lleno durante download/save | Config save falla silenciosamente | try/except |
| B7 | 🟡 medium | SIGTERM/SIGINT | Sin handler = estado no guardado | `finally` block |
| B8 | 🟡 medium | Concurrent config writes | Last-writer-wins | Ninguna |
| B9 | 🟡 medium | yt-dlp cambia formato output | Filename parsing falla → wrong file_path | String splitting frágil |
| B10 | 🟡 medium | VLC 4.x liberado | API breaks, equalizer cambia | Sin upper bound pin |

---

## 📊 Resumen por Severidad

| Severidad | Seguridad | Dependencias | Arquitectura | Escenarios | Total |
|-----------|-----------|--------------|--------------|------------|-------|
| 🔴 Critical | 0 | 2 (D1,D8) | 0 | 0 | **2** |
| 🔴 High | 4 (S1,S2,S4,S9) | 3 (D2,D3,D9) | 2 (W1,W2) | 2 (B1,B5) | **11** |
| 🟡 Medium | 13 | 10 | 4 | 8 | **35** |
| 🟢 Low | 0 | 0 | 2 | 0 | **2** |

## 📊 Top 5 Prioridades de Fix

1. **D1+D8**: Hacer `--js-runtime node` condicional + wrap VLC import con graceful fallback
2. **D2+D9**: Pin `yt-dlp==<tested>` y `python-vlc>=3.0.0,<4.0.0`
3. **S1+S2**: Agregar `--` end-of-options a todos los subprocess de yt-dlp
4. **S9+S12**: Atomic writes para config/persistence + lock en Stack._items
5. **S15+S16**: Agregar `_confirm` antes de borrado de download history
