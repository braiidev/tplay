# STATE — tplay

## Versión actual
- **v1.5.57**
- **Último commit**: `33128ae` — docs: refactor 5.1+5.2 completado

## Estado del código
- **Compila**: ✅ (mypy strict pasa)
- **Tests**: ⚠️ No hay tests unitarios
- **Último feature**: v1.5.50 — EQ refinado (preamp configurable, Custom en Config, teclas E/e)

## Features activos
| ID | Feature | Estado |
|----|---------|--------|
| F2 | Ecualizador gráfico (VLC API) | ✅ Hecho |
| F4 | Exportar/Importar M3U/PLS | ✅ Hecho |
| F8 | Cover art (chafa/viu) | Descartado |
| F28 | Streaming/Radio | ✅ Hecho |

## Sesión actual (v1.5.57)
- UI polish:
  - Listen view: metadata centrada (estado, título, artista/álbum) en full y compact
  - Indicador de volumen visual con barras (8 chars full, 4 chars compact)
  - Config/Audio: bandas EQ siempre visibles, solo lectura para presets non-Custom
  - Config/Audio: hints contextuales por tipo de item (±0.5dB, cambiar, reset)
- Refactor:
  - draw_tab_carousel() — helper unificado para carousel de pestañas (Help + Config)
  - clamp_scroll() — normaliza scroll clamping en 6 vistas
  - draw_list_indicators() — dibuja ▲/▼ de forma consistente
- Bug fixes:
  - Config/Audio bands siempre visibles (B14)
  - History g/G implementados (B15)

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
