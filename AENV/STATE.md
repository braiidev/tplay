# STATE — tplay

## Estado actual
- **Version**: v1.5.79
- **Plan activo**: F10 yt-dlp Web Explorer v2 — **DownloadManager COMPLETO**
- **Bugs abiertos**: 0
- **Docs**: Sincronizados con v1.5.79

## Último commit
- `fix - 1.5.79 - B60: q exit bug — count only active downloads + reset counter after 5s`

## Resumen v1.5.75→v1.5.79
| Versión | Cambio |
|---------|--------|
| 1.5.75 | Migración Python API → subprocess (yt-dlp bot detection fix) |
| 1.5.76 | B55-B58: pause/resume fix, vista7 slowness, temp .part cleanup |
| 1.5.77 | B59: pause/resume restart — `--continue` flag |
| 1.5.78 | `DownloadManager` class: worker loop, cola, concurrencia, SIGSTOP/SIGCONT |
| 1.5.79 | B60: Integración completa DownloadManager + YouTube bot detection (`--js-runtime node` + `online_cookies` config) |

## Pendiente para próxima sesión
- [ ] #4: Download history (trackear descargas en downloads.json)
- [ ] #5: Stream replay (persistir info de streams)
- [ ] #6: Cache management (limpiar preloads)
