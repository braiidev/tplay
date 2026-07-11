# KEYBINDINGS.md — Mapa completo de teclas

> Fuente de verdad para el sistema de keybindings de tplay.
> Cada tecla hace **UNA sola cosa** por vista.

---

## 1. Arquitectura de dispatch

```
tecla → Help overlay? → Dir picker? → Modo específico? → Switch vista? → Global → Vista
```

- **Global** (`_handle_key_global`): solo Space, S, n/b, +/-, q, Esc, 0-6, ?/F1
- **Vista** (`handle_*`): todo lo demás
- Si global matchea, la vista **no recibe** la tecla

---

## 2. Capa Global (siempre funciona)

| Tecla      | Acción                | Notas                                    |
| ---------- | --------------------- | ---------------------------------------- |
| `Space`    | Play / Pause          |                                          |
| `S`        | Stop                  | Solo mayúscula                           |
| `n`        | Siguiente track       |                                          |
| `b`        | Anterior track        |                                          |
| `+`        | Volumen +5            |                                          |
| `-`        | Volumen -5            |                                          |
| `0`        | Vista Config          |                                          |
| `1`        | Vista Listen          |                                          |
| `2`        | Vista Explorer        |                                          |
| `3`        | Vista Playlist        |                                          |
| `4`        | Vista History         |                                          |
| `5`        | Vista Radio           |                                          |
| `6`        | Vista Favoritos       |                                          |
| `?` / `F1` | Abrir/cerrar ayuda    |                                          |
| `q`        | Salir (guarda todo)   |                                          |
| `Esc`      | Cerrar overlay actual | Help, Stack, Goto, KB editor, Dir picker |

---

## 3. Capa Listen (vista 1)

### Vista principal

| Tecla     | Acción                      |
| --------- | --------------------------- |
| `h` / `←` | Seek -5s                    |
| `l` / `→` | Seek +5s                    |
| `j`       | Volumen -5                  |
| `k`       | Volumen +5                  |
| `r`       | Shuffle toggle (ON/OFF)     |
| `R`       | Repeat toggle (ON/OFF)      |
| `t`       | Sleep timer toggle          |
| `T`       | Sleep timer config (prompt) |
| `m`       | Mute toggle                 |
| `g`       | Goto (ir a tiempo)          |
| `Tab`     | Abrir Stack View            |
| `I`       | Editor de tags ID3          |
| `f`       | Añadir/quitar a favoritos   |
| `W`       | -0.25 speed                 |
| `w`       | +0.25 speed                 |

### Stack View (sub-modo de Listen)

| Tecla              | Acción                         |
| ------------------ | ------------------------------ |
| `hjkl` / `flechas` | Navegar items                  |
| `Enter`            | Reproducir item cursor         |
| `r`                | Ciclar modo item (Normal→1x→∞) |
| `d`                | Eliminar item (confirmación)   |
| `x`                | Limpiar todo el Stack          |
| `s`                | Guardar Stack como playlist    |
| `X`                | Exportar Stack como M3U        |
| `J` / `K`          | Reordenar (abajo/arriba)       |
| `u` / `U`          | Undo / Redo                    |
| `g` / `G`          | Inicio / Fin                   |
| `PgDn` / `PgUp`    | Página abajo/arriba            |
| `Tab` / `Esc`      | Cerrar Stack View              |

### Goto (sub-modo de Listen)

| Tecla     | Acción                        |
| --------- | ----------------------------- |
| `←` / `→` | Seleccionar campo (min/seg)   |
| `↑` / `↓` | Incrementar/decrementar valor |
| `Enter`   | Saltar a tiempo               |
| `Esc`     | Cancelar                      |

---

## 4. Capa Explorer (vista 2)

