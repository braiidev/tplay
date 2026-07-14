from __future__ import annotations

import curses
import os
import shutil
import subprocess
import threading
import time
import copy
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from player.audio import AudioEngine
    from player.stack import Stack, StackItem

from .audio import AudioEngine
from .config import load as load_config, save as save_config, apply_theme
from .config import PAIR_TEXTO, PAIR_DESTACAR
from .playlist import load_all as load_all_playlists, save_all as save_playlists
from .metadata import MetadataCache
from .file_utils import list_dir as _list_dir
from .stack import Stack, StackItem
from . import views
from . import ui
from .ui import _build_hints, COMPACT_THRESHOLD
from . import handlers
from . import keybindings as kb
from .state import load_state, save_state, load_history, save_history
from .radios import load_radios
from .favorites import load_favorites, save_favorites


class PlayerApp:
    LIST_H: int = 4
    FILTER_LIST_H: int = 5

    # view IDs
    V_CONFIG: int = 0
    V_LISTEN: int = 1
    V_EXPLORER: int = 2
    V_PLAYLIST: int = 3
    V_HISTORY: int = 4
    V_RADIO: int = 5
    V_FAVORITES: int = 6

    def __init__(self, stdscr: curses.window) -> None:
        self.stdscr: curses.window = stdscr
        self.running: bool = True

        self.config: dict[str, Any] = load_config()
        self.current_view: int = self.V_LISTEN
        self.current_dir: str = self.config.get(
            "music_dir", os.path.expanduser("~/Music")
        )
        self.cursor: int = 0
        self.scroll: int = 0
        self.entries: list[tuple[str, bool, str]] = _list_dir(self.current_dir)

        self.audio: AudioEngine = AudioEngine()
        self.audio.set_volume(self.config.get("volume", 50))

        all_pl, active_name = load_all_playlists()
        self.playlist_data: dict[str, list[tuple[str, str]]] = all_pl
        self.active_name: str = active_name
        self.playlist_cursor: int = 0
        self.playlist_scroll: int = 0

        self.dialog: dict[str, Any] | None = (
            None  # {"type": "confirm"|"prompt"|"dest", ...}
        )

        self.meta_cache: MetadataCache = MetadataCache()
        self.stack: Stack = Stack()
        self.show_stack_view: bool = False
        self.stack_cursor: int = 0
        self.stack_scroll: int = 0

        self.playlist_filter: str = ""
        self.playlist_filtered: list[int] = []
        self.playlist_filter_mode: bool = False
        self.playlist_filter_cursor: int = 0

        self.explorer_filter: str = ""
        self.explorer_filtered: list[int] = []
        self.explorer_filter_mode: bool = False
        self.explorer_filter_cursor: int = 0
        self.explorer_marked: set[int] = set()

        self.show_help: bool = False
        self.help_tab: int = 0
        self.help_scroll: int = 0

        self.goto_mode: bool = False
        self.goto_field: int = 0
        self.goto_mins: int = 0
        self.goto_secs: int = 0

        self.meta_edit_mode: bool = False
        self.meta_edit_file: str = ""
        self.meta_edit_fields: list[tuple[str, str, str]] = []
        self.meta_edit_changed: dict[str, str] = {}
        self.meta_edit_cursor: int = 0
        self.meta_edit_editing: bool = False
        self.meta_edit_buf: str = ""
        self.meta_edit_cursor_pos: int = 0
        self.meta_edit_labels: list[str] = ["Título", "Artista", "Álbum", "Género"]
        self.meta_edit_keys: list[str] = ["title", "artist", "album", "genre"]

        self.config_tabs: list[dict[str, Any]] = []
        self.config_tab_idx: int = 0
        self.config_cursor: int = 0
        self.config_scroll: int = 0
        self.update_available: bool = False
        self.update_check_done: bool = False
        self._update_toast_shown: bool = False
        self.update_behind: int = 0

        self.history: list[dict[str, Any]] = load_history()
        self.history_cursor: int = 0
        self.history_scroll: int = 0
        self._history_last: str | None = None

        self.radios: list[dict[str, str]] = load_radios()
        self.radio_cursor: int = 0
        self.radio_scroll: int = 0

        self.favorites: list[dict[str, str]] = load_favorites()
        self.favorites_cursor: int = 0
        self.favorites_scroll: int = 0
        self._radio_pending_name: str = ""
        self.radio_edit_idx: int | None = None
        self.radio_edit_field: str | None = None
        self.radio_edit_cycle: bool = False

        self.undo_stack: list[dict[str, Any]] = []
        self.redo_stack: list[dict[str, Any]] = []

        self.file_op_mode: str | None = None
        self.file_op_source: str | None = None
        self._file_undo: dict[str, Any] | None = None

        self.dir_picker_mode: bool = False
        self.dir_picker_config_key: str = ""
        self.dir_picker_path: str = ""
        self.dir_picker_entries: list[tuple[str, bool, str]] = []
        self.dir_picker_cursor: int = 0
        self.dir_picker_scroll: int = 0

        self.kb_keybinding_view: bool = False

        self.toast_msg: str = ""
        self.toast_ticks: int = 0

        self.keybinding_mode: str = "default"
        self.key_lookup: dict[int, str] = {}
        self.kb_cursor: int = 0
        self.kb_capturing: bool = False
        self.kb_capturing_action: str | None = None
        self.kb_conflict_msg: str = ""
        self.kb_conflict_other: str = ""

        self._action_handlers: dict[str, Callable[[], None]] = {}
        self._view_handlers: dict[int, Callable[[PlayerApp, int], None]] = {}
        self._view_drawers: dict[int, Callable[[PlayerApp, int, int], None]] = {}

        self._setup_keybindings()
        self._build_config_tabs()
        self._build_action_handlers()

        self._view_handlers = {
            self.V_LISTEN: handlers.handle_listen,
            self.V_EXPLORER: handlers.handle_explorer,
            self.V_PLAYLIST: handlers.handle_playlist,
            self.V_HISTORY: handlers.handle_history,
            self.V_CONFIG: handlers.handle_config,
            self.V_RADIO: handlers.handle_radio,
            self.V_FAVORITES: handlers.handle_favorites,
        }
        self._view_drawers = {
            self.V_LISTEN: views.draw_listen,
            self.V_EXPLORER: views.draw_explorer,
            self.V_PLAYLIST: views.draw_playlist,
            self.V_HISTORY: views.draw_history,
            self.V_CONFIG: views.draw_config,
            self.V_RADIO: views.draw_radio,
            self.V_FAVORITES: views.draw_favorites,
        }

        curses.curs_set(0)
        self.stdscr.nodelay(True)
        self.stdscr.keypad(True)
        curses.start_color()
        curses.use_default_colors()
        self._apply_theme()
        self._start_update_check()
        self._resume_session()

    @property
    def playlist(self) -> list[tuple[str, str]]:
        return self.playlist_data.get(self.active_name, [])

    @property
    def paused(self) -> bool:
        return bool(self.audio.paused)

    @property
    def current_file(self) -> str | None:
        val: str | None = self.audio.current_file
        return val

    @current_file.setter
    def current_file(self, val: str | None) -> None:
        self.audio.current_file = val

    @property
    def volume(self) -> int:
        return int(self.audio.volume)

    @volume.setter
    def volume(self, val: int) -> None:
        self.audio.volume = val

    @property
    def config_items(self) -> list[tuple[str, str, str]]:
        if not self.config_tabs:
            return []
        items: list[tuple[str, str, str]] = self.config_tabs[self.config_tab_idx][
            "items"
        ]
        return items

    def _apply_theme(self) -> None:
        apply_theme(self.config)

    @property
    def _repo_dir(self) -> str:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def _save_session(self) -> None:
        pos = 0
        if self.audio.playing and self.audio.player:
            try:
                pos = max(0, self.audio.get_time())
            except Exception:
                pos = 0
        stack_items = [
            {"path": item.path, "name": item.name, "mode": item.mode}
            for item in self.stack.items
        ]
        save_state(
            playing=self.audio.playing,
            file=os.path.abspath(self.current_file) if self.current_file else "",
            position=pos,
            stack_items=stack_items,
            playhead=self.stack.playhead,
            shuffle=self.stack.shuffle,
            repeat=self.stack.repeat,
            volume=self.audio.volume,
            rate=self.audio.rate,
            eq_enabled=self.audio._eq_enabled,
            eq_bands=self.config.get("eq_bands", [0.0] * 10),
            eq_preamp=self.config.get("eq_preamp", 0.0),
            eq_preset=self.config.get("eq_preset", "Flat"),
        )

    def _start_update_check(self) -> None:
        self.update_check_done = False
        self.update_available = False
        self.update_behind = 0
        git_dir = os.path.join(self._repo_dir, ".git")
        if not os.path.isdir(git_dir):
            self.update_check_done = True
            return
        t = threading.Thread(target=self._check_updates, daemon=True)
        t.start()

    def _check_updates(self) -> None:
        try:
            subprocess.run(
                ["git", "fetch", "origin"],
                cwd=self._repo_dir,
                capture_output=True,
                timeout=10,
            )
            result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD..origin/main"],
                cwd=self._repo_dir,
                capture_output=True,
                text=True,
                timeout=10,
            )
            behind = int(result.stdout.strip() or 0)
            self.update_behind = behind
            self.update_available = behind > 0
        except Exception:
            self.update_behind = 0
            self.update_available = False
        self.update_check_done = True

    def _apply_updates(self) -> tuple[bool, str]:
        repo = self._repo_dir
        try:
            subprocess.run(
                ["git", "fetch", "origin"], cwd=repo, capture_output=True, timeout=10
            )
            result = subprocess.run(
                ["git", "pull", "--ff-only"],
                cwd=repo,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                self.update_available = False
                return True, "Actualizado correctamente"
            result2 = subprocess.run(
                ["git", "reset", "--hard", "origin/main"],
                cwd=repo,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result2.returncode == 0:
                self.update_available = False
                return True, "Actualizado correctamente"
            return False, result.stderr.strip() or "Error al actualizar"
        except Exception as e:
            return False, str(e)

    def _setup_keybindings(self) -> None:
        self.keybinding_mode = self.config.get("keybinding_mode", "default")
        raw: dict[str, Any] = self.config.get("keybindings", {})
        if self.keybinding_mode == "custom" and raw:
            cleaned = kb.resolve_conflicts(raw)
            self.key_lookup = kb.build_lookup(cleaned)
        else:
            self.key_lookup = {}
        self.kb_cursor = 0
        self.kb_capturing = False
        self.kb_capturing_action = None
        self.kb_conflict_msg = ""
        self.kb_conflict_other = ""

    def _build_action_handlers(self) -> None:
        self._action_handlers = {
            "play_pause": lambda: self.audio.toggle_play_pause(),
            "stop": lambda: self.audio.stop(),
            "next": lambda: self._play_next(),
            "prev": lambda: self._play_prev(),
            "volume_up": lambda: self.audio.set_volume(self.audio.volume + 5),
            "volume_down": lambda: self.audio.set_volume(self.audio.volume - 5),
            "shuffle": lambda: setattr(self.stack, "shuffle", not self.stack.shuffle),
            "repeat": lambda: setattr(self.stack, "repeat", not self.stack.repeat),
            "help": lambda: setattr(self, "show_help", not self.show_help),
            "sleep_timer": lambda: self._toggle_sleep_timer(),
            "mute": lambda: self.audio.toggle_mute(),
        }

    def _resume_session(self) -> None:
        st: dict[str, Any] = load_state()
        items = st.get("stack_items", [])
        if items:
            self.stack.items = [
                StackItem(
                    path=i["path"],
                    name=i.get("name", os.path.basename(i["path"])),
                    mode=i.get("mode", "normal"),
                )
                for i in items
                if isinstance(i, dict) and os.path.isfile(i.get("path", ""))
            ]
            ph = st.get("playhead", -1)
            if 0 <= ph < len(self.stack.items):
                self.stack.playhead = ph
            self.stack.shuffle = bool(st.get("shuffle", False))
            self.stack.repeat = bool(st.get("repeat", False))
        vol = st.get("volume", 75)
        if 0 <= vol <= 100:
            self.audio.set_volume(vol)
        rate = st.get("rate", 1.0)
        if rate != 1.0:
            self.audio.set_rate(rate)
        eq_enabled = st.get("eq_enabled", False)
        eq_bands = st.get("eq_bands", [0.0] * 10)
        eq_preamp = st.get("eq_preamp", 0.0)
        eq_preset = st.get("eq_preset", "Flat")
        self.config["eq_enabled"] = eq_enabled
        self.config["eq_bands"] = eq_bands
        self.config["eq_preamp"] = eq_preamp
        self.config["eq_preset"] = eq_preset
        if eq_enabled:
            self.audio.set_equalizer(eq_bands, eq_preamp)
        if (
            st.get("playing")
            and self.stack.current
            and os.path.isfile(self.stack.current.path)
        ):
            self.audio.play_file(self.stack.current.path)
            pos = st.get("position", 0)
            if pos > 0:
                self.audio.player.set_time(pos)
            self.current_view = self.V_LISTEN

    def _build_config_tabs(self) -> None:
        eq_items = [
            ("eq_enabled", "Ecualizador", "bool"),
            ("eq_preset", "Preset EQ", "choice"),
            ("eq_preamp", "Preamp", "eq_preamp"),
            ("_sep_bands", "", "separator"),
        ]
        band_names = ["60 Hz", "170 Hz", "310 Hz", "600 Hz", "1k",
                      "3k", "6k", "12k", "14k", "16k"]
        for i, name in enumerate(band_names):
            eq_items.append((f"eq_band_{i}", name, "eq_band"))
        self.config_tabs = [
            {
                "name": "General",
                "items": [
                    ("music_dir", "Directorio de música", "path"),
                    ("volume", "Volumen", "int"),
                    ("sleep_timer_minutes", "Sleep timer (min)", "int"),
                ],
            },
            {
                "name": "Apariencia",
                "items": [
                    ("theme", "Tema", "choice"),
                    ("ui_minimal", "Modo minimal", "bool"),
                    ("ui_navbar", "Barra de navegación", "bool"),
                ],
            },
            {
                "name": "Audio",
                "items": eq_items,
            },
            {
                "name": "Sistema",
                "items": [
                    ("keybindings", "Keybindings", "action"),
                    ("update", "Actualizar tplay", "action"),
                ],
            },
        ]
        if self.config.get("theme") == "custom":
            self.config_tabs[1]["items"] += [
                ("marco", "Marco", "color"),
                ("texto", "Texto", "color"),
                ("destacar", "Destacar", "color"),
                ("nav", "Nav", "color"),
                ("overlay", "Overlay", "color"),
            ]
        self.config_tab_idx = min(self.config_tab_idx, len(self.config_tabs) - 1)
        self.config_cursor = 0
        self.config_scroll = 0

    def _play_current(self) -> None:
        cur = self.stack.current
        if cur:
            self.audio.play_file(cur.path)
            self.current_view = self.V_LISTEN

    def _play_next(self) -> None:
        if self.stack.is_empty:
            return
        nxt = self.stack.next_playhead()
        if nxt < 0:
            self.audio.stop()
            self.stack.clear()
            return
        self.stack.playhead = nxt
        self._play_current()

    def _play_prev(self) -> None:
        if self.stack.is_empty:
            return
        prev = self.stack.prev_playhead()
        if prev < 0:
            return
        self.stack.playhead = prev
        self._play_current()

    def _check_playback_end(self) -> None:
        if not self.audio.is_ended():
            return
        if self.stack.is_empty:
            return
        cur = self.stack.current
        if cur is None:
            self._play_next()
            return
        if cur.mode == "repeat_inf":
            self.audio.play_file(cur.path)
            return
        if cur.mode == "repeat_once":
            cur.mode = "normal"
            self.audio.play_file(cur.path)
            return
        self._play_next()

    def _add_history(self, path: str, name: str | None = None) -> None:
        existing: dict[str, Any] | None = None
        for h in self.history:
            if h.get("path") == path:
                existing = h
                break
        count = (existing.get("count", 0) + 1) if existing else 1
        self.history = [h for h in self.history if h.get("path") != path]
        entry_name = name if name else os.path.basename(path)
        self.history.insert(0, {"name": entry_name, "path": path, "count": count})
        if len(self.history) > 100:
            self.history.pop()

    def run(self) -> None:
        while self.running:
            self._check_playback_end()
            self.audio.check_sleep_timer()
            cur = self.audio.current_file
            if cur and cur != self._history_last:
                self._add_history(cur)
                self._history_last = cur
            if self.update_check_done and not self._update_toast_shown:
                self._update_toast_shown = True
                if self.update_available:
                    self.toast("Nueva versión disponible")
            key = self.stdscr.getch()
            if key == curses.KEY_RESIZE:
                self.stdscr.clear()
                continue
            if key != -1:
                if (
                    self.toast_ticks > 0
                    and key in (10, 13, 32, 27)
                    and not self.dialog
                    and not self.show_help
                ):
                    self.toast_ticks = 0
                elif self.dialog:
                    self._handle_dialog_key(key)
                elif self.meta_edit_mode:
                    self._handle_meta_edit(key)
                else:
                    self._handle_key(key)
            self._draw()
            time.sleep(0.01 if self.dialog else 0.05)

    def _handle_key(self, key: int) -> None:
        if self._handle_key_help(key):
            return
        if self.dir_picker_mode:
            handlers.handle_dir_picker(self, key)
            return
        if self._handle_key_mode_specific(key):
            return
        if self._handle_key_view_switch(key):
            return
        if self.current_view == self.V_CONFIG and self.kb_keybinding_view:
            handlers.handle_keybindings(self, key)
            return

        # Config tab navigation with H/L (Shift) — before hjkl aliasing
        if self.current_view == self.V_CONFIG and not self.kb_keybinding_view:
            if key == ord("H"):
                self.config_tab_idx = (self.config_tab_idx - 1) % max(
                    1, len(self.config_tabs)
                )
                self.config_cursor = 0
                self.config_scroll = 0
                return
            elif key == ord("L"):
                self.config_tab_idx = (self.config_tab_idx + 1) % max(
                    1, len(self.config_tabs)
                )
                self.config_cursor = 0
                self.config_scroll = 0
                return

        # hjkl navigation aliases for non-Listen views
        if self.current_view != self.V_LISTEN:
            if key == ord("j"):
                key = curses.KEY_DOWN
            elif key == ord("k"):
                key = curses.KEY_UP
            elif key == ord("h"):
                key = curses.KEY_LEFT
            elif key == ord("l"):
                key = curses.KEY_RIGHT

        if self._handle_key_global(key):
            return
        handler = self._view_handlers.get(self.current_view)
        if handler:
            handler(self, key)

    def _handle_dialog_key(self, key: int) -> None:
        assert self.dialog is not None
        d: dict[str, Any] = self.dialog
        if d["type"] == "confirm":
            cb = d["callback"]
            self.dialog = None
            curses.curs_set(0)
            curses.flushinp()
            confirm = key in (ord("s"), ord("S"), ord("y"), ord("Y"), 10, 13)
            if cb and (confirm):
                h, w = self.stdscr.getmaxyx()
                ui.draw_dialog(
                    self.stdscr,
                    h,
                    w,
                    "Confirmar",
                    "  ✓  ",
                    is_confirm=True,
                    compact=h < COMPACT_THRESHOLD,
                )
                self.stdscr.refresh()
                cb()
        elif d["type"] == "prompt":
            cur: int = d.get("cursor_pos", len(d["buf"]))
            if key == 27:
                self.dialog = None
                curses.curs_set(0)
                curses.flushinp()
            elif key in (10, 13):
                buf = d["buf"].strip()
                cb = d["callback"]
                self.dialog = None
                curses.curs_set(0)
                if cb:
                    cb(self, buf)
            elif key in (127, curses.KEY_BACKSPACE):
                if cur > 0:
                    d["buf"] = d["buf"][: cur - 1] + d["buf"][cur:]
                    d["cursor_pos"] = cur - 1
                    self._clamp_prompt_scroll()
            elif key == curses.KEY_LEFT:
                if cur > 0:
                    d["cursor_pos"] = cur - 1
                    self._clamp_prompt_scroll()
            elif key == curses.KEY_RIGHT:
                if cur < len(d["buf"]):
                    d["cursor_pos"] = cur + 1
                    self._clamp_prompt_scroll()
            elif key == curses.KEY_HOME:
                d["cursor_pos"] = 0
                self._clamp_prompt_scroll()
            elif key == curses.KEY_END:
                d["cursor_pos"] = len(d["buf"])
                self._clamp_prompt_scroll()
            elif 32 <= key <= 126 and len(d["buf"]) < 60:
                d["buf"] = d["buf"][:cur] + chr(key) + d["buf"][cur:]
                d["cursor_pos"] = cur + 1
                self._clamp_prompt_scroll()
        elif d["type"] == "dest":
            if key in (27,):
                self.dialog = None
                curses.flushinp()
                return
            if key == ord("s"):
                item = StackItem(path=d["path"], name=os.path.basename(d["path"]))
                if d["mode"] == "append":
                    self.stack.append(item)
                elif d["mode"] == "after_current":
                    self.stack.insert_after_current(item)
                if self.stack.playhead == 0 and not self.audio.playing:
                    self._play_current()
            elif key == ord("p"):
                name = os.path.basename(d["path"])
                self._push_snapshot()
                if d["mode"] == "after_current":
                    pos = self.playlist_cursor + 1 if self.playlist else 0
                    self.playlist.insert(pos, (name, d["path"]))
                else:
                    self.playlist.append((name, d["path"]))
                handlers._save_playlist(self)
                self.toast(f"Añadido a '{self.active_name}'")
            else:
                self.dialog = None
                curses.flushinp()
                return
            self.dialog = None
            curses.flushinp()

    def _clamp_prompt_scroll(self) -> None:
        d: dict[str, Any] | None = self.dialog
        if not d or d["type"] != "prompt":
            return
        h, w = self.stdscr.getmaxyx()
        compact = h < COMPACT_THRESHOLD
        box_w = w - 2 if compact else min(60, w - 10)
        inner_w = box_w - 2
        field_w = max(1, inner_w - len(d["label"]) - 6)
        buf_len = len(d["buf"])
        cur = d.get("cursor_pos", buf_len)
        if buf_len <= field_w:
            d["scroll"] = 0
        elif cur < d["scroll"]:
            d["scroll"] = cur
        elif cur >= d["scroll"] + field_w:
            d["scroll"] = cur - field_w + 1
        d["scroll"] = max(0, min(d["scroll"], max(0, buf_len - field_w)))

    def _handle_key_help(self, key: int) -> bool:
        if key in (ord("?"), curses.KEY_F1, getattr(curses, "KEY_HELP", -1)):
            self.show_help = not self.show_help
            self.help_scroll = 0
            self.help_tab = ui.VIEW_TO_HELP_TAB.get(self.current_view, 0)
            curses.flushinp()
            return True
        if self.show_help:
            if key in (27, ord("?"), ord("q"), curses.KEY_F1):
                self.show_help = False
                self.help_scroll = 0
            elif key in (curses.KEY_DOWN, ord("j")):
                h, _ = self.stdscr.getmaxyx()
                list_h = max(2, h - 4) if h >= 12 else max(2, h - 2)
                total = len(ui.HELP_TABS[self.help_tab]["lines"])
                max_scroll = max(0, total - list_h)
                self.help_scroll = min(self.help_scroll + 1, max_scroll)
            elif key in (curses.KEY_UP, ord("k")):
                self.help_scroll = max(self.help_scroll - 1, 0)
            elif key in (curses.KEY_NPAGE, ord(" ")):
                h, _ = self.stdscr.getmaxyx()
                list_h = max(2, h - 4) if h >= 12 else max(2, h - 2)
                total = len(ui.HELP_TABS[self.help_tab]["lines"])
                max_scroll = max(0, total - list_h)
                self.help_scroll = min(self.help_scroll + list_h, max_scroll)
            elif key in (curses.KEY_PPAGE, ord("b")):
                h, _ = self.stdscr.getmaxyx()
                list_h = max(2, h - 4) if h >= 12 else max(2, h - 2)
                total = len(ui.HELP_TABS[self.help_tab]["lines"])
                max_scroll = max(0, total - list_h)
                self.help_scroll = max(self.help_scroll - list_h, 0)
            elif key in (curses.KEY_RIGHT, ord("l"), ord("]")):
                self.help_tab = (self.help_tab + 1) % len(ui.HELP_TABS)
                self.help_scroll = 0
            elif key in (curses.KEY_LEFT, ord("h"), ord("[")):
                self.help_tab = (self.help_tab - 1) % len(ui.HELP_TABS)
                self.help_scroll = 0
            else:
                self.show_help = False
                self.help_scroll = 0
            return True
        return False

    def _handle_key_mode_specific(self, key: int) -> bool:
        if self.current_view == self.V_LISTEN and self.show_stack_view:
            handlers.handle_stack_view(self, key)
            return True
        if self.current_view == self.V_LISTEN and self.goto_mode:
            handlers.handle_goto(self, key)
            return True
        if self.current_view == self.V_EXPLORER and self.explorer_filter_mode:
            handlers.handle_explorer(self, key)
            return True
        if self.current_view == self.V_PLAYLIST and self.playlist_filter_mode:
            handlers.handle_playlist(self, key)
            return True
        if key == ord("/"):
            if self.current_view == self.V_EXPLORER:
                handlers.handle_explorer(self, key)
                return True
            if self.current_view == self.V_PLAYLIST:
                handlers.handle_playlist(self, key)
                return True
        return False

    def _handle_key_view_switch(self, key: int) -> bool:
        if ord("0") <= key <= ord("6"):
            self.current_view = key - ord("0")
            self.cursor = 0
            self.scroll = 0
            self.show_stack_view = False
            self.goto_mode = False
            self.explorer_filter_mode = False
            self.playlist_filter_mode = False
            self.kb_keybinding_view = False
            self.dialog = None
            self.meta_edit_mode = False
            self.meta_edit_editing = False
            self.meta_edit_changed = {}
            self.file_op_mode = None
            self.file_op_source = None
            self.dir_picker_mode = False
            curses.curs_set(0)
            curses.flushinp()
            return True
        return False

    def _handle_key_global(self, key: int) -> bool:
        if self.keybinding_mode == "custom":
            action = self.key_lookup.get(key)
            if action:
                handler = self._action_handlers.get(action)
                if handler:
                    handler()
                    curses.flushinp()
                    return True
        if key == ord(" "):
            self.audio.toggle_play_pause()
            curses.flushinp()
            return True
        if key == ord("S"):
            if not self.show_stack_view:
                self.audio.stop()
                self.audio.sleep_timer_active = False
                self.audio.sleep_timer_expired = False
                curses.flushinp()
                return True
        if key == ord("n"):
            self._play_next()
            curses.flushinp()
            return True
        if key == ord("b"):
            self._play_prev()
            curses.flushinp()
            return True
        if key in (ord("+"),):
            self.audio.set_volume(self.audio.volume + 5)
            curses.flushinp()
            return True
        if key in (ord("-"),):
            self.audio.set_volume(self.audio.volume - 5)
            curses.flushinp()
            return True
        if key == ord("q"):
            self._save_session()
            save_history(self.history)
            self.config["volume"] = self.audio.volume
            save_config(self.config)
            self._save_all_playlists()
            self.audio.player.stop()
            self.audio.close()
            self.running = False
            return True
        if key == 27:
            if self.file_op_mode:
                return False  # Let view handler (_handle_file_op_picker) handle it
            if self.current_view == self.V_HISTORY and not any(
                (
                    self.show_stack_view,
                    self.goto_mode,
                    self.kb_keybinding_view,
                    self.dir_picker_mode,
                )
            ):
                return False  # Let history handler set view to Listen
            self.show_stack_view = False
            self.goto_mode = False
            self.kb_keybinding_view = False
            curses.flushinp()
            return True
        return False

    def _save_all_playlists(self) -> None:
        save_playlists(self.playlist_data, self.active_name)

    def _toggle_sleep_timer(self) -> None:
        if self.audio.sleep_timer_active:
            self.audio.sleep_timer_active = False
            self.audio.sleep_timer_expired = False
        else:
            minutes: int = self.config.get("sleep_timer_minutes", 30)
            self.audio.set_sleep_timer(minutes)

    def _setup_sleep_timer(self, buf: str) -> None:
        try:
            mins = max(1, int(buf.strip()))
        except ValueError:
            mins = 30
        self.config["sleep_timer_minutes"] = mins
        save_config(self.config)
        self.audio.set_sleep_timer(mins)

    def _clear_stack(self) -> None:
        self.audio.stop()
        self.stack.clear()

    def toast(self, msg: str) -> None:
        self.toast_msg = msg
        self.toast_ticks = 40

    # ── Undo / Redo ──

    def _snapshot_state(self) -> dict[str, Any]:
        return {
            "playlist_data": copy.deepcopy(self.playlist_data),
            "active_name": self.active_name,
            "stack_items": copy.deepcopy(self.stack.items),
            "stack_playhead": self.stack.playhead,
            "stack_shuffle": self.stack.shuffle,
            "stack_repeat": self.stack.repeat,
            "file_undo": self._file_undo,
        }

    def _restore_snapshot(self, snap: dict[str, Any]) -> None:
        self.playlist_data = snap["playlist_data"]
        self.active_name = snap["active_name"]
        self.stack.load_items(snap["stack_items"])
        self.stack.playhead = snap["stack_playhead"]
        self.stack.shuffle = snap["stack_shuffle"]
        self.stack.repeat = snap["stack_repeat"]

    def _push_snapshot(self) -> None:
        self.undo_stack.append(self._snapshot_state())
        if len(self.undo_stack) > 50:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def _undo(self) -> None:
        if not self.undo_stack:
            return
        self.redo_stack.append(self._snapshot_state())
        self._apply_file_undo()
        self._restore_snapshot(self.undo_stack.pop())
        self.playlist_cursor = max(0, min(self.playlist_cursor, len(self.playlist) - 1))

    def _redo(self) -> None:
        if not self.redo_stack:
            return
        self.undo_stack.append(self._snapshot_state())
        snap = self.redo_stack.pop()
        fu = snap.get("file_undo")
        if fu:
            self._apply_file_redo(fu)
        self._restore_snapshot(snap)
        self.playlist_cursor = max(0, min(self.playlist_cursor, len(self.playlist) - 1))

    def _apply_file_undo(self) -> None:
        if not self._file_undo:
            return
        import shutil

        fu = self._file_undo
        self._file_undo = None
        try:
            if fu["type"] == "move":
                shutil.move(fu["dest"], fu["src"])
            elif fu["type"] == "copy" and os.path.isfile(fu["dest"]):
                os.remove(fu["dest"])
            self.entries = _list_dir(self.current_dir)
        except Exception as e:
            self.toast(f"No se pudo deshacer: {e}")

    def _apply_file_redo(self, fu: dict[str, Any]) -> None:
        import shutil

        try:
            if fu["type"] == "move":
                shutil.move(fu["src"], fu["dest"])
            elif fu["type"] == "copy":
                shutil.copy2(fu["src"], fu["dest"])
            self.entries = _list_dir(self.current_dir)
        except Exception as e:
            self.toast(f"No se pudo rehacer: {e}")

    # ── Meta Editor ──

    def _handle_meta_edit(self, key: int) -> None:
        if self.meta_edit_editing:
            cur = self.meta_edit_cursor_pos
            if key == 27:
                self.meta_edit_editing = False
            elif key in (10, 13):
                new_val = self.meta_edit_buf.strip()
                fname = self.meta_edit_keys[self.meta_edit_cursor]
                orig = self.meta_edit_fields[self.meta_edit_cursor][2]
                if new_val != orig:
                    self.meta_edit_changed[fname] = new_val
                elif fname in self.meta_edit_changed:
                    del self.meta_edit_changed[fname]
                self.meta_edit_editing = False
            elif key == curses.KEY_LEFT:
                if cur > 0:
                    self.meta_edit_cursor_pos = cur - 1
            elif key == curses.KEY_RIGHT:
                if cur < len(self.meta_edit_buf):
                    self.meta_edit_cursor_pos = cur + 1
            elif key in (127, curses.KEY_BACKSPACE):
                if cur > 0:
                    self.meta_edit_buf = (
                        self.meta_edit_buf[: cur - 1] + self.meta_edit_buf[cur:]
                    )
                    self.meta_edit_cursor_pos = cur - 1
            elif 32 <= key <= 126 and len(self.meta_edit_buf) < 60:
                self.meta_edit_buf = (
                    self.meta_edit_buf[:cur] + chr(key) + self.meta_edit_buf[cur:]
                )
                self.meta_edit_cursor_pos = cur + 1
            return
        if key in (ord("q"), 27):
            self.meta_edit_mode = False
            self.meta_edit_changed = {}
        elif key == ord("s"):
            if self._save_meta_edits():
                self.meta_edit_mode = False
        elif key in (ord("j"), curses.KEY_DOWN):
            self.meta_edit_cursor = min(
                self.meta_edit_cursor + 1, len(self.meta_edit_fields) - 1
            )
        elif key in (ord("k"), curses.KEY_UP):
            self.meta_edit_cursor = max(self.meta_edit_cursor - 1, 0)
        elif key in (10, 13):
            self.meta_edit_editing = True
            fname = self.meta_edit_keys[self.meta_edit_cursor]
            self.meta_edit_buf = (
                self.meta_edit_changed.get(fname)
                or self.meta_edit_fields[self.meta_edit_cursor][2]
            )
            self.meta_edit_cursor_pos = len(self.meta_edit_buf)

    def _save_meta_edits(self) -> bool:
        import mutagen

        try:
            audio = mutagen.File(self.meta_edit_file, easy=True)  # type: ignore[attr-defined]
            if audio is not None:
                for f, v in self.meta_edit_changed.items():
                    audio[f] = v
                audio.save()
            self.meta_cache.clear()
            return True
        except Exception as e:
            self.toast(f"Error al guardar metadata: {e}")
            return False

    # ── Drawing ──

    def _draw(self) -> None:
        try:
            h, w = self.stdscr.getmaxyx()
            self.stdscr.erase()

            self.scroll = max(0, self.scroll)
            self.cursor = max(0, self.cursor)
            self.playlist_cursor = max(0, self.playlist_cursor)
            self.history_cursor = max(0, self.history_cursor)
            self.stack_cursor = max(0, self.stack_cursor)
            self.radio_cursor = max(0, self.radio_cursor)
            self.config_cursor = max(0, self.config_cursor)
            self.dir_picker_cursor = max(0, self.dir_picker_cursor)

            minimal = self.config.get("ui_minimal", False)
            compact = (
                minimal or h < COMPACT_THRESHOLD or (self.current_view == self.V_LISTEN and w < 61)
            )

            if h < 8 or w < 40:
                err = f"MIN 40x8, NOW({h}x{w})"
                ui.safe_addstr(self.stdscr, 0, 0, err, None, h, w)
                self.stdscr.refresh()
                return

            needs_cursor = False

            if self.meta_edit_mode:
                views.draw_meta_editor(self, self.stdscr, h, w)
            elif self.dir_picker_mode:
                views.draw_dir_picker(self, self.stdscr, h, w)
            elif self.current_view == self.V_CONFIG and self.kb_keybinding_view:
                views.draw_keybindings(self, h, w)
            elif compact and self.current_view == self.V_LISTEN:
                views.draw_listen_compact(self, h, w)
            else:
                drawer = self._view_drawers.get(self.current_view)
                if drawer:
                    drawer(self, h, w)

            if compact:
                if self.toast_ticks > 0:
                    ui.safe_addstr(
                        self.stdscr,
                        1,
                        2,
                        self.toast_msg[: w - 4],
                        curses.color_pair(PAIR_TEXTO),
                        h,
                        w,
                    )
                    self.toast_ticks -= 1
            else:
                self._draw_status(h, w)
            if self.dialog is not None:
                d: dict[str, Any] = self.dialog
                if d["type"] == "confirm":
                    ui.draw_dialog(
                        self.stdscr,
                        h,
                        w,
                        "Confirmar",
                        d["label"],
                        is_confirm=True,
                        compact=compact,
                    )
                elif d["type"] == "prompt":
                    ui.draw_dialog(
                        self.stdscr,
                        h,
                        w,
                        "Entrada",
                        d["label"],
                        compact=compact,
                        prompt_buf=d["buf"],
                        prompt_scroll=d["scroll"],
                        prompt_cursor_pos=d.get("cursor_pos", len(d["buf"])),
                    )
                elif d["type"] == "dest":
                    dest_text = (
                        _build_hints(
                            [
                                ("s", "Pila"),
                                ("p", "Lista"),
                                ("Esc", "Cancelar"),
                            ],
                            w,
                        )
                        or "s: Pila  |  p: Lista  |  Esc: Cancelar"
                    )
                    ui.draw_dialog(
                        self.stdscr, h, w, "Destino", dest_text, compact=compact
                    )
            elif (
                not self.meta_edit_mode
                and not compact
                and self.config.get("ui_navbar", True)
            ):
                ui.draw_nav(self.stdscr, h, w)
            if self.toast_ticks > 0:
                ui.safe_addstr(
                    self.stdscr,
                    h - 3,
                    2,
                    self.toast_msg,
                    curses.color_pair(PAIR_TEXTO),
                    h,
                    w,
                )
                self.toast_ticks -= 1
            if self.update_available and not self.dialog and not self.show_help:
                if not compact:
                    msg = " ! Actualización disponible "
                    if w > len(msg) + 2:
                        ui.safe_addstr(
                            self.stdscr,
                            0,
                            w - len(msg) - 1,
                            msg,
                            curses.color_pair(PAIR_DESTACAR),
                            h,
                            w,
                        )
            if self.show_help:
                ui.draw_help(self.stdscr, h, w, self.help_scroll, self.help_tab)

            self.stdscr.refresh()
        except curses.error:
            pass

    def _draw_status(self, h: int, w: int) -> None:
        ui.draw_status(
            self.stdscr,
            h,
            w,
            self.audio,
            self.audio.playing,
            self.audio.current_file,
            self.audio.volume,
            self.stack.shuffle,
            self.stack.repeat,
            self.active_name,
            self.current_view,
            self.stack,
        )
