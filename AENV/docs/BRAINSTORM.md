# BRAINSTORM — Features futuros

> Sesión 2025-07-14 — Investigación y planificación de 3 features.

---

## 1. Equalizer (F2) — ELEGIDO PARA IMPLEMENTAR

### API VLC
- `vlc.AudioEqualizer` — wrapper completo
- 10 bandas: 60Hz, 170Hz, 310Hz, 600Hz, 1kHz, 3kHz, 6kHz, 12kHz, 14kHz, 16kHz
- Preamp: -20 a +20 dB
- 18 presets nativos de VLC
- Cambios aplican en tiempo real (sin reiniciar playback)
- `player.set_equalizer(eq)` — NO `audio_set_equalizer` (no existe)
- `player.set_equalizer(None)` — desactivar

### Presets seleccionados (12 + Custom)
| # | Preset | Uso |
|---|--------|-----|
| 0 | Flat | Referencia (todo 0 dB) |
| 1 | Rock | Bass +3, treble +4 |
| 2 | Pop | Mid realzado suave |
| 3 | Classical | Amplio, dinámico |
| 4 | Dance | Bass alto (+6) |
| 5 | Techno | Bass +5, treble +5 |
| 6 | Electronic | Bass +4, mid cortado, treble +6 |
| 7 | Full Bass | Bass máximo |
| 8 | Full Treble | Treble máximo |
| 9 | Headphones | Optimizado auriculares |
| 10 | Live | En vivo |
| 11 | Soft | Suave, sin picos |
| 12 | Custom | Edición manual de 10 bandas + preamp |

### UI propuesta
- **Config tab "Audio"**: toggle ON/OFF + selector de preset
- **Tecla Listen**: `E` toggle rápido
- **Custom mode**: overlay con 10 barras ASCII + preamp, editables con ←/→
- **Persistencia**: config.json (eq_enabled, eq_preset, eq_bands, eq_preamp)
- **Status bar**: mostrar `[EQ]` cuando activo

### Sin dependencias nuevas
VLC ya tiene todo integrado.

---

## 2. Visualizer — PENDIENTE

### Investigación
- VLC **no** expone datos de audio para visualización
- `audio_set_callbacks` mata la salida de audio (no se puede escuchar)
- VLC visual effects (spectrum, scope) renderizan en ventana de video, inaccesibles desde API

### Solución viable
- Capturar audio desde **PulseAudio monitor** con `sounddevice`
- FFT con `numpy` (`np.fft.rfft`)
- Renderizar barras ASCII en curses

### Dependencias nuevas
- `numpy` — FFT
- `sounddevice` — captura de audio (requiere `portaudio`)
- Solo funciona en Linux/PulseAudio

### Complejidad
Media. Proyectos que usan este patrón: TUNA, sahil-music-tui, clidrop.

### Arquitectura propuesta
```
VLC reproduce → PulseAudio sink → Monitor source → sounddevice captura → numpy FFT → curses bars
```

### Pendiente
- Definir número de barras (20-40?)
- Definir estilo (barras verticales, spectrum, VU meter?)
- Decidir si se integra en Listen o como vista separada
- Investigar si funciona en sistemas sin PulseAudio

---

## 3. yt-dlp Web Explorer — PENDIENTE

### Investigación
- `yt-dlp` se puede usar como librería Python (no subprocess)
- Búsqueda: `ytsearch5:query` con `extract_flat=True` → ~2s
- Streaming: extraer URL → pasar a VLC directamente (sin descargar)
- Descarga: `progress_hooks` para barra de progreso curses
- Formatos: audio-only (mp3/m4a), best quality, max resolution

### API principal
```python
import yt_dlp
with yt_dlp.YoutubeDL(opts) as ydl:
    info = ydl.extract_info("ytsearch5:query", download=False)
    # info['entries'] → lista de resultados
    url = entry['url']  # direct stream URL → vlc.MediaPlayer(url)
```

### Dependencias nuevas
- `yt-dlp` (pip)
- `ffmpeg` (sistema, para audio extraction)

### Complejidad
Alta. Feature considerable con nueva vista, búsqueda, streaming, descarga.

### Arquitectura propuesta
```
Nueva vista "Web" (V7)
  → Prompt de búsqueda
  → Lista de resultados (ytsearch)
  → Enter: streaming (URL → VLC) o descarga (con progress bar)
  → Selector de formato (audio-only, best quality)
  → Descarga a ~/Music/ o directorio configurable
```

### Pendiente
- Definir si se integra en tplay o como app separada
- Decidir destino de descargas (¿music_dir? ¿carpeta aparte?)
- Manejo de errores de red
- Cache de búsquedas anteriores
- Soporte para playlists de YouTube
