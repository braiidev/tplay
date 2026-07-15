from __future__ import annotations

import os
import json
import copy
import curses
from typing import Any

CONFIG_DIR: str = os.path.expanduser("~/.config/tplay/data")
CONFIG_FILE: str = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG: dict[str, Any] = {
    "music_dir": os.path.expanduser("~/Music"),
    "volume": 50,
    "theme": "clasico",
    "custom_colors": {"marco": "Cian", "texto": "Blanco", "destacar": "Amarillo", "nav": "Verde", "overlay": "Magenta"},
    "sleep_timer_minutes": 30,
    "keybinding_mode": "default",
    "keybindings": {},
    "ui_navbar": True,
    "ui_minimal": False,
    "eq_enabled": False,
    "eq_preset": "Flat",
    "eq_bands": [0.0] * 10,
    "eq_preamp": 12.0,
    "custom_bands": [0.0] * 10,
    "show_listen_hints": True,
    "online_max_results": 5,
    "online_audio_quality": "128",
    "online_search_history": [],
    "online_platform": "YouTube",
    "online_download_format": "audio",
    "online_download_quality": "480p",
    "online_download_stream": "fastest",
    "online_download_max": 3,
    "online_cookies": "none",
}

EQ_PRESETS: dict[str, list[float]] = {
    "Flat": [0.0] * 10,
    "Classical": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -4.4, -4.4, -4.4, -6.0],
    "Club": [0.0, 0.0, 4.8, 3.4, 3.4, 3.4, 1.8, 0.0, 0.0, 0.0],
    "Dance": [6.2, 4.4, 1.2, 0.0, 0.0, -3.6, -4.4, -4.4, 0.0, 0.0],
    "Full Bass": [5.0, 5.0, 5.0, 3.0, 0.8, -2.4, -4.8, -6.4, -6.8, -6.8],
    "Headphones": [2.8, 6.8, 3.2, -2.0, -1.2, 1.0, 3.2, 6.4, 8.0, 9.6],
    "Large Hall": [6.4, 6.4, 3.6, 3.6, 0.0, -3.0, -3.0, -3.0, 0.0, 0.0],
    "Live": [-3.0, 0.0, 2.4, 3.4, 3.6, 3.6, 2.4, 1.8, 1.8, 1.4],
    "Party": [4.8, 4.8, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 4.8, 4.8],
    "Pop": [-1.0, 2.8, 4.4, 4.8, 3.2, 0.0, -1.2, -1.2, -1.0, -1.0],
    "Reggae": [0.0, 0.0, 0.0, -3.6, 0.0, 4.0, 4.0, 0.0, 0.0, 0.0],
    "Rock": [4.8, 2.8, -3.6, -4.8, -2.0, 2.4, 5.4, 6.8, 6.8, 6.8],
    "Ska": [-1.2, -2.8, -2.4, 0.0, 2.4, 3.4, 5.4, 5.8, 6.8, 5.8],
    "Soft": [2.8, 0.8, 0.0, -1.6, 0.0, 2.4, 5.4, 6.4, 6.8, 7.2],
    "Soft Rock": [2.4, 2.4, 1.0, 0.0, -2.4, -3.6, -2.0, 0.0, 1.4, 5.4],
    "Techno": [4.8, 3.6, 0.0, -3.6, -3.0, 0.0, 4.8, 6.4, 6.4, 5.8],
    "Custom": [0.0] * 10,
}

EQ_PRESET_NAMES: list[str] = list(EQ_PRESETS.keys())

COLORS: dict[str, int] = {
    "Negro": curses.COLOR_BLACK, "Rojo": curses.COLOR_RED,
    "Verde": curses.COLOR_GREEN, "Amarillo": curses.COLOR_YELLOW,
    "Azul": curses.COLOR_BLUE, "Magenta": curses.COLOR_MAGENTA,
    "Cian": curses.COLOR_CYAN, "Blanco": curses.COLOR_WHITE,
}

