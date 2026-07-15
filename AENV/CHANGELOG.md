# CHANGELOG — tplay

## v1.5.70
- fix: B33 — yt-dlp progress=False + eliminadas opciones falsas stdout/stddev (corrompía curses)
- fix: B34 — _get_download_url quality_map: worst/144p/240p
- fix: B35 — _config_int_inc/dec: online_download_max ahora funcional
- fix: thread safety — bounds check en progress callback + completion handler

## v1.5.69
- fix: B32 — toast reposicionado a h-2 (borde inferior del box)

## v1.5.68
- fix: B31 — yt-dlp output redirect a /dev/null (no corrompe curses)
- fix: B30 — download config: Esc cancela, aesthetic `[val] ←→`
- fix: B29 — quality options: worst,144p,240p,480p,720p,1080p,best
- feat: config tab "Sistema" — settings de descarga (formato, calidad, máx)

## v1.5.67
- fix: B26 — download config cíclico (←→/hl para format y quality)
- fix: B27 — estado play preciso con web_playing_idx
- fix: B28 — toast reposicionado arriba de status bar

## v1.5.66
- fix: B25 — download no bloqueante (thread + progress % en lista)
- fix: B25 — nombre archivo usa título (page URL en vez de stream URL)
- fix: B25 — Explorer refresca post-descarga
- fix: B24 — feedback visual de carga en búsqueda ("Buscando..." blink)
- fix: B23 — prompt persiste query post-búsqueda

## v1.5.65
- feat: config.py — defaults downloads (platform, format, quality, stream, max)
- feat: ui.py — help tab Web actualizado con todas las teclas nuevas

## v1.5.64
- feat: views.py — draw_web() reescrito con motor+prompt+divider+lista
- feat: views.py — draw_motor_editor() y draw_download_config()
- feat: views.py — estados en lista: [-] [►] [D] [P] [Q] [✓] [X] [!]

## v1.5.63
- feat: webexplorer.py — 3 modos (normal/search/motor)
- feat: webexplorer.py — gestión de plataformas (add/edit/delete)
- feat: webexplorer.py — descarga directa (D) y con config (d)
- feat: webexplorer.py — cola de descarga (max 3)
- feat: app.py — nuevos estados web

## v1.5.62
- fix: B22 — search() con extract_flat=True retorna resultados reales
- feat: web.py — download() para audio (mp3) / video (mp4)
- feat: web.py — WebResult.download_url

## v1.5.61
- feat: platforms.py — Platform dataclass + 6 defaults
- feat: platforms.py — load/save/get_search_prefix/increment_downloads

## v1.5.59
- fix: Custom EQ — key `custom_bands` guarda estado independiente
- refactor: eliminado `r` reset de Config/Audio
- feat: Listen hints toggle con `;`

## v1.5.57
- fix: Config/Audio bands siempre visibles
- fix: History g/G implementados

## v1.5.56
- refactor: draw_tab_carousel() helper
- refactor: clamp_scroll() + draw_list_indicators() helpers

## v1.5.55
- feat: Config/Audio — bandas EQ en modo solo lectura
- feat: Config/Audio — hints contextuales

## v1.5.54
- feat: Listen view — metadata centrada
- feat: Listen view — indicador de volumen visual

## v1.5.53
- feat: draw_box_inline() — box inline para sub-views
- feat: Scroll indicators — ▲/▼ en vistas con scroll

## v1.5.52
- feat: COMPACT_THRESHOLD — vista compacta
- feat: Icono pausa ❚❚ en listen view
- feat: Separadores en Config/Audio

## v1.5.50
- feat: EQ refinado — preamp configurable, Custom en Config

## v1.5.49
- feat: Ecualizador gráfico — VLC API, 10 bandas, presets

## v1.5.48
- fix: symlinks-to-dirs en Explorer

## v1.5.47
- feat: 9 extensiones nuevas

## v1.5.46
- feat: Explorer read-only fuera del root

## v1.5.45
- feat: AENV setup
