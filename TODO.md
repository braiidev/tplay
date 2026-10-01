# TODO

## Doing
- [ ] Migración del instalador al patrón de Clock/MonitorPC (v0.17 → v0.23, abajo)

## Next
- [ ] #6: Cache Management (limpiar cache yt-dlp)
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

**⚠ Decisión REVISADA (v0.17 en adelante): NO es uv, es el mismo patrón que Clock y MonitorPC.**

El plan anterior elegía `uv` + CPython 3.14 gestionado + `uv.lock`. Se descartó al revisar el código
de `player/ytdlp_update.py`, y la razón es técnica, no de gusto:

- `yt-dlp` se rompe seguido: cuando YouTube cambia, el extractor viejo devuelve **403** (comentario
  en `ytdlp_update.py:4`). Por eso tplay ya consulta PyPI cada 24 h y actualiza solo, con cache en
  `~/.config/tplay/data/ytdlp_check.json`. **Un `uv.lock` congelaría justo la dependencia que necesita
  moverse**, y el código que ya resuelve ese problema pelearía contra el lock.
- El "pin" no es fijar 3.12 para siempre: es un **rango con preferencia** (`MIN_MINOR=10`,
  `MAX_MINOR=15`, igual que MonitorPC). Cuando el SO sube a 3.14, el pin se re-resuelve solo.
- uv exige bootstrap (instalar uv, `.python-version`, generar el lock) y sería un patrón distinto,
  sin probar, en el único proyecto de los tres que tiene deps reales.

**Deps — las 3 verificadas como `py3-none-any`** (Python puro, sin extensiones compiladas, sin
restricción de ABI, sin compilador). El venv de tplay no existe por ABI: existe por **reconciliación
de dependencias**. Techos en `pyproject.toml`: `python-vlc<4`, `mutagen<2`, **yt-dlp sin techo a
propósito** (ver arriba). `requirements.txt` eliminado: `pyproject.toml` queda como fuente única.

**Único irreducible:** `libvlc`, la librería C que python-vlc carga por ctypes. El venv aísla la capa
Python, no la nativa. Deuda conocida, se verifica como dependencia del sistema.

#### Bugs que aparecieron al auditar (fuera del plan original)

1. **`yt-dlp` se usa como binario del PATH, no como módulo** (`player/web.py:19`, `web.py:71`:
   `subprocess.run(["yt-dlp", ...])`). En el venv cae en `$VENV/bin/yt-dlp`, y los wrappers de
   Clock/MonitorPC hacen `exec "$VENV/bin/python" -m ...` **sin tocar PATH** →
   `web.is_available()` daría `False` y se perderían búsqueda, descarga y Web Explorer **sin error
   visible**. El wrapper de tplay tiene que prepende `$VENV/bin` al PATH.
2. **No existe `--version` ni `--help`** (`player/__init__.py:154`), así que no hay smoke test posible.
3. **`README.md:44` documenta `python3 -m player`, que está roto**: no existe `player/__main__.py`.
4. **`pytest` pelado falla** con `ModuleNotFoundError: No module named 'player'`; los 70 tests solo
   corren con `python3 -m pytest`, porque no hay `conftest.py`.
5. **`--reinstall` clona una copia nueva**: `player/__init__.py:93` corre `install.sh` sin pasar `$1`,
   así que ignora dónde vive el repo.
6. **Los datos viven DENTRO del repo**: `INSTALL_DIR=~/.config/tplay` y `CONFIG_DIR=~/.config/tplay/data`
   son el mismo árbol. `player/__init__.py:115` hace `rm -rf data/` **sin confirmación** y después
   borra el repo. Favoritos, historial y descargas quedan en un `rm -rf`. Se mueven a
   `~/.local/share/tplay/data` con migración por **copia** (el original sobrevive si algo falla).

#### Las 4 capas (se mantienen, sin uv)

1. **Fuente única: `pyproject.toml`.** Deps con techo en `[project].dependencies`; `requirements.txt`
   eliminado. El repo declara qué necesita y es instalable (`pip install -e .`).
2. **El venv se reconcilia, no se congela.** En cada `install.sh` y en cada `--update`, después del
   `git pull`, se reinstalan las deps declaradas. Si un commit futuro sube `yt-dlp`, el update lo sube
   solo, sin verificación manual.
3. **Guard de arranque.** Antes de levantar la TUI, importar las deps declaradas; si falta alguna →
   reparar ahí mismo o abortar con el comando exacto. **Nunca más muere por `ModuleNotFoundError`.**
4. **Health-check en el wrapper.** `~/.local/bin/tplay` valida que el intérprete del venv exista y sea
   el pineado; si no, repara. Cierra el agujero de que el comando mismo esté muerto.

**Degradación limpia:** si el venv ya está sano, nada toca la red. El chequeo ocurre solo cuando algo
ya falló — nunca en cada arranque.

- [x] v0.17: `pyproject.toml` — `[build-system]` + `[project]` (name/version/deps con techo) +
  `[project.scripts] tplay` + `requires-python`. **El repo no era instalable con pip.** `requirements.txt` eliminado
- [ ] v0.18: `--version` y `--help` + `player/__main__.py` (arregla `python3 -m player`) + `conftest.py` (`pytest` pelado) — precondición del smoke test
- [ ] v0.19: install.sh — pin + venv con intérprete versionado del SO (rango 3.10-3.14), idempotente, **eliminar la cascada `--break-system-packages`**, conservar la verificación de deps de sistema (`libvlc` por `ldconfig -p`, `ffmpeg` por `command -v`, `pipewire-alsa` solo si hay socket)
- [ ] v0.20: wrapper en `~/.local/bin/tplay` (sale de `/usr/local/bin`, deja de needing sudo para lo Python) + auto-reparación con guarda de un intento + **`export PATH="$VENV/bin:$PATH"`** para que `yt-dlp` se encuentre (bug 1)
- [ ] v0.21: `--update` y `--reinstall` reconcilian deps tras el `git pull`; `--reinstall` pasa `$1` (bug 5)
- [ ] v0.22: datos a `~/.local/share/tplay/data` — paths en un solo módulo, auto-migración por copia con backup, y `--uninstall` pide confirmación antes de borrar (bug 6)
- [ ] v0.23: `tests/e2e_install.sh` (no existe: hoy nada testea install.sh de verdad) + smoke test con `tplay --version` + README y AGENTS.md al día

**Entrega:** un commit por ítem, cada uno con su tag `v0.N` (regla de oro de `AGENTS.md`), verificado
con `python3 -m pytest` + el e2e de instalación.

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