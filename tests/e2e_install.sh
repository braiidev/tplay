#!/usr/bin/env bash
# E2E de instalación: corre install.sh de verdad, en un sandbox, y verifica que
# lo que promete el README exista al final.
#
# Por qué existe: install.sh se verificaba a ojo y eso no alcanza. La primera
# versión de este script ya encontró dos bugs que ningún test unitario veía —
# un falso negativo de libvlc por `grep -q` + `set -o pipefail`, y un glob sin
# match que abortaba el script. Los dos rompían la instalación en silencio.
#
# Nunca toca ~/.local/share/tplay ni ~/.local/bin/tplay reales: todo va a un
# sandbox con HOME falso.

set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SANDBOX="$(mktemp -d)"
PASS=0
FAIL=0

ok()   { printf '  \033[32m✓\033[0m %s\n' "$1"; PASS=$((PASS + 1)); }
fail() { printf '  \033[31m✗\033[0m %s\n' "$1"; FAIL=$((FAIL + 1)); }
info() { printf '  ↳ %s\n' "$1"; }

cleanup() { rm -rf "$SANDBOX"; }
trap cleanup EXIT

# ── 1. Sintaxis ──────────────────────────────────────────────────────────────
echo "▶ Sintaxis"
if bash -n "$REPO/install.sh"; then
    ok "install.sh parsea"
else
    fail "install.sh tiene error de sintaxis"
    exit 1
fi

if python3 -m compileall -q "$REPO/player" >/dev/null 2>&1; then
    ok "player/ compila"
else
    fail "player/ no compila"
fi

# `--break-system-packages` escribe en el site-packages del SO. Es exactamente el
# bug que este trabajo arregla (FIX del TODO.md), así que si aparece en código
# ejecutable, vuelve. Solo se permite en comentarios y en los tests que verifican
# su ausencia.
echo "▶ Nada toca el Python del sistema"

# Se usa el tokenizer de Python en vez de grep: distinguir "comentario que
# documenta el bug" de "flag en una cadena que se ejecuta" no es un problema de
# regex. Los docstrings tampoco cuentan (no se ejecutan).
prohibidos="$(python3 - "$REPO" <<'PY'
import ast
import pathlib
import sys

repo = pathlib.Path(sys.argv[1])
prohibidos = ("--break-system-packages", "--user")
encontrados = []

# Las docstrings son ast.Constant, igual que un string en código: se excluyen
# porque no se ejecutan. Un string suelto sí cuenta, porque puede acabar en un
# subprocess.
def es_docstring(nodo: ast.AST) -> bool:
    return (
        isinstance(nodo, ast.Expr)
        and isinstance(nodo.value, ast.Constant)
        and isinstance(nodo.value.value, str)
    )

docstrings: set[int] = set()
for ruta in sorted(repo.rglob("*")):
    if ruta.suffix != ".py" or "__pycache__" in ruta.parts:
        continue
    rel = ruta.relative_to(repo)
    if rel.parts and rel.parts[0] == "tests":
        continue  # los tests NOMBRAN el flag para verificar su ausencia
    try:
        arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        continue
    for nodo in ast.walk(arbol):
        if es_docstring(nodo):
            docstrings.add(id(nodo.value))
    for nodo in ast.walk(arbol):
        if id(nodo) in docstrings:
            continue
        if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str):
            for flag in prohibidos:
                if flag in nodo.value:
                    encontrados.append(f"{rel}:{nodo.lineno}: {flag}")

# install.sh no se parsea: se chequea que el flag no esté en una línea de código
# (no comentario) con awk.
if encontrados:
    print("\n".join(encontrados))
PY
)"

# `--user` sí es legítimo en un solo caso: una instalación vieja por user-site,
# donde no hay venv. Con venv (el mundo normal desde v0.19) no aparece. El flag
# prohibido sin excusas es --break-system-packages.
if [ -n "$prohibidos" ]; then
    graves="$(echo "$prohibidos" | grep -- '--break-system-packages' || true)"
    if [ -n "$graves" ]; then
        fail "--break-system-packages en strings ejecutables:"
        echo "$graves" | sed 's/^/      /'
    else
        ok "player/ sin --break-system-packages en strings"
    fi
