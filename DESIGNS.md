# DESIGNS.md — Propuesta de Rediseño Visual tplay

## Estado actual: 7/10

- Funcional, coherente, responsive
- Falta jerarquía visual, separadores, vida interior
- Inconsistencias menores (3 implementaciones de box drawing, umbrales compact disparejos)

## Filosofía del rediseño

**"Mismo idioma, mejor gramática"** — no cambiar la personalidad (minimalismo denso, hint-driven, keyboard-first), sino pulir la ejecución: jerarquía, ritmo, consistencia.

---

## FASE 1 — Consistencia estructural (baja complejidad, alto impacto)

### 1.1 Unificar draw_box con draw_listen_compact y draw_mini_stack

**Problema**: 3 implementaciones de box drawing manuales que duplican lógica.

**Solución**: Extraer helper `draw_box_inline(win, h, w, title, heavy=False)` que soporte título inline (para compact) y optionally heavy chars.

```
┌─ Helper unificado ─────────────────────────────────────┐
│  draw_box_inline(win, h, w, title, heavy=False)        │
│  - heavy=True  → ╔═══╗  ║  ╚═══╝                       │
│  - heavy=False → ┌───┐  │  └───┘                       │
│  - title=""    → borde sin título                      │
│  - title="▶ Listen" → título embebido en top border    │
└────────────────────────────────────────────────────────┘
```

**Archivos**: `player/ui.py`
**Esfuerzo**: ~30 min

### 1.2 Unificar umbral compact

**Problema**: `h < 16` en 15+ lugares, `h < 12` solo en draw_help. Inconsistencia visual.

**Solución**: Constante `COMPACT_THRESHOLD = 16` en `ui.py`, usarla en todo.

**Archivos**: `player/ui.py`, `player/views.py`, `player/app.py`
**Esfuerzo**: ~15 min

### 1.3 Unificar icono de pausa

**Problema**: `||` (ASCII) en status bar, `❚❚` (Unicode) en compact title, `▶ / ||` en help.

**Solución**: Elegir `❚❚` como representación canónica. Actualizar status bar y help.

**Archivos**: `player/ui.py`
**Esfuerzo**: ~10 min

---

## FASE 2 — Jerarquía visual (media complejidad, alto impacto)

### 2.1 Separadores de sección en Config

**Problema**: Config/Audio muestra 13 items corridos (Ecualizador, Preset, Preamp, 10 bandas). Sin separación visual.

**Solución**: Línea divisoria `──────────────` antes del grupo de bandas.

```
┌───────────────────────────────────────────────────┐
│ ─── General │ ◉Audio │ Apariencia │ Sistema ───── │
│                                                   │
│   Ecualizador: Sí  ← →                            │
│   Preset EQ: Flat  ← →                            │
│   Preamp  : +12.0  ████████████████████░░░░░░░░░░ │
│ ───────────────────────────────────────────────── │  <- separador
│   60 Hz   : +3.5   ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│   170 Hz  : +2.0   █░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│   ...                                             │
└───────────────────────────────────────────────────┘
```

**Archivos**: `player/views.py` (draw_config)
**Esfuerzo**: ~20 min

### 2.2 Listen view — "Now Playing" card refinado

**Problema**: El layout centrado es bueno, pero la información se siente flotando sin anclaje.

**Solución**: Agregar borde sutil alrededor del bloque de metadata (no un box completo, sino guiones decorativos).

```
┌───────────────────────────────────────────────────┐
│                                                   │
│                    ► PLAY                         │
│                                                   │
│              ┌──────────────────┐                 │
│              │  Some Song Name  │                 │
│              │  Artist — Album  │                 │
│              └──────────────────┘                 │
│                                                   │
│       0:42 ████████████████████████░░░ 3:21       │
│                                                   │
│              ◀◀   ▶||   ▶▶   ◼                    │
│              b   space   n   s                    │
│       [Tab]Pila │ [g]Ir a │ [t/T]Tmp │ ...        │
└───────────────────────────────────────────────────┘
        0:Config │ 1:Listen │ 2:Expl │ ...
```

**Alternativa más conservadora** (sin box, solo indentación mejorada):

```
│                                                    │
│                    ► PLAY                          │
│                                                    │
│                  Some Song Name                    │  <- x=4, destacar
│                  Artist  —  Album                  │  <- x=4, texto
│                                                    │
│       0:42 ████████████████████████░░░ 3:21        │
│                                                    │
│              ◀◀   ▶||   ▶▶   ◼                     │
```

**Mi recomendación**: La alternativa conservadora. El box interno puede verse pesado en terminales pequeñas.

**Archivos**: `player/views.py` (draw_listen)
**Esfuerzo**: ~25 min
**Estado**: ✅ Hecho (v1.5.54)

### 2.3 Indicador de volumen visual

**Problema**: Volumen mostrado solo como `Vol:50%` en status bar.

**Solución**: Mini barra de volumen en Listen view, junto a los controles.

```
│       Vol: ████████░░░ 50%   [S] [R] [M]          │
```

**Archivos**: `player/views.py` (draw_listen), `player/ui.py` (draw_status)
**Esfuerzo**: ~20 min
**Estado**: ✅ Hecho (v1.5.54)

---

## FASE 3 — Ritmo y respiración (baja complejidad, impacto sutil)

### 3.1 Espaciado consistente entre items