| Tecla                   | Acción                                                   |
| ----------------------- | -------------------------------------------------------- |
| `h` / `←` / `Backspace` | Directorio padre                                         |
| `l` / `→` / `Enter`     | Entrar directorio / Reproducir archivo / Cargar marcados |
| `Tab`                   | Marcar/desmarcar archivo (multi-select)                  |
| `j` / `k` / `↑↓`        | Cursor arriba/abajo                                      |
| `~`                     | Ir a home                                                |
| `g` / `G`               | Inicio / Fin                                             |
| `PgDn` / `PgUp`         | Página abajo/arriba                                      |
| `F5`                    | Refrescar directorio                                     |
| `/`                     | Filtro inline                                            |
| `a`                     | Añadir a pila (final)                                    |
| `A`                     | Añadir a pila (tras playhead)                            |
| `C`                     | Copiar archivo/dir                                       |
| `V`                     | Mover archivo/dir                                        |
| `E`                     | Renombrar archivo/dir                                    |
| `I`                     | Editar tags ID3                                          |
| `d`                     | Eliminar archivo (confirmación)                          |
| `M`                     | Crear directorio                                         |
| `P`                     | Reproducar carpeta completa                              |
| `f`                     | Añadir archivo a favoritos                               |
| `F`                     | Abrir vista Favoritos                                    |
| `u` / `U`               | Undo / Redo                                              |

---

## 5. Capa Playlist (vista 3)

| Tecla            | Acción                        |
| ---------------- | ----------------------------- |
| `[` / `]`        | Playlist anterior / siguiente |
| `j` / `k` / `↑↓` | Cursor arriba/abajo           |
| `g` / `G`        | Inicio / Fin                  |
| `PgDn` / `PgUp`  | Página abajo/arriba           |
| `Enter`          | Reproducir playlist           |
| `d`              | Eliminar item de la lista     |
| `x`              | Limpiar toda la lista         |
| `E`              | Renombrar item en la lista    |
| `R`              | Renombrar playlist            |
| `c`              | Crear nueva playlist          |
| `D`              | Eliminar playlist             |
| `J` / `K`        | Reordenar item (abajo/arriba) |
| `s`              | Guardar playlist              |
| `X`              | Exportar como M3U             |
| `I`              | Editar tags ID3               |
| `u` / `U`        | Undo / Redo                   |
| `/`              | Filtro inline                 |

---

## 6. Capa History (vista 4)

| Tecla            | Acción                        |
| ---------------- | ----------------------------- |
| `j` / `k` / `↑↓` | Cursor arriba/abajo           |
| `g` / `G`        | Inicio / Fin                  |
| `Enter`          | Reproducir archivo / radio    |
| `d`              | Eliminar entrada              |
| `x`              | Limpiar historial             |
| `a`              | Añadir a pila (final)         |
| `A`              | Añadir a pila (tras playhead) |
| `I`              | Editar tags ID3               |
| `Esc`            | Volver a Listen               |

---

## 7. Capa Radio (vista 5)

| Tecla            | Acción                            |
| ---------------- | --------------------------------- |
| `j` / `k` / `↑↓` | Cursor arriba/abajo               |
| `g` / `G`        | Inicio / Fin                      |
| `PgDn` / `PgUp`  | Página abajo/arriba               |
| `Enter`          | Reproducir radio                  |
| `a`              | Agregar radio (prompt nombre→URL) |
| `d`              | Eliminar radio                    |
| `E`              | Editar nombre o URL (prompt)      |
| `s`              | Guardar radios                    |
| `X`              | Exportar como M3U                 |

---

## 8. Capa Favoritos (vista 6)

| Tecla            | Acción                        |
| ---------------- | ----------------------------- |
| `j` / `k` / `↑↓` | Cursor arriba/abajo           |
| `g` / `G`        | Inicio / Fin                  |
| `PgDn` / `PgUp`  | Página abajo/arriba           |
| `Enter`          | Reproducir favorito           |
| `d`              | Eliminar de favoritos         |
| `a`              | Añadir a pila (final)         |
| `A`              | Añadir a pila (tras playhead) |
| `F` (desde Expl) | Abrir vista Favoritos         |
| `f` (desde Expl) | Añadir archivo a favoritos    |

