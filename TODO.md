# TODO

## Doing
- [ ] #6: Cache Management (limpiar cache yt-dlp)

## Next
- [ ] #7: Paginación continua de resultados

### 🔧 FIX — install.sh sobrevive al upgrade a Ubuntu 26.04 (Python 3.14)

**Síntoma:** en la máquina `.38` (actualizada 24.04 → 26.04) `tplay` dejó de arrancar. Es el caso
más grave de los tres porque es el único que **no tenía venv**.

**Causa raíz:** `install.sh` usaba `pip install --user -r requirements.txt`, así que python-vlc /
mutagen / yt-dlp quedaron en `~/.local/lib/python3.12/site-packages`. En 26.04 `python3` es 3.14 y
Python 3.14 mira `~/.local/lib/python3.14/site-packages` → los tres paquetes invisibles. El wrapper
`/usr/local/bin/tplay` hacía `exec python3 app.py`: intérprete del SO + deps colgadas del user-site
equivocado. Sin venv no había nada que aislar. El bug del symlink flotante también está presente
(`/usr/local/bin/tplay` → `python3`), pero acá es secundario.

**Verificado:** las 3 deps son **`py3-none-any`** (Python puro, sin extensiones compiladas, sin
restricción de ABI, sin compilador). El venv de tplay no existe por ABI — existe por **reconciliación
de dependencias**. Eso es lo que hay que resolver.

**Único irreducible:** `libvlc`, la librería C que python-vlc carga por ctypes. El venv no la aísla y
no se puede meter adentro. Queda como dependencia del sistema, verificada por install.sh y por el
guard de arranque.

**Decisión para tplay — opción A: uv con CPython 3.14 gestionado + `uv.lock`.** Acá sí vale la pena,
porque el venv tiene que ser independiente del SO y hay que reconciliar deps reales. uv queda como
dueño del intérprete y de las deps.

#### Las 4 capas

1. **Fuente única: `pyproject.toml`.** Deps con sus límites en `[project].dependencies`;
   `requirements.txt` deja de ser fuente (pasa a artefacto generado o se elimina). `uv.lock` fija las
   versiones exactas. El repo declara qué necesita.
2. **El venv se reconcilia, no se congela.** En cada `install.sh` y en cada `--update`, después del
   `git pull` se corre `uv sync --locked` / `uv pip install -e .`. uv lee pyproject, resuelve e
   instala **solo lo que cambió**. Si un commit futuro sube `yt-dlp>=2026.09`, el update lo sube solo —
   sin verificación manual de deps.
3. **Guard de arranque.** Antes de levantar la TUI, chequeo barato: importar las deps declaradas y
   compararlas contra el lock. Si algo falta o quedó viejo → reparar ahí mismo, o abortar con el
   comando exacto. **Nunca más muere por `ModuleNotFoundError`.**
4. **Health-check en el wrapper.** `~/.local/bin/tplay` valida que el intérprete del venv exista y sea
   el pineado; si no, repara. Cierra el agujero de que el comando mismo esté muerto.

**Degradación limpia:** si el venv ya está sano, nada toca la red. El chequeo de red/uv ocurre solo
cuando algo ya falló — nunca en cada arranque.

- [ ] v0.16: `pyproject.toml` — agregar `[project]` (hoy solo tiene `[tool.mypy]`, o sea que **no es instalable**) con name/version/deps: `python-vlc>=3.0.0,<4.0.0`, `mutagen>=1.46.0`, `yt-dlp>=2026.07.04`; `.python-version` = `3.14` + generar `uv.lock` + unificar `requirements.txt`
- [ ] v0.17: install.sh — bootstrap de uv (instalar el oficial a `~/.local/bin` sin sudo si falta, re-resolver PATH) + `uv python install 3.14` (gestionado, no del SO) + venv con `uv venv --python 3.14 --seed`
- [ ] v0.18: install.sh — `uv sync --locked` / `uv pip install -e .` + **eliminar la cascada `--break-system-packages`** (las deps van al venv, ya no al sistema)
- [ ] v0.19: install.sh — mover `/usr/local/bin/tplay` → `~/.local/bin/tplay` con wrapper al venv pineado. Efecto secundario: install.sh deja de pedir sudo para todo lo Python; sudo queda solo para `vlc`/`ffmpeg`/`pipewire-alsa`
- [ ] v0.20: install.sh — **conservar** la verificación de deps de sistema que ya funciona: `libvlc` por `ldconfig -p | grep libvlc` (no por import, para no confundir "falta VLC" con "falta python-vlc"), `ffmpeg` por `command -v`, `pipewire-alsa` solo si hay socket de PipeWire en `$XDG_RUNTIME_DIR`
- [ ] v0.21: guard de arranque (capa 3) — validar deps contra el lock al iniciar, reparar o abortar con comando exacto + health-check del venv en el wrapper (capa 4)
- [ ] v0.22: `--update` y `--reinstall` (flag de v0.15) reconcilian deps vía uv tras el `git pull`; regenerar `~/Dev/Player/.venv` si existe
- [ ] v0.23: smoke test final (`tplay --help`) con salida ≠ 0 si falla + test del escenario real (venv con intérprete inexistente → auto-reparación) + README

**Entrega:** un solo commit (v0.16-v0.23 unificados) + `git tag v0.16`, con este bloque como registro.

**Ojo:** python-vlc es binding sobre `libvlc` (binario C del sistema). El venv aísla la capa Python,
no la librería nativa. Deuda conocida, no arreglable desde el venv.

**Nota:** se sirve desde `raw.githubusercontent.com/braiidev/tplay/main/install.sh`. El fix no llega a
otra máquina hasta que esté pusheado a `main`.

## Done
- [x] Flag --reinstall: re-ejecuta install.sh del repo (deps python, vlc, ffmpeg, wrapper) - v0.15
- [x] Hardening install.sh: pip faltante detectado, cascada PEP668, verificación final libvlc/yt-dlp/ffmpeg - v0.13-v0.14
- [x] Audio hardening: aout explícito (PipeWire/Pulse), deps de sistema en install.sh, wrapper POSIX, logs de estado - v0.3-v0.8
- [x] Temas compartidos con Clock (leer `~/.config/clock` o `~/Dev/Clock`) + hot-reload de theme sin reiniciar - v0.2
- [x] Migrar tracking a sistema de tareas atómicas (eliminar AENV) - v0.1
- [x] v1.9.1: IPC síncrono + `mute` + `-q/--quiet` + mensajes de estado explícitos
- [x] v1.9.0: API control externo vía Unix socket (`tplay --ctl`)
- [x] v1.8.0: Fix 403 YouTube — auto-update yt-dlp al inicio + `--rm-cache-dir`
- [x] v1.7.0-72: Security fixes (F1-F8, S3-S14, D12-D16) + cookies web + config cycling
- [x] v1.6.0-67: Audits completos (concurrencia, dead code, perf, DRY, UX, visual) + FilterState + navigación unificada
- [x] v1.5.4x-80: Web Explorer v2 (subprocess) + DownloadManager + historial unificado + EQ 10 bandas + rediseño visual + setup AENV

Detalle por versión: `git log` y tags.