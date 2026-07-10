from __future__ import annotations

import os
import json
import curses
from typing import Any

CONFIG_DIR: str = os.path.expanduser("~/.config/tplay/data")
CONFIG_FILE: str = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG: dict[str, Any] = {
    "music_dir": os.path.expanduser("~/Music"),
    "volume": 50,
    "theme": "clasico",
    "custom_colors": {"marco": "Cian", "texto": "Blanco", "destacar": "Amarillo", "nav": "Cian"},
    "sleep_timer_minutes": 30,
    "keybinding_mode": "default",
    "keybindings": {},
    "ui_navbar": True,
    "ui_minimal": False,
}

COLORS: dict[str, int] = {
    "Negro": curses.COLOR_BLACK, "Rojo": curses.COLOR_RED,
    "Verde": curses.COLOR_GREEN, "Amarillo": curses.COLOR_YELLOW,
    "Azul": curses.COLOR_BLUE, "Magenta": curses.COLOR_MAGENTA,
    "Cian": curses.COLOR_CYAN, "Blanco": curses.COLOR_WHITE,
}

THEMES: dict[str, dict[str, int]] = {
    "clasico": {"marco": curses.COLOR_CYAN, "texto": curses.COLOR_WHITE,
                "destacar": curses.COLOR_YELLOW, "nav": curses.COLOR_CYAN},
    "mono": {"marco": curses.COLOR_WHITE, "texto": curses.COLOR_WHITE,
             "destacar": curses.COLOR_WHITE, "nav": curses.COLOR_WHITE},
    "calido": {"marco": curses.COLOR_YELLOW, "texto": curses.COLOR_WHITE,
               "destacar": curses.COLOR_RED, "nav": curses.COLOR_RED},
    "contraste": {"marco": curses.COLOR_MAGENTA, "texto": curses.COLOR_WHITE,
                       "destacar": curses.COLOR_GREEN, "nav": curses.COLOR_MAGENTA},
    "flatline": {"marco": curses.COLOR_CYAN, "texto": curses.COLOR_WHITE,
                 "destacar": curses.COLOR_RED, "nav": curses.COLOR_CYAN},
    "custom": {"marco": 0, "texto": 0, "destacar": 0, "nav": 0},
}
THEME_NAMES: list[str] = list(THEMES.keys())

PAIR_MARCO: int = 1
PAIR_TEXTO: int = 2
PAIR_DESTACAR: int = 3
PAIR_NAV: int = 4


def load() -> dict[str, Any]:
    try:
        with open(CONFIG_FILE) as f:
            cfg: dict[str, Any] = json.load(f)
            for k in DEFAULT_CONFIG:
                cfg.setdefault(k, DEFAULT_CONFIG[k])
            return cfg
    except (FileNotFoundError, json.JSONDecodeError):
        fallback: dict[str, Any] = dict(DEFAULT_CONFIG)
        return fallback


def save(cfg: dict[str, Any]) -> None:
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=2)
    except OSError:
        pass


def apply_theme(config: dict[str, Any]) -> None:
    theme_name = config.get("theme", "clasico")
    if theme_name == "custom":
        cc = config.get("custom_colors", {})
        merged = {**DEFAULT_CONFIG["custom_colors"], **cc}
        t = {k: COLORS.get(v, curses.COLOR_WHITE) for k, v in merged.items()}
    else:
        t = THEMES.get(theme_name, THEMES["clasico"])
    curses.init_pair(PAIR_MARCO, t["marco"], -1)
    curses.init_pair(PAIR_TEXTO, t["texto"], -1)
    curses.init_pair(PAIR_DESTACAR, t["destacar"], -1)
    curses.init_pair(PAIR_NAV, t["nav"], -1)
