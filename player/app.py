import curses
import os
import shutil
import subprocess
import time
import copy

from .audio import AudioEngine
from .config import load as load_config, save as save_config, apply_theme
from .playlist import load_all as load_all_playlists, save_all as save_playlists
from .metadata import MetadataCache
from .file_utils import list_dir as _list_dir
from .stack import Stack, StackItem
from . import views
from . import ui
from . import handlers
from . import keybindings as kb
from .state import load_state, save_state, load_history, save_history


class PlayerApp:
    LIST_H = 5
    FILTER_LIST_H = 6
    STATUS_ROW = 3
    NAV_ROW = 1
    EXPLORER_MARGIN = 8
    PLAYLIST_MARGIN = 6

    # view IDs
    V_CONFIG = 0
    V_LISTEN = 1
    V_EXPLORER = 2
    V_PLAYLIST = 3
    V_HISTORY = 4

    def __init__(self, stdscr) -> None:
        self.stdscr = stdscr
        self.running = True

        self.config = load_config()
        self.current_view = self.V_LISTEN
        self.current_dir = self.config.get("music_dir", os.path.expanduser("~/Music"))
        self.cursor = 0
        self.scroll = 0
        self.entries = _list_dir(self.current_dir)

        self.audio = AudioEngine()
        self.audio.set_volume(self.config.get("volume", 50))

        all_pl, active_name = load_all_playlists()
        self.playlist_data = all_pl
        self.active_name = active_name
        self.playlist_cursor = 0
        self.playlist_scroll = 0

        self.prompt_mode = False
        self.prompt_buf = ""
        self.prompt_label = ""
        self.prompt_callback = None

        self.meta_cache = MetadataCache()
        self.stack = Stack()
        self.show_stack_view = False
        self.stack_cursor = 0
        self.stack_scroll = 0

        self.playlist_filter = ""
        self.playlist_filtered = []
        self.playlist_filter_mode = False

        self.explorer_filter = ""
        self.explorer_filtered = []
        self.explorer_filter_mode = False

        self.show_help = False

        self.goto_mode = False
        self.goto_field = 0
        self.goto_mins = 0
        self.goto_secs = 0

        self.config_cursor = 0
        self.config_scroll = 0
        self.update_available = False
        self.update_check_done = False
        self.update_behind = 0

        self.history: list[dict] = load_history()
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
        self._file_undo = None

        self.kb_keybinding_view = False

        self.awaiting_dest = False
        self._pending_add_path = ""
        self._pending_add_mode: str = "append"

        self._setup_keybindings()
        self._build_config_items()
        self._build_action_handlers()

        self._view_handlers = {
            self.V_LISTEN: handlers.handle_listen,
            self.V_EXPLORER: handlers.handle_explorer,
            self.V_PLAYLIST: handlers.handle_playlist,
            self.V_HISTORY: handlers.handle_history,
            self.V_CONFIG: handlers.handle_config,
        }
        self._view_drawers = {
            self.V_LISTEN: views.draw_listen,
            self.V_EXPLORER: views.draw_explorer,
            self.V_PLAYLIST: views.draw_playlist,
            self.V_HISTORY: views.draw_history,
            self.V_CONFIG: views.draw_config,
        }

        curses.curs_set(0)
        self.stdscr.nodelay(True)
        self.stdscr.keypad(True)
        curses.start_color()
        curses.use_default_colors()
        self._apply_theme()
        self._check_updates()
        self._resume_session()

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
        return self.stack.shuffle

    @shuffle.setter
    def shuffle(self, val: bool):
        self.stack.shuffle = val

    @property
    def repeat(self) -> bool:
        return self.stack.repeat

    @repeat.setter
    def repeat(self, val: bool):
        self.stack.repeat = val

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

    def _apply_updates(self) -> tuple[bool, str]:
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
            "next": lambda: (self._play_next(), None),
            "prev": lambda: (self._play_prev(), None),
            "volume_up": lambda: (self.audio.set_volume(self.audio.volume + 5), None),
            "volume_down": lambda: (self.audio.set_volume(self.audio.volume - 5), None),
            "shuffle": lambda: (setattr(self.stack, 'shuffle', not self.stack.shuffle), None),
            "repeat": lambda: (setattr(self.stack, 'repeat', not self.stack.repeat), None),
            "help": lambda: (setattr(self, 'show_help', not self.show_help), None),
            "sleep_timer": lambda: (self._toggle_sleep_timer(), None),
            "mute": lambda: (self.audio.toggle_mute(), None),
        }

    def _resume_session(self) -> None:
        st = load_state()
        if st.get("playing") and st.get("file") and os.path.isfile(st["file"]):
            self.stack.items = [StackItem(path=st["file"], name=os.path.basename(st["file"]))]
            self.audio.play_file(st["file"])
            pos = st.get("position", 0)
            if pos > 0:
                self.audio.player.set_time(pos)
            self.current_view = self.V_LISTEN

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

    def _add_history(self, path: str) -> None:
        self.history = [h for h in self.history if h.get("path") != path]
        self.history.insert(0, {"name": os.path.basename(path), "path": path, "count": 1})
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
        if self._handle_key_view_switch(key):
            return
        if self.current_view == self.V_CONFIG and self.kb_keybinding_view:
            handlers.handle_keybindings(self, key)
            return

        if self.awaiting_dest:
            self._handle_dest_key(key)
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

    def _handle_dest_key(self, key: int) -> None:
        if key in (27,):
            self.awaiting_dest = False
            self._pending_add_path = ""
            curses.flushinp()
            return
        if key == ord("s"):
            item = StackItem(path=self._pending_add_path,
                             name=os.path.basename(self._pending_add_path))
            if self._pending_add_mode == "append":
                self.stack.append(item)
            elif self._pending_add_mode == "after_current":
                self.stack.insert_after_current(item)
            if self.stack.playhead == 0 and not self.audio.playing:
                self._play_current()
        elif key == ord("p"):
            name = os.path.basename(self._pending_add_path)
            self._push_snapshot()
            if self._pending_add_mode == "after_current":
                pos = self.playlist_cursor + 1 if self.playlist else 0
                self.playlist.insert(pos, (name, self._pending_add_path))
            else:
                self.playlist.append((name, self._pending_add_path))
            handlers._save_playlist(self)
            handlers._confirm(self, f"Añadido a '{self.active_name}'", None)
        else:
            self.awaiting_dest = False
            self._pending_add_path = ""
            curses.flushinp()
            return
        self.awaiting_dest = False
        self._pending_add_path = ""
        curses.flushinp()

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
        if ord("0") <= key <= ord("4"):
            self.current_view = key - ord("0")
            self.cursor = 0
            self.scroll = 0
            self.show_stack_view = False
            self.goto_mode = False
            self.explorer_filter_mode = False
            self.playlist_filter_mode = False
            self.kb_keybinding_view = False
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
        if key in (ord("s"), ord("S")):
            if self.current_view != self.V_PLAYLIST and not self.show_stack_view:
                self.audio.stop()
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
        if key in (ord("+"), ord("k")):
            self.audio.set_volume(self.audio.volume + 5)
            curses.flushinp()
            return True
        if key in (ord("-"), ord("j")):
            self.audio.set_volume(self.audio.volume - 5)
            curses.flushinp()
            return True
        if key == ord("r"):
            self.stack.shuffle = not self.stack.shuffle
            curses.flushinp()
            return True
        if key == ord("R"):
            self.stack.repeat = not self.stack.repeat
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
            save_state(False)
            save_history(self.history)
            self.config["volume"] = self.audio.volume
            save_config(self.config)
            self._save_all_playlists()
            self.audio.player.stop()
            self.audio.close()
            self.running = False
            return True
        if key == 27:
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

    def _clear_stack(self) -> None:
        self.audio.stop()
        self.stack.clear()

    # ── Undo / Redo ──

    def _snapshot_state(self) -> dict:
        return {
            "playlist_data": copy.deepcopy(self.playlist_data),
            "active_name": self.active_name,
            "stack_items": copy.deepcopy(self.stack.items),
            "stack_playhead": self.stack.playhead,
            "stack_shuffle": self.stack.shuffle,
            "stack_repeat": self.stack.repeat,
        }

    def _restore_snapshot(self, snap: dict) -> None:
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
        self._restore_snapshot(self.undo_stack.pop())
        self.playlist_cursor = max(0, min(self.playlist_cursor, len(self.playlist) - 1))

    def _redo(self) -> None:
        if not self.redo_stack:
            return
        self.undo_stack.append(self._snapshot_state())
        self._restore_snapshot(self.redo_stack.pop())
        self.playlist_cursor = max(0, min(self.playlist_cursor, len(self.playlist) - 1))

    def _undo_file_op(self) -> bool:
        if not self._file_undo:
            return False
        info = self._file_undo
        self._file_undo = None
        try:
            if info["type"] == "move":
                shutil.move(info["dest"], info["src"])
            elif info["type"] == "copy":
                if os.path.isfile(info["dest"]):
                    os.remove(info["dest"])
            self.entries = _list_dir(self.current_dir)
        except Exception:
            pass
        return True

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
        if cb and (chr(key).lower() == "s" or key in (ord("\n"), 10, 13)):
            cb()

    # ── Drawing ──

    def _draw(self) -> None:
        try:
            h, w = self.stdscr.getmaxyx()
            self.stdscr.erase()

            if h < 6 or w < 20:
                self.stdscr.addstr(0, 0, f"Terminal muy pequeña ({h}x{w}) — necesito al menos 20x6")
                self.stdscr.refresh()
                return

            needs_cursor = ((self.current_view == self.V_EXPLORER and self.explorer_filter_mode)
                            or (self.current_view == self.V_PLAYLIST and self.playlist_filter_mode)
                            or self.prompt_mode)
            if needs_cursor:
                curses.curs_set(1)

            drawer = self._view_drawers.get(self.current_view)
            if drawer:
                drawer(self, h, w)

            self._draw_status(h, w)
            if self.confirm_mode:
                buf = "  s/Enter  " if not self.confirm_is_info else "  OK  "
                ui.draw_prompt(self.stdscr, h, w, self.confirm_label, buf)
            elif self.prompt_mode:
                ui.draw_prompt(self.stdscr, h, w, self.prompt_label, self.prompt_buf)
            else:
                ui.draw_nav(self.stdscr, h, w)
            if self.awaiting_dest:
                msg = " ¿Destino?  s:stack  |  p:playlist  |  Esc:cancelar "
                if w > len(msg) + 1:
                    try:
                        self.stdscr.addstr(h - 2, (w - len(msg)) // 2, msg, curses.A_REVERSE)
                    except curses.error:
                        pass
            if self.update_available and not self.confirm_mode and not self.prompt_mode and not self.show_help:
                msg = " Nueva actualización disponible "
                if w > len(msg) + 1:
                    try:
                        self.stdscr.addstr(0, w - len(msg), msg, curses.A_REVERSE)
                    except curses.error:
                        pass
            if self.show_help:
                ui.draw_help(self.stdscr, h, w)

            if self.current_view == self.V_EXPLORER and self.explorer_filter_mode:
                y = 3 if self.file_op_mode else 2
                self.stdscr.move(y, 4 + len(self.explorer_filter))
                curses.curs_set(1)
            elif self.current_view == self.V_PLAYLIST and self.playlist_filter_mode:
                self.stdscr.move(2, 4 + len(self.playlist_filter))
                curses.curs_set(1)

            self.stdscr.refresh()
        except curses.error:
            pass

    def _draw_status(self, h: int, w: int) -> None:
        ui.draw_status(self.stdscr, h, w, self.audio, self.audio.playing,
                       self.audio.current_file, self.audio.volume,
                       self.stack.shuffle, self.stack.repeat,
                       self.active_name, self.current_view,
                       self.stack)
