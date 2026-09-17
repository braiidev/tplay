"""Tests del CLI de ciclo de vida (tplay --reinstall)."""
from __future__ import annotations

import os
import subprocess
from typing import Any

import pytest

import player as cli


class TestCliReinstall:
    def test_sin_install_sh_falla(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(os.path, "isfile", lambda path: False)
        assert not cli._cli_reinstall()

    def test_ejecuta_install_sh_del_repo(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        called: list[list[str]] = []

        class _Proc:
            returncode: int = 0

        def fake_run(cmd: list[str], *args: Any, **kwargs: Any) -> _Proc:
            called.append(cmd)
            return _Proc()

        monkeypatch.setattr(subprocess, "run", fake_run)
        assert cli._cli_reinstall()
        assert called == [
            ["bash", os.path.join(cli._repo_dir(), "install.sh")]
        ]

    def test_falla_si_install_sh_devuelve_error(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        class _Proc:
            returncode: int = 1

        monkeypatch.setattr(
            subprocess, "run", lambda cmd, *a, **k: _Proc(),
        )
        assert not cli._cli_reinstall()