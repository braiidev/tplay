#!/usr/bin/env bash
# install.sh — Instala tplay (reproductor multimedia TUI)
# Uso: curl -fsSL https://raw.githubusercontent.com/USER/tplay/main/install.sh | bash
#      bash install.sh
#      bash install.sh /ruta/personalizada

set -e

REPO_URL="https://github.com/USER/tplay.git"
INSTALL_DIR="${1:-$HOME/.config/tplay}"
BIN="/usr/local/bin/tplay"

echo "▶ Instalando tplay en $INSTALL_DIR"

# 1. Clonar repositorio
if [ -d "$INSTALL_DIR" ]; then
    echo "  ↳ $INSTALL_DIR ya existe, actualizando..."
    cd "$INSTALL_DIR" && git pull
else
    mkdir -p "$(dirname "$INSTALL_DIR")"
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# 2. Instalar dependencias Python
echo "  ↳ Instalando dependencias Python..."
pip install -r requirements.txt --break-system-packages

# 3. Crear ejecutable en /usr/local/bin
echo "  ↳ Creando $BIN..."
sudo tee "$BIN" > /dev/null << 'TSCRIPT'
#!/usr/bin/env bash
exec python3 "$(dirname "$(readlink -f "$0")")/../.config/tplay/app.py" "$@"
TSCRIPT

# Ajustar el path real del binario (el tee de arriba no puede expandir variables)
sudo tee "$BIN" > /dev/null << TSCRIPT
#!/usr/bin/env bash
exec python3 "$INSTALL_DIR/app.py" "\$@"
TSCRIPT

sudo chmod +x "$BIN"

echo ""
echo "✅ tplay instalado correctamente"
echo "   Ejecutá:  tplay"
echo "   Config:   $INSTALL_DIR"
echo "   Datos:    ~/.config/player/"
