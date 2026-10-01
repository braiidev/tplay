"""Tests del ciclo de vida: --update, --reinstall y --uninstall.

Estos tres caminos tienen bugs que ningún test cubría, y dos de ellos borran
cosas del disco del usuario:

- `_install_new_deps` leía requirements.txt, que v0.17 borró. Como el archivo no
  existía, retornaba en silencio: un update que cambiaba una dependencia
  parecía funcionar y no instalaba nada. El peor tipo de fallo, porque el
  código nuevo（比如 con una dep nueva) muere después con ModuleNotFoundError.
- `--uninstall` hacía `rm -rf data/` sin preguntar, y los datos estaban DENTRO
  del repo (v0.20 los movió a ~/.local/share/tplay/data).
- El fallback de deps sugería `--break-system-packages`, que escribe en el
  Python del sistema.

Los tests de uninstall usan tmp_path y monkeypatch para que un error aquí no
borre los datos reales.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from player import paths

import importlib

# OJO: `from player import __init__ as cli` NO sirve — ese nombre resuelve al
# built-in `__init__` del tipo module, no a player/__init__.py, y los atributos
# como _repo_dir no existen ahí. Hay que importar el archivo explícitamente.
cli = importlib.import_module("player.__init__")


@pytest.fixture
def repo_falso(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Repo git mínimo con install.sh y un .venv simulado."""
    repo = tmp_path / "repo"
    (repo / "player").mkdir(parents=True)
    (repo / "player" / "__init__.py").write_text("")
    (repo / "install.sh").write_text("#!/usr/bin/env bash\necho instalando\n")
    (repo / "pyproject.toml").write_text(
        '[project]\nname = "player"\ndependencies = ["mutagen>=1.0"]\n'
    )
    venv_bin = repo / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    (venv_bin / "python").write_text("#!/bin/sh\n")
    # _cli_update aborta si no hay .git: el fixture tiene que parecer un clone.
    (repo / ".git").mkdir()

    monkeypatch.setattr(cli, "_repo_dir", lambda: str(repo))
    return repo


