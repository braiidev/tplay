# CHANGELOG — tplay

## v1.5.59
- fix: Custom EQ — key `custom_bands` guarda estado independiente al salir de Custom, restaura al entrar
- fix: Custom EQ — `r` reset banda actualiza solo esa banda en custom_bands
- fix: Custom EQ — `r` preset limpia custom_bands a [0.0]*10
- fix: Listen handler `E`同步 lógica custom_bands
- fix: B17 — `_skip_disabled` para en PRIMER item válido (no salta de eq_enabled a Preamp)
- fix: B17 — cursor revierte a posición original cuando no hay item accesible
- fix: B16 — `_cycle_eq_preset` guarda/restaura custom_bands al cambiar preset
- feat: Listen hints toggle con `;` — config show_listen_hints (B13)
- fix: Help Listen — sección ECUALIZADOR con e/E (B18)
- fix: Help Lista/Historial/Radio — g/G Inicio/Fin (B19)

## v1.5.57
- fix: Config/Audio bands siempre visibles (no solo Custom) — modo solo lectura para presets non-Custom
- fix: History g/G implementados — ir a inicio/fin de historial

## v1.5.56
- refactor: draw_tab_carousel() helper — reemplaza código duplicado en Help y Config (~30 líneas eliminadas)
- refactor: clamp_scroll() + draw_list_indicators() helpers — reemplaza scroll clamping e indicadores en 6 vistas (~18 líneas eliminadas)

## v1.5.55
- feat: Config/Audio — bandas EQ en modo solo lectura (color texto cuando preset ≠ Custom)
- feat: Config/Audio — hints contextuales por tipo de item (±0.5dB para bandas/preamp, cambiar para choice)

## v1.5.54
- feat: Listen view — metadata centrada (estado, título, artista/álbum)
- feat: Listen view — indicador de volumen visual con barras

## v1.5.53
- feat: draw_box_inline() — box inline para sub-views (Config Audio hints, Help)
- feat: Scroll indicators — ▲/▼ en vistas con scroll

## v1.5.52
- feat: COMPACT_THRESHOLD — vista compacta para terminales pequeñas (≤15 rows)
- feat: Icono pausa ❚❚ en listen view
- feat: Separadores en Config/Audio

## v1.5.50
- feat: EQ refinado — preamp configurable, Custom en Config, teclas E/e

## v1.5.49
- feat: Ecualizador gráfico — VLC API, 10 bandas, presets

## v1.5.48
- fix: symlinks-to-dirs en Explorer

## v1.5.47
- feat: 9 extensiones nuevas (.m4a, .aac, .opus, .weba, .wma, .aiff, .aif, .flv, .wmv)

## v1.5.46
- feat: Explorer read-only fuera del root

## v1.5.45
- feat: AENV setup (migración tracking)
