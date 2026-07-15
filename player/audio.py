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
    rate: float
    _eq: vlc.AudioEqualizer | None
    _eq_enabled: bool

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
        self.rate = 1.0
        self._eq = None
        self._eq_enabled = False
        self._cached_time: int = -1
        self._cached_length: int = -1

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
        self.rate = 1.0
        self._cached_time = -1
        self._cached_length = -1

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

    def set_rate(self, rate: float) -> None:
        self.rate = max(0.25, min(4.0, rate))
        self.player.set_rate(self.rate)

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
        self._cached_time = -1
        self._cached_length = -1
        self.reapply_equalizer()
        self.player.set_rate(self.rate)

    def is_ended(self) -> bool:
        return (self.playing and not self.paused
                and self.player.get_state() == vlc.State.Ended)

    def refresh_time_cache(self) -> None:
        """Cachea time/length una vez por frame (evita locks de VLC por acceso)."""
        try:
            self._cached_time = int(self.player.get_time())
            self._cached_length = int(self.player.get_length())
        except Exception:
            self._cached_time = 0
            self._cached_length = 0

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
        if self._cached_time >= 0:
            return self._cached_time
        try:
            return int(self.player.get_time())
        except Exception:
            return 0

    def get_length(self) -> int:
        if self._cached_length >= 0:
            return self._cached_length
        try:
            return int(self.player.get_length())
        except Exception:
            return 0

    def set_equalizer(self, bands: list[float], preamp: float) -> None:
        """Crear y aplicar EQ con bandas personalizadas."""
        self._eq = vlc.AudioEqualizer()
        for i, gain in enumerate(bands[:10]):
            self._eq.set_amp_at_index(gain, i)
        self._eq.set_preamp(preamp)
        self.player.set_equalizer(self._eq)
        self._eq_enabled = True

    def apply_preset(self, preset_index: int) -> None:
        """Aplicar preset nativo de VLC."""
        count = vlc.libvlc_audio_equalizer_get_preset_count()
        if 0 <= preset_index < count:
            self._eq = vlc.libvlc_audio_equalizer_new_from_preset(preset_index)
            self.player.set_equalizer(self._eq)
            self._eq_enabled = True

    def disable_equalizer(self) -> None:
        """Desactivar EQ."""
        self.player.set_equalizer(None)
        self._eq = None
        self._eq_enabled = False

    def get_equalizer_info(self) -> dict[str, object]:
        """Retornar info actual del EQ (bands, preamp, enabled)."""
        bands: list[float] = []
        preamp: float = 0.0
        if self._eq:
            bands = [self._eq.get_amp_at_index(i) for i in range(10)]
            preamp = self._eq.get_preamp()
        return {"bands": bands, "preamp": preamp, "enabled": self._eq_enabled}

    def reapply_equalizer(self) -> None:
        """Re-aplicar EQ actual (útil después de play_file)."""
        if self._eq_enabled and self._eq:
            self.player.set_equalizer(self._eq)

    def close(self) -> None:
        if self.player:
            self.player.stop()
            self.player.release()
            self.player = None
        if self.instance:
            self.instance.release()
            self.instance = None
        if hasattr(self, '_saved_stderr') and self._saved_stderr is not None:
            os.dup2(self._saved_stderr, 2)
            os.close(self._saved_stderr)
            self._saved_stderr = None
