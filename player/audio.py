from __future__ import annotations

import os
import time

import vlc
from .config import CONFIG_DIR

LOG_FILE: str = os.path.join(CONFIG_DIR, "error.log")


class AudioEngine:
    _saved_stderr: int | None
    instance: vlc.Instance
    player: vlc.MediaPlayer
    playing: bool
    paused: bool
    current_file: str | None
    volume: int
    sleep_timer_start: float
    sleep_timer_duration: int
    sleep_timer_active: bool
    sleep_timer_expired: bool
    muted: bool
    _prev_volume: int

    def __init__(self) -> None:
        self._saved_stderr = os.dup(2)
        os.makedirs(CONFIG_DIR, exist_ok=True)
        log_fd: int = os.open(LOG_FILE, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        os.dup2(log_fd, 2)
        os.close(log_fd)

        self.instance = vlc.Instance("--no-video", "--quiet")
        self.player = self.instance.media_player_new()
        self.playing = False
        self.paused = False
        self.current_file = None
        self.volume = 50
        self.sleep_timer_start = 0.0
        self.sleep_timer_duration = 0
        self.sleep_timer_active = False
        self.sleep_timer_expired = False
        self.muted = False
        self._prev_volume = 50

    @property
    def is_playing(self) -> bool:
        return self.playing

    def toggle_play_pause(self) -> None:
        if self.playing:
            if self.paused:
                self.player.play()
                self.paused = False
            else:
                self.player.pause()
                self.paused = True

    def stop(self) -> None:
        self.player.stop()
        self.playing = False
        self.paused = False
        self.current_file = None
        self.sleep_timer_active = False

    def toggle_mute(self) -> None:
        if self.muted:
            self.set_volume(self._prev_volume)
            self.muted = False
        else:
            self._prev_volume = self.volume
            self.set_volume(0)
            self.muted = True

    def set_volume(self, vol: int) -> None:
        self.volume = max(0, min(100, vol))
        self.player.audio_set_volume(self.volume)
        if self.volume > 0:
            self.muted = False

    def play_file(self, path: str) -> None:
        old = self.player.get_media()
        if old:
            old.release()
        media = self.instance.media_new(path)
        self.player.set_media(media)
        self.player.play()
        self.player.audio_set_volume(self.volume)
        self.playing = True
        self.paused = False
        self.current_file = path
        self.sleep_timer_expired = False

    def is_ended(self) -> bool:
        return (self.playing and not self.paused
                and self.player.get_state() == vlc.State.Ended)

    def check_sleep_timer(self) -> None:
        if self.sleep_timer_active:
            elapsed = time.monotonic() - self.sleep_timer_start
            remaining = self.sleep_timer_duration - elapsed
            if remaining <= 0:
                self.sleep_timer_active = False
                self.sleep_timer_expired = True
                self.stop()

    def set_sleep_timer(self, minutes: int) -> None:
        if minutes <= 0:
            return
        self.sleep_timer_duration = minutes * 60
        self.sleep_timer_start = time.monotonic()
        self.sleep_timer_active = True
        self.sleep_timer_expired = False

    def sleep_timer_str(self) -> str:
        if self.sleep_timer_expired:
            return "[◴ FIN]"
        if not self.sleep_timer_active:
            return ""
        elapsed = time.monotonic() - self.sleep_timer_start
        remaining = max(0, int(self.sleep_timer_duration - elapsed))
        m, s = divmod(remaining, 60)
        return f"[◴ {m}:{s:02d}]"

    def get_time(self) -> int:
        try:
            return int(self.player.get_time())
        except Exception:
            return 0

    def get_length(self) -> int:
        try:
            return int(self.player.get_length())
        except Exception:
            return 0

    def close(self) -> None:
        if hasattr(self, '_saved_stderr') and self._saved_stderr is not None:
            os.dup2(self._saved_stderr, 2)
            os.close(self._saved_stderr)
            self._saved_stderr = None
