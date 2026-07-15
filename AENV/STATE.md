# STATE — tplay

## Estado actual
- **Version**: v1.5.66
- **Plan activo**: F10 yt-dlp Web Explorer v2 — **COMPLETADO**
- **Bugs abiertos**: 0
- **Docs**: Sincronizados con v1.5.66

## Último commit
- `fix - 1.5.66 - B25: download async + progress, B24: loading spinner, B23: prompt persistence`

## F10 Web Explorer v2 — Resumen
| Fase | Archivo | Estado |
|------|---------|--------|
| 1 | `player/platforms.py` | ✅ |
| 2 | `player/web.py` | ✅ |
| 3 | `player/handlers/webexplorer.py` | ✅ |
| 4 | `player/views.py` | ✅ |
| 5 | `player/config.py` + `player/ui.py` | ✅ |
| 6 | Testing + bugs | ✅ |

## Bugs fixeados post-implementación
- B22: abr None comparison → search vacío
- B23: prompt desaparece al buscar
- B24: sin feedback visual de carga
- B25: download bloqueante + nombre incorrecto + Explorer no refresca

## Features implementadas
- Registry de 6 plataformas (YouTube, SoundCloud, Vimeo, Dailymotion, Twitch, Niconico)
- Búsqueda con `extract_flat=True`
- Descarga audio (mp3) / video (mp4) con progress %
- Download async (thread daemon)
- Explorer refresh post-descarga
- 3 modos: normal, search, motor
- Gestión de plataformas: add/edit/delete
- Estados en lista: [-] [►] [D] [P] [Q] [✓] [X] [!] [##%]
- Cola de descarga (max 3)
- Navegación g/G
- Loading spinner en búsqueda
- Help tab actualizado
