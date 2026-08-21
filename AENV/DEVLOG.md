# DEVLOG — tplay

## Entrada [consolidado] — v1.5.45→v1.7.2 (2025-07-14 → 2026-07-15)
Setup AENV, Web Explorer v2 (subprocess), DownloadManager, historial unificado,
EQ 10 bandas, rediseño visual, audits (C1-C8, A1-A10, D1-D12, DRY, performance,
UX), security fixes F1-F8 y S3-S14.
Detalle por entrada: `.devlog_archive.md` — resumen por versión: `CHANGELOG.md`.

---

## Entrada 26 — 2026-08-21 — v1.8.0 Fix 403 YouTube + auto-update yt-dlp
- **Bug**: todos los videos daban 403 al descargar/reproducir. Causa: yt-dlp 2026.7.4 desactualizado vs cambios server-side de YouTube (experimentos PO Token en clientes mweb/android_vr, issues upstream #17395/#17404)
- Fix inmediato: `pip install --break-system-packages -U yt-dlp` (→ 2026.8.19) + `yt-dlp --rm-cache-dir`. Descarga verificada OK
- **Feature nueva**: `player/ytdlp_update.py` — chequeo de versión contra PyPI al iniciar tplay
  - Cache 24h en `~/.config/tplay/data/ytdlp_check.json` (evita hit de red en cada arranque)
  - Auto-actualiza via pip solo si el binario es pip-managed (`~/.local/bin` o venv); si es apt u otro gestor, solo avisa
  - Fallbacks pip: `--break-system-packages` y `--user` se pruean en cascada según el entorno
  - Thread daemon al inicio + toast con resultado ("yt-dlp actualizado a X" / hint manual)
  - Config key `online_ytdlp_autoupdate` (default True) + toggle en Config → Sistema
- Tests: `tests/test_ytdlp_update.py` — 12 tests (parse ver, outdated, cache fresco/stale, disabled, no-pip-managed, fallbacks pip). Todos pasan
- Mypy strict pasa

**Estado**: v1.8.0, mypy strict, 12 tests nuevos OK

---

## Entrada 27 — 2026-08-21 — v1.9.0 API de control externo (IPC)
- **Feature**: control de tplay desde fuera via Unix domain socket (`player/ipc.py`)
  - Socket: `$XDG_RUNTIME_DIR/tplay-$UID/ctl.sock` (fallback `~/.local/state/tplay/`, dir 0700)
  - Comandos: toggle, play, pause, stop, next, prev, vol+, vol-, vol N, status
  - Server en daemon thread; mutantes se encolan (`_ctl_pending`) y el main loop los ejecuta vía `_process_ctl_pending()` — nunca curses/VLC desde el thread (patrón S10)
  - `status` responde directo del thread (solo lecturas GIL-safe)
  - Whitelist exacta + max 64 bytes + timeout recv 2s + excepciones del handler capturadas en `dispatch_command`
  - Si bind falla (otra instancia), tplay sigue sin IPC silenciosamente
- **Cliente CLI**: `tplay --ctl <cmd>` en `__init__.py` — antes del check isatty (tmux run-shell no tiene TTY); exit 0 OK / 1 error
- Integración app.py: `_start_ipc()` en setup, cleanup `ipc_server.stop()` en finally del run()
- Tests: `tests/test_ipc.py` — 33 casos (path resolution, whitelist, dispatch, round-trip real, stale socket, sin server). Total suite: 45 passed
- E2E verificado con tplay real dentro de tmux: status/toggle/vol N/vol+/play/stop respondieron y el estado reflejó los cambios
- Mypy strict pasa (30 archivos)

**Estado**: v1.9.0, mypy strict, 45 tests OK, IPC E2E verificado

---

## Entrada 28 — 2026-08-21 — v1.9.1 IPC: mute, -q y mensajes explícitos
- **feat**: comando `mute` → `audio.toggle_mute()` (respuesta: `muted (vol previa N%)` / `unmuted · vol N%`)
- **feat**: flag `-q/--quiet` en `--ctl` — silencia stdout/stderr, mantiene exit codes (para binds tmux sin panel bloqueante)
- **refactor**: IPC ahora síncrono — eliminada la cola `_ctl_pending`/`_process_ctl_pending`/`_exec_ctl` + import queue
  - Justificación: libvlc es thread-safe; las acciones (audio/stack) no tocan curses (verificado: `_play_next/_play_prev/_play_current` solo stack+audio+int)
  - Beneficio: el cliente recibe el estado POST-acción real
- **mensajes explícitos** (`_ipc_state_msg`): `▶ playing · título · vol N%` / `⏸ paused · ...` / `■ stopped · ...`; stop → `■ stopped`; vol → `vol N%[ · muted]`
- Fix regresión detectada en E2E: `status` caía al branch de volumen (solo mostraba `vol N%`) — agregado branch explícito
- Tests: 50 passed (+5: mute válido, 4 de `-q` con capsys). Mypy strict pasa

**Estado**: v1.9.1, mypy strict, 50 tests OK
