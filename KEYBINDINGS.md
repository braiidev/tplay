# KEYBINDINGS.md — Mapa completo de teclas

> Fuente de verdad para el sistema de keybindings de tplay.
> Cada tecla hace **UNA sola cosa** por vista.

---

## 1. Arquitectura de dispatch

```
tecla → Help overlay? → Dir picker? → Modo específico? → Switch vista? → Global → Vista
```

- **Global** (`_handle_key_global`): solo Space, S, n/b, +/-, q, Esc, 0-5, ?/F1
- **Vista** (`handle_*`): todo lo demás
- Si global matchea, la vista **no recibe** la tecla

---

## 2. Capa Global (siempre funciona)

| Tecla | Acción | Notas |
|-------|--------|-------|
| `Space` | Play / Pause | |
| `S` | Stop | Solo mayúscula |
| `n` | Siguiente track | |
| `b` | Anterior track | |
| `+` | Volumen +5 | |
| `-` | Volumen -5 | |
| `0` | Vista Config | |
| `1` | Vista Listen | |
| `2` | Vista Explorer | |
| `3` | Vista Playlist | |
| `4` | Vista History | |
| `5` | Vista Radio | |
| `?` / `F1` | Abrir/cerrar ayuda | |
| `q` | Salir (guarda todo) | |
| `Esc` | Cerrar overlay actual | Help, Stack, Goto, KB editor, Dir picker |

---

## 3. Capa Listen (vista 1)

### Vista principal

| Tecla | Acción |
|-------|--------|
| `h` / `←` | Seek -5s |
| `l` / `→` | Seek +5s |
| `j` | Volumen -5 |
| `k` | Volumen +5 |
| `r` | Shuffle toggle (ON/OFF) |
| `R` | Repeat toggle (ON/OFF) |
| `t` | Sleep timer toggle |
| `T` | Sleep timer config (prompt) |
| `m` | Mute toggle |
| `g` | Goto (ir a tiempo) |
| `Tab` | Abrir Stack View |
| `I` | Editor de tags ID3 |

### Stack View (sub-modo de Listen)

| Tecla | Acción |
|-------|--------|
| `hjkl` / `flechas` | Navegar items |
| `Enter` | Reproducir item cursor |
| `r` | Ciclar modo item (Normal→1x→∞) |
| `d` | Eliminar item (confirmación) |
| `x` | Limpiar todo el Stack |
| `s` | Guardar Stack como playlist |
| `X` | Exportar Stack como M3U |
| `J` / `K` | Reordenar (abajo/arriba) |
| `u` / `U` | Undo / Redo |
| `g` / `G` | Inicio / Fin |
| `PgDn` / `PgUp` | Página abajo/arriba |
| `Tab` / `Esc` | Cerrar Stack View |

### Goto (sub-modo de Listen)

| Tecla | Acción |
|-------|--------|
| `←` / `→` | Seleccionar campo (min/seg) |
| `↑` / `↓` | Incrementar/decrementar valor |
| `Enter` | Saltar a tiempo |
| `Esc` | Cancelar |

---

## 4. Capa Explorer (vista 2)

| Tecla | Acción |
|-------|--------|
| `h` / `←` / `Backspace` | Directorio padre |
| `l` / `→` / `Enter` | Entrar directorio / Reproducir archivo |
| `j` / `k` / `↑↓` | Cursor arriba/abajo |
| `~` | Ir a home |
| `g` / `G` | Inicio / Fin |
| `PgDn` / `PgUp` | Página abajo/arriba |
| `F5` | Refrescar directorio |
| `/` | Filtro inline |
| `a` | Añadir a pila (final) |
| `A` | Añadir a pila (tras playhead) |
| `C` | Copiar archivo/dir |
| `V` | Mover archivo/dir |
| `E` | Renombrar archivo/dir |
| `I` | Editar tags ID3 |
| `d` | Eliminar archivo (confirmación) |
| `M` | Crear directorio |
| `P` | Reproducar carpeta completa |
| `u` / `U` | Undo / Redo |

---

## 5. Capa Playlist (vista 3)

| Tecla | Acción |
|-------|--------|
| `h` / `[` | Playlist anterior |
| `l` / `]` | Playlist siguiente |
| `j` / `k` / `↑↓` | Cursor arriba/abajo |
| `g` / `G` | Inicio / Fin |
| `PgDn` / `PgUp` | Página abajo/arriba |
| `Enter` | Reproducir playlist |
| `d` | Eliminar item de la lista |
| `x` | Limpiar toda la lista |
| `e` | Renombrar item en la lista |
| `R` | Renombrar playlist |
| `c` | Crear nueva playlist |
| `D` | Eliminar playlist |
| `J` / `K` | Reordenar item (abajo/arriba) |
| `s` | Guardar playlist |
| `X` | Exportar como M3U |
| `I` | Editar tags ID3 |
| `u` / `U` | Undo / Redo |
| `/` | Filtro inline |

---

## 6. Capa History (vista 4)