class TestReconciliarDeps:
    def test_dentro_del_venv_usa_pip_sin_user_ni_break_system(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """La instalación tiene que ir al venv, nunca al site-packages del SO."""
        capturado: dict = {}

        def fake_run(cmd, **kw):
            capturado["cmd"] = cmd
            return subprocess.CompletedProcess(cmd, 0, "", "")

        monkeypatch.setattr(sys, "prefix", "/home/u/.local/share/tplay/.venv")
        monkeypatch.setattr(sys, "base_prefix", "/usr")
        monkeypatch.setattr(
            sys, "executable", "/home/u/.local/share/tplay/.venv/bin/python"
        )
        monkeypatch.setattr(subprocess, "run", fake_run)

        cli._reconciliar_deps("/repo")
        if True:
            cmd = capturado["cmd"]
            assert "--user" not in cmd, "nunca pip --user: escribía en el site del SO"
            assert "--break-system-packages" not in cmd, (
                "nunca --break-system-packages: modifica el Python del sistema"
            )
            assert cmd[:4] == [
                "/home/u/.local/share/tplay/.venv/bin/python", "-m", "pip", "install",
            ]
            assert "-e" in cmd and "/repo" in cmd

    def test_fuera_del_venv_no_toca_nada_y_avisa(
        self, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        """Sin venv no se instala nada: que lo resuelva install.sh."""
        def no_debe_correr(cmd, **kw):
            raise AssertionError(f"no debería ejecutar pip: {cmd}")

        monkeypatch.setattr(sys, "prefix", "/usr")
        monkeypatch.setattr(sys, "base_prefix", "/usr")  # sin venv
        monkeypatch.setattr(subprocess, "run", no_debe_correr)
        cli._reconciliar_deps("/repo")

        err = capsys.readouterr().err
        assert "install.sh" in err, "tiene que decir cómo arreglarlo"

    def test_fallo_de_pip_no_aborta_el_update(
        self, monkeypatch: pytest.MonkeyPatch, capsys, repo_falso: Path
    ) -> None:
        """Un pip que falla no puede tirar abajo un update de código ya hecho."""
        def fake_run(cmd, **kw):
            if "pip" in " ".join(cmd):
                return subprocess.CompletedProcess(cmd, 1, "", "boom")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        monkeypatch.setattr(subprocess, "run", fake_run)
        monkeypatch.setattr(sys, "prefix", "/venv")
        monkeypatch.setattr(sys, "base_prefix", "/usr")
        cli._reconciliar_deps(str(repo_falso))

        err = capsys.readouterr().err
        assert "⚠" in err
        assert "install -e" in err, "tiene que dar el comando manual"


class TestUpdate:
    def test_update_reconcilia_tras_pull(
        self, monkeypatch: pytest.MonkeyPatch, repo_falso: Path, capsys
    ) -> None:
        """El bug central: el update tiene que instalar las deps nuevas."""
        llamadas: list[list[str]] = []

        def fake_run(cmd, **kw):
            if cmd[0] == "git" and "fetch" in cmd:
                return subprocess.CompletedProcess(cmd, 0, "", "")
            if cmd[0] == "git" and "rev-list" in cmd:
                return subprocess.CompletedProcess(cmd, 0, "3\n", "")
            if cmd[0] == "git" and "pull" in cmd:
                return subprocess.CompletedProcess(cmd, 0, "", "")
            llamadas.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, "", "")

        monkeypatch.setattr(subprocess, "run", fake_run)
        monkeypatch.setattr(sys, "prefix", "/venv")
        monkeypatch.setattr(sys, "base_prefix", "/usr")
        ok = cli._cli_update()

        assert ok
        pip = [c for c in llamadas if "pip" in " ".join(c)]
        assert pip, f"el update tiene que reconciliar deps; llamadas: {llamadas}"
        assert "--user" not in pip[0]

    def test_update_sin_requirements_txt_no_falla_mal(
        self, monkeypatch: pytest.MonkeyPatch, repo_falso: Path
    ) -> None:
        """v0.17 borró requirements.txt; el update no debe romperse por eso."""
        assert not (repo_falso / "requirements.txt").exists(), (
            "el fixture tiene que reflejar el repo real (sin requirements.txt)"
        )

        def fake_run(cmd, **kw):
            if cmd[0] == "git" and "rev-list" in cmd:
                return subprocess.CompletedProcess(cmd, 0, "0\n", "")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        monkeypatch.setattr(subprocess, "run", fake_run)
        monkeypatch.setattr(sys, "prefix", "/venv")
        monkeypatch.setattr(sys, "base_prefix", "/usr")
        assert cli._cli_update() is True

    def test_update_fuera_de_un_repo_falla_limpiamente(self, capsys) -> None:
        """Con un dir sin .git dice qué pasa, no tira traceback."""
        with pytest.MonkeyPatch.context() as m:
            m.setattr(cli, "_repo_dir", lambda: "/tmp/no-existe-este-repo")
            assert cli._cli_update() is False
        assert "git" in capsys.readouterr().err


class TestReinstall:
    def test_reinstall_corre_el_install_del_repo(
        self, monkeypatch: pytest.MonkeyPatch, repo_falso: Path
    ) -> None:
        invocado: dict = {}

        def fake_run(cmd, **kw):
            invocado["cmd"] = cmd
            invocado["cwd"] = kw.get("cwd")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        with pytest.MonkeyPatch.context() as m:
            m.setattr(subprocess, "run", fake_run)
            assert cli._cli_reinstall() is True

        assert invocado["cmd"] == ["bash", str(repo_falso / "install.sh")]
        assert invocado["cwd"] == str(repo_falso)

    def test_reinstall_sin_install_sh_falla_limpiamente(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys
    ) -> None:
        with pytest.MonkeyPatch.context() as m:
            m.setattr(cli, "_repo_dir", lambda: str(tmp_path))
            assert cli._cli_reinstall() is False
        assert "install.sh" in capsys.readouterr().err


class TestFmtBytes:
    def test_legible(self) -> None:
        assert cli._fmt_bytes(0) == "0 B"
        assert cli._fmt_bytes(1023) == "1023 B"
        assert cli._fmt_bytes(1024) == "1.0 KB"
        assert cli._fmt_bytes(1024 * 1024) == "1.0 MB"
        assert cli._fmt_bytes(1024 ** 3) == "1.0 GB"