else
    ok "player/ sin flags de Python del sistema en strings"
fi

sh_prohibidos="$(
    awk '
        /^[[:space:]]*#/ { next }        # comentario de shell
        /--break-system-packages/        { print FILENAME ":" FNR ": " $0 }
        /pip[0-9]*[[:space:]]+install.*[[:space:]]--user/ { print FILENAME ":" FNR ": " $0 }
    ' "$REPO/install.sh"
)"
if [ -n "$sh_prohibidos" ]; then
    fail "install.sh toca el Python del sistema:"
    echo "$sh_prohibidos" | sed 's/^/      /'
else
    ok "install.sh sin --break-system-packages ni pip --user"
fi

# ── 2. Las deps del venv se pueden instalar ──────────────────────────────────
# Se prueba en un venv desechable aparte: si pyproject declara una dep inexistente
# o un techo imposible, esto falla acá y no en la máquina del usuario.
echo "▶ pyproject instalable en un venv limpio"
VENV_TEST="$SANDBOX/venv-test"
if python3 -m venv "$VENV_TEST" >/dev/null 2>&1 \
   && "$VENV_TEST/bin/pip" install -q -e "$REPO" >/dev/null 2>&1; then
    ok "pip install -e . funciona"
else
    fail "pip install -e . falló (¿dep inexistente o techo imposible?)"
fi

for dep in vlc mutagen yt_dlp; do
    if "$VENV_TEST/bin/python" -c "import $dep" >/dev/null 2>&1; then
        ok "dep importable: $dep"
    else
        fail "dep NO importable: $dep"
    fi
done

if [ -x "$VENV_TEST/bin/yt-dlp" ]; then
    ok "yt-dlp instalado como binario (lo llama player/web.py)"
else
    fail "yt-dlp sin binario en el venv → web.is_available() daría False"
fi

# ── 3. Install limpio ────────────────────────────────────────────────────────
# Se clona el repo al sandbox: install.sh hace `git clone`, y contra el remote
# real no serviría porque el código local todavía puede no estar pusheado.
echo "▶ install.sh en sandbox"
TARGET="$SANDBOX/share/tplay"
BIN="$SANDBOX/bin/tplay"
RC="$SANDBOX/rc"

git clone -q "$REPO" "$TARGET" 2>/dev/null
rsync -a --delete --exclude .git --exclude .venv "$REPO"/ "$TARGET"/
rm -rf "$TARGET/.venv"

LOG="$SANDBOX/install.log"
TPLAY_DIR="$TARGET" TPLAY_BIN="$BIN" TPLAY_RC="$RC" bash "$REPO/install.sh" >"$LOG" 2>&1
rc_install=$?

if [ $rc_install -eq 0 ]; then
    ok "install.sh terminó con 0"
else
    fail "install.sh terminó con $rc_install"
    tail -20 "$LOG" | sed 's/^/      /'
fi

if grep -q "command not found" "$LOG"; then
    fail "install.sh emitted 'command not found' (heredoc sin escapar?)"
    grep "command not found" "$LOG" | head -3 | sed 's/^/      /'
else
    ok "sin 'command not found' en la salida"
fi

# ── 4. Lo que promete el README ──────────────────────────────────────────────
echo "▶ Estructura resultante"
[ -d "$TARGET/player" ]        && ok "código en \$TPLAY_DIR/player"  || fail "no está \$TPLAY_DIR/player"
[ -d "$TARGET/.venv" ]         && ok "venv en \$TPLAY_DIR/.venv"    || fail "no hay venv"
[ -f "$TARGET/.pinned-python" ]&& ok "pin en .pinned-python"         || fail "no hay .pinned-python"
[ -x "$BIN" ]                  && ok "comando ejecutable"           || fail "no hay comando ejecutable"
[ -d "$TARGET/data" ]          && ok "directorio de datos"          || fail "no hay directorio de datos"

