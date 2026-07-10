# RESPONSIVE_HINTS.md — Hints y navbar adaptables por ancho

> Plan para hacer hints/status bars y navbar adaptables a cualquier tamaño de terminal.

## Problema

Los hints son strings hardcodeados que se cortan abrupto con `[:w-4]` en terminales chicas:

```
# ~73 chars, se corta en w<70
"  [Tab] Pila │ [g] Ir a │ [t/T] Tmp │ [h/l] Buscar │ [r]Azar [R]Rep [m]Sil"
```

En una terminal de 40 cols se ve: `"  [Tab] Pila │ [g] Ir a │ [t/T] Tmp │ [h/l"` — cortado a mitad de token.

## Solución: `_build_hints()`

### Helper en `ui.py`

```python
def _build_hints(segments: list[tuple[str, str]], w: int, prefix: str = "  ") -> str:
    """
    segments = [("Tab", "Pila"), ("g", "Ir a"), ("t/T", "Tmp"), ...]
    
    Tiers:
      w >= 70  →  "  [Tab] Pila │ [g] Ir a │ [t/T] Tmp │ ..."
      w >= 45  →  "  [Tab]Pila │ [g]Ir │ [t]Tmp │ ..."  (labels cortos)
      w >= 25  →  "  Tab│g│t│h│r"  (solo keys, sin labels)
      w < 25   →  ""  (sin hints)
    """
```

### Lógica interna

1. Para cada tier, construir string con separador `│`
2. Si `len(result) + prefix <= w - 4` → return result
3. Si no entra → drop segmentos desde la derecha hasta que entre
4. Si un solo segmento no entra → truncar con `…`
5. Si `w < 25` → return `""`

### Definición de segments

Cada vista define sus hints como `list[tuple[str, str]]`:

```python
# views.py
HINT_LISTEN: list[tuple[str, str]] = [
    ("Tab", "Pila"), ("g", "Ir a"), ("t/T", "Tmp"),
    ("h/l", "Buscar"), ("r", "Azar"), ("R", "Rep"), ("m", "Sil"),
]
```

### Rendering

```python
# Antes (views.py:198)
extra = "  [Tab] Pila │ [g] Ir a │ [t/T] Tmp │ [h/l] Buscar │ [r]Azar [R]Rep [m]Sil"
safe_addstr(app.stdscr, h - 3, 2, extra[:w - 4], nav, h, w)

# Después
hint = _build_hints(HINT_LISTEN, w)
if hint:
    safe_addstr(app.stdscr, h - 3, 2, hint, nav, h, w)
```

## Áreas a actualizar

### 1. Listen view hints (`views.py:198`)
- Hints: `[Tab]Pila │ [g]Ir │ [t/T]Tmp │ [h/l]Buscar │ [r]Az [R]Rep [m]Sil`
- **Tiers**: completo / medio / solo-keys / none

### 2. Stack sub-view hints (`views.py:98-101`)
- Fila 1: `[Enter]►  [Tab] Volver  [d]el  [x]clear  [J/K]orden  [s]guardar`
- Fila 2: `[r/R]modo  [g/G]Inicio/Fin  [X]export  [u/U]deshacer`
- **Tiers**: completo / medio / solo-keys / none

### 3. Dir picker hints (`views.py:779-780`)
- `Enter=seleccionar  h/l=subir/bajar  Esc=cancelar`
- **Tiers**: completo / solo-keys / none

### 4. Nav bar tabs (`ui.py:50`)
```python
# Completo (~65 chars)
" 0:Config │ 1:Listen │ 2:Expl │ 3:Playlist │ 4:Hist │ 5:Radio │ 6:Fav │ q:Salir "

# Medio (~45 chars)
" 0:Cfg│1:Lis│2:Exp│3:PL│4:His│5:Rad│6:Fav│q:Salir"

# Mínimo (~25 chars)
" 0│1│2│3│4│5│6│q"

# w < 25 → sin nav bar (ya existe suppress en compact)
```

### 5. Dest picker dialog hint (`app.py:972`)
- `"s: Pila  |  p: Lista  |  Esc: Cancelar"`
- Similar adaptación

## Constantes

```python
# En ui.py
HINT_FULL_W: int = 70    # Ancho mínimo para hints completos
HINT_MID_W: int = 45     # Ancho mínimo para hints medios
HINT_MIN_W: int = 25     # Ancho mínimo para solo-keys
NAV_FULL_W: int = 65     # Ancho mínimo para nav bar completa
NAV_MID_W: int = 45      # Ancho mínimo para nav bar media
NAV_MIN_W: int = 25      # Ancho mínimo para nav bar mínima
```

## Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `player/ui.py` | Crear `_build_hints()`, constantes de tiers, adaptar `draw_nav()` |
| `player/views.py` | Reemplazar strings hardcodeados por `_build_hints()` con segments |
| `player/app.py` | Adaptar dialog hint y nav bar |

## Verificación

- Terminal 80x24 → hints completos
- Terminal 50x16 → hints medios
- Terminal 30x12 → solo keys
- Terminal 20x10 → sin hints
- tmux split 1/4 → todo funciona sin cortes abruptos
- mypy --strict → 0 errores
