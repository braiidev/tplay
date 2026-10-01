#!/usr/bin/env bash
# install.sh — Instala/actualiza tplay (reproductor multimedia TUI)
# Uso: curl -fsSL https://raw.githubusercontent.com/braiidev/tplay/main/install.sh | bash
# Instala SIN sudo en ~/.local: código en ~/.local/share/tplay, comando en ~/.local/bin/tplay.
# Datos personales: viven aparte, en ~/.local/share/tplay/data, y NO se tocan.
#
# ── Por qué el venv se crea con la RUTA VERSIONADA del intérprete ──
# `python3 -m venv` graba .venv/bin/python3 -> /usr/bin/python3. Ese symlink flotante
# SIEMPRE resuelve a la última versión de Python instalada, así que al subir el SO el venv
# queda con layout de una versión ejecutando el intérprete de otra: el install editable se
# vuelve invisible y tplay muere con ModuleNotFoundError. Invocando /usr/bin/python3.14 -m
# venv el symlink queda en la ruta versionada y sobrevive al upgrade. La versión elegida se
# persiste en .pinned-python para que las próximas ejecuciones no se desvíen.
#
# Este script es la ÚNICA fuente de instalación: la instalación inicial y `tplay --update`
# pasan por acá. No hay una segunda implementación del venv.
#
# Overrides (tests): TPLAY_DIR, TPLAY_BIN, TPLAY_RC

set -euo pipefail

REPO_URL="https://github.com/braiidev/tplay.git"
RAW_INSTALL="https://raw.githubusercontent.com/braiidev/tplay/main/install.sh"
TARGET="${TPLAY_DIR:-$HOME/.local/share/tplay}"
BIN="${TPLAY_BIN:-$HOME/.local/bin/tplay}"
DATA_DIR="$TARGET/data"
VENV="$TARGET/.venv"
PINNED="$TARGET/.pinned-python"
WRAPPER_MARKER="# tplay: managed wrapper (install.sh) — no editar a mano"

# Rango de intérpretes aceptados. Subir MAX_MINOR es una decisión explícita del
# proyecto: hasta entonces no se apunta a una versión mayor sin verificar.
MIN_MINOR=10
MAX_MINOR=15

die() {
    printf 'Error: %s\n' "$*" >&2
    exit 1
}

# ── Helpers de paquetes del sistema ──
detect_pkg_mgr() {
    local mgr
    for mgr in apk apt-get dnf pacman; do
        if command -v "$mgr" &>/dev/null; then
            printf '%s\n' "$mgr"
            return 0
        fi
    done
    return 1
}

install_system_pkg() {
    local mgr="$1"
    shift
    case "$mgr" in
        apk)     sudo apk add --no-cache "$@" ;;
        apt-get) sudo apt-get install -y "$@" ;;
        dnf)     sudo dnf install -y "$@" ;;
        pacman)  sudo pacman -S --noconfirm --needed "$@" ;;
    esac
}

aviso_manual() {
    local mgr="$1"
    local pkg="$2"
    case "$mgr" in
        apk)     echo "sudo apk add $pkg" ;;
        apt-get) echo "sudo apt install $pkg" ;;
        dnf)     echo "sudo dnf install $pkg" ;;
        pacman)  echo "sudo pacman -S $pkg" ;;
    esac
}

# Intenta instalar un paquete del sistema sin abortar la instalación: son
# dependencias que tplay tolera no tener (con avisos), no el intérprete.
intentar_pkg() {
    local etiqueta="$1" pkg="$2" mgr
    shift 2
    if mgr="$(detect_pkg_mgr)"; then
        if install_system_pkg "$mgr" "$@"; then
            return 0
        fi
        printf '  ⚠ No se pudo instalar %s automáticamente.\n' "$etiqueta" >&2
        printf '    Instalalo a mano: %s\n' "$(aviso_manual "$mgr" "$pkg")" >&2
    else
        printf '  ⚠ No se detectó gestor de paquetes. Instalá %s a mano.\n' "$etiqueta" >&2
    fi
    return 1
}

# major.minor de un intérprete; vacío si no responde.
py_minor() {
    [ -x "$1" ] || return 1
    "$1" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null
}

in_range() {
    local maj="${1%%.*}" min="${1##*.}"
    [ "$maj" = "3" ] || return 1
    [ "$min" -ge "$MIN_MINOR" ] 2>/dev/null && [ "$min" -lt "$MAX_MINOR" ] 2>/dev/null
}