---

## 9. Capa Config (vista 0)

| Tecla            | Acción                       |
| ---------------- | ---------------------------- |
| `j` / `k` / `↑↓` | Cursor arriba/abajo          |
| `[` / `]`        | Pestaña anterior / siguiente |
| `H` / `L`        | Pestaña anterior / siguiente |
| `→` / `Enter`    | Activar / cambiar valor      |
| `←` / `h` / `l`  | Cambiar valor                |

### Sub-modo Keybindings

| Tecla            | Acción                      |
| ---------------- | --------------------------- |
| `←` / `→`        | Cambiar modo default/custom |
| `j` / `k` / `↑↓` | Navegar acciones            |
| `Enter`          | Capturar tecla para acción  |
| `Esc`            | Guardar y salir             |

### Sub-modo Dir Picker (music_dir)

| Tecla                   | Acción                 |
| ----------------------- | ---------------------- |
| `hjkl` / `flechas`      | Navegar directorios    |
| `Enter`                 | Seleccionar directorio |
| `h` / `←` / `Backspace` | Directorio padre       |
| `~`                     | Ir a home              |
| `g` / `G`               | Inicio / Fin           |
| `Esc`                   | Cancelar               |

---

## 10. Capa Help (?/F1 overlay)

| Tecla            | Acción                        |
| ---------------- | ----------------------------- |
| `[` / `]`        | Pestaña anterior / siguiente  |
| `h` / `l`        | Pestaña anterior / siguiente  |
| `j` / `k`        | Scroll abajo / arriba         |
| `g` / `G`        | Inicio / Fin                  |
| `Esc` / `?`/`F1` | Cerrar Help                  |

---

## 11. Consistencia de teclas (cross-reference)

| Tecla   | Global   | Listen     | Stack         | Explorer     | Playlist      | History       | Radio           | Config       | Favoritos  |
| ------- | -------- | ---------- | ------------- | ------------ | ------------- | ------------- | --------------- | ------------ | ---------- |
| `d`     | —        | —          | delete item   | delete file  | remove item   | remove entry  | delete radio    | —            | remove fav |
| `D`     | —        | —          | —             | —            | delete playlist | —           | —               | —            | —          |
| `E`     | —        | —          | —             | rename file  | rename item   | —             | edit name → URL | —            | —          |
| `s`     | —        | stop       | save playlist | —            | save playlist | —             | save radios     | —            | —          |
| `S`     | **STOP** | —          | —             | —            | —             | —             | —               | —            | —          |
| `r`     | —        | shuffle    | cycle mode    | —            | —             | —             | —               | —            | —          |
| `R`     | —        | repeat     | cycle mode    | —            | rename PL     | —             | —               | —            | —          |
| `a`     | —        | —          | —             | add stack    | —             | add stack     | add radio       | —            | add stack  |
| `A`     | —        | —          | —             | add after    | —             | add after     | —               | —            | add after  |
| `f`     | —        | toggle fav | toggle fav    | toggle fav   | toggle fav    | toggle fav    | toggle fav      | —            | toggle fav |
| `F`     | —        | —          | —             | open favs    | —             | —             | —               | —            | —          |
| `g`     | —        | goto       | top           | top          | top           | —             | top             | —            |
| `G`     | —        | —          | bottom        | bottom       | bottom        | —             | bottom          | —            |
| `x`     | —        | —          | clear stack   | —            | clear list    | clear history | —               | —            |
| `X`     | —        | —          | export M3U    | —            | export M3U    | —             | export M3U      | —            |
| `u`     | —        | —          | undo          | undo         | undo          | —             | —               | —            |
| `U`     | —        | —          | redo          | redo         | redo          | —             | —               | —            |
| `I`     | —        | tag editor | —             | tag editor   | tag editor    | tag editor    | —               | —            |
| `j`/`k` | —        | vol -/+5   | cursor        | cursor       | cursor        | cursor        | cursor          | cursor       |
| `h`/`l` | —        | seek -/+5  | —             | parent/enter | —             | —             | —               | modify value |
| `[]`    | —        | —          | —             | —             | change PL     | —             | —               | change tab   |
| `F5`    | —        | —          | —             | refresh      | —             | —             | —               | —            |
| `/`     | —        | —          | —             | filter       | filter        | —             | —               | —            |

