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
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3,10) else 1)"; then
    echo "Error: se necesita Python >= 3.10 (actual: $PY_VER)" >&2
    exit 1
fi

# ── Helpers de paquetes del sistema ──
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
# pip puede no venir instalado (Alpine: py3-pip, Debian/Ubuntu: python3-pip)
if ! python3 -m pip --version >/dev/null 2>&1; then
    echo "  ↳ No se detectó pip. Intentando instalarlo con tu gestor de paquetes..."
    if mgr=$(detect_pkg_mgr); then
        case "$mgr" in
            apk)     pip_pkg="py3-pip" ;;
            apt-get) pip_pkg="python3-pip" ;;
            dnf)     pip_pkg="python3-pip" ;;
            pacman)  pip_pkg="python-pip" ;;
        esac
        if ! install_system_pkg "$mgr" "$pip_pkg"; then
            echo "  ⚠ No se pudo instalar pip automáticamente." >&2
            echo "    Instalalo a mano: $(aviso_manual "$mgr" "$pip_pkg")" >&2
        fi
    fi
fi

if python3 -m pip --version >/dev/null 2>&1; then
    echo "  ↳ Instalando dependencias Python..."
    # Cascada compatible con PEP 668 (Ubuntu/Debian modernos) y sin privilegios
    if ! python3 -m pip install --user -r requirements.txt >/dev/null 2>&1 \
        && ! python3 -m pip install --break-system-packages --user -r requirements.txt >/dev/null 2>&1 \
        && ! python3 -m pip install --break-system-packages -r requirements.txt >/dev/null 2>&1; then
        echo "  ⚠ No se pudieron instalar las dependencias Python automáticamente." >&2
        echo "    Comando manual: python3 -m pip install --break-system-packages -r requirements.txt" >&2
    fi
else
    echo "  ⚠ pip no disponible — no se pudieron instalar las dependencias Python." >&2
fi

# ── Dependencias del sistema (vlc / ffmpeg / pipewire-alsa) ──

# libvlc: sin esta librería tplay no arranca — 100% necesario.
# Se detecta por librería del sistema (ldconfig/ls), no por import python,
# para no confundir "falta VLC" con "falta python-vlc".
if ! (ldconfig -p 2>/dev/null | grep -q "libvlc" || ls /usr/lib*/libvlc.so* >/dev/null 2>&1); then
    echo "  ↳ No se detectó libvlc (VLC). Instalando vlc..."
    if mgr=$(detect_pkg_mgr); then
        if ! install_system_pkg "$mgr" vlc; then
            echo "  ⚠ No se pudo instalar vlc automáticamente." >&2
            echo "    Instalalo a mano: $(aviso_manual "$mgr" vlc)" >&2
        fi
    else
        echo "  ⚠ No se detectó gestor de paquetes. Instalá VLC a mano:" >&2
        echo "    Debian/Ubuntu: sudo apt install vlc" >&2
        echo "    Alpine:        sudo apk add vlc" >&2
        echo "    Arch:          sudo pacman -S vlc" >&2
        echo "    Fedora:        sudo dnf install vlc" >&2
    fi
fi

# ffmpeg: yt-dlp lo necesita para extraer/convertir audio y mergear video — sin él las descargas fallan
if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "  ↳ No se detectó ffmpeg. Instalando ffmpeg (necesario para descargas)..."
    if mgr=$(detect_pkg_mgr); then
        if ! install_system_pkg "$mgr" ffmpeg; then
            echo "  ⚠ No se pudo instalar ffmpeg automáticamente." >&2
            echo "    Instalalo a mano: $(aviso_manual "$mgr" ffmpeg)" >&2
        fi
    else
        echo "  ⚠ No se detectó gestor de paquetes. Instalá ffmpeg a mano:" >&2
        echo "    Debian/Ubuntu: sudo apt install ffmpeg" >&2
        echo "    Alpine:        sudo apk add ffmpeg" >&2
        echo "    Arch:          sudo pacman -S ffmpeg" >&2
        echo "    Fedora:        sudo dnf install ffmpeg" >&2
    fi
fi

# pipewire-alsa: solo si hay PipeWire activo — evita tplay mudo
if [ -n "$XDG_RUNTIME_DIR" ] && [ -S "$XDG_RUNTIME_DIR/pipewire-0" ]; then
    if mgr=$(detect_pkg_mgr); then
        echo "  ↳ PipeWire detectado. Instalando pipewire-alsa (puente ALSA→PipeWire)..."
        if ! install_system_pkg "$mgr" pipewire-alsa; then
            echo "  ⚠ No se pudo instalar pipewire-alsa automáticamente." >&2
            echo "    Instalalo a mano: $(aviso_manual "$mgr" pipewire-alsa)" >&2
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

# ── Verificación final ──
echo ""
echo "  ↳ Verificando instalación:"
if python3 -c "import vlc; vlc.libvlc_get_version()" >/dev/null 2>&1; then
    echo "    ✓ libvlc (VLC) OK"
else
    echo "    ⚠ libvlc no responde — revisá la instalación de VLC/python-vlc" >&2
fi
if command -v yt-dlp >/dev/null 2>&1; then
    echo "    ✓ yt-dlp $(yt-dlp --version 2>/dev/null || echo '?')"
else
    echo "    ⚠ yt-dlp no encontrado — búsquedas y descargas no funcionarán" >&2
fi
if command -v ffmpeg >/dev/null 2>&1; then
    echo "    ✓ ffmpeg"
else
    echo "    ⚠ ffmpeg no encontrado — las descargas fallarán al final" >&2
fi

echo ""
echo "✅ tplay instalado correctamente"
echo "   Ejecutá:  tplay"
echo "   Código:   $INSTALL_DIR"
echo "   Datos:    $INSTALL_DIR/data/"