"""Rutas y guard de arranque.

Dos cosas que estaban repartidas y ahora tienen una sola fuente:

1. **Rutas.** Antes cada módulo hardcodeaba `~/.config/tplay/data` por su cuenta
   (config.py, state.py, playlist.py, favorites.py, radios.py, downloads.py,
   platforms.py, ytdlp_update.py: nueve copias). Como `INSTALL_DIR` también era
   `~/.config/tplay`, los datos vivían DENTRO del repo clonado, y `rm -rf` de la
   desinstalación se los llevaba sin preguntar.

   Ahora el código va a `~/.local/share/tplay` y los datos quedan al lado, en
   `~/.local/share/tplay/data`, fuera del árbol de git. Si ya existe un árbol
   legacy en `~/.config/tplay/data`, se copia —nunca se mueve— así que el
   original sobrevive si algo sale mal.

2. **Guard de arranque.** tplay tiene 3 deps y dos de ellas (mutagen, yt-dlp)
   se importan peladas, sin try/except. Una ausente daba un ModuleNotFoundError
   crudo que no decía cómo arreglarlo. `chequear_deps()` import�� las tres y
   devuelve un mensaje con el comando exacto, que main() imprime antes de
   levantar la TUI.

La migración es one-shot por arranque y no toca la red.
"""

from __future__ import annotations

import os
import shutil
import sys

# Código instalado. ~/.local/share es el lugar para datos de apps (no caché
# descartable, no config editable a mano); ~/.config queda para lo que el
# usuario abre con un editor.
INSTALL_DIR = os.path.expanduser("~/.local/share/tplay")

DATA_DIR = os.path.join(INSTALL_DIR, "data")

# CONFIG_DIR es el nombre que ya usaban cinco módulos (audio, favorites,
# playlist, radios, state) y los tests. Se mantiene como alias para no tocar
# todos los call sites; la ruta real sale de DATA_DIR.
CONFIG_DIR = DATA_DIR
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")

# Árbol legacy: datos dentro del repo clonado en ~/.config/tplay.
LEGACY_DATA_DIR = os.path.expanduser("~/.config/tplay/data")

# Repo legacy completo, para nombrarlo en los mensajes de error. El launcher
# viejo /usr/local/bin/tplay hace `exec python3 <LEGACY_REPO>/app.py`.
LEGACY_REPO = os.path.expanduser("~/.config/tplay")

# `yt-dlp` se llama como binario del PATH (ver player/web.py), no como módulo. El
# wrapper pone el bin del venv en el PATH; si alguien invoca el módulo sin
# wrapper (python -m player), no lo encuentra. Esta es la razón por la que
# install.sh genera el wrapper con `export PATH="$VENV/bin:$PATH"`.
_YTDLP_BIN = "yt-dlp"


def _copiar_arbol(origen: str, destino: str) -> bool:
    """Copia `origen` a `destino` sin pisar lo que ya existe ahí.

    `dirs_exist_ok=True` + overwrite en False: si algo ya existe en el destino se
    deja como está. Una migración nunca debe pisar datos más nuevos.
    """
    for dirpath, _dirnames, filenames in os.walk(origen):
        rel = os.path.relpath(dirpath, origen)
        destino_dir = os.path.join(DATA_DIR, rel) if rel != "." else DATA_DIR
        os.makedirs(destino_dir, exist_ok=True)
        for nombre in filenames:
            if nombre.endswith(".tmp"):
                continue  # escrituras atómicas en curso, no datos
            src = os.path.join(dirpath, nombre)
            dst = os.path.join(destino_dir, nombre)
            if os.path.exists(dst):
                continue
            shutil.copy2(src, dst)
    return True


def migrar_datos_legacy() -> str | None:
    """Copia los datos de ~/.config/tplay/data al nuevo DATA_DIR si hace falta.

    Idempotente: si el destino ya tiene archivos, no se pisa nada. Se llama una
    vez por arranque y no toca la red.

    Devuelve un mensaje para imprimir si migró algo, o None si no había nada.
    """
    if os.path.realpath(LEGACY_DATA_DIR) == os.path.realpath(DATA_DIR):
        return None
    if not os.path.isdir(LEGACY_DATA_DIR):
        return None
    # Ya migrado: hay archivos en el destino, no se vuelve a copiar.
    if os.path.isdir(DATA_DIR) and os.listdir(DATA_DIR):
        return None

    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        _copiar_arbol(LEGACY_DATA_DIR, DATA_DIR)
    except OSError as e:
        return (
            f"No se pudieron copiar los datos de {LEGACY_DATA_DIR} a {DATA_DIR}: {e}\n"
            f"Tus datos siguen intactos en el lugar viejo."
        )
    return (
        f"Datos migrados: {LEGACY_DATA_DIR} → {DATA_DIR}\n"
        f"  copia, no movimiento: el original queda intacto hasta que confirmes que todo está bien."
    )