---

## 12. Fix aplicado (auditoría)

### Problema: `R` como refresh en Explorer

**Antes:** `R` = refresh en Explorer. Conflicto con `R` = repeat global.
**Ahora:** `F5` = refresh en Explorer. `R` queda libre para repeat en Listen.

**Archivos modificados:**

- `player/handlers/explorer.py:87` — `ord("R")` → `curses.KEY_F5`
- `player/ui.py:262` — Help tab Explorer: `R` → `F5`

### Fix: j/k/r/R/t/T/m movidos de global a Listen

**Antes:** `j/k` (volumen), `r/R` (shuffle/repeat), `m` (mute), `t/T` (timer) eran globales.
**Ahora:** Solo funcionan en vista Listen (y sub-vistas Stack/Goto).

**Archivos modificados:**

- `player/app.py` — `_handle_key_global()`: eliminados j/k/r/R/t/T/m
- `player/handlers/listen.py` — `handle_listen()`: agregados j/k/r/R/t/T/m

### Fix: s/S ya no atrapa en Radio

**Antes:** `s` global atrapaba en todas las vistas excepto Playlist.
**Ahora:** `s` global atrapa solo en vistas que no sean Playlist ni Radio.

**Archivos modificados:**

- `player/app.py:665` — condición: `not in (V_PLAYLIST, V_RADIO)`

### Fix: Esc permite volver desde History

**Antes:** `Esc` global atrapaba siempre, History nunca lo veía.
**Ahora:** Si no hay overlay abierto y estamos en History, `Esc` pasa al handler de History.

**Archivos modificados:**

- `player/app.py:698-705` — guard para `V_HISTORY`

### Fix: e/E consistencia en Radio

**Antes:** `e` = editar nombre, `E` = editar URL (inconsistente con otras vistas).
**Ahora:** `E` = editar radio (prompt: n=nombre / u=URL). `e` eliminado.

**Archivos modificados:**

- `player/handlers/radio.py` — `_radio_edit_choice_cb()` + handler `E`

### Pendiente (próxima sesión)

| ID  | Descripción                                          | Estado             |
| --- | ---------------------------------------------------- | ------------------ |
| K1  | Quitar `j/k/r/R/t/T/m` de `_handle_key_global()`     | ✅ Hecho           |
| K2  | Mover `r/R/t/T/m` a `handle_listen()`                | ✅ Hecho           |
| K3  | Guard `Esc` en global para History                   | ✅ Hecho           |
| K4  | Verificar `s` en Radio (global lo atrapa)            | ✅ Hecho           |
| K5  | e/E consistencia — unificar edit en todas las vistas | ✅ Hecho (v1.5.24) |
| K6  | Actualizar todos los HELP_TABS con teclas correctas  | ✅ Hecho (v1.5.24) |
| K7  | Actualizar COMPACT_SPEC.md con keybindings finales   | ✅ Hecho (v1.5.24) |

---

## 13. e/E — Análisis de consistencia

| Vista      | `e` | `E`                         |
| ---------- | --- | --------------------------- |
| Explorer   | —   | Renombrar archivo/dir       |
| Playlist   | —   | Renombrar item              |
| Radio      | —   | Editar nombre → URL (ciclo) |
| History    | —   | —                           |
| Stack View | —   | —                           |

**Observación:** `E` es consistentemente "editar/renombrar" en todas las vistas. `e` no existe en ninguna vista (eliminado en v1.5.24).

---

_v1.1 — Auditoría keybindings tplay (v1.5.45 — `[]` tab nav universal, Help carousel, meta_edit h/l)_
