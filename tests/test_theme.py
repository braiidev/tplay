"""Tests para el sistema de themes (portados de Clock).

Verifica que los themes de tplay espejan los de Clock (braiidev/clock)
con el mapeo de roles marco/helpers/nav/clima -> marco/destacar/nav/overlay,
y que el alias legacy `contraste` → `alto_contraste` funciona.
"""
from __future__ import annotations

import curses

from player.config import (
    COLORS,
    THEMES,
    THEME_NAMES,
    apply_theme,
    resolve_theme_name,
)

ROLES = ("marco", "texto", "destacar", "nav", "overlay")

# Temas de Clock (src/clock_tui/core/theme.py) ya mapeados a roles de tplay.
EXPECTED_THEMES: dict[str, dict[str, int]] = {
    "clasico": {"marco": curses.COLOR_CYAN, "texto": curses.COLOR_WHITE,
                "destacar": curses.COLOR_YELLOW, "nav": curses.COLOR_CYAN, "overlay": curses.COLOR_GREEN},
    "mono": {"marco": curses.COLOR_WHITE, "texto": curses.COLOR_WHITE,
             "destacar": curses.COLOR_WHITE, "nav": curses.COLOR_WHITE, "overlay": curses.COLOR_WHITE},
    "calido": {"marco": curses.COLOR_YELLOW, "texto": curses.COLOR_WHITE,
               "destacar": curses.COLOR_YELLOW, "nav": curses.COLOR_RED, "overlay": curses.COLOR_RED},
    "alto_contraste": {"marco": curses.COLOR_MAGENTA, "texto": curses.COLOR_WHITE,
                       "destacar": curses.COLOR_MAGENTA, "nav": curses.COLOR_MAGENTA, "overlay": curses.COLOR_GREEN},
    "flatline": {"marco": curses.COLOR_CYAN, "texto": curses.COLOR_WHITE,
                 "destacar": curses.COLOR_RED, "nav": curses.COLOR_RED, "overlay": curses.COLOR_RED},
}


def test_themes_espejan_clock() -> None:
    for nombre, esperado in EXPECTED_THEMES.items():
        t = THEMES[nombre]
        for rol in ROLES:
            assert t.get(rol) == esperado[rol], (nombre, rol)


def test_theme_names_incluye_clock_y_renombra_contraste() -> None:
    assert THEME_NAMES == list(EXPECTED_THEMES) + ["custom"]
    assert "contraste" not in THEME_NAMES
    assert "alto_contraste" in THEME_NAMES


def test_todos_los_themes_tienen_los_cinco_roles() -> None:
    for nombre, t in THEMES.items():
        for rol in ROLES:
            assert rol in t, (nombre, rol)
        if nombre != "mono":
            assert t[rol] in COLORS.values()


def test_apply_theme_clasico_inicializa_pares(monkeypatch: object) -> None:
    seen: dict[int, tuple[int, int]] = {}

    def fake_init_pair(pair: int, fg: int, bg: int) -> None:
        seen[pair] = (fg, bg)

    import player.config as config_mod

    monkeypatch.setattr(config_mod.curses, "init_pair", fake_init_pair)
    apply_theme({"theme": "clasico"})
    assert seen == {
        1: (curses.COLOR_CYAN, -1),
        2: (curses.COLOR_WHITE, -1),
        3: (curses.COLOR_YELLOW, -1),
        4: (curses.COLOR_CYAN, -1),
        5: (curses.COLOR_GREEN, -1),
    }


def test_apply_theme_mono_setea_mono_bold(monkeypatch: object) -> None:
    import player.config as config_mod

    monkeypatch.setattr(config_mod.curses, "init_pair", lambda *_: None)
    apply_theme({"theme": "mono"})
    assert config_mod.MONO_BOLD is True


def test_apply_theme_legacy_contraste_mapea_alto_contraste(
    monkeypatch: object,
) -> None:
    import player.config as config_mod

    seen: dict[int, tuple[int, int]] = {}
    monkeypatch.setattr(
        config_mod.curses, "init_pair", lambda p, fg, bg: seen.__setitem__(p, (fg, bg)),
    )
    apply_theme({"theme": "contraste"})
    assert seen == {
        1: (curses.COLOR_MAGENTA, -1),
        2: (curses.COLOR_WHITE, -1),
        3: (curses.COLOR_MAGENTA, -1),
        4: (curses.COLOR_MAGENTA, -1),
        5: (curses.COLOR_GREEN, -1),
    }


def test_resolve_theme_name_alias_y_identity() -> None:
    assert resolve_theme_name("contraste") == "alto_contraste"
    assert resolve_theme_name("flatline") == "flatline"
    assert resolve_theme_name("desconocido") == "desconocido"