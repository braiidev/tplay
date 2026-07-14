# ONLINE — tplay

> Features de streaming y descarga online via yt-dlp.

## Dependencias
- **yt-dlp** (pip) — librería Python para extracción de audio/video
- **ffmpeg** (sistema) — solo para Fase 2 (descarga con conversión)
- Sin ffmpeg en Fase 1 (streaming puro)

## Arquitectura

```
Vista V7 "Web"
  → Prompt de búsqueda (estilo filter mode)
  → yt-dlp.extract_info("ytsearch5:query", download=False)
  → Lista de resultados (título, duración, canal, URL)
  → Enter → Streaming: URL → VLC MediaPlayer
  → Return a Listen con stream activo
```

## Datos

### WebResult (dataclass)
```python
@dataclass
class WebResult:
    title: str          # Título del video
    url: str            # URL de streaming (directa a VLC)
    duration: int       # Duración en segundos
    channel: str        # Nombre del canal
    webpage_url: str    # URL original de YouTube
    platform: str       # "youtube", "dailymotion", etc.
```

### Platform Registry
```python
# Lazy loading — se agrega plataforma al detectar
PLATFORMS: dict[str, str] = {
    "youtube": "YouTube",
    "dailymotion": "Dailymotion",
    "soundcloud": "SoundCloud",
    # Se expande automáticamente
}
```

## Config (pestaña "Online")

### Defaults
```python
"online_max_results": 5,        # Cantidad de resultados por búsqueda
"online_audio_quality": "128",  # Calidad de descarga (kbps) — Fase 2
"online_search_history": [],    # Últimas 10 búsquedas
```

### Config tab Online (Fase 2)
| Key | Tipo | Default | Descripción |
|-----|------|---------|-------------|
| `online_max_results` | int | 5 | Resultados por búsqueda (1-20) |
| `online_audio_quality` | str | "128" | Calidad descarga: 128/192/320 |
| `online_download_dir` | str | music_dir | Directorio de descargas |
| `online_search_history` | list | [] | Historial de búsquedas (max 10) |

## Flujo de búsqueda

```
1. Usuario presiona 7 → V_WEB
2. Prompt: "Buscar: " (cursor parpadeando)
3. Usuario escribe query
4. Enter → yt-dlp extrae info (~2s)
   - extract_info("ytsearch5:query", download=False)
   - Para cada entry: extraer stream URL
   - Si no hay URL directa, buscar mejor formato de audio
5. Lista de resultados aparece
6. j/k navegar, Enter reproduce
```

## Flujo de streaming

```
1. Enter en resultado → _play_web_result()
2. StackItem(path=stream_url, name=title)
3. app.stack.items = [item]
4. app.audio.play_file(stream_url)
5. VLC reproduce stream HTTP directamente
6. Cambia a V_LISTEN
```

## Errores manejados

| Error | Mensaje | Acción |
|-------|---------|--------|
| yt-dlp no instalado | "Instalar: pip install yt-dlp" | Toast |
| Sin resultados | "Sin resultados: query" | Toast |
| Error de red | "Error de red — verificar conexión" | Toast |
| URL stream inválida | VLC maneja internamente | Fallback |

## Fases de implementación

### Fase 1: Streaming (MVP)
- [ ] 1.1 Wrapper `player/web.py`
- [ ] 1.2 Handler `player/handlers/webexplorer.py`
- [ ] 1.3 Drawer `draw_web()` en `views.py`
- [ ] 1.4 Integración `app.py` (V_WEB, dispatch)
- [ ] 1.5 Nav bar + Help tab en `ui.py`
- [ ] 1.6 Config defaults en `config.py`
- [ ] 1.7 Historial de búsquedas

### Fase 2: Descarga
- [ ] 2.1 Key `D` en Listen para descargar
- [ ] 2.2 Prompt de opciones (formato, calidad)
- [ ] 2.3 Progress bar curses
- [ ] 2.4 Pestaña Config "Online"
- [ ] 2.5 Guardar en music_dir

### Fase 3: Multi-plataforma
- [ ] 3.1 Detectar plataforma desde URL
- [ ] 3.2 Soporte Dailymotion, SoundCloud
- [ ] 3.3 Platform registry lazy
- [ ] 3.4 UI indicador de plataforma

## Plataformas soportadas (yt-dlp)

| Plataforma | Dominio | Estado |
|------------|---------|--------|
| YouTube | youtube.com, youtu.be | MVP |
| Dailymotion | dailymotion.com | Fase 3 |
| SoundCloud | soundcloud.com | Fase 3 |
| Vimeo | vimeo.com | Fase 3 |
| Twitch | twitch.tv | Fase 3 |
| Bandcamp | bandcamp.com | Fase 3 |
| +900 más | varías | yt-dlp nativo |
