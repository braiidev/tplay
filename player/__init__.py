import curses
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from .app import PlayerApp
from .paths import chequear_deps, migrar_datos_legacy

__version__ = "0.16.0"

_USAGE = """\
Uso: tplay [opción]

Reproductor de música TUI: biblioteca local, YouTube y radio, con ecualizador
y tema configurable.

Opciones:
  (sin flags)      abre el reproductor (requiere terminal interactivo)
  --update         descarga la última versión del repo y reconcilia las deps
  --reinstall      re-ejecuta install.sh de este repo
  --uninstall      desinstala tplay (pide confirmación antes de tocar datos)
  --ctl <cmd>      control externo por socket: play|pause|next|prev|status|...
  --version        imprime la versión y sale
  --help           imprime esta ayuda y sale
"""


def _repo_dir() -> str:
    """Raíz del repo: el directorio padre del paquete `player`.

    Sigue siendo válida después del cambio a ~/.local/share/tplay porque
    describe la estructura del repo, no una ruta hardcodeada. Los datos ya no
    viven acá adentro (ver player/paths.py).
    """
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _cli_update() -> bool:
    repo = _repo_dir()
    git_dir = os.path.join(repo, ".git")
    if not os.path.isdir(git_dir):
        print("Error: no es un repositorio git, no se puede actualizar", file=sys.stderr)
        return False
    try:
        subprocess.run(["git", "fetch", "origin"], cwd=repo, capture_output=True, timeout=10)
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD..origin/main"],
            cwd=repo, capture_output=True, text=True, timeout=10,
        )
        behind = int(result.stdout.strip() or 0)
        if behind == 0:
            print("✓ tplay ya está actualizado")
            _reconciliar_deps(repo)
            return True
        print(f"  ↳ {behind} commits detrás, actualizando...")
        pull = subprocess.run(["git", "pull", "--ff-only"], cwd=repo,
                              capture_output=True, text=True, timeout=30)
        if pull.returncode == 0:
            print("✓ tplay actualizado correctamente")
            _reconciliar_deps(repo)
            return True
        reset = subprocess.run(["git", "reset", "--hard", "origin/main"],
                                cwd=repo, capture_output=True, text=True, timeout=10)
        if reset.returncode == 0:
            print("✓ tplay actualizado correctamente (historial corregido)")
            _reconciliar_deps(repo)
            return True
        print(f"Error: {pull.stderr.strip()}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False


def _pip_venv() -> str | None:
    """El pip del venv, o None si estamos fuera de un venv.

    Importante: nunca usamos `sys.executable -m pip --user` ni
    `--break-system-packages`. Con el venv de install.sh, `sys.executable` YA
    es el intérprete del venv, así que un pip simple instala en el lugar
    correcto. Si no hay venv, saymoso y que el usuario use install.sh.
    """
    if sys.prefix == sys.base_prefix:
        return None  # intérprete del sistema, sin venv
    return sys.executable


def _reconciliar_deps(repo: str) -> None:
    """Instala el proyecto y sus deps en el venv, después de un git pull.

    Reemplaza a la versión anterior, que comparaba `requirements.txt` línea por
    línea. Ese archivo ya no existe (v0.17 lo borró: pyproject.toml es la única
    fuente), así que `_install_new_deps` retornaba en silencio y un update que
    cambiaba una dependencia no la instalaba — el peor fallo posible, porque
    parecía haber funcionado.

    `pip install -e .` resuelve por sí solo el conjunto completo de deps: si
    pyproject agrega, quita o sube el techo de algo, esto lo reconcilia sin
    tocar código.
    """
    pip = _pip_venv()
    if pip is None:
        print(
            "  ⚠ No estás en el venv de tplay; no se tocan las deps.\n"
            "  ⚠ Para reconciliarlas: curl -fsSL "
            "https://raw.githubusercontent.com/braiidev/tplay/main/install.sh | bash",
            file=sys.stderr,
        )
        return

    try:
        r = subprocess.run(
            [pip, "-m", "pip", "install", "-e", repo],
            capture_output=True, text=True, timeout=300,
        )
    except (OSError, subprocess.TimeoutExpired):
        print("  ⚠ No se pudo reconciliar las deps automáticamente.", file=sys.stderr)
        print(f"  ⚠ Ejecutá: {pip} -m pip install -e {repo}", file=sys.stderr)
        return

    if r.returncode == 0:
        print("✓ Dependencias reconciliadas en el venv")
    else:
        # No abortamos: el código ya está actualizado y puede funcionar igual.
        print("  ⚠ No se pudieron reconciliar todas las deps.", file=sys.stderr)
        print(f"  ⚠ Ejecutá: {pip} -m pip install -e {repo}", file=sys.stderr)


def _cli_reinstall() -> bool:
    repo = _repo_dir()
    installer = os.path.join(repo, "install.sh")
    if not os.path.isfile(installer):
        print(f"Error: no se encontró {installer}", file=sys.stderr)
        return False
    print("▶ Reinstalando tplay (corre install.sh del repo)...")
    print("   Esto puede pedir sudo para vlc/ffmpeg/wrapper.")
    try:
        # install.sh v0.19 acepta overrides por variables de entorno
        # (TPLAY_DIR/TPLAY_BIN/TPLAY_RC) y no usa posicionales, así que no
        # hay argumentos que reenviar. La versión anterior usaba un $1 que ya
        # no existe; hoy queda explícito para que no parezca un olvido.
        r = subprocess.run(["bash", installer], cwd=repo)
    except OSError as e:
        print(f"Error: {e}", file=sys.stderr)
        return False
    if r.returncode == 0:
        print("✓ tplay reinstalado correctamente")
        return True
    print("✗ install.sh falló", file=sys.stderr)
    return False


def _confirmar(pregunta: str) -> bool:
    """Confirmación por stdin. Sin TTY = no, siempre.

    El `rm -rf` de los datos tiene que ser explícito. Si no hay terminal no
    hay a quién preguntarle, y asumir "sí" desde un script o un pipe es
    exactamente cómo se pierden favoritos e historial.
    """
    if not sys.stdin.isatty():
        print(
            f"{pregunta}\n  (sin terminal interactiva no se puede confirmar: "
            "se aborta por seguridad)",
            file=sys.stderr,
        )
        return False
    try:
        r = input(f"{pregunta} [s/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    return r in ("s", "si", "sí", "y", "yes")


def _tamano_duro(path: str) -> int:
    """Bytes en disco de un árbol. Para mostrarle al usuario qué va a perder."""
    total = 0
    for dirpath, _dirnames, filenames in os.walk(path):
        for n in filenames:
            try:
                total += os.path.getsize(os.path.join(dirpath, n))
            except OSError:
                pass
    return total


def _cli_uninstall() -> bool:
    repo = _repo_dir()
    from . import paths

    # Se leen los atributos del módulo (y no `from .paths import DATA_DIR`) para
    # que los tests puedan redirigirlos con monkeypatch: importando el valor al
    # principio de la función, quedaría congelado y no se podría testear sin
    # tocar el disco real del usuario.
    #
    # Rutas viejas: el uninstall tiene que alcanzar lo que instalaciones
    # anteriores dejaron, no solo la disposición nueva.
    candidatos_datos = [
        paths.DATA_DIR,
        os.path.join(repo, "data"),
        paths.LEGACY_DATA_DIR,
    ]
    datos = [d for d in dict.fromkeys(candidatos_datos) if os.path.isdir(d)]

    # El comando ya no está en /usr/local/bin (v0.19), pero installations viejas
    # sí lo dejaron ahí, y sin sudo el rm silencioso no avisaba nada.
    comandos = [os.path.expanduser("~/.local/bin/tplay"), "/usr/local/bin/tplay"]
    binarios = [b for b in dict.fromkeys(comandos) if os.path.isfile(b) or os.path.islink(b)]

    print("▶ Desinstalando tplay...")
    print()
    print("  Se va a eliminar:")
    for b in binarios:
        print(f"    · comando   {b}")
    for d in datos:
        archivos = sum(1 for _ in (Path(d).rglob("*"))) if Path(d).exists() else 0
        tam = _tamano_duro(d)
        print(f"    · datos     {d}  ({archivos} entradas, {_fmt_bytes(tam)})")
    print(f"    · repo      {repo}")
    print()

    # El repo y el comando se van siempre; los datos requieren confirmación
    # explícita. Sin TTY no hay a quién preguntarle, así que los datos se
    # conservan: assumption de "sí" desde un script es cómo se pierden
    # favoritos e historial.
    borrar_datos = False
    if datos:
        print(
            "  Los datos contienen tu biblioteca, favoritos, historial y descargas.\n"
            "  No se pueden recuperar una vez borrados."
        )
        borrar_datos = _confirmar("  ¿Borrar los datos también?")
        if not borrar_datos:
            print("  → Se conservan los datos (se puede borrar a mano después).")
    else:
        print("  No hay datos que borrar.")

    for b in binarios:
        print(f"  ↳ Eliminando {b}...")
        try:
            os.remove(b)
        except OSError as e:
            # No puede pasar con el wrapper propio (~/.local/bin), pero con el
            # legacy de /usr/local/bin sí: es de root. El aviso va después de
            # la línea correspondiente, no mezclado con el listado.
            print(f"  ⚠ No se pudo eliminar {b}: {e}")
            print(f"    Si es de root: sudo rm -f {b}")

    if borrar_datos:
        for d in datos:
            print(f"  ↳ Eliminando datos: {d}...")
            shutil.rmtree(d, ignore_errors=True)

    if os.path.isdir(repo):
        print(f"  ↳ Eliminando repositorio: {repo}...")
        shutil.rmtree(repo, ignore_errors=True)

    print("✓ tplay desinstalado")
    return True


def _fmt_bytes(n: int) -> str:
    """Bytes legibles. 1023 B → '1023 B'; 2048 → '2.0 KB'."""
    if n < 1024:
        return f"{n} B"
    valor = float(n)
    for unidad in ("KB", "MB", "GB"):
        valor /= 1024.0
        if valor < 1024.0 or unidad == "GB":
            return f"{valor:.1f} {unidad}"
    return f"{valor:.1f} GB"


def _cli_ctl(args: list[str]) -> int:
    from . import ipc

    quiet = False
    while args and args[0] in ("-q", "--quiet"):
        quiet = True
        args = args[1:]
    if not args or args[0] in ("-h", "--help", "help"):
        print("uso: tplay --ctl [-q] <comando>")
        print(f"comandos: {', '.join(sorted(ipc.COMMANDS))} | vol <0-100>")
        return 0
    cmd = " ".join(args[:2]) if args[0] == "vol" and len(args) > 1 else args[0]
    try:
        resp = ipc.send_command(cmd)
    except (FileNotFoundError, ConnectionRefusedError):
        if not quiet:
            print("tplay no está corriendo", file=sys.stderr)
        return 1
    except OSError as e:
        if not quiet:
            print(f"error IPC: {e}", file=sys.stderr)
        return 1
    if not quiet:
        print(resp)
    return 0 if not resp.startswith("ERR") else 1


def main() -> None:
    # --version y --help van primero y con return: son los dos únicos caminos que
    # no necesitan TTY, y son los que usan el smoke test de install.sh y el e2e.
    # Antes no existían, así que no había forma de verificar la instalación sin
    # levantar la TUI.
    if "--version" in sys.argv or "-V" in sys.argv:
        print(f"tplay {__version__}")
        return
    if "--help" in sys.argv or "-h" in sys.argv:

        print(_USAGE, end="")
        return
    if "--update" in sys.argv:
        if not _cli_update():
            sys.exit(1)
    if "--reinstall" in sys.argv:
        sys.exit(0 if _cli_reinstall() else 1)
    if "--uninstall" in sys.argv:
        sys.exit(0 if _cli_uninstall() else 1)
    if "--ctl" in sys.argv:
        idx = sys.argv.index("--ctl")
        sys.exit(_cli_ctl(sys.argv[idx + 1:]))
    # Guard de arranque (capa 3 del plan). Va después de los flags de ciclo de
    # vida y antes de la TUI: `--ctl` y `--update` tienen que funcionar aunque falte
    # una dep, porque son justamente los comandos con los que se repara.
    #
    # Antes, si faltaba mutagen o yt-dlp, la app moría con ModuleNotFoundError
    # crudo en player/metadata.py:5 (que hace `import mutagen` sin guard) o en
    # player/web.py. Ahora el mensaje dice qué falta y cómo arreglarlo.
    faltan = chequear_deps()
    if faltan:
        print(faltan, file=sys.stderr)
        sys.exit(1)

    # Migración de datos: one-shot, por copia, sin red. Los datos iban a vivir
    # dentro del repo clonado (~/.config/tplay/data); ahora van a
    # ~/.local/share/tplay/data. Si ya hubo migración antes, no se repite.
    msg_migracion = migrar_datos_legacy()
    if msg_migracion:
        print(msg_migracion)

    if not sys.stdout.isatty():
        print("Error: tplay requiere un terminal (TTY)", file=sys.stderr)
        sys.exit(1)
    try:
        curses.wrapper(lambda stdscr: PlayerApp(stdscr).run())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