# Las 3 deps declaradas en pyproject [project.dependencies]. Los nombres de
# import no coinciden con los de distribución: python-vlc importa como `vlc`.
DEPS_IMPORT: tuple[tuple[str, str], ...] = (
    ("vlc", "python-vlc"),
    ("mutagen", "mutagen"),
    ("yt_dlp", "yt-dlp"),
)


def _hay_venv() -> bool:
    """True si estamos corriendo desde el venv que creó install.sh.

    `sys.prefix != sys.base_prefix` es la forma canónica de saberlo. Fuera del
    venv, `sys.prefix` es el del intérprete del sistema.
    """
    return sys.prefix != sys.base_prefix


def chequear_deps() -> str | None:
    """Devuelve un mensaje de error si falta alguna dep, o None si todo está.

    Se llama desde main() antes de la TUI. El objetivo es que nunca más se muera
    con un ModuleNotFoundError crudo: o se repara, o se dice qué correr.
    """
    faltantes: list[str] = []
    for modulo, distribucion in DEPS_IMPORT:
        try:
            __import__(modulo)
        except (ImportError, OSError):
            faltantes.append(distribucion)

    if not os.path.exists(os.path.join(sys.prefix, "bin", _YTDLP_BIN)):
        # yt-dlp se llama como binario del PATH. Importarlo bien no alcanza:
        # sin el ejecutable, búsqueda y descargas no funcionan sin error visible.
        # El sufijo "(binario)" distingue este caso del import roto, para que
        # quede claro que hay que revisar el PATH del venv y no solo las deps.
        if not any(d.startswith("yt-dlp (binario)") for d in faltantes):
            faltantes.append("yt-dlp (binario)")

    if not faltantes:
        return None

    return _mensaje_deps(faltantes)


def _mensaje_deps(faltantes: list[str]) -> str:
    """Arma el mensaje, adaptándolo a si hay venv o no.

    Este detalle costó una sesión de diagnóstico: la primera versión decía
    siempre "Faltan dependencias en el entorno virtual" y daba "repará el venv"
    como única solución. Pero cuando tplay corre FUERA de un venv —el caso del
    launcher legacy `/usr/local/bin/tplay`, que hace `exec python3 app.py`— no
    hay ningún venv que reparar, y el mensaje mandaba a tocar el sitio
    equivocado.

    Ese caso es confuso de ver porque las 3 deps SÍ importan (están en el
    user-site de una instalación vieja) pero el binario de yt-dlp no existe en
    `/usr/bin`. El síntoma visible es un solo ítem, "yt-dlp (binario)", que
    parece una dep suelta y no una instalación en el sitio incorrecto.
    """
    if _hay_venv():
        cabecera = "Faltan dependencias en el entorno virtual:\n"
        solucion = (
            "\nReparalo con:\n"
            "  curl -fsSL https://raw.githubusercontent.com/braiidev/tplay/main/install.sh | bash\n"
            f"\n(o reinstallá el venv: {os.path.join(INSTALL_DIR, '.venv', 'bin', 'pip')}"
            f" install -e {INSTALL_DIR})"
        )
    else:
        # Sin venv: el código está en el intérprete del sistema y las deps
        # pueden venir de un user-site viejo. Decirlo es la mitad del arreglo.
        cabecera = (
            "Faltan dependencias, y además tplay NO está corriendo en su entorno virtual.\n"
            f"  intérprete: {sys.executable}\n"
            f"  sys.prefix: {sys.prefix}  (no es un venv)\n"
            "\nEsto pasa con el launcher viejo /usr/local/bin/tplay, que hace\n"
            f"  exec python3 {LEGACY_REPO}/app.py\n"
            "y corre con el Python del sistema en vez del venv de tplay.\n"
            "\nLas deps de arriba pueden estar viniendo de un user-site viejo\n"
            f"(~/.local/lib/python3.X/site-packages), y ese no se usa desde {INSTALL_DIR}.\n"
        )
        solucion = (
            "\nSolución: instalá tplay y usá el comando del venv:\n"
            "  curl -fsSL https://raw.githubusercontent.com/braiidev/tplay/main/install.sh | bash\n"
            f"\n  {os.path.expanduser('~/.local/bin/tplay')}\n"
            "\nSi el comando sigue resolviendo al launcher viejo, tu PATH tiene\n"
            "/usr/local/bin antes que ~/.local/bin. Corregilo, o:\n"
            f"  hash -r    # zsh/bash: limpia el comando cacheado de la sesión\n"
            f"  rehash     # zsh, alternativa"
        )

    return cabecera + "".join(f"  · {d}\n" for d in faltantes) + solucion