# Devuelve la ruta del mejor intérprete VERSIONADO disponible en el rango.
# Ignora a propósito /usr/bin/python3 (el flotante): solo python3.X.
resolve_python() {
    local cand best="" best_min=-1 minor real v
    for cand in /usr/bin/python3.* /usr/local/bin/python3.*; do
        [ -x "$cand" ] || continue
        case "${cand##*/}" in
            python3.*) ;;
            *) continue ;;
        esac
        v="$(py_minor "$cand")" || continue
        in_range "$v" || continue
        minor="${cand##*.}"
        case "$minor" in
            *[!0-9]*) continue ;;
        esac
        if [ "$minor" -gt "$best_min" ]; then
            best_min="$minor"
            real="$(readlink -f "$cand" 2>/dev/null || printf '%s' "$cand")"
            best="$real"
        fi
    done
    [ -n "$best" ] || return 1
    printf '%s\n' "$best"
}

# Intérprete a usar: el pineado si sigue vivo, si no el mejor disponible.
pick_python() {
    local pinned_py="" pinned_real
    if [ -f "$PINNED" ]; then
        pinned_py="$(cat "$PINNED")"
        pinned_real="$(readlink -f "$pinned_py" 2>/dev/null || printf '%s' "$pinned_py")"
        if [ -x "$pinned_real" ] && in_range "$(py_minor "$pinned_real" || true)"; then
            printf '%s\n' "$pinned_real"
            return 0
        fi
    fi
    resolve_python
}

# ¿El venv cuelga del alias flotante /usr/bin/python3?
#
# Comparar rutas RESUELTAS no alcanza: un venv flotante (python → python3 →
# /usr/bin/python3 → python3.12) resuelve exactamente a la misma ruta que uno
# sano, así que un health-check por destino lo daría por bueno. El destino no
# delata la estructura; hay que recorrer el enlace.
#   sano:     .venv/bin/python3 -> python3.12
#   flotante: .venv/bin/python3 -> /usr/bin/python3
# Un venv con --copies no tiene symlink: readlink falla y se considera estable.
venv_flota() {
    local target abs
    target="$(readlink "$VENV/bin/python3" 2>/dev/null)" || return 1
    [ -n "$target" ] || return 1
    case "$target" in
        /*) abs="$target" ;;
        *) abs="$VENV/bin/$target" ;;
    esac
    # Si el destino final no es symlink, no puede cambiar de versión: estable.
    [ -L "$abs" ] || return 1
    case "${abs##*/}" in
        python3) return 0 ;;
    esac
    return 1
}

# ¿El venv responde, corre el intérprete pineado, y las 3 deps se importan?
#
# A diferencia de pc-monitor (que solo usa stdlib), tplay depende de vlc, mutagen
# y yt-dlp. Un venv al que le falte una sola tiene que considerarse roto: si no,
# el wrapper lanzaría el comando y tplay moriría con ModuleNotFoundError crudo.
venv_ok() {
    [ -x "$VENV/bin/python" ] || return 1
    venv_flota && return 1
    "$VENV/bin/python" -c '' >/dev/null 2>&1 || return 1
    [ -f "$PINNED" ] || return 1
    local want have
    want="$(readlink -f "$(cat "$PINNED")" 2>/dev/null || true)"
    have="$(readlink -f "$VENV/bin/python" 2>/dev/null || true)"
    [ -n "$want" ] || return 1
    [ "$want" = "$have" ] || return 1
    "$VENV/bin/python" -c 'import player' >/dev/null 2>&1 || return 1
    "$VENV/bin/python" -c 'import vlc, mutagen' >/dev/null 2>&1 || return 1
    # yt-dlp se usa como BINARIO del PATH (player/web.py:19), no como módulo.
    [ -x "$VENV/bin/yt-dlp" ] || return 1
}

create_venv() {
    # $1 = ruta versionada del intérprete. Nunca `python3`.
    "$1" -m venv "$VENV"
    "$VENV/bin/pip" install --quiet --upgrade pip
    # Las deps salen de pyproject [project.dependencies], que es la fuente única
    # (v0.17). No hay requirements.txt: declararlas en dos lugares era la
    # duplicación que arrancó esta migración.
    #
    # `-e .` en vez de las 3 sueltas: si pyproject agrega una dep en el futuro,
    # esta línea la instala sola, sin editar install.sh.
    #
    # Sin --break-system-packages y sin --user: las deps van al venv. La cascada
    # anterior que llegaba a `pip install --break-system-packages` sobre el
    # site-packages del sistema queda eliminada: modificaba el Python del SO.
    "$VENV/bin/pip" install --quiet -e "$TARGET"
    # Marca de recreación con nanosegundos. _cli_update la compara antes y
    # después de reejecutar este script para poder avisar "reiniciá tplay": si el
    # venv se reemplazó, el proceso que corre quedó apuntando a un árbol que ya no
    # existe. (Comparar el inode del symlink no sirve: al borrarlo y recrearlo el
    # filesystem reutiliza el número y el rebuild pasa inadvertido.)
    date +%s%N >"$VENV/.created-at"
}

