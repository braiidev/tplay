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

# ── Ejecutable ──
echo "  ↳ Creando $BIN (requiere sudo)..."
sudo tee "$BIN" > /dev/null << TSCRIPT
#!/usr/bin/env bash
exec python3 "$INSTALL_DIR/app.py" "\$@"
TSCRIPT
sudo chmod +x "$BIN"

echo ""
echo "✅ tplay instalado correctamente"
echo "   Ejecutá:  tplay"
echo "   Código:   $INSTALL_DIR"
echo "   Datos:    $INSTALL_DIR/data/"
