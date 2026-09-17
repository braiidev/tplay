"""Tests de clasificación de errores de descarga (player.web._classify_error)."""
from __future__ import annotations

import pytest

from player.web import _classify_error


@pytest.mark.parametrize("msg", [
    "ERROR: ffmpeg not found. Please install or provide the path using --ffmpeg-location",
    "ERROR: Postprocessing: ffmpeg not found",
    "ERROR: Postprocessing: ffmpeg exited with code 1",
])
def test_clasifica_ffmpeg(msg: str) -> None:
    assert "ffmpeg" in _classify_error(msg)


def test_error_generico_pasa_mensaje() -> None:
    assert _classify_error("algo raro pasó") == "Error: algo raro pasó"


def test_red_mantiene_patron() -> None:
    assert _classify_error("timeout reading from stream") == \
        "Error de conexión — verificá tu red"