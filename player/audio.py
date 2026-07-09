import time
import random
import vlc


class AudioEngine:
    def __init__(self):
        self.instance = vlc.Instance("--no-video", "--quiet",
                                      "--msg-level=mpg123=0",
                                      "--no-stderr")
        self.player = self.instance.media_player_new()
        self.playing = False
        self.paused = False
        self.current_file = None
        self.volume = 50
        self.shuffle = False
        self.repeat = False
        self.playlist_idx = -1
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

    def play_playlist_idx(self, idx: int, playlist: list) -> None:
        if idx < 0 or idx >= len(playlist):
            return
        self.playlist_idx = idx
        self.play_file(playlist[idx][1])

    def next(self, playlist: list) -> None:
        if not playlist:
            return
        if self.shuffle:
            nxt = random.randrange(len(playlist))
        else:
            nxt = self.playlist_idx + 1
            if nxt >= len(playlist):
                if self.repeat:
                    nxt = 0
                else:
                    return
        self.play_playlist_idx(nxt, playlist)

    def prev(self, playlist: list) -> None:
        if not playlist:
            return
        prev = self.playlist_idx - 1
        if prev < 0:
            if self.repeat:
                prev = len(playlist) - 1
            else:
                return
        self.play_playlist_idx(prev, playlist)

    def is_ended(self) -> bool:
        return (self.playing and not self.paused
                and self.player.get_state() == vlc.State.Ended)

    def auto_next(self, playlist: list) -> None:
        if not playlist or self.playlist_idx < 0:
            self.playing = False
            self.current_file = None
            return
        if self.shuffle:
            nxt = random.randrange(len(playlist))
        else:
            nxt = self.playlist_idx + 1
            if nxt >= len(playlist):
                if not self.repeat:
                    self.playing = False
                    self.current_file = None
                    return
                nxt = 0
        self.play_playlist_idx(nxt, playlist)

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
            return self.player.get_time()
        except Exception:
            return 0

    def get_length(self) -> int:
        try:
            return self.player.get_length()
        except Exception:
            return 0
