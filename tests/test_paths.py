"""Tests de player/paths.py: guard de arranque y migración de datos.

La migración es lo importante: los datos de tplay (favoritos, historial,
descargas) viven en disco y el error anterior era que `--uninstall` los borraba
con rm -rf sin preguntar, porque compartían directorio con el repo clonado.

Estos tests usan tmp_path y monkeypatch para no tocar ~/.local/share ni
~/.config de verdad.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

from player import paths


@pytest.fixture
def rutas_temporales(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> dict:
    """Redirige INSTALL_DIR, DATA_DIR y LEGACY_DATA_DIR a un tmp."""
    nuevo = tmp_path / "share" / "tplay"
    legacy = tmp_path / "config" / "tplay" / "data"
    monkeypatch.setattr(paths, "INSTALL_DIR", str(nuevo))
    monkeypatch.setattr(paths, "DATA_DIR", str(nuevo / "data"))
    monkeypatch.setattr(paths, "CONFIG_DIR", str(nuevo / "data"))
    monkeypatch.setattr(paths, "CONFIG_FILE", str(nuevo / "data" / "config.json"))
    monkeypatch.setattr(paths, "LEGACY_DATA_DIR", str(legacy))
    return {"nuevo": nuevo, "data": nuevo / "data", "legacy": legacy}


def _sembrar_legacy(legacy: Path, archivos: dict[str, str]) -> None:
    legacy.mkdir(parents=True, exist_ok=True)
    for nombre, contenido in archivos.items():
        (legacy / nombre).write_text(contenido)


class TestMigracion:
    def test_no_hace_nada_sin_arbol_legacy(
        self, rutas_temporales: dict
    ) -> None:
        assert paths.migrar_datos_legacy() is None

    def test_copia_los_datos_y_anuncia(
        self, rutas_temporales: dict
    ) -> None:
        _sembrar_legacy(
            rutas_temporales["legacy"],
            {
                "config.json": json.dumps({"volume": 42}),
                "favorites.json": json.dumps([{"title": "x"}]),
                "downloads.json": json.dumps([{"id": 1}]),
            },
        )
        msg = paths.migrar_datos_legacy()

        assert msg is not None
        assert "migrad" in msg.lower()
        destino = rutas_temporales["data"]
        assert json.loads((destino / "config.json").read_text())["volume"] == 42
        assert (destino / "favorites.json").exists()
        assert (destino / "downloads.json").exists()

    def test_es_por_copia_el_original_sobrevive(
        self, rutas_temporales: dict
    ) -> None:
        """Lo importante: si algo sale mal, los datos siguen en el viejo."""
        _sembrar_legacy(rutas_temporales["legacy"], {"favorites.json": "[]"})
        paths.migrar_datos_legacy()

        assert (rutas_temporales["legacy"] / "favorites.json").exists(), (
            "la migración NO debe mover los datos: los borra si algo falla después"
        )

    def test_no_pisa_lo_que_ya_esta_en_el_destino(
        self, rutas_temporales: dict
    ) -> None:
        _sembrar_legacy(rutas_temporales["legacy"], {"config.json": '{"nuevo":true}'})
        destino = rutas_temporales["data"]
        destino.mkdir(parents=True, exist_ok=True)
        (destino / "config.json").write_text('{"ya_migrado":true}')

        paths.migrar_datos_legacy()

        assert json.loads((destino / "config.json").read_text()) == {"ya_migrado": True}

    def test_es_idempotente_no_repite_ni_avisa(
        self, rutas_temporales: dict
    ) -> None:
        _sembrar_legacy(rutas_temporales["legacy"], {"history.json": "[]"})
        assert paths.migrar_datos_legacy() is not None
        # segunda vez: ya hay archivos en el destino, no se toca ni se avisa
        assert paths.migrar_datos_legacy() is None

    def test_ignora_escrituras_atomicas_en_curso(
        self, rutas_temporales: dict
    ) -> None:
        """atomic_write() usa archivo.tmp + replace; un .tmp no es un dato."""
        _sembrar_legacy(
            rutas_temporales["legacy"],
            {"state.json": "{}", "state.json.tmp": "basura a medias"},
        )
        paths.migrar_datos_legacy()

        assert (rutas_temporales["data"] / "state.json").exists()
        assert not (rutas_temporales["data"] / "state.json.tmp").exists()

    def test_crea_el_arbol_intermedio(
        self, rutas_temporales: dict
    ) -> None:
        _sembrar_legacy(rutas_temporales["legacy"], {"radios.json": "[]"})
        destino = rutas_temporales["data"]
        assert not destino.exists()

        paths.migrar_datos_legacy()

        assert destino.is_dir()

    def test_copia_subdirectorios(
        self, rutas_temporales: dict
    ) -> None:
        legacy = rutas_temporales["legacy"]
        legacy.mkdir(parents=True, exist_ok=True)
        (legacy / "tmp").mkdir()
        (legacy / "tmp" / "parcial.mp3").write_bytes(b"x" * 10)

        paths.migrar_datos_legacy()

        assert (rutas_temporales["data"] / "tmp" / "parcial.mp3").exists()


class TestGuardDeps:
    def test_sin_faltantes_no_devuelve_mensaje(self) -> None:
        # En el venv de desarrollo están las 3; si no, el propio test lo dice
        # claro al fallar.
        try:
            import mutagen  # noqa: F401
            import vlc  # noqa: F401
            import yt_dlp  # noqa: F401
        except ImportError:
            pytest.skip("deps no instaladas en este intérprete")
        if not os.path.exists(os.path.join(sys.prefix, "bin", "yt-dlp")):
            pytest.skip("yt-dlp no está en el PATH de este intérprete")

        assert paths.chequear_deps() is None

    def test_nombra_las_faltantes_y_el_comando(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Con una dep rota tiene que decir QUÉ falta y CÓMO arreglarlo."""
        real_import = __builtins__["__import__"] if isinstance(
            __builtins__, dict
        ) else __builtins__.__import__

        def import_falso(nombre: str, *a: object, **k: object) -> object:
            if nombre in ("vlc", "mutagen", "yt_dlp"):
                raise ImportError(f"No module named {nombre!r}")
            return real_import(nombre, *a, **k)

        monkeypatch.setitem(
            __builtins__ if isinstance(__builtins__, dict) else __builtins__.__dict__,
            "__import__",
            import_falso,
        )
        monkeypatch.setattr(
            os.path, "exists", lambda path: False,
        )

        msg = paths.chequear_deps()

        assert msg is not None
        for dep in ("python-vlc", "mutagen", "yt-dlp"):
            assert dep in msg
        assert "install.sh" in msg, "tiene que decir cómo repararlo"
        assert "Traceback" not in msg

    def test_detecta_el_binario_de_yt_dlp_faltante(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """yt-dlp se llama como binario del PATH: importarlo bien no alcanza."""
        real_import = __builtins__["__import__"] if isinstance(
            __builtins__, dict
        ) else __builtins__.__import__

        def import_falso(nombre: str, *a: object, **k: object) -> object:
            if nombre == "yt_dlp":
                raise ImportError("No module named 'yt_dlp'")
            return real_import(nombre, *a, **k)

        monkeypatch.setitem(
            __builtins__ if isinstance(__builtins__, dict) else __builtins__.__dict__,
            "__import__",
            import_falso,
        )
        monkeypatch.setattr(os.path, "exists", lambda path: False)

        msg = paths.chequear_deps()

        assert msg is not None
        assert "yt-dlp (binario)" in msg


class TestRutas:
    def test_datos_no_viven_dentro_del_codigo(self) -> None:
        """La razón del cambio: antes CONFIG_DIR estaba DENTRO del repo."""
        assert os.path.realpath(paths.INSTALL_DIR) != os.path.realpath(
            paths.LEGACY_DATA_DIR
        )
        assert paths.DATA_DIR.startswith(paths.INSTALL_DIR)
        assert not paths.DATA_DIR.startswith(paths.LEGACY_DATA_DIR)

    def test_config_dir_es_alias_de_data_dir(self) -> None:
        assert paths.CONFIG_DIR == paths.DATA_DIR
