# STATE — tplay

## Estado actual
- **Version**: v1.5.65
- **Plan activo**: F10 yt-dlp Web Explorer v2 — **COMPLETADO**
- **Bugs abiertos**: 0
- **Docs**: Sincronizados con v1.5.65

## Último commit
- `Fase 5 - code - 1.5.65 - F10: actualizar config.py + ui.py (defaults downloads + help Web)`

## F10 Web Explorer v2 — Resumen
| Fase | Archivo | Estado |
|------|---------|--------|
| 1 | `player/platforms.py` | ✅ |
| 2 | `player/web.py` | ✅ |
| 3 | `player/handlers/webexplorer.py` | ✅ |
| 4 | `player/views.py` | ✅ |
| 5 | `player/config.py` + `player/ui.py` | ✅ |

## Features implementadas
- Registry de 6 plataformas (YouTube, SoundCloud, Vimeo, Dailymotion, Twitch, Niconico)
- Búsqueda con `extract_flat=True` (fix B22)
- Descarga audio (mp3) / video (mp4)
- 3 modos: normal, search, motor
- Gestión de plataformas: add/edit/delete
- Estados en lista: [-] [►] [D] [P] [Q] [✓] [X] [!]
- Cola de descarga (max 3)
- Navegación g/G
- Help tab actualizado

## Pendiente para próxima sesión
- [ ] Testing manual: `tplay → 7 → Tab → YouTube → Tab → "beethoven" → Enter`
- [ ] Fixear bugs que aparezcan