**Problema**: Items de lista apretados, sin aire.

**Solución**: No agregar líneas vacías (costo de espacio terminal), pero sí usar `·` o `·` como guía visual sutil entre grupos.

**Decisión**: NO hacer esto — sacrifica densidad que es parte de la personalidad.

### 3.2 Scroll indicators consistentes

**Problema**: `▲`/`▼` solo en Help view.

**Solución**: Agregar indicadores de scroll en todas las listas cuando hay items ocultos arriba/abajo.

```
│  ▲ (3 más arriba)                                   │
│    ► item visible 1                                 │
│    item visible 2                                   │
│  ▼ (5 más abajo)                                    │
```

**Archivos**: `player/views.py` (todas las vistas de lista)
**Esfuerzo**: ~40 min (6+ vistas)

### 3.3 Status bar con icono de EQ activo

**Problema**: `[EQ]` en status bar solo muestra si está activo, no el preset.

**Solución**: Mostrar `[EQ:Rock]` o `[EQ:Flat]` cuando está activo.

**Archivos**: `player/ui.py` (draw_status)
**Esfuerzo**: ~10 min

---

## FASE 4 — Polish visual (media complejidad, impacto en UX)

### 4.1 Config — Visual bars en modo solo lectura para presets

**Problema**: Al seleccionar un preset que no es Custom, las bandas son de solo lectura pero se ven igual que las editables.

**Solución**: Cuando el preset no es Custom, mostrar las bandas con color `texto` en vez de `destacar`, indicando que son informativas.

```
│   Preset EQ: Rock  ← →                             │
│   Preamp  : +12.0  ████████████████████░░░░░░░░░░░ │
│ ────────────────────────────────────────────────── │
│   60 Hz   : +4.8   █████░░░░░░░░░░░░░░░░░░░░░░░░░░ │  <- color texto
│   170 Hz  : +2.8   ███░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │  <- color texto
│   ...                                              │
│   [r] resetear                                      │
```

**Archivos**: `player/views.py` (draw_config)
**Esfuerzo**: ~15 min
**Estado**: ✅ Hecho (v1.5.55)

### 4.2 Hints contextuales en Config —(Audio

**Problema**: Audio tab muestra `← → cambiar` genérico.

**Solución**: Hints específicos por tipo de item:

- `eq_band`: `← → ±0.5dB │ r reset`
- `eq_preamp`: `← → ±0.5dB │ r reset`
- `choice`: `← → cambiar │ r reset`

```
│  ← → ±0.5dB │ r resetear                            │
```

**Archivos**: `player/views.py` (draw_config)
**Esfuerzo**: ~20 min
**Estado**: ✅ Hecho (v1.5.55)

### 4.3 Explorer — Icono de directorio más visible

**Problema**: Directorios mostrados con `[+]/` que se ve como tag, no como icono.

**Solución**: Usar `📁` o `▸` como prefijo de directorio (solo si el terminal soporta unicode, fallback a `[+]`).

**Decisión**: NO hacer esto — `[+]` es consistente con el resto del vocabulario visual. No romper lo que funciona.

---

## FASE 5 — Refactor de código visual (alta complejidad, impacto en mantenibilidad)

### 5.1 Extraer tab carousel a helper compartido

**Problema**: Código de tab carousel duplicado en `draw_help` (~35 líneas) y `draw_config` (~30 líneas).

**Solución**: `draw_tab_carousel(win, y, x, w, tabs, current_idx, attr, h)`.

**Archivos**: `player/ui.py`, `player/views.py`
**Esfuerzo**: ~30 min

### 5.2 Extraer list renderer con scroll indicators

**Problema**: Cada vista de lista reimplementa scroll + render + cursor.

**Solución**: `draw_scrollable_list(win, y0, items, cursor, scroll, list_h, render_fn, h, w)`.

**Archivos**: `player/ui.py`, `player/views.py`
**Esfuerzo**: ~60 min (refactor grande)

---

## Resumen de impacto

| Fase | Cambios      | Impacto visual       | Esfuerzo   |
| ---- | ------------ | -------------------- | ---------- |
| 1    | Consistencia | ⭐⭐⭐               | ~1 hora    |
| 2    | Jerarquía    | ⭐⭐⭐⭐⭐           | ~1.5 horas |
| 3    | Ritmo        | ⭐⭐                 | ~1 hora    |
| 4    | Polish       | ⭐⭐⭐               | ~1 hora    |
| 5    | Refactor     | ⭐ (maintainability) | ~1.5 horas |

## Orden sugerido

1. **Fase 1** primero — son fixes de consistencia que no cambian diseño
2. **Fase 2.1** (separadores Config) — impacto inmediato
3. **Fase 2.2** (Listen card) — el hero screen
4. **Fase 4.1-4.2** (Config polish) — UX de EQ
5. **Fase 3.2** (scroll indicators) — polish global
6. **Fase 5** solo si hay ganas de refactor

## Lo que NO rediseñar

- ❌ No agregar Background colors (rompe portabilidad terminal)
- ❌ No agregar animaciones (curses no las soporta bien)
- ❌ No cambiar el vocabulario de box chars (┌┐└┘│─ ya es correcto)
- ❌ No agregar subdivisiones internas con borders (muy pesado para TUI)
- ❌ No cambiar el sistema de 5 color pairs (es elegante y suficiente)
