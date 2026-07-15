import curses
import os
import subprocess
import sys
from typing import Any

from .app import PlayerApp


def _cli_update() -> bool:
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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


def _cli_uninstall() -> bool:
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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


def main() -> None:
    if "--update" in sys.argv:
        if not _cli_update():
            sys.exit(1)
    if "--uninstall" in sys.argv:
        sys.exit(0 if _cli_uninstall() else 1)
    try:
        curses.wrapper(lambda stdscr: PlayerApp(stdscr).run())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
