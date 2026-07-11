# TODO — tplay

## Bugs

- [x] **B1** — History `count` siempre es 1 (`app.py:432-437`) — `_add_history` re-inserta con `count: 1` sin preservar el count anterior
- [x] **B2** — Playlist Enter siempre arranca desde índice 0 (`handlers/playlist.py:207-214`) — Debería usar `playlist_cursor`
- [x] **B3** — Favorites `a/A` bypass `Stack.append` (`handlers/favorites.py:54-64`) — Manipula lista directamente, rompe playhead cuando pila vacía
- [x] **B4** — `_play_folder` y `_play_marked` sin snapshot (`handlers/explorer.py:243-271`) — Reemplazan pila sin `_push_snapshot()`
- [x] **B5** — `metadata.py` IndexError silenciado (`metadata.py:23-28`) — Tag malformado destruye toda la entrada de cache
- [x] **B6** — `playlist` property valida y loguea en cada acceso (`app.py:194-201`) — Multi-acceso por frame, genera salida en error.log
- [x] **B7** — `_handle_dialog_key` confirm: `chr(key)` para teclas no-imprimibles (`app.py:521`) — Confuso, mejor verificar explícitamente
- [ ] **B8** — ~~`_apply_updates` no verifica cambios locales antes de pull~~ — REVERTIDO: usuario final no toca código, reset hard es correcto
- [x] **B9** — Config view scroll clamp inconsistente (`handlers/config_view.py:67` vs `views.py:582`)
- [x] **B10** — Explorer vacío no permite navegar atrás (`handlers/explorer.py:26`) — `if not app.entries: return` bloquea h/←/Backspace/~/F5
- [x] **B11** — Status bar row no descontada en handlers — `list_h` usa `h - 4` sin Account para status bar en `h-3`

## UX

- [x] **U1** — Toast deshabilitado en compacto (`app.py:957-958`) — Sin feedback visual en terminales chicas
- [x] **U2** — Undo/redo archivos falla silenciosamente (`app.py:824-848`) — Toast con razón del error
- [x] **U3** — Metadata save falla silenciosamente (`app.py:898-908`) — Toast + permanece en editor
- [x] **U4** — Sesión solo se guarda al salir (`app.py:726-734`) — REVERTIDO: usuario final no modifica código local
- [x] **U5** — `_apply_updates` reset hard silencioso (`app.py:296-298`) — REVERTIDO: usuario final no modifica código local

## Rendimiento / Estructura

- [x] **P1** — `os.listdir` + stat innecesario (`file_utils.py:19-36`) — Reemplazado por `os.scandir()`
- [x] **P2** — Scroll clamping redundante 13x por frame en `_draw()` (`app.py:917-931`) — Eliminado, handlers ya clampean
- [x] **P3** — `playlist.py` hardcodea CONFIG_DIR (`playlist.py:7`) — Importado de config

## Estética

- [x] **E1** — Radio emoji `📻` puede no renderizar (`views.py:819`) — Cambiado a `[R]`
- [x] **E2** — Barra controles Listen ancho fijo (`views.py:176-204`) — Responsive con mínimos + distribución de espacio
- [x] **E3** — Indicador `cur_s - dur_s` usa guion que parece resta (`ui.py:129`) — Cambiado a ` / `