# ~/.local/bin/tplay deja de ser un symlink al venv y pasa a ser un wrapper con
# health-check Y auto-reparación.
#
# Por qué puede repararse solo: este script es bash, no Python. No necesita el venv
# para correr, así que puede ejecutar install.sh (que solo usa git y un
# /usr/bin/python3.X del sistema) aunque el venv esté muerto. Ese es exactamente el
# caso del upgrade de SO que lo dejaba sin salida: cuando el venv cuelga de una
# versión que el SO borró, `tplay --update` tampoco puede correr, porque el comando
# que lo haría está muerto.
write_wrapper() {
    mkdir -p "$(dirname "$BIN")"
    cat >"$BIN" <<EOF
#!/usr/bin/env bash
$WRAPPER_MARKER
set -uo pipefail

VENV="$VENV"
PINNED="$PINNED"
DEST="$TARGET"
REPAIR="curl -fsSL $RAW_INSTALL | bash"

# ── yt-dlp se usa como BINARIO del PATH, no como módulo ──
# player/web.py:19 tiene _YTDLP_BIN = "yt-dlp" y lo llama con subprocess.run.
# En el venv cae en \$VENV/bin/yt-dlp, así que sin esto web.is_available()
# devuelve False y se pierden búsqueda, descarga y Web Explorer — sin ningún
# error visible, que es la peor forma de romperse. pc-monitor no necesita esto
# porque no llama binarios externos.
export PATH="\$VENV/bin:\$PATH"

# Los argumentos del comando se guardan aparte porque dentro de repair() "\$@"
# son los de la función (vacíos), no los del wrapper: sin esto el relanzamiento
# perdería --version y entraría directo a la TUI.
ARGS=("\$@")
[ "\${#ARGS[@]}" -gt 0 ] || ARGS=()

# Intenta reconstruir el entorno con el install.sh que ya está en el repo. Es bash
# puro, así que funciona aunque el venv no exista. Auto-limitado a un intento por
# invocación para no quedar en loop si install.sh no lo logra.
repair() {
    local n="\${TPLAY_REPAIR_ATTEMPT:-0}"
    if [ "\$n" -ge 1 ]; then
        return 1
    fi
    if [ ! -f "\$DEST/install.sh" ] || ! command -v git >/dev/null 2>&1; then
        return 1
    fi
    echo "tplay: el entorno virtual no sirve. Reparando..." >&2
    if ! TPLAY_DIR="\$DEST" TPLAY_REPAIR_ATTEMPT=1 bash "\$DEST/install.sh" >&2; then
        echo "tplay: la reparación automática falló." >&2
        return 1
    fi
    # install.sh acaba de REESCRIBIR este mismo archivo. Bash lee los scripts por
    # partes y no vuelve atrás, así que seguir ejecutando acá leería basura del
    # archivo viejo. Hay que releer el wrapper nuevo desde \$0.
    #
    # TPLAY_REPAIR_ATTEMPT=1 evita el loop: si el wrapper recién escrito sigue
    # sin encontrar venv, esta segunda pasada no repara y cae al mensaje final.
    TPLAY_REPAIR_ATTEMPT=1 exec bash "\$0" "\${ARGS[@]}"
}

# El venv no responde (intérprete borrado por un upgrade del SO, o venv roto).
if [ ! -x "\$VENV/bin/python" ] || ! "\$VENV/bin/python" -c '' >/dev/null 2>&1; then
    echo "tplay: el entorno virtual está roto — \$VENV/bin/python no responde." >&2
    if [ -f "\$PINNED" ]; then
        echo "  intérprete pineado: \$(cat "\$PINNED") (ya no existe o no es ejecutable)" >&2
    fi
    if repair; then
        exit 1
    fi
    echo "  Reparalo a mano con:  \$REPAIR" >&2
    exit 1
fi

# Cubre el caso del upgrade del SO: layout del venv y versión del intérprete
# desalineados dejan el install editable invisible (ModuleNotFoundError).
if ! "\$VENV/bin/python" -c 'import player' >/dev/null 2>&1; then
    echo "tplay: el paquete player no se importa con \$VENV/bin/python." >&2
    echo "  Suele ser un venv viejo (\$(\$VENV/bin/python -V 2>&1)) re-hecho contra otra versión." >&2
    if repair; then
        exit 1
    fi
    echo "  Reparalo a mano con:  \$REPAIR" >&2
    exit 1
fi

# Falta alguna de las 3 deps (vlc / mutagen / yt-dlp). Sin este chequeo el comando
# arranca y muere con ModuleNotFoundError crudo en player/metadata.py:5, que hace
# "import mutagen" sin guard.
if ! "\$VENV/bin/python" -c 'import vlc, mutagen' >/dev/null 2>&1; then
    echo "tplay: faltan dependencias en el entorno virtual." >&2
    if repair; then
        exit 1
    fi
    echo "  Reparalo a mano con:  \$REPAIR" >&2
    exit 1
fi

# Aviso (no error): el venv funciona, pero el pin quedó desalineado. install.sh lo
# corrige en la próxima corrida, así que no vale la pena tocar nada.
if [ -f "\$PINNED" ]; then
    pinned_real="\$(readlink -f "\$(cat "\$PINNED")" 2>/dev/null || true)"
    have_real="\$(readlink -f "\$VENV/bin/python" 2>/dev/null || true)"
    if [ -n "\$pinned_real" ] && [ "\$pinned_real" != "\$have_real" ]; then
        echo "tplay: aviso — el venv corre \$have_real pero el pin dice \$pinned_real." >&2
    fi
fi

exec "\$VENV/bin/python" -m player "\$@"
EOF
    chmod +x "$BIN"
}

