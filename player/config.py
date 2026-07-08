import os
import json
import curses

CONFIG_DIR = os.path.expanduser("~/.config/player")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
os.makedirs(CONFIG_DIR, exist_ok=True)

DEFAULT_CONFIG = {
    "music_dir": os.path.expanduser("~/Music"),
    "volume": 50,
    "theme": "clasico",
    "custom_colors": {"marco": "Cian", "texto": "Blanco", "destacar": "Amarillo", "nav": "Cian"},
    "sleep_timer_minutes": 30,
    "keybinding_mode": "default",
    "keybindings": {},
}

COLORS = {
    "Negro": curses.COLOR_BLACK, "Rojo": curses.COLOR_RED,
    "Verde": curses.COLOR_GREEN, "Amarillo": curses.COLOR_YELLOW,
    "Azul": curses.COLOR_BLUE, "Magenta": curses.COLOR_MAGENTA,
    "Cian": curses.COLOR_CYAN, "Blanco": curses.COLOR_WHITE,
}

THEMES = {
    "clasico": {"marco": curses.COLOR_CYAN, "texto": curses.COLOR_WHITE,
                "destacar": curses.COLOR_YELLOW, "nav": curses.COLOR_CYAN},
    "mono": {"marco": curses.COLOR_WHITE, "texto": curses.COLOR_WHITE,
             "destacar": curses.COLOR_WHITE, "nav": curses.COLOR_WHITE},
    "calido": {"marco": curses.COLOR_YELLOW, "texto": curses.COLOR_WHITE,
               "destacar": curses.COLOR_RED, "nav": curses.COLOR_RED},
    "alto_contraste": {"marco": curses.COLOR_MAGENTA, "texto": curses.COLOR_WHITE,
                       "destacar": curses.COLOR_GREEN, "nav": curses.COLOR_MAGENTA},
    "custom": {"marco": 0, "texto": 0, "destacar": 0, "nav": 0},
}
THEME_NAMES = list(THEMES.keys())

PAIR_MARCO = 1
PAIR_TEXTO = 2
PAIR_DESTACAR = 3
PAIR_NAV = 4


def load() -> dict:
    try:
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
            for k in DEFAULT_CONFIG:
                cfg.setdefault(k, DEFAULT_CONFIG[k])
            return cfg
    except (FileNotFoundError, json.JSONDecodeError):
        return dict(DEFAULT_CONFIG)


def save(cfg: dict) -> None:
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=2)
    except OSError:
        pass


def apply_theme(config: dict) -> None:
    theme_name = config.get("theme", "clasico")
    if theme_name == "custom":
        cc = config.get("custom_colors", DEFAULT_CONFIG["custom_colors"])
        t = {k: COLORS.get(v, curses.COLOR_WHITE) for k, v in cc.items()}
    else:
        t = THEMES.get(theme_name, THEMES["clasico"])
    curses.init_pair(PAIR_MARCO, t["marco"], -1)
    curses.init_pair(PAIR_TEXTO, t["texto"], -1)
    curses.init_pair(PAIR_DESTACAR, t["destacar"], -1)
    curses.init_pair(PAIR_NAV, t["nav"], -1)