| Tecla | Acción |
|-------|--------|
| `j` / `k` / `↑↓` | Cursor arriba/abajo |
| `g` / `G` | Inicio / Fin |
| `Enter` | Reproducir archivo |
| `d` | Eliminar entrada |
| `x` | Limpiar historial |
| `a` | Añadir a pila (final) |
| `A` | Añadir a pila (tras playhead) |
| `I` | Editar tags ID3 |
| `Esc` | Volver a Listen |

---

## 7. Capa Radio (vista 5)

| Tecla | Acción |
|-------|--------|
| `j` / `k` / `↑↓` | Cursor arriba/abajo |
| `g` / `G` | Inicio / Fin |
| `PgDn` / `PgUp` | Página abajo/arriba |
| `Enter` | Reproducir radio |
| `a` | Agregar radio (prompt nombre→URL) |
| `d` | Eliminar radio |
| `E` | Editar nombre o URL (prompt) |
| `s` | Guardar radios |
| `X` | Exportar como M3U |

---

## 8. Capa Config (vista 0)

| Tecla | Acción |
|-------|--------|
| `j` / `k` / `↑↓` | Cursor arriba/abajo |
| `h` / `[` | Pestaña anterior |
| `l` / `]` / `H` / `L` | Pestaña siguiente |
| `→` / `Enter` | Modificar valor (ciclar/incrementar/abrir) |
| `←` | Modificar valor (decrementar) |

### Sub-modo Keybindings

| Tecla | Acción |
|-------|--------|
| `←` / `→` | Cambiar modo default/custom |
| `j` / `k` / `↑↓` | Navegar acciones |
| `Enter` | Capturar tecla para acción |
| `Esc` | Guardar y salir |

### Sub-modo Dir Picker (music_dir)

| Tecla | Acción |
|-------|--------|
| `hjkl` / `flechas` | Navegar directorios |
| `Enter` | Seleccionar directorio |
| `h` / `←` / `Backspace` | Directorio padre |
| `~` | Ir a home |
| `g` / `G` | Inicio / Fin |
| `Esc` | Cancelar |

---

## 9. Consistencia de teclas (cross-reference)

| Tecla | Global | Listen | Stack | Explorer | Playlist | History | Radio | Config |
|-------|--------|--------|-------|----------|----------|---------|-------|--------|
| `d` | — | — | delete item | delete file | remove item | remove entry | delete radio | — |
| `D` | — | — | — | — | delete playlist | — | — | — |
| `e` | — | — | — | — | rename item | — | edit name | — |
| `E` | — | — | — | rename file | rename playlist | — | edit URL | — |
| `s` | — | — | save playlist | — | save playlist | — | save radios | — |
| `S` | **STOP** | — | — | — | — | — | — | — |
| `r` | — | shuffle | cycle mode | — | — | — | — | — |
| `R` | — | repeat | cycle mode | — | rename PL | — | — | — |
| `a` | — | — | — | add stack | — | add stack | add radio | — |
| `A` | — | — | — | add after | — | add after | — | — |
| `g` | — | goto | top | top | top | top | top | — |
| `G` | — | — | bottom | bottom | bottom | — | bottom | — |
| `x` | — | — | clear stack | — | clear list | clear history | — | — |
| `X` | — | — | export M3U | — | export M3U | — | export M3U | — |
| `u` | — | — | undo | undo | undo | — | — | — |
| `U` | — | — | redo | redo | redo | — | — | — |
| `I` | — | tag editor | — | tag editor | tag editor | tag editor | — | — |
| `j`/`k` | — | vol -/+5 | cursor | cursor | cursor | cursor | cursor | cursor |
| `h`/`l` | — | seek -/+5 | cursor | parent/enter | prev/next PL | — | — | tab prev/next |
| `F5` | — | — | — | refresh | — | — | — | — |
| `/` | — | — | — | filter | filter | — | — | — |

---

## 10. Fix aplicado (auditoría)

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

| ID | Descripción | Estado |
|----|-------------|--------|
| K1 | Quitar `j/k/r/R/t/T/m` de `_handle_key_global()` | Pendiente |
| K2 | Mover `r/R/t/T/m` a `handle_listen()` | Pendiente |
| K3 | Guard `Esc` en global para History | Pendiente |
| K4 | Verificar `s` en Radio (global lo atrapa) | Pendiente |
| K5 | e/E consistencia — unificar edit en todas las vistas | Pendiente |
| K6 | Actualizar todos los HELP_TABS con teclas correctas | Pendiente |
| K7 | Actualizar COMPACT_SPEC.md con keybindings finales | Pendiente |

---

## 11. e/E — Análisis de consistencia

| Vista | `e` | `E` |
|-------|-----|-----|
| Explorer | — | Renombrar archivo/dir |
| Playlist | Renombrar item | Renombrar playlist |
| Radio | Editar nombre | Editar URL |
| History | — | — |
| Stack View | — | — |

**Observación:** `E` es consistentemente "editar/renombrar" en todas las vistas. `e` solo existe en Playlist (rename item) y Radio (edit name). Para máxima consistencia, `E` podría unificarse como la única tecla de edición, pero requeriría cambios en Playlist y Radio.

---

_v1.0 — Auditoría keybindings tplay_