# Si hay algo en $BIN que no es nuestro, lo respaldamos antes de pisarlo.
prepare_bin() {
    mkdir -p "$(dirname "$BIN")"
    [ -e "$BIN" ] || [ -L "$BIN" ] || return 0
    if grep -qF "$WRAPPER_MARKER" "$BIN" 2>/dev/null; then
        return 0 # es nuestro wrapper: se sobrescribe
    fi
    if [ -L "$BIN" ]; then
        local link
        link="$(readlink -f "$BIN" 2>/dev/null || true)"
        case "$link" in
            "$VENV"/*)
                # Symlink viejo de la instalación anterior. Hay que BORRAR el
                # enlace, no solo dejar pasar: `cat > $BIN` escribe atravesando
                # symlinks, así que sin esto el wrapper se endosaba sobre el
                # console script de pip dentro del .venv y ~/.local/bin/tplay
                # seguía siendo un symlink en vez del wrapper.
                rm -f "$BIN"
                return 0
                ;;
        esac
    fi
    local backup="$BIN.bak.$(date +%Y%m%d%H%M%S)"
    mv "$BIN" "$backup"
    printf '  ↳ binario previo respaldado en %s\n' "$backup"
}

# Append idempotente al rc del shell de login. La versión anterior solo avisaba y
# nunca escribía, así que un usuario sin ~/.local/bin en PATH terminaba con
# "command not found" después de un install exitoso.
ensure_path() {
    local rc
    if [ -n "${TPLAY_RC:-}" ]; then
        rc="${TPLAY_RC}"
    elif [ -n "${ZDOTDIR:-}" ] && [ -f "${ZDOTDIR}/.zshrc" ]; then
        rc="${ZDOTDIR}/.zshrc"
    elif [ -f "$HOME/.zshrc" ]; then
        rc="$HOME/.zshrc"
    else
        rc="$HOME/.bashrc"
    fi
    [ -f "$rc" ] || touch "$rc"
    if grep -qF '.local/bin' "$rc"; then
        return 0
    fi
    {
        printf '\n# tplay: comandos de usuario\n'
        printf 'export PATH="$HOME/.local/bin:$PATH"\n'
    } >>"$rc"
    printf '  ↳ ~/.local/bin agregado al PATH en %s\n' "$rc"
}

# ── Prerrequisitos ──
command -v git >/dev/null 2>&1 || die "git no está instalado"

# ── Obtener/actualizar el código ──
printf '▶ tplay — instalando en %s\n' "$TARGET"
if [ -d "$TARGET/.git" ]; then
    echo "  ↳ ya existe, actualizando..."
    git -C "$TARGET" pull --ff-only
elif [ -d "$TARGET" ]; then
    echo "  ↳ existe pero no es un repo, respaldando como tplay.bak..."
    mv "$TARGET" "$TARGET.bak"
    git clone "$REPO_URL" "$TARGET"
else
    mkdir -p "$(dirname "$TARGET")"
    git clone "$REPO_URL" "$TARGET"
fi

# ── Intérprete pineado ──
# El pin se reescribe SIEMPRE: si el intérprete pineado murió (upgrade del SO que
# lo borró) hay que apuntar al nuevo, o el chequeo de venv_ok de abajo compara
# contra un pin viejo y da falso negativo.
PY="$(pick_python)" || die "no hay un /usr/bin/python3.X entre 3.$MIN_MINOR y 3.$((MAX_MINOR - 1))"
if [ -f "$PINNED" ] && [ "$(cat "$PINNED")" = "$PY" ]; then
    echo "  ↳ intérprete pineado: $PY (reusado)"
else
    if [ -f "$PINNED" ]; then
        echo "  ↳ intérprete pineado: $PY (cambió: $(cat "$PINNED"))"
    else
        echo "  ↳ intérprete pineado: $PY"
    fi
    printf '%s\n' "$PY" >"$PINNED"
fi

# ── Entorno virtual + deps desde pyproject ──
if venv_ok; then
    echo "  ↳ venv sano ($(py_minor "$VENV/bin/python")) — se reusa"
else
    if [ -d "$VENV" ]; then
        echo "  ↳ venv roto, desalineado, anclado al alias flotante o sin deps — recreando con $PY"
        rm -rf "$VENV"
    fi
    create_venv "$PY"
    venv_ok || die "el venv se creó pero tplay no arranca — revisá $VENV"
    echo "  ↳ venv creado con $PY"
fi

# ── Dependencias del sistema (vlc / ffmpeg / pipewire-alsa) ──
#
# Estas NO van en el venv: libvlc es una librería C que python-vlc carga por
# ctypes. El venv aísla la capa Python, no la nativa. Deuda conocida.

# libvlc: sin esta librería tplay no arranca — 100% necesario.
# Se detecta por librería del sistema (ldconfig/ls), no por import python,
# para no confundir "falta VLC" con "falta python-vlc".
#
# grep SIN -q a propósito: con `set -o pipefail`, `grep -q` cierra el pipe en
# cuanto encuentra la coincidencia y ldconfig muere con SIGPIPE, así que el
# pipeline devuelve error y la detección da FALSO NEGATIVO en una máquina que
# sí tiene VLC. Sin -q, grep lee toda la entrada y no hay SIGPIPE.
#
# El fallback usa compgen y no `ls /usr/lib*/libvlc.so*`: un glob sin match
# hace fallar el globbing y con `set -e` eso aborta el script entero. compgen
# devuelve 1 sin match, que es exactamente lo que queremos.
if ! (ldconfig -p 2>/dev/null | grep libvlc >/dev/null || compgen -G "/usr/lib*/libvlc.so*" >/dev/null); then
    echo "  ↳ No se detectó libvlc (VLC). Intentando instalar vlc..."
    intentar_pkg "vlc" "vlc" vlc || true
else
    echo "  ↳ libvlc (VLC) OK"
fi

# ffmpeg: yt-dlp lo necesita para extraer/convertir audio y mergear video — sin él las descargas fallan
if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "  ↳ No se detectó ffmpeg. Intentando instalar (necesario para descargas)..."
    intentar_pkg "ffmpeg" "ffmpeg" ffmpeg || true
else
    echo "  ↳ ffmpeg OK"
fi

# pipewire-alsa: solo si hay PipeWire activo — evita tplay mudo
if [ -n "${XDG_RUNTIME_DIR:-}" ] && [ -S "$XDG_RUNTIME_DIR/pipewire-0" ]; then
    if command -v ffmpeg >/dev/null 2>&1; then
        echo "  ↳ PipeWire detectado. Instalando pipewire-alsa (puente ALSA→PipeWire)..."
        intentar_pkg "pipewire-alsa" "pipewire-alsa" pipewire-alsa || true
    fi
fi

# ── Datos ──
# Los datos NO se tocan. Si ya existe un árbol legacy en ~/.config/tplay/data se
# deja donde está: la migración la hace player/paths.py en el primer arranque,
# por copia, para que el original sobreviva si algo sale mal (v0.22).
mkdir -p "$DATA_DIR"

# ── Ejecutable ──
prepare_bin
write_wrapper
ensure_path

# ── Smoke test: si esto falla, no declaramos éxito ──
if ! out="$("$BIN" --version 2>&1)"; then
    printf '%s\n' "$out" >&2
    die "instalación incompleta: '$BIN --version' falló"
fi

echo ""
echo "✅ tplay instalado. Ejecutá:  tplay"
echo "   Versión:    $out"
echo "   Código:     $TARGET"
echo "   Intérprete: $PY (pineado en $(basename "$PINNED"))"
echo "   Datos:      $DATA_DIR (intactos)"
echo "   Comandos: tplay · tplay --update · tplay --reinstall · tplay --uninstall · tplay --version"
