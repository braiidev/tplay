"""Chequeo y auto-actualización de yt-dlp al iniciar tplay.

YouTube rompe extractores con frecuencia; un binario viejo produce
errores 403. Este módulo compara la versión instalada contra PyPI
(una vez cada 24h, con cache en disco) y actualiza via pip si hace falta.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from typing import Any

_BIN = "yt-dlp"
_PYPI_URL = "https://pypi.org/pypi/yt-dlp/json"
_CHECK_INTERVAL_SECS = 24 * 3600
_CACHE_FILE = os.path.expanduser("~/.config/tplay/data/ytdlp_check.json")
_UPDATE_TIMEOUT_SECS = 180


def get_installed_version() -> str | None:
    """Retorna la versión del binario yt-dlp en PATH, o None si no está."""
    try:
        r = subprocess.run(
            [_BIN, "--version"], capture_output=True, text=True, timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None
    version = r.stdout.strip()
    if r.returncode != 0 or not version:
        return None
    return version.split("\n")[0].strip()


def _parse_ver(version: str) -> tuple[int, ...]:
    """Convierte '2026.8.19' en (2026, 8, 19) para comparar."""
    parts: list[int] = []
    for chunk in version.strip().split("."):
        digits = ""
        for ch in chunk:
            if ch.isdigit():
                digits += ch
            else:
                break
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def is_outdated(installed: str, latest: str) -> bool:
    try:
        return _parse_ver(latest) > _parse_ver(installed)
    except ValueError:
        return False


def fetch_latest_version(timeout: float = 5.0) -> str | None:
    """Consulta PyPI por la última versión estable publicada."""
    try:
        req = urllib.request.Request(
            _PYPI_URL, headers={"User-Agent": "tplay"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data: Any = json.load(resp)
        version = str(data.get("info", {}).get("version", "")).strip()
        return version or None
    except (OSError, ValueError, KeyError):
        return None


def _read_cache() -> dict[str, Any] | None:
    try:
        with open(_CACHE_FILE) as f:
            data: Any = json.load(f)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _write_cache(latest: str) -> None:
    from .file_utils import atomic_write

    try:
        os.makedirs(os.path.dirname(_CACHE_FILE), exist_ok=True)
        atomic_write(
            _CACHE_FILE,
            json.dumps({"last_check": time.time(), "latest": latest}),
        )
    except OSError:
        pass


def _latest_cached() -> str | None:
    """Retorna la última versión conocida si el cache es fresco (<24h)."""
    cache = _read_cache()
    if not cache:
        return None
    try:
        age = time.time() - float(cache.get("last_check", 0))
    except (TypeError, ValueError):
        return None
    if age >= _CHECK_INTERVAL_SECS:
        return None
    latest = cache.get("latest")
    return latest if isinstance(latest, str) and latest else None


def _pip_managed() -> bool:
    """True si el binario en PATH fue instalado por pip (user o venv).

    Si yt-dlp viene de apt u otro gestor, no intentamos actualizarlo
    automaticamente para no ensuciar el sistema; solo avisamos.
    """
    path = shutil.which(_BIN)
    if not path:
        return False
    real = os.path.realpath(path)
    user_bin = os.path.join(os.path.expanduser("~"), ".local", "bin", "")
    venv_bin = os.path.join(sys.prefix, "bin", "")
    return real.startswith(user_bin) or real.startswith(venv_bin)


def _pip_flags_attempts() -> list[list[str]]:
    base = [sys.executable, "-m", "pip", "install"]
    return [
        base + ["--break-system-packages", "--user", "--upgrade"],
        base + ["--break-system-packages", "--upgrade"],
        base + ["--user", "--upgrade"],
        base + ["--upgrade"],
    ]


def run_update(timeout: float = _UPDATE_TIMEOUT_SECS) -> tuple[bool, str]:
    """Actualiza yt-dlp via pip. Retorna (ok, mensaje_para_usuario)."""
    before = get_installed_version()
    last_err = ""
    for prefix in _pip_flags_attempts():
        try:
            r = subprocess.run(
                prefix + [_BIN], capture_output=True, text=True, timeout=timeout,
            )
        except (subprocess.TimeoutExpired, OSError) as e:
            last_err = str(e)
            continue
        if r.returncode == 0:
            after = get_installed_version()
            if after and (before is None or _parse_ver(after) >= _parse_ver(before)):
                return True, f"yt-dlp actualizado a {after}"
            last_err = r.stderr.strip()[:200]
            continue
        last_err = (r.stderr or r.stdout).strip().split("\n")[-1][:200]
    return False, f"yt-dlp desactualizado — actualizá manualmente ({last_err})"


def check_and_update(enabled: bool = True) -> str:
    """Chequea versión contra PyPI y auto-actualiza si corresponde.

    Returns:
        Mensaje corto para toast ('' = nada que reportar).
    """
    installed = get_installed_version()
    if installed is None:
        return ""
    latest = _latest_cached()
    if latest is None:
        latest = fetch_latest_version()
        if latest is None:
            return ""
        _write_cache(latest)
    if not is_outdated(installed, latest):
        return ""
    if not enabled:
        return f"yt-dlp desactualizado ({installed} → {latest})"
    if not _pip_managed():
        return (
            f"yt-dlp desactualizado ({installed} → {latest}) "
            "— no se puede auto-actualizar esta instalación"
        )
    _, msg = run_update()
    return msg
