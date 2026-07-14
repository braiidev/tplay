# CHANGELOG — tplay

## v1.5.51
- fix: alineación visual de labels en Config/Audio — todos los labels de bandas EQ padeados a 6 chars, colon/values/barras perfectamente alineados

## v1.5.50
- refactor: EQ refinado — preamp configurable todos los presets, Custom en Config/Audio (no overlay), teclas E/e reasignadas, preamp default +12dB
- feat: barras visuales EQ en Config/Audio (40 chars full, 4 chars compact)
- fix: r resetea bandas/preamp/preset en Config, cursor no se resetea al cambiar preset

## v1.5.49
- feat: F2 ecualizador gráfico — 10 bandas, preamp, 16 presets, modo Custom, toggle `E`, persistencia session

## v1.5.48
- fix: Explorer no ve symlinks-to-dirs — follow_symlinks=True en scandir (regresión de P1)

## v1.5.47
- feat: 9 extensiones nuevas — .m4a .aac .opus .weba .wma .aiff .aif (audio) + .flv .wmv (video)

## v1.5.46
- feat: Explorer read-only fuera del directorio raíz — bloqueo de ops de escritura + indicador [RO]

## v1.5.45
- fix: meta_edit editing — h/l insertan chars en vez de mover cursor

## v1.5.44
- feat: full-row cursor highlight + Help tab bar inside marco

## v1.5.43
- fix: Playlist carousel simplificado ◀[name]▶ + Help scroll clamp corregido

## v1.5.42
- fix: [] navegan pestañas en todas las vistas — playlist ya no usa h/l para tabs

## v1.5.41
- feat: Playlist + Config carousel tabs — cyclic, ◀[name]▶ / [prev|current|next]

## v1.5.40
- feat: Help carousel tabs + hints NAV consistentes en todas las vistas

## v1.5.39
- fix: Radio REVERSE gap, Pila hints con NAV color

## v1.5.38
- feat: 5to par de colores OVERLAY — redistribución UI + COLOR_SPEC.md

## v1.5.37
- refactor: estandarización de rows — margenes, metadata, duración, Radio [R]

## v1.5.36
- style: E1-E3 — [R] icon para streams, controles Listen responsive, time separator '/'

## v1.5.35
- refactor: P1-P3 — os.scandir(), scroll clamping redundante, playlist CONFIG_DIR import

## v1.5.34
- fix: U2-U3 — undo/redo archivos toast + metadata save toast y permanencia en editor

## v1.5.33
- fix: B10-B11 — explorer back-nav en directorios vacíos + status bar row descontada en handlers

## v1.5.27
- feat: f toggle favoritos global (Listen, Stack, Explorer, Playlist, History, Radio, Favoritos)

## v1.5.26
- feat: F5 multi-select Explorer + F6 Favoritos (vista 6, f/F, d, persistencia JSON)

## v1.5.25
- feat: F2 speed control (w/W ±0.25x, 0.25x–4.0x, persistente en state.json)

## v1.5.23
- fix: Stack d con confirmación, audio para al último item, eliminar helper [o] obsoleto

## v1.5.22
- feat: ←/→ para mover cursor en Explorer filter, Playlist filter y Meta editor

## v1.5.21
- feat: filtros con cursor visual, hjk global→Listen, s/S consistente, radio e/E cyclic, dir picker, KEYBINDINGS.md

## v1.5.12
- feat: F4 import M3U/PLS desde Explorer

## v1.5.10
- fix: C4 _restart_app ruta incorrecta tras A4 → app._repo_dir

## v1.5.8
- feat: U2-U5 (update async, toast, s/y confirm, sleep timer reset)

## v1.5.7
- feat: U1 PgDn/PgUp g/G en Playlist

## v1.5.6
- refactor: A4 handlers.py → package + A5/A6

## v1.5.5
- fix: A1 stderr→error.log + A3 lazy mkdir

## v1.5.4
- fix: A2 KEY_RESIZE resize handling

## v1.5.3
- feat: B3/B4 stack persistente

## v1.5.2
- fix: B2 undo unificado
