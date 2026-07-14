# PLAN — Equalizer (F2)

> Feature: Ecualizador gráfico de 10 bandas con presets y modo custom.
> Versión target: v1.5.49+

---

## Resumen

Integrar el ecualizador de VLC en la TUI. 10 bandas, preamp, 12 presets + custom. Persistente en config.json. Toggle rápido con `E` desde Listen.

---

## Archivos a modificar

| Archivo | Cambios |
|---------|---------|
| `player/audio.py` | +5 métodos EQ |
| `player/config.py` | +defaults EQ, +preset definitions |
| `player/app.py` | +config tab Audio, +persistencia session |
| `player/handlers/listen.py` | +tecla `E` toggle EQ |
| `player/handlers/config_view.py` | +handler para preset cycling y custom band editing |
| `player/views.py` | +hint `[E]` en status, +EQ indicator |
| `player/ui.py` | +draw_eq_overlay (10 bandas + preamp) |

---

## Paso 1: AudioEngine — métodos EQ

En `player/audio.py`, agregar:

```python
# Atributos nuevos en __init__
self._eq: vlc.AudioEqualizer | None = None
self._eq_enabled: bool = False

# Métodos
def set_equalizer(self, bands: list[float], preamp: float) -> None:
    """Crear y aplicar EQ con bandas personalizadas."""

def apply_preset(self, preset_index: int) -> None:
    """Aplicar preset nativo de VLC."""

def disable_equalizer(self) -> None:
    """Desactivar EQ."""

def get_equalizer_info(self) -> dict:
    """Retornar info actual del EQ (bands, preamp, enabled)."""
```

Notas:
- `vlc.AudioEqualizer()` crea EQ flat
- `vlc.libvlc_audio_equalizer_new_from_preset(i)` crea desde preset
- `player.set_equalizer(eq)` aplica (NO `audio_set_equalizer`)
- `player.set_equalizer(None)` desactiva
- Re-aplicar después de `play_file()` por seguridad

---

## Paso 2: Config — defaults y presets

En `player/config.py`:

```python
DEFAULT_CONFIG = {
    ...,
    "eq_enabled": False,
    "eq_preset": "Flat",
    "eq_bands": [0.0] * 10,
    "eq_preamp": 0.0,
}

EQ_PRESETS: dict[str, list[float]] = {
    "Flat": [0.0] * 10,
    "Rock": [3.0, 4.0, 2.0, 0.0, -1.0, 2.0, 3.0, 4.0, 4.0, 3.0],
    "Pop": [1.0, 2.0, 3.0, 2.0, 0.0, -1.0, 0.0, 1.0, 2.0, 2.0],
    # ... 12 presets totales
}
```

---

## Paso 3: Config tab "Audio"

En `player/app.py` → `_build_config_tabs()`:

```python
{
    "name": "Audio",
    "items": [
        ("eq_enabled", "Ecualizador", "bool"),
        ("eq_preset", "Preset EQ", "choice"),  # cycle: Flat→Rock→...→Custom
    ],
}
```

Si preset = "Custom", mostrar sub-items de bandas (o overlay).

---

## Paso 4: Tecla `E` en Listen

En `player/handlers/listen.py`:

```python
elif key == ord("E"):
    app.audio._eq_enabled = not app.audio._eq_enabled
    if app.audio._eq_enabled:
        # re-aplicar EQ actual
        app.audio.set_equalizer(app.config["eq_bands"], app.config["eq_preamp"])
    else:
        app.audio.disable_equalizer()
    _toast(app, f"EQ: {'ON' if app.audio._eq_enabled else 'OFF'}")
```

---

## Paso 5: Persistencia session

En `player/app.py` → `_save_session()` / `_resume_session()`:
- Guardar/cargar `eq_enabled`, `eq_bands`, `eq_preamp`, `eq_preset`

---

## Paso 6: UI — hints y overlay

### Status bar Listen
Cuando EQ activo, agregar `[EQ]` junto a `[S] [R] [M]`.

### Custom mode overlay
Si preset = "Custom" y el usuario presiona Enter en config:
- Overlay con 10 filas (una por banda) + 1 fila preamp
- Cada banda muestra barra ASCII de 20 chars
- ←/→ ajustan banda seleccionada (±0.5 dB)
- j/k navegan entre bandas
- s guarda, Esc cancela

---

## Orden de implementación

1. `audio.py` — métodos EQ
2. `config.py` — defaults + presets
3. `app.py` — config tab + persistencia
4. `handlers/listen.py` — tecla E
5. `handlers/config_view.py` — preset cycling
6. `views.py` — hints
7. `ui.py` — overlay custom
8. mypy strict
9. Test manual

---

## Dependencias
**Ninguna** — VLC ya tiene todo integrado.

## Riesgos
- EQ bands pueden no persistir correctamente entre play_file() calls → re-aplicar siempre
- VLC presets en bytes, no str → decodificar
- Custom overlay puede ser complejo → empezar con presets, agregar custom después
