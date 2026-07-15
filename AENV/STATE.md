# STATE — tplay

## Estado actual
- **Version**: v1.5.78
- **Plan activo**: F10 yt-dlp Web Explorer v2 — **EN PROCESO: DownloadManager refactor**
- **Bugs abiertos**: 1 (B60: cola de descargas no funciona correctamente)
- **Docs**: Sincronizados con v1.5.78

## Último commit
- `feat - 1.5.78 - web.py: DownloadManager class (INCOMPLETO — ver detalle abajo)`

## Estado del refactor DownloadManager (v1.5.78)
- ✅ `DownloadState` enum implementado (QUEUED, DOWNLOADING, PAUSED, COMPLETED, FAILED, STOPPED)
- ✅ `DownloadItem` dataclass implementado (id, url, title, state, progress, _process, _cancel_event)
- ✅ `DownloadManager` class implementado con worker loop, cola, concurrencia limitada
- ✅ `pause_item()` usa SIGSTOP/SIGCONT (Linux)
- ✅ `stop_item()` mata proceso y limpia .part
- ✅ `get_download_manager()` singleton
- ⏳ **PENDIENTE**: Actualizar `webexplorer.py` para usar DownloadManager
- ⏳ **PENDIENTE**: Actualizar `app.py` (remover variables viejas, agregar dm)
- ⏳ **PENDIENTE**: Actualizar `views.py` (leer estado del DownloadManager)
- ⏳ **PENDIENTE**: Test de cola con 3+ descargas

## Bugs fixeados post-implementación
- B22-B59: ver historial
- B60: Cola de descargas — todos los items comparten estado del primero, [Q] nunca se ejecuta, cancel/pause afecta todos

## Pendiente para próxima sesión
- [ ] Completar integración de DownloadManager en handler/views
- [ ] Test cola con 3+ descargas
- [ ] #4: Download history (trackear descargas en downloads.json)
- [ ] #5: Stream replay (persistir info de streams)
- [ ] #6: Cache management (limpiar preloads)
