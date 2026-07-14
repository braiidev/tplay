# BUGS — tplay

## Activos
_No hay bugs activos conocidos._

## Resueltos
| ID | Descripción | Solución |
|----|-------------|----------|
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
