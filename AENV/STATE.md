# STATE — tplay

## Versión actual
- **v1.5.49**
- **Último commit**: pendiente

## Estado del código
- **Compila**: ✅ (mypy strict pasa)
- **Tests**: ⚠️ No hay tests unitarios
- **Último feature**: v1.5.49 — Ecualizador gráfico (10 bandas, preamp, 16 presets, Custom)

## Features activos
| ID | Feature | Estado |
|----|---------|--------|
| F2 | Ecualizador gráfico (VLC API) | ✅ Hecho |
| F4 | Exportar/Importar M3U/PLS | ✅ Hecho |
| F8 | Cover art (chafa/viu) | Descartado |
| F28 | Streaming/Radio | ✅ Hecho |

## Sesión actual (v1.5.49)
- Ecualizador gráfico implementado
  - audio.py: métodos EQ (set_equalizer, apply_preset, disable_equalizer, reapply_equalizer)
  - config.py: defaults EQ + 16 presets + Custom
  - app.py: config tab Audio + persistencia session + eq_edit_mode
  - handlers/listen.py: tecla E toggle EQ
  - handlers/config_view.py: preset cycling + Custom abre overlay
  - views.py: [EQ] indicator, hints, draw_eq_overlay
  - state.py: save/load EQ state

## Módulos del sistema
| Módulo | Archivos | Estado |
|--------|----------|--------|
| Core | app.py, audio.py | Estable + EQ |
| Config | config.py | Estable + EQ presets |
| Handlers | handlers/ (8 archivos) | Estable + EQ |
| Views | views.py | Estable + EQ overlay |
| UI | ui.py | Estable |
| State | state.py, stack.py | Estable + EQ |
| Data | playlist.py, favorites.py, radios.py | Estable |
| Utils | file_utils.py, metadata.py, keybindings.py | Estable |

## Deuda técnica conocida
- Sin tests unitarios
- `mutagen.File` usa `# type: ignore[attr-defined]`
- handlers/__init__.py re-exporta 65 símbolos

## Próximo paso sugerido
- F9 — Visualizer (FFT bars)
