#!/usr/bin/env bash
# install.sh — Instala tplay (reproductor multimedia TUI)
# Uso: curl -fsSL https://raw.githubusercontent.com/braiidev/tplay/main/install.sh | bash

set -e

REPO_URL="https://github.com/braiidev/tplay.git"
INSTALL_DIR="${1:-$HOME/.config/tplay}"
BIN="/usr/local/bin/tplay"

# ── Prerrequisitos ──
for cmd in git python3; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "Error: $cmd no está instalado" >&2
        exit 1
    fi
done

# Verificar Python 3.10+
PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if python3 -c "import sys; exit(0 if sys.version_info >= (3,10) else 1)"; then
    :
else
    echo "Error: se necesita Python >= 3.10 (actual: $PY_VER)" >&2
    exit 1
fi

# ── Instalación ──
echo "▶ Instalando tplay en $INSTALL_DIR"

if [ -d "$INSTALL_DIR/.git" ]; then
    echo "  ↳ $INSTALL_DIR ya existe, actualizando..."
    cd "$INSTALL_DIR" && git pull
elif [ -d "$INSTALL_DIR" ]; then
    echo "  ↳ $INSTALL_DIR ya existe pero no es un repo, respaldando como tplay.bak..."
    mv "$INSTALL_DIR" "${INSTALL_DIR}.bak"
    git clone "$REPO_URL" "$INSTALL_DIR"
else
    mkdir -p "$(dirname "$INSTALL_DIR")"
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# ── Dependencias Python ──
echo "  ↳ Instalando dependencias Python..."
if pip3 install -r requirements.txt 2>/dev/null; then
    :
else
    pip3 install -r requirements.txt --break-system-packages
fi

# ── Dependencias del sistema (libvlc / pipewire-alsa) ──

detect_pkg_mgr() {
    for mgr in apk apt-get dnf pacman; do
        if command -v "$mgr" &>/dev/null; then
            echo "$mgr"
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

# libvlc: sin esta librería tplay no arranca — 100% necesario
if ! python3 -c "import vlc; vlc.libvlc_get_version()" 2>/dev/null; then
    echo "  ↳ No se detectó libvlc (VLC). Instalando vlc..."
    if mgr=$(detect_pkg_mgr); then
        aviso_manual="sudo $mgr install"
        if [ "$mgr" = "apk" ]; then aviso_manual="sudo apk add"; fi
        if [ "$mgr" = "pacman" ]; then aviso_manual="sudo pacman -S"; fi
        if ! install_system_pkg "$mgr" vlc; then
            echo "  ⚠ No se pudo instalar vlc automáticamente."
            echo "    Instalalo manualmente y volvé a ejecutar este script:"
            echo "      $aviso_manual vlc" >&2
        fi
    else
        echo "  ⚠ No se detectó gestor de paquetes. Instalá VLC a mano:" >&2
        echo "    Debian/Ubuntu: sudo apt install vlc" >&2
        echo "    Alpine:        sudo apk add vlc" >&2
        echo "    Arch:          sudo pacman -S vlc" >&2
        echo "    Fedora:        sudo dnf install vlc" >&2
    fi
fi

# pipewire-alsa: solo si hay PipeWire activo — evita tplay mudo
if [ -n "$XDG_RUNTIME_DIR" ] && [ -S "$XDG_RUNTIME_DIR/pipewire-0" ]; then
    if mgr=$(detect_pkg_mgr); then
        echo "  ↳ PipeWire detectado. Instalando pipewire-alsa (puente ALSA→PipeWire)..."
        if ! install_system_pkg "$mgr" pipewire-alsa; then
            echo "  ⚠ No se pudo instalar pipewire-alsa automáticamente." >&2
            echo "    Instalalo manualmente si tplay se queda mudo." >&2
        fi
    fi
fi

# ── Ejecutable ──
echo "  ↳ Creando $BIN (requiere sudo)..."
sudo tee "$BIN" > /dev/null << TSCRIPT
#!/usr/bin/env sh
exec python3 "$INSTALL_DIR/app.py" "\$@"
TSCRIPT
sudo chmod +x "$BIN"

echo ""
echo "✅ tplay instalado correctamente"
echo "   Ejecutá:  tplay"
echo "   Código:   $INSTALL_DIR"
echo "   Datos:    $INSTALL_DIR/data/"
