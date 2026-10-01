import curses
import os
import subprocess
import sys
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
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _cli_update() -> bool:
    repo = _repo_dir()
    git_dir = os.path.join(repo, ".git")
    if not os.path.isdir(git_dir):
        print("Error: no es un repositorio git, no se puede actualizar", file=sys.stderr)
        return False
    try:
        req_path = os.path.join(repo, "requirements.txt")
        old_reqs: set[str] = set()
        if os.path.isfile(req_path):
            with open(req_path) as f:
                old_reqs = {l.strip() for l in f if l.strip() and not l.startswith("#")}

        subprocess.run(["git", "fetch", "origin"], cwd=repo, capture_output=True, timeout=10)
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD..origin/main"],
            cwd=repo, capture_output=True, text=True, timeout=10,
        )
        behind = int(result.stdout.strip() or 0)
        if behind == 0:
            print("✓ tplay ya está actualizado")
            _install_new_deps(repo, req_path, old_reqs)
            return True
        print(f"  ↳ {behind} commits detrás, actualizando...")
        pull = subprocess.run(["git", "pull", "--ff-only"], cwd=repo,
                              capture_output=True, text=True, timeout=30)
        if pull.returncode == 0:
            print("✓ tplay actualizado correctamente")
            _install_new_deps(repo, req_path, old_reqs)
            return True
        reset = subprocess.run(["git", "reset", "--hard", "origin/main"],
                                cwd=repo, capture_output=True, text=True, timeout=10)
        if reset.returncode == 0:
            print("✓ tplay actualizado correctamente (historial corregido)")
            _install_new_deps(repo, req_path, old_reqs)
            return True
        print(f"Error: {pull.stderr.strip()}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False


def _install_new_deps(repo: str, req_path: str, old_reqs: set[str]) -> None:
    if not os.path.isfile(req_path):
        return
    try:
        with open(req_path) as f:
            new_reqs = {l.strip() for l in f if l.strip() and not l.startswith("#")}
    except OSError:
        return
    added = new_reqs - old_reqs
    if not added:
        return
    pkgs = [p.split(">=")[0].split("==")[0] for p in added]
    print(f"  ↳ Instalando dependencias nuevas: {', '.join(pkgs)}")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--user"] + pkgs,
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode == 0:
            print(f"✓ Dependencias instaladas: {', '.join(pkgs)}")
        else:
            print(f"  ⚠ No se pudo instalar automáticamente.")
            print(f"  ⚠ Ejecutá manualmente: pip install --break-system-packages {' '.join(pkgs)}")
    except Exception:
        print(f"  ⚠ Ejecutá manualmente: pip install --break-system-packages {' '.join(pkgs)}")


def _cli_reinstall() -> bool:
    repo = _repo_dir()
    installer = os.path.join(repo, "install.sh")
    if not os.path.isfile(installer):
        print(f"Error: no se encontró {installer}", file=sys.stderr)
        return False
    print("▶ Reinstalando tplay (corre install.sh del repo)...")
    print("   Esto puede pedir sudo para vlc/ffmpeg/wrapper.")
    try:
        r = subprocess.run(["bash", installer], cwd=repo)
    except OSError as e:
        print(f"Error: {e}", file=sys.stderr)
        return False
    if r.returncode == 0:
        print("✓ tplay reinstalado correctamente")
        return True
    print("✗ install.sh falló", file=sys.stderr)
    return False


def _cli_uninstall() -> bool:
    repo = _repo_dir()
    data = os.path.join(repo, "data")
    bin_path = "/usr/local/bin/tplay"

    print("▶ Desinstalando tplay...")

    if os.path.isfile(bin_path):
        print(f"  ↳ Eliminando {bin_path}...")
        subprocess.run(["sudo", "rm", "-f", bin_path], check=False)

    if os.path.isdir(data):
        print(f"  ↳ Eliminando datos: {data}...")
        subprocess.run(["rm", "-rf", data], check=False)

    if os.path.isdir(repo):
        print(f"  ↳ Eliminando repositorio: {repo}...")
        subprocess.run(["rm", "-rf", repo], check=False)

    print("✓ tplay desinstalado")
    return True


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