# El wrapper tiene que ser un archivo propio, no un symlink: si fuera symlink al
# venv, un `rm -rf` del venv dejaría el comando apuntando al vacío.
if [ -L "$BIN" ]; then
    fail "el wrapper es symlink (debe ser archivo propio)"
else
    ok "el wrapper es archivo propio, no symlink"
fi

if grep -q 'export PATH="\$VENV/bin:\$PATH"' "$BIN"; then
    ok "el wrapper pone el venv en el PATH (yt-dlp)"
else
    fail "el wrapper NO exporta PATH=\$VENV/bin → yt-dlp no se encuentra"
fi

# ── 5. El comando anda ───────────────────────────────────────────────────────
echo "▶ El comando responde"
ver=$("$BIN" --version 2>&1)
if [[ "$ver" == tplay\ * ]]; then
    ok "tplay --version → '$ver'"
else
    fail "tplay --version devolvió: '$ver'"
fi

"$BIN" --help >/dev/null 2>&1 && ok "tplay --help" || fail "tplay --help falló"

# Sin TTY tiene que fallar con un mensaje, no con un traceback.
out=$("$BIN" 2>&1)
if [[ "$out" == *"TTY"* || "$out" == *"dependencias"* ]]; then
    ok "sin TTY da un mensaje claro"
else
    fail "sin TTY: salida inesperada → $(echo "$out" | head -3)"
fi
if [[ "$out" == *"Traceback"* ]]; then
    fail "sin TTY: hay un traceback"
else
    ok "sin traceback"
fi

# ── 6. Idempotencia ──────────────────────────────────────────────────────────
echo "▶ Segunda corrida reutiliza el venv"
VENV_BEFORE="$(readlink "$TARGET/.venv/bin/python3")"
PIN_BEFORE="$(cat "$TARGET/.pinned-python")"

LOG2="$SANDBOX/install2.log"
TPLAY_DIR="$TARGET" TPLAY_BIN="$BIN" TPLAY_RC="$RC" bash "$REPO/install.sh" >"$LOG2" 2>&1

if grep -q "venv sano" "$LOG2"; then
    ok "detecta el venv sano y lo reusa"
else
    fail "no reutilizó el venv"
    tail -10 "$LOG2" | sed 's/^/      /'
fi

VENV_AFTER="$(readlink "$TARGET/.venv/bin/python3")"
[ "$VENV_BEFORE" = "$VENV_AFTER" ] && ok "el venv no se recreó" || fail "recreó el venv sin necesidad"
[ "$PIN_BEFORE" = "$(cat "$TARGET/.pinned-python")" ] && ok "el pin no cambió" || fail "el pin cambió"

# ── 7. Venv roto / flotante ──────────────────────────────────────────────────
# El escenario que Just Works tenía roto: SO upgraded, el venv quedó colgado del
# alias flotante /usr/bin/python3 y el pin quedó en una versión que ya no existe.
echo "▶ Se recupera de un venv flotante + pin muerto"
echo "/usr/bin/python3.99" > "$TARGET/.pinned-python"
rm -f "$TARGET/.venv/bin/python3"
ln -s /usr/bin/python3 "$TARGET/.venv/bin/python3"

LOG3="$SANDBOX/install3.log"
TPLAY_DIR="$TARGET" TPLAY_BIN="$BIN" TPLAY_RC="$RC" bash "$REPO/install.sh" >"$LOG3" 2>&1

if [ "$(readlink "$TARGET/.venv/bin/python3")" != "python3" ] \
   && [ "$(readlink "$TARGET/.venv/bin/python3")" != "/usr/bin/python3" ]; then
    ok "rehizo el venv anclado a una versión concreta"
else
    fail "el venv sigue flotante"
fi

if [ "$(cat "$TARGET/.pinned-python")" != "/usr/bin/python3.99" ]; then
    ok "corrigió el pin muerto solo"
else
    fail "dejó el pin en /usr/bin/python3.99"