THEMES: dict[str, dict[str, int]] = {
    "clasico": {"marco": curses.COLOR_CYAN, "texto": curses.COLOR_WHITE,
                "destacar": curses.COLOR_YELLOW, "nav": curses.COLOR_GREEN, "overlay": curses.COLOR_MAGENTA},
    "mono": {"marco": curses.COLOR_WHITE, "texto": curses.COLOR_WHITE,
             "destacar": curses.COLOR_WHITE, "nav": curses.COLOR_WHITE, "overlay": curses.COLOR_WHITE,
             "mono_bold": True},
    "calido": {"marco": curses.COLOR_YELLOW, "texto": curses.COLOR_WHITE,
               "destacar": curses.COLOR_RED, "nav": curses.COLOR_GREEN, "overlay": curses.COLOR_YELLOW},
    "contraste": {"marco": curses.COLOR_MAGENTA, "texto": curses.COLOR_WHITE,
                  "destacar": curses.COLOR_GREEN, "nav": curses.COLOR_MAGENTA, "overlay": curses.COLOR_GREEN},
    "flatline": {"marco": curses.COLOR_CYAN, "texto": curses.COLOR_WHITE,
                 "destacar": curses.COLOR_RED, "nav": curses.COLOR_CYAN, "overlay": curses.COLOR_RED},
    "custom": {"marco": curses.COLOR_CYAN, "texto": curses.COLOR_WHITE,
               "destacar": curses.COLOR_YELLOW, "nav": curses.COLOR_GREEN, "overlay": curses.COLOR_MAGENTA},
}
THEME_NAMES: list[str] = list(THEMES.keys())

PAIR_MARCO: int = 1
PAIR_TEXTO: int = 2
PAIR_DESTACAR: int = 3
PAIR_NAV: int = 4
PAIR_OVERLAY: int = 5

MONO_BOLD: bool = False


_cache: dict[str, Any] | None = None
_cache_mtime: float = 0.0


def load() -> dict[str, Any]:
    global _cache, _cache_mtime
    try:
        mtime = os.path.getmtime(CONFIG_FILE)
    except OSError:
        mtime = 0.0
    if _cache is not None and mtime == _cache_mtime:
        return _cache
    try:
        with open(CONFIG_FILE) as f:
            cfg: dict[str, Any] = json.load(f)
            for k in DEFAULT_CONFIG:
                cfg.setdefault(k, DEFAULT_CONFIG[k])
            _cache = cfg
            _cache_mtime = mtime
            return cfg
    except (FileNotFoundError, json.JSONDecodeError):
        fallback: dict[str, Any] = copy.deepcopy(DEFAULT_CONFIG)
        _cache = fallback
        _cache_mtime = 0.0
        return fallback


def invalidate_cache() -> None:
    global _cache, _cache_mtime
    _cache = None
    _cache_mtime = 0.0


def save(cfg: dict[str, Any]) -> None:
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        from .file_utils import atomic_write
        atomic_write(CONFIG_FILE, json.dumps(cfg, indent=2))
        invalidate_cache()
    except OSError:
        pass


def apply_theme(config: dict[str, Any]) -> None:
    global MONO_BOLD
    theme_name = config.get("theme", "clasico")
    if theme_name == "custom":
        cc = config.get("custom_colors", {})
        merged = {**DEFAULT_CONFIG["custom_colors"], **cc}
        t = {k: COLORS.get(v, curses.COLOR_WHITE) for k, v in merged.items()}
        MONO_BOLD = False
    else:
        t = THEMES.get(theme_name, THEMES["clasico"])
        MONO_BOLD = bool(t.get("mono_bold", False))
    curses.init_pair(PAIR_MARCO, t["marco"], -1)
    curses.init_pair(PAIR_TEXTO, t["texto"], -1)
    curses.init_pair(PAIR_DESTACAR, t["destacar"], -1)
    curses.init_pair(PAIR_NAV, t["nav"], -1)
    curses.init_pair(PAIR_OVERLAY, t["overlay"], -1)
