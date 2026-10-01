"""Tests de `--version` y `--help`: los dos caminos que no necesitan TTY.

install.sh los usa como smoke test y tests/e2e_install.sh los usa para
verificar que el comando quedó vivo. Antes no existían, así que no había forma
de comprobar la instalación sin levantar la TUI (y `tplay` sin TTY sale con
error a propósito, player/__init__.py).
"""
from __future__ import annotations

import subprocess
import sys

import pytest

import player as cli


class TestVersionYHelp:
    def test_version_imprime_y_no_levanta_tui(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(sys, "argv", ["tplay", "--version"])
        cli.main()  # si cayera a curses.wrapper, sin TTY cortaría con exit
        out = capsys.readouterr().out
        assert out.strip() == f"tplay {cli.__version__}"

    def test_short_version_igual(self, monkeypatch: pytest.MonkeyPatch) -> None:
        r1 = subprocess.run(
            [sys.executable, "-m", "player", "--version"],
            capture_output=True, text=True, check=True,
        )
        r2 = subprocess.run(
            [sys.executable, "-m", "player", "-V"],
            capture_output=True, text=True, check=True,
        )
        assert r1.stdout.strip() == r2.stdout.strip()

    def test_help_lista_los_flags_de_ciclo_de_vida(self) -> None:
        r = subprocess.run(
            [sys.executable, "-m", "player", "--help"],
            capture_output=True, text=True, check=True,
        )
        for flag in ("--update", "--reinstall", "--uninstall", "--ctl",
                     "--version", "--help"):
            assert flag in r.stdout, f"{flag} no aparece en --help"

    def test_help_no_levanta_tui(self) -> None:
        # --help tiene que salir con 0 aunque no haya TTY
        r = subprocess.run(
            [sys.executable, "-m", "player", "--help"],
            capture_output=True, text=True, check=False,
        )
        assert r.returncode == 0

    def test_sin_flags_sin_tty_falla_con_mensaje_claro(self) -> None:
        r = subprocess.run(
            [sys.executable, "-m", "player"],
            capture_output=True, text=True, check=False,
        )
        # Sin deps y sin TTY puede ganar cualquiera de los dos guards; lo que
        # importa es que ninguno de los dos sea un traceback crudo.
        assert r.returncode == 1
        assert "Traceback" not in r.stderr
        assert ("TTY" in r.stderr) or ("Faltan dependencias" in r.stderr)

    def test_version_coincide_con_pyproject(self) -> None:
        # Si divergen, el smoke test de install.sh miente sobre qué se instaló.
        import tomllib
        from pathlib import Path

        root = Path(__file__).resolve().parent.parent
        declared = tomllib.loads((root / "pyproject.toml").read_text())
        assert declared["project"]["version"] == cli.__version__


class TestModuleEntryPoint:
    def test_python_m_player_funciona(self) -> None:
        # README.md documentaba `python3 -m player` y no existía __main__.py
        r = subprocess.run(
            [sys.executable, "-m", "player", "--version"],
            capture_output=True, text=True, check=True,
        )
        assert r.stdout.strip().startswith("tplay ")