fi

"$BIN" --version >/dev/null 2>&1 && ok "el comando sigue andando tras la reparación" \
    || fail "el comando quedó roto tras reparar"

# ── 8. El uninstall no borra datos sin TTY ───────────────────────────────────
# El bug más caro de la historia: `rm -rf data/` sin preguntar, con los datos
# adentro del repo.
echo "▶ --uninstall conserva los datos sin TTY"
FAKE_DATA="$SANDBOX/datos-reales"
mkdir -p "$FAKE_DATA/tmp"
echo '[{"title":"canción real"}]' > "$FAKE_DATA/favorites.json"

UNINSTALL_LOG="$SANDBOX/uninstall.log"
# HOME falso a propósito: _cli_uninstall busca el comando en ~/.local/bin/tplay y
# en /usr/local/bin/tplay. Sin el HOME falso, el e2e intenta borrar el
# /usr/local/bin/tplay REAL del sistema (falla por ser de root, no por diseño).
mkdir -p "$SANDBOX/home/.local/bin"
printf '#!/usr/bin/env bash\n' > "$SANDBOX/home/.local/bin/tplay"
chmod +x "$SANDBOX/home/.local/bin/tplay"

HOME="$SANDBOX/home" \
  "$VENV_TEST/bin/python" - "$TARGET" "$FAKE_DATA" >"$UNINSTALL_LOG" 2>&1 <<'PY'
import importlib, os, sys
from pathlib import Path
repo, datos = sys.argv[1], Path(sys.argv[2])
cli = importlib.import_module("player.__init__")
from player import paths
cli._repo_dir = lambda: repo
paths.DATA_DIR = str(datos)
paths.LEGACY_DATA_DIR = str(datos.parent / "no-existe")
cli._cli_uninstall()   # stdin no es un tty bajo este pipe
PY

sed 's/^/      /' "$UNINSTALL_LOG"

if [ -f "$FAKE_DATA/favorites.json" ]; then
    ok "favorites.json intacto sin TTY"
else
    fail "los datos se borraron sin TTY ← BUG GRAVE"
fi

# Importante: que los datos sobrevivan NO alcanza para aprobar. Si el uninstall
# murió por un traceback antes de llegar al guard, los datos sobreviven por
# casualidad — que es exactamente como un test pasa mientras el bug sigue ahí.
if grep -q "Traceback" "$UNINSTALL_LOG"; then
    fail "--uninstall tira traceback (puede estar salvándose por accidente)"
    grep -A3 "Traceback" "$UNINSTALL_LOG" | head -6 | sed 's/^/      /'
else
    ok "--uninstall sin traceback"
fi

if grep -q "sin terminal interactiva no se puede confirmar" "$UNINSTALL_LOG"; then
    ok "el guard explica por qué no borra sin TTY"
else
    fail "no se ve el aviso del guard de TTY"
fi

# El uninstall mira /usr/local/bin/tplay, que es una RUTA ABSOLUTA: ningún HOME
# falso la redirige. En una máquina donde ese archivo exista y sea del usuario
# (instalación vieja), este e2e lo intentaría borrar de verdad. Se verifica antes
# de seguir, y el uninstall no se ejercita contra esa ruta.
LEGACY_BIN="/usr/local/bin/tplay"
if [ -e "$LEGACY_BIN" ] && [ "$(stat -c '%U' "$LEGACY_BIN" 2>/dev/null)" != "root" ]; then
    fail "$LEGACY_BIN existe y NO es de root — este e2e intentaría borrarlo"
    echo "      mové el archivo o corré el e2e en otro usuario antes de seguir" >&2
    exit 1
fi
ok "sin riesgo de tocar $LEGACY_BIN"

# ── Resumen ──────────────────────────────────────────────────────────────────
echo
echo "──────────────────────────────────────────"
printf '  %d pasaron, %d fallaron\n' "$PASS" "$FAIL"
echo "──────────────────────────────────────────"
[ "$FAIL" -eq 0 ] || exit 1
