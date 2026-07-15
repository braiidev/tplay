# STATE — tplay

## Estado actual
- **Version**: v1.5.71
- **Plan activo**: F10 yt-dlp Web Explorer v2 — **COMPLETADO**
- **Bugs abiertos**: 0
- **Docs**: Sincronizados con v1.5.71

## Último commit
- `fix - 1.5.71 - yt-dlp noprogress fix, cancel/pause descargas, [P] pausa [PP] postprocessing`

## Bugs fixeados post-implementación
- B22: abr None comparison → search vacío
- B23: prompt desaparece al buscar
- B24: sin feedback visual de carga
- B25: download bloqueante + nombre incorrecto + Explorer no refresca
- B26: download config no permite cambiar valores
- B27: estado play persiste indebidamente
- B28: toast tapa status bar
- B29: quality options incompletas
- B30: q cierra app + aesthetic incorrecta
- B31: yt-dlp corrompe curses (primera approx)
- B32: toast borra borde inferior del box
- B33: yt-dlp stdout leak (raíz real de B31) — progress=False
- B34: _get_download_url quality_map incompleto
- B35: _config_int_inc/dec no maneja online_download_max

## Pendiente para próxima sesión
- [ ] #4: Download history (trackear descargas en downloads.json)
- [ ] #5: Stream replay (persistir info de streams)
- [ ] #6: Cache management (limpiar preloads)
