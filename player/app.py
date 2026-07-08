import curses
import os
import sys
import time

from .audio import AudioEngine
from .config import load as load_config, save as save_config, apply_theme, THEME_NAMES
from .playlist import load_all as load_all_playlists, save_all as save_all_playlists
from .metadata import MetadataCache
from .file_utils import list_dir as _list_dir, is_media as _is_media_file
from . import views
from . import ui
from . import keybindings as kb


class PlayerApp:
    HJKL = {ord("h"): curses.KEY_LEFT, ord("j"): curses.KEY_DOWN,
            ord("k"): curses.KEY_UP, ord("l"): curses.KEY_RIGHT}

    LIST_H = 5
    SEARCH_LIST_H = 7
    FILTER_LIST_H = 6
    STATUS_ROW = 3
    NAV_ROW = 1
    EXPLORER_MARGIN = 8
    PLAYLIST_MARGIN = 6

    def __init__(self, stdscr) -> None:
        self.stdscr = stdscr
        self.running = True

        self.config = load_config()
        self.current_view = 1
        self.current_dir = self.config.get("music_dir", os.path.expanduser("~/Music"))
        self.cursor = 0
        self.scroll = 0
        self.entries = _list_dir(self.current_dir)

        self.audio = AudioEngine()
        self.audio.set_volume(self.config.get("volume", 50))

        all_pl, active_name = load_all_playlists()
        self.playlist_data = all_pl
        self.active_name = active_name
        self.playlist_idx = 0 if self.playlist else -1
        self.playlist_cursor = 0
        self.playlist_scroll = 0

        self.prompt_mode = False
        self.prompt_buf = ""
        self.prompt_label = ""
        self.prompt_callback = None

        self.search_query = ""
        self.search_results = []
        self.search_cursor = 0
        self.search_scroll = 0

        self.meta_cache = MetadataCache()
        self.temp_queue: list[tuple[str, bool]] = []

        self.playlist_filter = ""
        self.playlist_filtered = []
        self.playlist_filter_mode = False

        self.show_help = False

        self.goto_mode = False
        self.goto_field = 0
        self.goto_mins = 0
        self.goto_secs = 0

        self.show_temp_queue = False
        self.tq_cursor = 0
        self.tq_scroll = 0
        self.tq_playhead = -1

        self.config_cursor = 0
        self.config_scroll = 0
        self._setup_keybindings()
        self._build_config_items()
        self._build_action_handlers()

        self._view_handlers = {
            1: self._handle_explorer,
            2: self._handle_playlist,
            3: self._handle_now_playing,
            0: self._handle_config,
            5: self._handle_keybindings,
        }
        self._view_drawers = {
            1: views.draw_explorer,
            2: views.draw_playlist,
            3: views.draw_now_playing,
            4: views.draw_search,
            0: views.draw_config,
            5: views.draw_keybindings,
        }

        curses.curs_set(0)
        self.stdscr.nodelay(True)
        self.stdscr.keypad(True)
        curses.start_color()
        curses.use_default_colors()
        self._apply_theme()

    def _setup_keybindings(self) -> None:
        self.keybinding_mode = self.config.get("keybinding_mode", "default")
        raw = self.config.get("keybindings", {})
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
            "play_pause": lambda: (self.audio.toggle_play_pause(), None),
            "stop": lambda: (self.audio.stop(), None),
            "next": lambda: (self.audio.next(self.playlist), None),
            "prev": lambda: (self.audio.prev(self.playlist), None),
            "volume_up": lambda: (self.audio.set_volume(self.audio.volume + 5), None),
            "volume_down": lambda: (self.audio.set_volume(self.audio.volume - 5), None),
            "shuffle": lambda: (setattr(self.audio, 'shuffle', not self.audio.shuffle), None),
            "repeat": lambda: (setattr(self.audio, 'repeat', not self.audio.repeat), None),
            "help": lambda: (setattr(self, 'show_help', not self.show_help), None),
            "play_next": lambda: (self._queue_next(), None),
            "queue_add": lambda: (self._queue_add(), None),
            "sleep_timer": lambda: (self._toggle_sleep_timer(), None),
            "mute": lambda: (self.audio.toggle_mute(), None),
        }

    @property
    def playlist(self) -> list:
        return self.playlist_data.get(self.active_name, [])

    @property
    def playing(self) -> bool:
        return self.audio.is_playing

    @property
    def paused(self) -> bool:
        return self.audio.paused

    @property
    def current_file(self):
        return self.audio.current_file

    @current_file.setter
    def current_file(self, val):
        self.audio.current_file = val

    @property
    def volume(self) -> int:
        return self.audio.volume

    @volume.setter
    def volume(self, val: int):
        self.audio.volume = val

    @property
    def shuffle(self) -> bool:
        return self.audio.shuffle

    @shuffle.setter
    def shuffle(self, val: bool):
        self.audio.shuffle = val

    @property
    def repeat(self) -> bool:
        return self.audio.repeat

    @repeat.setter
    def repeat(self, val: bool):
        self.audio.repeat = val

    @property
    def sleep_timer_start(self) -> float:
        return self.audio.sleep_timer_start

    @sleep_timer_start.setter
    def sleep_timer_start(self, val: float):
        self.audio.sleep_timer_start = val

    @property
    def sleep_timer_duration(self) -> int:
        return self.audio.sleep_timer_duration

    @sleep_timer_duration.setter
    def sleep_timer_duration(self, val: int):
        self.audio.sleep_timer_duration = val

    @property
    def sleep_timer_active(self) -> bool:
        return self.audio.sleep_timer_active

    @sleep_timer_active.setter
    def sleep_timer_active(self, val: bool):
        self.audio.sleep_timer_active = val

    @property
    def sleep_timer_expired(self) -> bool:
        return self.audio.sleep_timer_expired

    @sleep_timer_expired.setter
    def sleep_timer_expired(self, val: bool):
        self.audio.sleep_timer_expired = val

    def _apply_theme(self) -> None:
        apply_theme(self.config)

    def _build_config_items(self) -> None:
        self.config_items = [
            ("music_dir", "Directorio de música", "path"),
            ("volume", "Volumen", "int"),
            ("theme", "Tema", "choice"),
        ]
        if self.config.get("theme") == "custom":
            self.config_items += [
                ("marco", "Marco", "color"),
                ("texto", "Texto", "color"),
                ("destacar", "Destacar", "color"),
                ("nav", "Nav", "color"),
            ]
        self.config_items += [
            ("sleep_timer_minutes", "Sleep timer (min)", "int"),
            ("keybindings", "Keybindings", "action"),
        ]

    def _auto_next_temp(self) -> bool:
        """Returns True if handled from temp_queue, False to fall through to playlist."""
        if not self.temp_queue:
            return False
        # If the item that just finished was consumable (N), remove it
        if 0 <= self.tq_playhead < len(self.temp_queue):
            if self.temp_queue[self.tq_playhead][1]:
                self.temp_queue.pop(self.tq_playhead)
                if self.tq_playhead >= len(self.temp_queue):
                    self.tq_playhead = len(self.temp_queue) - 1
        # Consume any N items at the front (inserted during playback)
        if self.temp_queue and self.temp_queue[0][1]:
            path, _ = self.temp_queue.pop(0)
            self.audio.play_file(path)
            self.tq_playhead = -1
            return True
        # Advance playhead to next permanent item
        nxt = (self.tq_playhead + 1) if self.tq_playhead >= 0 else 0
        if nxt < len(self.temp_queue):
            self.tq_playhead = nxt
            self.audio.play_file(self.temp_queue[nxt][0])
            return True
        # End of temp_queue
        self.tq_playhead = -1
        return False

    def _auto_prev_temp(self) -> None:
        if not self.temp_queue:
            return
        if self.tq_playhead > 0:
            self.tq_playhead -= 1
            self.audio.play_file(self.temp_queue[self.tq_playhead][0])
        elif self.tq_playhead == 0 and self.audio.repeat:
            self.tq_playhead = len(self.temp_queue) - 1
            self.audio.play_file(self.temp_queue[self.tq_playhead][0])

    def _check_playback_end(self) -> None:
        if not self.audio.is_ended():
            return
        if self._auto_next_temp():
            return
        self.audio.auto_next(self.playlist)

    def run(self) -> None:
        while self.running:
            self._check_playback_end()
            self.audio.check_sleep_timer()
            key = self.stdscr.getch()
            if key != -1:
                if self.prompt_mode:
                    self._handle_prompt(key)
                else:
                    self._handle_key(key)
            self._draw()
            time.sleep(0.05)

    def _handle_key(self, key: int) -> None:
        if self._handle_key_help(key):
            return
        if self._handle_key_mode_specific(key):
            return
        key = self.HJKL.get(key, key)
        if self._handle_key_view_switch(key):
            return
        if self.current_view == 5:
            self._handle_keybindings(key)
            return
        if self._handle_key_global(key):
            return
        handler = self._view_handlers.get(self.current_view)
        if handler:
            handler(key)

    def _handle_key_help(self, key: int) -> bool:
        if key in (ord("?"), curses.KEY_F1, getattr(curses, "KEY_HELP", -1)):
            self.show_help = not self.show_help
            curses.flushinp()
            return True
        if self.show_help:
            if key in (27, ord("?"), ord("q"), curses.KEY_F1):
                self.show_help = False
            return True
        return False

    def _handle_key_mode_specific(self, key: int) -> bool:
        if self.current_view == 3 and self.show_temp_queue:
            self._handle_temp_queue(key)
            return True
        if self.current_view == 3 and self.goto_mode:
            self._handle_goto(key)
            return True
        if self.current_view == 4:
            self._handle_search(key)
            return True
        if self.current_view == 2 and self.playlist_filter_mode:
            self._handle_playlist(key)
            return True
        if key == ord("/"):
            if self.current_view == 2:
                self._handle_playlist(key)
                return True
            if self.current_view == 0:
                self._handle_config(key)
                return True
        return False

    def _handle_key_view_switch(self, key: int) -> bool:
        if ord("0") <= key <= ord("4"):
            self.current_view = key - ord("0")
            self.cursor = 0
            self.scroll = 0
            curses.flushinp()
            return True
        if key == ord("/"):
            self.current_view = 4
            self.cursor = 0
            self.scroll = 0
            self.search_query = ""
            self.search_results = []
            curses.flushinp()
            curses.curs_set(1)
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
        if key == ord("s"):
            self.audio.stop()
            curses.flushinp()
            return True
        if key == ord("n"):
            self.audio.next(self.playlist)
            curses.flushinp()
            return True
        if key == ord("p"):
            self.audio.prev(self.playlist)
            curses.flushinp()
            return True
        if key == ord("+"):
            self.audio.set_volume(self.audio.volume + 5)
            curses.flushinp()
            return True
        if key == ord("-"):
            self.audio.set_volume(self.audio.volume - 5)
            curses.flushinp()
            return True
        if key == ord("N"):
            self._queue_next()
            curses.flushinp()
            return True
        if key == ord("A"):
            self._queue_add()
            curses.flushinp()
            return True
        if key == ord("r"):
            self.audio.shuffle = not self.audio.shuffle
            curses.flushinp()
            return True
        if key == ord("R"):
            self.audio.repeat = not self.audio.repeat
            curses.flushinp()
            return True
        if key == ord("m"):
            self.audio.toggle_mute()
            curses.flushinp()
            return True
        if key == ord("t"):
            self._toggle_sleep_timer()
            return True
        if key == ord("q"):
            self.config["volume"] = self.audio.volume
            save_config(self.config)
            self._save_playlist()
            self.audio.player.stop()
            self.running = False
            return True
        if key == 27:
            curses.flushinp()
            return True
        return False

    def _queue_next(self) -> None:
        was_empty = not self.temp_queue
        if self.current_view == 1 and self.entries:
            _, is_dir, full = self.entries[self.cursor]
            if not is_dir:
                self.temp_queue.insert(0, (full, True))
                if self.tq_playhead >= 0:
                    self.tq_playhead += 1
        elif self.current_view == 2 and self.playlist:
            path = self.playlist[self.playlist_cursor][1]
            self.temp_queue.insert(0, (path, True))
            if self.tq_playhead >= 0:
                self.tq_playhead += 1
        if was_empty and self.temp_queue and not self.audio.playing:
            self.tq_playhead = 0
            self.audio.play_file(self.temp_queue[0][0])
            self.current_view = 3

    def _queue_add(self) -> None:
        was_empty = not self.temp_queue
        if self.current_view == 1 and self.entries:
            _, is_dir, full = self.entries[self.cursor]
            if not is_dir:
                self.temp_queue.append((full, False))
        elif self.current_view == 2 and self.playlist:
            path = self.playlist[self.playlist_cursor][1]
            self.temp_queue.append((path, False))
        if was_empty and self.temp_queue and not self.audio.playing:
            self.tq_playhead = 0
            self.audio.play_file(self.temp_queue[0][0])
            self.current_view = 3

    def _play_playlist_idx(self, idx: int) -> None:
        if idx < 0 or idx >= len(self.playlist):
            return
        self.playlist_idx = idx
        self.temp_queue.clear()
        self.tq_playhead = -1
        self.audio.play_file(self.playlist[idx][1])

    def _playlist_append(self, path: str) -> None:
        name = os.path.basename(path)
        self.playlist.append((name, path))
        self._save_playlist()
        if self.playlist_idx == -1:
            self.playlist_idx = 0
            self.temp_queue.clear()
            self.tq_playhead = -1
            self.audio.play_file(path)

    def _play_file_direct(self, path: str) -> None:
        self.temp_queue.clear()
        self.tq_playhead = -1
        self.audio.play_file(path)
        self.current_view = 3

    def _playlist_remove(self, idx: int) -> None:
        if idx < 0 or idx >= len(self.playlist):
            return
        is_current = (idx == self.playlist_idx and self.audio.playing)
        self.playlist.pop(idx)
        if idx < self.playlist_idx:
            self.playlist_idx -= 1
        if not self.playlist:
            self.playlist_idx = -1
        elif self.playlist_idx >= len(self.playlist):
            self.playlist_idx = len(self.playlist) - 1
        self._save_playlist()
        if is_current:
            self.audio.stop()
            if self.playlist and self.playlist_idx >= 0:
                self._play_playlist_idx(self.playlist_idx)

    def _save_playlist(self) -> None:
        save_all_playlists(self.playlist_data, self.active_name)

    def _switch_playlist(self, name: str) -> None:
        if name in self.playlist_data:
            self.active_name = name
            self.playlist_idx = 0 if self.playlist else -1
            self.playlist_cursor = 0
            self.playlist_scroll = 0
            self.current_view = 2
            self.playlist_filter_mode = False
            self.playlist_filter = ""
            self.playlist_filtered = []
            curses.curs_set(0)

    # ── Handlers ──

    def _handle_explorer(self, key: int) -> None:
        if key == curses.KEY_DOWN:
            if self.entries:
                self.cursor = min(self.cursor + 1, len(self.entries) - 1)
        elif key == curses.KEY_UP:
            self.cursor = max(self.cursor - 1, 0)
        elif key == curses.KEY_NPAGE:
            self.cursor = min(self.cursor + self._page_size(), len(self.entries) - 1)
        elif key == curses.KEY_PPAGE:
            self.cursor = max(self.cursor - self._page_size(), 0)
        elif key == ord("g"):
            self.cursor = 0
        elif key == ord("G"):
            self.cursor = len(self.entries) - 1
        elif key in (ord("\n"), 10, 13, curses.KEY_RIGHT):
            if self.entries:
                name, is_dir, full = self.entries[self.cursor]
                if is_dir:
                    self.current_dir = full
                    self.entries = _list_dir(full)
                    self.cursor = 0
                    self.scroll = 0
                else:
                    self._play_file_direct(full)
        elif key == ord("a"):
            if self.entries:
                name, is_dir, full = self.entries[self.cursor]
                if not is_dir:
                    self._playlist_append(full)
        elif key in (curses.KEY_LEFT, 127, curses.KEY_BACKSPACE):
            parent = os.path.dirname(self.current_dir)
            if parent and parent != self.current_dir:
                self.current_dir = parent
                self.entries = _list_dir(parent)
                self.cursor = 0
                self.scroll = 0
        elif key == ord("~"):
            self.current_dir = os.path.expanduser("~")
            self.entries = _list_dir(self.current_dir)
            self.cursor = 0
            self.scroll = 0

        h, _ = self.stdscr.getmaxyx()
        list_h = h - self.LIST_H
        if self.cursor < self.scroll:
            self.scroll = self.cursor
        elif self.cursor >= self.scroll + list_h:
            self.scroll = self.cursor - list_h + 1

    def _handle_playlist(self, key: int) -> None:
        if self.playlist_filter_mode:
            if key == 27:
                self.playlist_filter_mode = False
                self.playlist_filter = ""
                self.playlist_filtered = []
                self.playlist_cursor = 0
                self.playlist_scroll = 0
                curses.curs_set(0)
                return
            if key in (ord("\n"), 10, 13):
                if self.playlist_filtered and self.playlist_cursor < len(self.playlist_filtered):
                    self._play_playlist_idx(self.playlist_filtered[self.playlist_cursor])
                    self.playlist_filter_mode = False
                    self.playlist_filter = ""
                    self.playlist_filtered = []
                    curses.curs_set(0)
                return
            if key == curses.KEY_DOWN:
                if self.playlist_filtered:
                    self.playlist_cursor = min(self.playlist_cursor + 1, len(self.playlist_filtered) - 1)
                h, _ = self.stdscr.getmaxyx()
                list_h = h - self.FILTER_LIST_H
                if self.playlist_cursor >= self.playlist_scroll + list_h:
                    self.playlist_scroll = self.playlist_cursor - list_h + 1
                return
            if key == curses.KEY_UP:
                self.playlist_cursor = max(self.playlist_cursor - 1, 0)
                if self.playlist_cursor < self.playlist_scroll:
                    self.playlist_scroll = self.playlist_cursor
                return
            if key in (127, curses.KEY_BACKSPACE):
                self.playlist_filter = self.playlist_filter[:-1]
                self._do_playlist_filter()
                return
            if 32 <= key <= 126:
                self.playlist_filter += chr(key)
                self._do_playlist_filter()
                return
            return

        if key == ord("/"):
            self.playlist_filter_mode = True
            self.playlist_filter = ""
            self.playlist_filtered = list(range(len(self.playlist)))
            self.playlist_cursor = 0
            self.playlist_scroll = 0
            curses.curs_set(1)
            return
        if key == curses.KEY_DOWN:
            if self.playlist:
                self.playlist_cursor = min(self.playlist_cursor + 1, len(self.playlist) - 1)
        elif key == curses.KEY_UP:
            self.playlist_cursor = max(self.playlist_cursor - 1, 0)
        elif key in (ord("\n"), 10, 13):
            if self.playlist:
                self._play_playlist_idx(self.playlist_cursor)
        elif key == ord("d"):
            self._playlist_remove(self.playlist_cursor)
            if self.playlist_cursor >= len(self.playlist) and self.playlist_cursor > 0:
                self.playlist_cursor -= 1
        elif key == ord("x"):
            self.playlist.clear()
            self.playlist_idx = -1
            self.playlist_cursor = 0
            self.audio.stop()
            self._save_playlist()
        elif key == ord("["):
            names = list(self.playlist_data.keys())
            if len(names) > 1:
                idx = names.index(self.active_name)
                self._switch_playlist(names[(idx - 1) % len(names)])
        elif key == ord("]"):
            names = list(self.playlist_data.keys())
            if len(names) > 1:
                idx = names.index(self.active_name)
                self._switch_playlist(names[(idx + 1) % len(names)])
        elif key == ord("C"):
            self._prompt("Nombre de la nueva playlist", self._create_playlist_cb)
        elif key == ord("E"):
            if self.active_name == "default":
                return
            self._prompt(f"Renombrar '{self.active_name}' a", self._rename_playlist_cb)
        elif key == ord("D"):
            if len(self.playlist_data) > 1 and self.active_name != "default":
                self._prompt(f"¿Borrar '{self.active_name}'? (s/N)", self._delete_confirm_cb)
        elif key == ord("K"):
            if self.playlist_cursor > 0:
                i = self.playlist_cursor
                pl = self.playlist
                pl[i], pl[i - 1] = pl[i - 1], pl[i]
                self.playlist_cursor -= 1
                if self.playlist_idx == i:
                    self.playlist_idx = i - 1
                elif self.playlist_idx == i - 1:
                    self.playlist_idx = i
                self._save_playlist()
        elif key == ord("J"):
            if self.playlist_cursor < len(self.playlist) - 1:
                i = self.playlist_cursor
                pl = self.playlist
                pl[i], pl[i + 1] = pl[i + 1], pl[i]
                self.playlist_cursor += 1
                if self.playlist_idx == i:
                    self.playlist_idx = i + 1
                elif self.playlist_idx == i + 1:
                    self.playlist_idx = i
                self._save_playlist()

        h, _ = self.stdscr.getmaxyx()
        list_h = h - self.LIST_H
        if self.playlist_cursor < self.playlist_scroll:
            self.playlist_scroll = self.playlist_cursor
        elif self.playlist_cursor >= self.playlist_scroll + list_h:
            self.playlist_scroll = self.playlist_cursor - list_h + 1

    def _handle_search(self, key: int) -> None:
        if key == 27:
            self.current_view = 1
            curses.curs_set(0)
            return
        if key == ord("\n") or key == 10 or key == 13:
            if self.search_results:
                path = self.search_results[self.search_cursor]
                self._play_file_direct(path)
                self.current_view = 3
            curses.curs_set(0)
            return
        if key == curses.KEY_DOWN:
            if self.search_results:
                self.search_cursor = min(self.search_cursor + 1, len(self.search_results) - 1)
        elif key == curses.KEY_UP:
            self.search_cursor = max(self.search_cursor - 1, 0)
        elif key == 127 or key == curses.KEY_BACKSPACE:
            self.search_query = self.search_query[:-1]
            self._do_search()
        elif 32 <= key <= 126:
            self.search_query += chr(key)
            self._do_search()

        h, _ = self.stdscr.getmaxyx()
        list_h = h - self.SEARCH_LIST_H
        if self.search_cursor < self.search_scroll:
            self.search_scroll = self.search_cursor
        elif self.search_cursor >= self.search_scroll + list_h:
            self.search_scroll = self.search_cursor - list_h + 1

    def _handle_config(self, key: int) -> None:
        if key == curses.KEY_DOWN:
            self.config_cursor = min(self.config_cursor + 1, len(self.config_items) - 1)
        elif key == curses.KEY_UP:
            self.config_cursor = max(self.config_cursor - 1, 0)
        elif key in (curses.KEY_RIGHT, ord("\n"), 10, 13):
            key_name, _, ctype = self.config_items[self.config_cursor]
            if ctype == "choice":
                self._cycle_theme(1)
            elif ctype == "color":
                self._cycle_color(key_name, 1)
            elif ctype == "int":
                self._config_int_inc(key_name)
            elif ctype == "action" and key_name == "keybindings":
                self._open_keybindings()
        elif key == curses.KEY_LEFT:
            key_name, _, ctype = self.config_items[self.config_cursor]
            if ctype == "choice":
                self._cycle_theme(-1)
            elif ctype == "color":
                self._cycle_color(key_name, -1)
            elif ctype == "int":
                self._config_int_dec(key_name)
        elif key == ord("/") or key == ord("e"):
            key_name, _, ctype = self.config_items[self.config_cursor]
            if ctype == "path" and key_name == "music_dir":
                self.current_view = 1
                curses.flushinp()
        elif key == curses.KEY_F2:
            self._open_keybindings()

    def _config_int_inc(self, key_name: str) -> None:
        if key_name == "volume":
            self.audio.set_volume(self.audio.volume + 5)
        elif key_name == "sleep_timer_minutes":
            val = self.config.get("sleep_timer_minutes", 30)
            self.config["sleep_timer_minutes"] = min(val + 1, 999)
        save_config(self.config)

    def _config_int_dec(self, key_name: str) -> None:
        if key_name == "volume":
            self.audio.set_volume(self.audio.volume - 5)
        elif key_name == "sleep_timer_minutes":
            val = self.config.get("sleep_timer_minutes", 30)
            self.config["sleep_timer_minutes"] = max(val - 1, 1)
        save_config(self.config)

    def _handle_now_playing(self, key: int) -> None:
        if key in (ord("\t"),):
            self.show_temp_queue = True
            self.tq_cursor = 0
            self.tq_scroll = 0
            curses.flushinp()
            return
        SEEK_STEP = 5000
        if key in (curses.KEY_LEFT,):
            cur = self.audio.get_time()
            self.audio.player.set_time(max(0, cur - SEEK_STEP))
        elif key in (curses.KEY_RIGHT,):
            cur = self.audio.get_time()
            dur = self.audio.get_length()
            self.audio.player.set_time(min(dur, cur + SEEK_STEP))
        elif key == ord("g"):
            if self.audio.get_length() > 0:
                cur_s = self.audio.get_time() // 1000
                self.goto_mins = cur_s // 60
                self.goto_secs = cur_s % 60
                self.goto_field = 0
                self.goto_mode = True
                curses.curs_set(0)

    def _handle_temp_queue(self, key: int) -> None:
        if key in (ord("\t"), 27):
            self.show_temp_queue = False
            curses.flushinp()
            return
        if key in (ord("n"),):
            if not self._auto_next_temp():
                self.audio.next(self.playlist)
            return
        if key in (ord("p"),):
            self._auto_prev_temp()
            return
        if key == ord("+"):
            self.audio.set_volume(self.audio.volume + 5)
            return
        if key == ord("-"):
            self.audio.set_volume(self.audio.volume - 5)
            return
        if not self.temp_queue:
            return
        if key in (ord("\n"), ord("\r"), curses.KEY_ENTER):
            path, consumable = self.temp_queue[self.tq_cursor]
            if consumable:
                self.temp_queue.pop(self.tq_cursor)
                if self.tq_cursor >= len(self.temp_queue) and self.tq_cursor > 0:
                    self.tq_cursor -= 1
                if self.tq_playhead > self.tq_cursor:
                    self.tq_playhead -= 1
                elif self.tq_playhead == self.tq_cursor:
                    self.tq_playhead = -1
            else:
                self.tq_playhead = self.tq_cursor
            self.audio.play_file(path)
            self.current_view = 3
            return
        if key in (curses.KEY_DOWN, ord("j")):
            self.tq_cursor = min(self.tq_cursor + 1, len(self.temp_queue) - 1)
        elif key in (curses.KEY_UP, ord("k")):
            self.tq_cursor = max(self.tq_cursor - 1, 0)
        elif key == ord("d"):
            self.temp_queue.pop(self.tq_cursor)
            if self.tq_cursor >= len(self.temp_queue) and self.tq_cursor > 0:
                self.tq_cursor -= 1
            if self.tq_playhead >= len(self.temp_queue):
                self.tq_playhead = len(self.temp_queue) - 1
            if self.tq_cursor <= self.tq_playhead and self.tq_playhead >= 0:
                self.tq_playhead -= 1
        elif key == ord("x"):
            self.temp_queue.clear()
            self.tq_cursor = 0
            self.tq_playhead = -1
            self.tq_scroll = 0
        elif key == ord("K"):
            if self.tq_cursor > 0:
                i = self.tq_cursor
                self.temp_queue[i], self.temp_queue[i - 1] = self.temp_queue[i - 1], self.temp_queue[i]
                self.tq_cursor -= 1
                if self.tq_playhead == i:
                    self.tq_playhead = i - 1
                elif self.tq_playhead == i - 1:
                    self.tq_playhead = i
        elif key == ord("J"):
            if self.tq_cursor < len(self.temp_queue) - 1:
                i = self.tq_cursor
                self.temp_queue[i], self.temp_queue[i + 1] = self.temp_queue[i + 1], self.temp_queue[i]
                self.tq_cursor += 1
                if self.tq_playhead == i:
                    self.tq_playhead = i + 1
                elif self.tq_playhead == i + 1:
                    self.tq_playhead = i
        elif key == ord("s"):
            if self.temp_queue:
                self._prompt("Guardar cola como playlist", self._save_temp_queue_cb)
        elif key == ord("N"):
            item = self.temp_queue.pop(self.tq_cursor)
            self.temp_queue.insert(0, (item[0], True))
            if self.tq_cursor == self.tq_playhead:
                self.tq_playhead = 0
            elif self.tq_cursor > self.tq_playhead:
                self.tq_playhead += 1
            self.tq_cursor = 0
            self.tq_scroll = 0
        elif key == ord("g"):
            self.tq_cursor = 0
            self.tq_scroll = 0
        elif key == ord("G"):
            self.tq_cursor = len(self.temp_queue) - 1
        elif key in (curses.KEY_NPAGE,):
            h, _ = self.stdscr.getmaxyx()
            page = h - 8
            self.tq_cursor = min(self.tq_cursor + page, len(self.temp_queue) - 1)
        elif key in (curses.KEY_PPAGE,):
            h, _ = self.stdscr.getmaxyx()
            page = h - 8
            self.tq_cursor = max(self.tq_cursor - page, 0)
        h, _ = self.stdscr.getmaxyx()
        list_h = h - 8
        if self.tq_cursor < self.tq_scroll:
            self.tq_scroll = self.tq_cursor
        elif self.tq_cursor >= self.tq_scroll + list_h:
            self.tq_scroll = self.tq_cursor - list_h + 1

    def _handle_goto(self, key: int) -> None:
        if key == 27:
            self.goto_mode = False
            curses.flushinp()
            return
        if key in (ord("\n"), 10, 13):
            target = self.goto_mins * 60 + self.goto_secs
            self.audio.player.set_time(target * 1000)
            self.goto_mode = False
            curses.flushinp()
            return
        if key in (curses.KEY_LEFT, ord("h")):
            self.goto_field = 0
            return
        if key in (curses.KEY_RIGHT, ord("l")):
            self.goto_field = 1
            return
        if key in (curses.KEY_UP, ord("k")):
            if self.goto_field == 0:
                self.goto_mins = min(self.goto_mins + 1, 999)
            else:
                self.goto_secs = min(self.goto_secs + 1, 59)
            return
        if key in (curses.KEY_DOWN, ord("j")):
            if self.goto_field == 0:
                self.goto_mins = max(self.goto_mins - 1, 0)
            else:
                self.goto_secs = max(self.goto_secs - 1, 0)
            return

    def _open_keybindings(self) -> None:
        self.current_view = 5
        self.kb_cursor = 0
        self.kb_capturing = False
        self.kb_capturing_action = None
        self.kb_conflict_msg = ""
        self.kb_conflict_other = ""

    def _handle_keybindings(self, key: int) -> None:
        if key == 27:
            self._save_keybindings()
            self.current_view = 0
            curses.flushinp()
            return

        if self.kb_capturing:
            if key in kb.RESERVED_KEYS or key in (27,):
                self.kb_capturing = False
                self.kb_capturing_action = None
                return
            if 32 <= key <= 126:
                self.kb_capturing = False
                self._assign_key(self.kb_capturing_action, key)
                self.kb_capturing_action = None
                return
            return

        if key in (curses.KEY_LEFT, curses.KEY_RIGHT):
            self._toggle_keybinding_mode()
            return

        if self.keybinding_mode != "custom":
            return

        if key == curses.KEY_DOWN:
            self.kb_cursor = min(self.kb_cursor + 1, len(kb.BINDABLE_ACTIONS) - 1)
        elif key == curses.KEY_UP:
            self.kb_cursor = max(self.kb_cursor - 1, 0)
        elif key in (ord("\n"), 10, 13):
            action = kb.BINDABLE_ACTIONS[self.kb_cursor]
            self.kb_capturing = True
            self.kb_capturing_action = action
            self.kb_conflict_msg = ""

    def _toggle_keybinding_mode(self) -> None:
        if self.keybinding_mode == "custom":
            self.config["keybinding_mode"] = "default"
            self.config["keybindings"] = {}
            self.keybinding_mode = "default"
            self.key_lookup = {}
        else:
            self.config["keybindings"] = dict(kb.DEFAULT_BINDINGS)
            self.config["keybinding_mode"] = "custom"
            self.keybinding_mode = "custom"
            self.key_lookup = kb.build_lookup(kb.DEFAULT_BINDINGS)
        self.kb_cursor = 0
        self._save_keybindings()

    def _assign_key(self, action: str, keycode: int) -> None:
        self.kb_conflict_msg = ""
        self.kb_conflict_other = ""

        conflicts = [a for a in kb.BINDABLE_ACTIONS
                     if a != action and self._get_current_key(a) == keycode]
        if conflicts:
            self.kb_conflict_msg = f"Colisión: {kb.key_name(keycode)} ya está en '{conflicts[0]}'"
            self.kb_conflict_other = conflicts[0]

        bindings = self._build_bindings_from_current()
        for a in list(bindings.keys()):
            if bindings[a] == keycode and a != action:
                bindings[a] = kb.DEFAULT_BINDINGS[a]
        bindings[action] = keycode
        cleaned = kb.resolve_conflicts(bindings)
        self.config["keybindings"] = cleaned
        self.config["keybinding_mode"] = "custom"
        self.keybinding_mode = "custom"
        self.key_lookup = kb.build_lookup(cleaned)
        self._save_keybindings()

    def _get_current_key(self, action: str) -> int:
        if self.keybinding_mode == "custom":
            return self.config.get("keybindings", {}).get(action, kb.DEFAULT_BINDINGS[action])
        return kb.DEFAULT_BINDINGS[action]

    def _build_bindings_from_current(self) -> dict:
        return {a: self._get_current_key(a) for a in kb.BINDABLE_ACTIONS}

    def _save_keybindings(self) -> None:
        self.config["keybinding_mode"] = self.keybinding_mode
        save_config(self.config)

    def _do_playlist_filter(self) -> None:
        q = self.playlist_filter.lower().strip()
        if not q:
            self.playlist_filtered = list(range(len(self.playlist)))
        else:
            self.playlist_filtered = [i for i, (name, path) in enumerate(self.playlist)
                                      if q in name.lower() or q in path.lower()]
        self.playlist_cursor = 0
        self.playlist_scroll = 0

    def _do_search(self) -> None:
        q = self.search_query.lower().strip()
        if not q:
            self.search_results = []
            self.search_cursor = 0
            self.search_scroll = 0
            return
        results = []
        limit = 200

        def _walk(path):
            nonlocal results
            if len(results) >= limit:
                return
            try:
                with os.scandir(path) as entries:
                    for entry in entries:
                        if len(results) >= limit:
                            return
                        if entry.name.startswith("."):
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            _walk(entry.path)
                        elif _is_media_file(entry.name) and q in entry.name.lower():
                            results.append(entry.path)
            except (PermissionError, OSError):
                pass

        _walk(self.current_dir)
        self.search_results = sorted(results)
        self.search_cursor = 0
        self.search_scroll = 0

    def _cycle_theme(self, direction: int) -> None:
        idx = THEME_NAMES.index(self.config["theme"])
        new_theme = THEME_NAMES[(idx + direction) % len(THEME_NAMES)]
        self.config["theme"] = new_theme
        self._build_config_items()
        self.config_cursor = min(self.config_cursor, len(self.config_items) - 1)
        self._apply_theme()
        save_config(self.config)

    def _cycle_color(self, key_name: str, direction: int) -> None:
        from .config import COLORS
        colors = list(COLORS.keys())
        cc = self.config.setdefault("custom_colors", {})
        current = cc.get(key_name, "Blanco")
        idx = colors.index(current)
        cc[key_name] = colors[(idx + direction) % len(colors)]
        self._apply_theme()
        save_config(self.config)

    def _save_temp_queue_cb(self, name: str) -> None:
        if name and name not in self.playlist_data:
            self.playlist_data[name] = [(os.path.basename(p), p) for p, _ in self.temp_queue]
            self._save_playlist()

    # ── Prompt ──

    def _prompt(self, label: str, callback, initial: str = "") -> None:
        self.prompt_mode = True
        self.prompt_label = label
        self.prompt_buf = initial
        self.prompt_callback = callback
        curses.curs_set(1)
        curses.flushinp()

    def _handle_prompt(self, key: int) -> None:
        if key == 27:
            self.prompt_mode = False
            self.prompt_buf = ""
            self.prompt_label = ""
            self.prompt_callback = None
            curses.curs_set(0)
            curses.flushinp()
        elif key in (ord("\n"), 10, 13):
            buf = self.prompt_buf.strip()
            self.prompt_mode = False
            self.prompt_label = ""
            self.prompt_buf = ""
            curses.curs_set(0)
            if buf and self.prompt_callback:
                self.prompt_callback(buf)
            self.prompt_callback = None
        elif key in (127, curses.KEY_BACKSPACE):
            self.prompt_buf = self.prompt_buf[:-1]
        elif 32 <= key <= 126 and len(self.prompt_buf) < 60:
            self.prompt_buf += chr(key)

    def _create_playlist_cb(self, name: str) -> None:
        if name and name not in self.playlist_data:
            self.playlist_data[name] = []
            self._switch_playlist(name)
            self._save_playlist()

    def _delete_confirm_cb(self, answer: str) -> None:
        if answer.lower() == "s" and len(self.playlist_data) > 1 and self.active_name != "default":
            del self.playlist_data[self.active_name]
            new_name = next(n for n in self.playlist_data if n != self.active_name)
            self._switch_playlist(new_name)
            self._save_playlist()

    def _set_int_cb(self, val: str) -> None:
        key_name, _, _ = self.config_items[self.config_cursor]
        try:
            n = int(val)
            if key_name == "volume":
                self.audio.set_volume(max(0, min(100, n)))
            elif key_name == "sleep_timer_minutes":
                self.config[key_name] = max(1, n)
            self.config[key_name] = n
            save_config(self.config)
        except ValueError:
            pass

    def _toggle_sleep_timer(self) -> None:
        if self.audio.sleep_timer_active:
            self.audio.sleep_timer_active = False
            self.audio.sleep_timer_expired = False
        else:
            minutes = self.config.get("sleep_timer_minutes", 30)
            self.audio.set_sleep_timer(minutes)

    def _rename_playlist_cb(self, new_name: str) -> None:
        if new_name and new_name != self.active_name and new_name not in self.playlist_data:
            self.playlist_data[new_name] = self.playlist_data.pop(self.active_name)
            self.active_name = new_name
            self._save_playlist()

    # ── Drawing ──

    def _page_size(self) -> int:
        h, _ = self.stdscr.getmaxyx()
        return max(1, h - self.LIST_H)

    def _draw(self) -> None:
        try:
            h, w = self.stdscr.getmaxyx()
            self.stdscr.erase()

            if h < 6 or w < 20:
                self.stdscr.addstr(0, 0, f"Terminal muy pequeña ({h}x{w}) — necesito al menos 20x6")
                self.stdscr.refresh()
                return

            needs_cursor = (self.current_view == 4
                            or (self.current_view == 2 and self.playlist_filter_mode)
                            or self.prompt_mode)
            if needs_cursor:
                curses.curs_set(0)

            drawer = self._view_drawers.get(self.current_view)
            if drawer:
                drawer(self, h, w)

            self._draw_status(h, w)
            if self.prompt_mode:
                ui.draw_prompt(self.stdscr, h, w, self.prompt_label, self.prompt_buf)
            else:
                ui.draw_nav(self.stdscr, h, w)
            if self.show_help:
                ui.draw_help(self.stdscr, h, w)

            if self.current_view == 4:
                self.stdscr.move(2, 4 + len(self.search_query))
                curses.curs_set(1)
            elif self.current_view == 2 and self.playlist_filter_mode:
                self.stdscr.move(2, 4 + len(self.playlist_filter))
                curses.curs_set(1)

            self.stdscr.refresh()
        except curses.error:
            pass

    def _draw_status(self, h: int, w: int) -> None:
        ui.draw_status(self.stdscr, h, w, self.audio, self.audio.playing,
                       self.audio.current_file, self.audio.volume,
                       self.audio.shuffle, self.audio.repeat,
                       self.active_name, self.current_view,
                       self.temp_queue)


def main() -> None:
    try:
        curses.wrapper(lambda stdscr: PlayerApp(stdscr).run())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
