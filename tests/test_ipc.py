"""Tests para player.ipc."""
from __future__ import annotations

import os
from typing import Any

import pytest

from player import ipc


class TestSocketPath:
    def test_con_xdg_runtime_dir(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any,
    ) -> None:
        monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
        path = ipc.socket_path()
        assert path == os.path.join(
            str(tmp_path), f"tplay-{os.getuid()}", "ctl.sock",
        )

    def test_fallback_sin_xdg(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("XDG_RUNTIME_DIR", raising=False)
        path = ipc.socket_path()
        assert ".local/state/tplay" in path
        assert path.endswith("ctl.sock")


class TestValidCommand:
    @pytest.mark.parametrize("cmd", [
        "toggle", "play", "pause", "stop", "next", "prev",
        "vol+", "vol-", "status", "vol 30", "vol 0", "vol 100",
    ])
    def test_validos(self, cmd: str) -> None:
        assert ipc.is_valid_command(cmd)

    @pytest.mark.parametrize("cmd", [
        "", "hax", "rm -rf", "vol abc", "vol 1234", "vol ", "vol 30; x",
        "TOGGLE", "togglex", "x" * 65,
    ])
    def test_invalidos(self, cmd: str) -> None:
        assert not ipc.is_valid_command(cmd)


class TestDispatch:
    def test_despacha_valido(self) -> None:
        seen: list[str] = []
        resp = ipc.dispatch_command("toggle", lambda c: seen.append(c) or "OK")
        assert seen == ["toggle"]
        assert resp == "OK"

    def test_rechaza_desconocido(self) -> None:
        seen: list[str] = []
        resp = ipc.dispatch_command("hax", lambda c: seen.append(c) or "OK")
        assert resp.startswith("ERR")
        assert seen == []

    def test_rechaza_vacio_y_oversize(self) -> None:
        assert ipc.dispatch_command("", lambda c: "OK").startswith("ERR")
        assert ipc.dispatch_command("x" * 100, lambda c: "OK").startswith("ERR")

    def test_handler_excepcion_no_propaga(self) -> None:
        def boom(cmd: str) -> str:
            raise RuntimeError("x")

        assert ipc.dispatch_command("toggle", boom).startswith("ERR")


class TestServerRoundTrip:
    def test_roundtrip_real(self, tmp_path: Any) -> None:
        seen: list[str] = []
        sock = str(tmp_path / "ctl.sock")

        def handler(cmd: str) -> str:
            seen.append(cmd)
            return f"OK:{cmd}"

        server = ipc.start_server(sock, handler)
        try:
            assert ipc.send_command("toggle", path=sock) == "OK:toggle"
            assert ipc.send_command("vol 40", path=sock) == "OK:vol 40"
            assert seen == ["toggle", "vol 40"]
            assert os.path.exists(sock)
        finally:
            server.stop()

    def test_stop_unlink_socket(self, tmp_path: Any) -> None:
        sock = str(tmp_path / "ctl.sock")
        server = ipc.start_server(sock, lambda cmd: "OK")
        assert os.path.exists(sock)
        server.stop()
        assert not os.path.exists(sock)

    def test_comando_invalido_responde_err(self, tmp_path: Any) -> None:
        seen: list[str] = []
        sock = str(tmp_path / "ctl.sock")
        server = ipc.start_server(
            sock, lambda cmd: seen.append(cmd) or "OK",
        )
        try:
            resp = ipc.send_command("hax", path=sock)
            assert resp.startswith("ERR")
            assert seen == []
        finally:
            server.stop()

    def test_send_sin_server_lanza(self, tmp_path: Any) -> None:
        with pytest.raises(FileNotFoundError):
            ipc.send_command("toggle", path=str(tmp_path / "nope.sock"))

    def test_stale_socket_se_recicla(self, tmp_path: Any) -> None:
        sock = str(tmp_path / "ctl.sock")
        s1 = ipc.start_server(sock, lambda cmd: "uno")
        s1.stop()
        s2 = ipc.start_server(sock, lambda cmd: "dos")
        try:
            assert ipc.send_command("status", path=sock) == "dos"
        finally:
            s2.stop()
