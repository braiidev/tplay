import curses
import os
import subprocess
import time
import copy

from .audio import AudioEngine
from .config import load as load_config, save as save_config, apply_theme
from .playlist import load_all as load_all_playlists
from .metadata import MetadataCache
from .file_utils import list_dir as _list_dir
from . import views
from . import ui
from . import handlers
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
        self.update_available = False
        self.update_check_done = False
        self.update_behind = 0

        self.history = []
        self.history_cursor = 0
        self.history_scroll = 0
        self._history_last = None

        self.undo_stack = []
        self.redo_stack = []

        self.confirm_mode = False
        self.confirm_label = ""
        self.confirm_callback = None
        self.confirm_is_info = False

        self.file_op_mode = None
        self.file_op_source = None

        self._setup_keybindings()
        self._build_config_items()
        self._build_action_handlers()

        self._view_handlers = {
            1: handlers.handle_explorer,
            2: handlers.handle_playlist,
            3: handlers.handle_now_playing,
            0: handlers.handle_config,
            5: handlers.handle_keybindings,
            6: handlers.handle_history,
        }
        self._view_drawers = {
            1: views.draw_explorer,
            2: views.draw_playlist,
            3: views.draw_now_playing,
            4: views.draw_search,
            0: views.draw_config,
            5: views.draw_keybindings,
            6: views.draw_history,
        }

        curses.curs_set(0)
        self.stdscr.nodelay(True)
        self.stdscr.keypad(True)
        curses.start_color()
        curses.use_default_colors()
        self._apply_theme()
        self._check_updates()

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

    @property
    def _repo_dir(self) -> str:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def _check_updates(self) -> None:
        repo = self._repo_dir
        git_dir = os.path.join(repo, ".git")
        if not os.path.isdir(git_dir):
            self.update_check_done = True
            return
        try:
            subprocess.run(["git", "fetch", "origin"], cwd=repo,
                           capture_output=True, timeout=10)
            result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD..origin/main"],
                cwd=repo, capture_output=True, text=True, timeout=10,
            )
            behind = int(result.stdout.strip() or 0)
            self.update_behind = behind
            self.update_available = behind > 0
        except Exception:
            self.update_behind = 0
            self.update_available = False
        self.update_check_done = True

    def _apply_updates(self) -> None:
        repo = self._repo_dir
        try:
            result = subprocess.run(["git", "pull"], cwd=repo,
                                    capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                self.update_available = False
                return True, "Actualizado correctamente"
            return False, result.stderr.strip() or "Error al actualizar"
        except Exception as e:
            return False, str(e)

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
            ("update", "Actualizar tplay", "action"),
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

    def _add_history(self, path: str) -> None:
        name = os.path.basename(path)
        self.history = [(n, p) for n, p in self.history if p != path]
        self.history.insert(0, (name, path))
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
            key = self.stdscr.getch()
            if key != -1:
                if self.confirm_mode:
                    self._handle_confirm(key)
                elif self.prompt_mode:
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
            handlers.handle_keybindings(self, key)
            return
        if self._handle_key_global(key):
            return
        handler = self._view_handlers.get(self.current_view)
        if handler:
            handler(self, key)

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
            handlers.handle_temp_queue(self, key)
            return True
        if self.current_view == 3 and self.goto_mode:
            handlers.handle_goto(self, key)
            return True
        if self.current_view == 4:
            handlers.handle_search(self, key)
            return True
        if self.current_view == 2 and self.playlist_filter_mode:
            handlers.handle_playlist(self, key)
            return True
        if key == ord("/"):
            if self.current_view == 2:
                handlers.handle_playlist(self, key)
                return True
            if self.current_view == 0:
                handlers.handle_config(self, key)
                return True
        return False

    def _handle_key_view_switch(self, key: int) -> bool:
        if ord("0") <= key <= ord("4"):
            self.current_view = key - ord("0")
            self.cursor = 0
            self.scroll = 0
            curses.flushinp()
            return True
        if key == ord("H"):
            if self.current_view == 6:
                self.current_view = 3
            else:
                self.current_view = 6
                self.history_cursor = 0
                self.history_scroll = 0
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
        if key == ord("T"):
            handlers._prompt(self, "Minutos sleep timer",
                             lambda a, b: self._setup_sleep_timer(b),
                             str(self.config.get("sleep_timer_minutes", 30)))
            return True
        if key == ord("q"):
            self.config["volume"] = self.audio.volume
            save_config(self.config)
            handlers._save_playlist(self)
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

    # ── Undo / Redo ──

    def _playlist_snapshot(self) -> dict:
        return {
            "data": copy.deepcopy(self.playlist_data),
            "active": self.active_name,
            "idx": self.playlist_idx,
            "tq": list(self.temp_queue),
            "tq_head": self.tq_playhead,
        }

    def _push_snapshot(self) -> None:
        self.undo_stack.append(self._playlist_snapshot())
        if len(self.undo_stack) > 50:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def _undo(self) -> None:
        if not self.undo_stack:
            return
        self.redo_stack.append(self._playlist_snapshot())
        snap = self.undo_stack.pop()
        self.playlist_data = snap["data"]
        self.active_name = snap["active"]
        self.playlist_idx = snap["idx"]
        self.temp_queue = snap["tq"]
        self.tq_playhead = snap["tq_head"]
        self.playlist_cursor = max(0, min(self.playlist_cursor, len(self.playlist) - 1))

    def _redo(self) -> None:
        if not self.redo_stack:
            return
        self.undo_stack.append(self._playlist_snapshot())
        snap = self.redo_stack.pop()
        self.playlist_data = snap["data"]
        self.active_name = snap["active"]
        self.playlist_idx = snap["idx"]
        self.temp_queue = snap["tq"]
        self.tq_playhead = snap["tq_head"]
        self.playlist_cursor = max(0, min(self.playlist_cursor, len(self.playlist) - 1))

    # ── Prompt ──

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
                self.prompt_callback(self, buf)
            self.prompt_callback = None
        elif key in (127, curses.KEY_BACKSPACE):
            self.prompt_buf = self.prompt_buf[:-1]
        elif 32 <= key <= 126 and len(self.prompt_buf) < 60:
            self.prompt_buf += chr(key)

    def _handle_confirm(self, key: int) -> None:
        cb = self.confirm_callback
        is_info = self.confirm_is_info
        self.confirm_mode = False
        self.confirm_label = ""
        self.confirm_callback = None
        self.confirm_is_info = False
        curses.curs_set(0)
        curses.flushinp()
        if is_info:
            return
        if cb and chr(key).lower() in ("s", "y"):
            cb()

    def _toggle_sleep_timer(self) -> None:
        if self.audio.sleep_timer_active:
            self.audio.sleep_timer_active = False
            self.audio.sleep_timer_expired = False
        else:
            minutes = self.config.get("sleep_timer_minutes", 30)
            self.audio.set_sleep_timer(minutes)

    def _setup_sleep_timer(self, buf: str) -> None:
        try:
            mins = max(1, int(buf.strip()))
        except ValueError:
            mins = 30
        self.config["sleep_timer_minutes"] = mins
        save_config(self.config)
        self.audio.set_sleep_timer(mins)

    # ── Drawing ──

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
                curses.curs_set(1)

            drawer = self._view_drawers.get(self.current_view)
            if drawer:
                drawer(self, h, w)

            self._draw_status(h, w)
            if self.confirm_mode:
                buf = "  s/N  " if not self.confirm_is_info else "  OK  "
                ui.draw_prompt(self.stdscr, h, w, self.confirm_label, buf)
            elif self.prompt_mode:
                ui.draw_prompt(self.stdscr, h, w, self.prompt_label, self.prompt_buf)
            else:
                ui.draw_nav(self.stdscr, h, w)
            if self.update_available and not self.confirm_mode and not self.prompt_mode and not self.show_help:
                msg = " Nueva actualización disponible "
                if w > len(msg) + 1:
                    try:
                        self.stdscr.addstr(0, w - len(msg), msg, curses.A_REVERSE)
                    except curses.error:
                        pass
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



