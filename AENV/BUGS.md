# BUGS — tplay

## Activos
| ID | Descripción | Archivos afectados | Solución sugerida |
|----|-------------|--------------------|--------------------|

## Resueltos
| ID | Descripción | Solución |
|----|-------------|----------|
| B13 | Listen hints no se pueden ocultar | Config `show_listen_hints` + toggle con `;` |
| B16 | Custom EQ no se guarda — bands se sobreescriben al cambiar preset | Key `custom_bands` en config; guarda al salir de Custom, restaura al entrar |
| B17 | Config/Audio cursor navega bands en non-Custom | `_skip_disabled` para en PRIMER item válido; guards en RIGHT/LEFT para eq_band |
| B18 | Help tab Listen: no muestra hints de EQ (`e`/`E`) | Agregada sección ECUALIZADOR a HELP_TABS[1] con `e`/`E` |
| B19 | Help tabs Lista/Historial/Radio: no muestran hints de `g`/`G` | Agregados `g/G Inicio/Fin` a tabs Lista, Historial, Radio |
| B14 | Config/Audio bands no visibles para presets non-Custom | `_build_config_tabs()` siempre agrega bands (no solo Custom) |
| B15 | History g/G no implementado | Agregados handlers `g` (inicio) y `G` (fin) en history.py |
| B12 | Explorer no ve symlinks-to-dirs (ej: ~/Music) | `follow_symlinks=True` en scandir |
| B1 | History `count` siempre es 1 | Preserva/incrementa count existente |
| B2 | Playlist Enter siempre arranca desde índice 0 | Usa `playlist_cursor` |
| B3 | Favorites `a/A` bypass `Stack.append` | Usa `stack.append`/`insert_after_current` |
| B4 | `_play_folder`/`_play_marked` sin snapshot | Llaman `_push_snapshot()` |
| B5 | `metadata.py` IndexError silenciado | `_safe_tag()` helper |
| B6 | `playlist` property valida y loguea en cada acceso | Simplificada sin validación per-access |
| B7 | `_handle_dialog_key` confirm: `chr(key)` para teclas no-imprimibles | Verificación explícita de s/S/y/Y |
| B8 | `_apply_updates` no verifica cambios locales | REVERTIDO — end users no tienen local changes |
| B9 | Config view scroll clamp inconsistente | `h-5 if h<16 else h-6` consistente |
| B10 | Explorer vacío no permite navegar atrás | Back-nav antes de `if not entries` |
| B11 | Status bar row no descontada en handlers | `list_h` usa `h - 4` con account para status bar |
