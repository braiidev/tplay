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


class TestRunUpdateFallbacks:
    def test_flag_rechazado_cae_al_siguiente(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        cmds: list[list[str]] = []

        class FakeCompleted:
            def __init__(self, code: int) -> None:
                self.returncode = code
                self.stdout = ""
                self.stderr = "error: unrecognized arguments" if code else ""

        def fake_run(cmd: list[str], **kw: Any) -> FakeCompleted:
            cmds.append(cmd)
            return FakeCompleted(2 if "--break-system-packages" in cmd else 0)

        monkeypatch.setattr(yu.subprocess, "run", fake_run)
        monkeypatch.setattr(yu, "get_installed_version", lambda: "2026.8.19")
        ok, msg = yu.run_update()
        assert ok
        assert "2026.8.19" in msg
        assert len(cmds) >= 2
