"""Tests de selección de backend de audio (player.audio.detect_aout)."""
from __future__ import annotations

import os
from typing import Any

import pytest

from player.audio import detect_aout


class TestDetectAout:
    def test_sin_xdg_runtime_dir_devuelve_none(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("XDG_RUNTIME_DIR", raising=False)
        assert detect_aout() is None

    def test_xdg_vacio_sin_sockets_devuelve_none(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any,
    ) -> None:
        monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
        assert detect_aout() is None

    def test_socket_pipewire_devuelve_pulse(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any,
    ) -> None:
        monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
        os.makedirs(tmp_path / "pipewire-0")
        assert detect_aout() == "pulse"

    def test_socket_pulse_native_devuelve_pulse(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any,
    ) -> None:
        monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
        os.makedirs(tmp_path / "pulse" / "native")
        assert detect_aout() == "pulse"

    def test_solo_otros_archivos_devuelve_none(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any,
    ) -> None:
        monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
        os.makedirs(tmp_path / "wayland-1")
        assert detect_aout() is None