"""Tests para player.ytdlp_update."""
from __future__ import annotations

import json
import time
from typing import Any

import pytest

from player import ytdlp_update as yu


class TestParseVer:
    def test_orden_basico(self) -> None:
        assert yu._parse_ver("2026.8.19") == (2026, 8, 19)

    def test_comparacion(self) -> None:
        assert yu.is_outdated("2026.7.4", "2026.8.19")
        assert yu.is_outdated("2025.12.8", "2026.1.31")
        assert not yu.is_outdated("2026.8.19", "2026.8.19")
        assert not yu.is_outdated("2026.8.20", "2026.8.19")

    def test_sufijos_no_numericos(self) -> None:
        assert yu.is_outdated("2026.7.4", "2026.8.19.post1")


class TestCheckAndUpdate:
    @pytest.fixture(autouse=True)
    def _cache_tmp(self, tmp_path: Any, monkeypatch: pytest.MonkeyPatch) -> None:
        self.cache_file = tmp_path / "ytdlp_check.json"
        monkeypatch.setattr(yu, "_CACHE_FILE", str(self.cache_file))

    def _write_cache(self, latest: str, age_secs: float = 0.0) -> None:
        self.cache_file.write_text(
            json.dumps({"last_check": time.time() - age_secs, "latest": latest})
        )

    def test_al_dia_retorna_vacio(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(yu, "get_installed_version", lambda: "2026.8.19")
        monkeypatch.setattr(yu, "fetch_latest_version", lambda timeout=5.0: "2026.8.19")
        assert yu.check_and_update(enabled=True) == ""

    def test_sin_binario_retorna_vacio(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(yu, "get_installed_version", lambda: None)
        called = []
        monkeypatch.setattr(
            yu, "fetch_latest_version", lambda timeout=5.0: called.append(1),
        )
        assert yu.check_and_update(enabled=True) == ""
        assert called == []

    def test_desactualizado_actualiza(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(yu, "get_installed_version", lambda: "2026.7.4")
        monkeypatch.setattr(yu, "fetch_latest_version", lambda timeout=5.0: "2026.8.19")
        monkeypatch.setattr(yu, "_pip_managed", lambda: True)
        monkeypatch.setattr(
            yu, "run_update", lambda: (True, "yt-dlp actualizado a 2026.8.19"),
        )
        msg = yu.check_and_update(enabled=True)
        assert msg == "yt-dlp actualizado a 2026.8.19"
        data = json.loads(self.cache_file.read_text())
        assert data["latest"] == "2026.8.19"

    def test_desactualizado_disabled_solo_avisa(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(yu, "get_installed_version", lambda: "2026.7.4")
        monkeypatch.setattr(yu, "fetch_latest_version", lambda timeout=5.0: "2026.8.19")
        ran = []
        monkeypatch.setattr(yu, "run_update", lambda: ran.append(1))
        msg = yu.check_and_update(enabled=False)
        assert "2026.7.4" in msg and "2026.8.19" in msg
        assert ran == []

    def test_no_pip_managed_no_actualiza(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(yu, "get_installed_version", lambda: "2026.7.4")
        monkeypatch.setattr(yu, "fetch_latest_version", lambda timeout=5.0: "2026.8.19")
        monkeypatch.setattr(yu, "_pip_managed", lambda: False)
        ran = []
        monkeypatch.setattr(yu, "run_update", lambda: ran.append(1))
        msg = yu.check_and_update(enabled=True)
        assert "auto-actualizar" in msg
        assert ran == []

    def test_cache_fresco_evita_red(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        self._write_cache("2026.8.19")
        called = []
        monkeypatch.setattr(yu, "get_installed_version", lambda: "2026.8.19")

        def _fail(timeout: float = 5.0) -> None:
            called.append(1)

        monkeypatch.setattr(yu, "fetch_latest_version", _fail)
        assert yu.check_and_update(enabled=True) == ""
        assert called == []

    def test_cache_stale_consulta_red(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        self._write_cache("2026.7.1", age_secs=yu._CHECK_INTERVAL_SECS + 10)
        monkeypatch.setattr(yu, "get_installed_version", lambda: "2026.8.19")
        monkeypatch.setattr(yu, "fetch_latest_version", lambda timeout=5.0: "2026.8.19")
        assert yu.check_and_update(enabled=True) == ""
        data = json.loads(self.cache_file.read_text())
        assert data["latest"] == "2026.8.19"

    def test_fallo_red_retorna_vacio(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(yu, "get_installed_version", lambda: "2026.7.4")
        monkeypatch.setattr(yu, "fetch_latest_version", lambda timeout=5.0: None)
        assert yu.check_and_update(enabled=True) == ""


class TestPipFlags:
    """El auto-actualizador NO puede escribir en el Python del sistema.

    Antes `_pip_flags_attempts()` devolvía cuatro variantes que empezaban por
    `pip install --break-system-packages --user` y degradaban hasta `--upgrade`
    pelado: era la misma cascada que v0.19 eliminó de install.sh, y quedaba
    viva acá. Un test viejo incluso la exigía como comportamiento esperado
    (`return 2 if "--break-system-packages" in cmd`), o sea que el bug estaba
    codificado en la suite.
    """

    def _flags(self, monkeypatch: pytest.MonkeyPatch, en_venv: bool) -> list[list[str]]:
        if en_venv:
            monkeypatch.setattr(yu.sys, "prefix", "/venv")
            monkeypatch.setattr(yu.sys, "base_prefix", "/usr")
        else:
            monkeypatch.setattr(yu.sys, "prefix", "/usr")
            monkeypatch.setattr(yu.sys, "base_prefix", "/usr")
        return yu._pip_flags_attempts()

    def test_dentro_del_venv_un_solo_intento(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Con venv, `pip install --upgrade` pelado ya instala en el lugar
        correcto: sys.executable es el intérprete del venv."""
        flags = self._flags(monkeypatch, en_venv=True)

        assert len(flags) == 1
        assert flags[0][-1] == "--upgrade"

    def test_fuera_del_venv_no_pisa_el_python_del_sistema(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        flags = self._flags(monkeypatch, en_venv=False)

        assert flags, "tiene que haber algún camino de actualización"
        for cmd in flags:
            assert "--break-system-packages" not in cmd, (
                f"nunca --break-system-packages: escribe en el Python del SO → {cmd}"
            )

    def test_fuera_del_venv_prefiere_user(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Instalación vieja (user-site): primero --user, que es lo que va."""
        flags = self._flags(monkeypatch, en_venv=False)

        assert "--user" in flags[0]

    def test_nunca_devuelve_break_system_packages(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Barrido: ninguna combinación de venv/user produce el flag prohibido."""
        for en_venv in (True, False):
            for cmd in self._flags(monkeypatch, en_venv=en_venv):
                assert "--break-system-packages" not in cmd


class TestRunUpdate:
    def test_actualiza_con_el_primer_intento_valido(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cmds: list[list[str]] = []

        class FakeCompleted:
            def __init__(self, code: int) -> None:
                self.returncode = code
                self.stdout = "Successfully installed"
                self.stderr = ""

        def fake_run(cmd: list[str], **kw: Any) -> FakeCompleted:
            cmds.append(cmd)
            return FakeCompleted(0)

        monkeypatch.setattr(yu.subprocess, "run", fake_run)
        monkeypatch.setattr(yu, "get_installed_version", lambda: "2026.8.19")
        monkeypatch.setattr(yu.sys, "prefix", "/venv")
        monkeypatch.setattr(yu.sys, "base_prefix", "/usr")

        ok, msg = yu.run_update()

        assert ok
        assert "2026.8.19" in msg
        assert len(cmds) == 1, "con venv alcanza un intento; no hay cascada"

    def test_no_escribe_en_el_python_del_sistema(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """aunque pip falle en todos los intentos, ninguno lleva el flag prohibido."""
        cmds: list[list[str]] = []

        class FakeCompleted:
            def __init__(self, code: int) -> None:
                self.returncode = code
                self.stdout = ""
                self.stderr = "boom"

        def fake_run(cmd: list[str], **kw: Any) -> FakeCompleted:
            cmds.append(cmd)
            return FakeCompleted(1)

        monkeypatch.setattr(yu.subprocess, "run", fake_run)
        monkeypatch.setattr(yu, "get_installed_version", lambda: "2026.8.19")
        monkeypatch.setattr(yu.sys, "prefix", "/usr")
        monkeypatch.setattr(yu.sys, "base_prefix", "/usr")

        ok, _msg = yu.run_update()

        assert ok is False
        assert cmds
        for cmd in cmds:
            assert "--break-system-packages" not in cmd
