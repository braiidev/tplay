# BUGS — tplay

## Activos
_(ninguno)_

## Resueltos (recientes)
- **403 Forbidden en todas las descargas YouTube** — causa externa: yt-dlp 2026.7.4 desactualizado vs cambios server-side de YouTube (issues upstream #17395/#17404, experimentos PO Token). Fix: actualizar a 2026.8.19 + `--rm-cache-dir`. Prevención: auto-update al inicio (v1.8.0). v1.8.0
- **ord("Enter") crash** — download_history.py, `ord()` en string de 5 chars. Fix: `key in (10, 13)`. v1.7.1
- **[ExtractAudio] file_path** — yt-dlp renombra .webm→.mp3 pero filename no se actualizaba. Fix: parsear `[ExtractAudio] Destination:`. v1.7.1
- **Download history cursor color** — usaba `PAIR_NAV` en vez de `destacar|REVERSE`. Fix: consistente con resto. v1.7.1
- **<d> sin confirmar** — re-download ejecutaba directo. Fix: `_confirm` dialog. v1.7.1

## Resueltos (legacy)
Ver historial de versiones anteriores (v1.5.75-1.6.7).
