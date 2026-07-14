# STATE — tplay

## Versión actual
- **v1.5.59**
- **Último commit**: `2902ae4` — refactor: eliminar r reset de Config/Audio

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

## Sesión actual (v1.5.59)
- **Custom EQ persistence**: key `custom_bands` en config.json
  - Guarda al salir de Custom → restaura al entrar
  - Listen handler `E`同步 lógica custom_bands
- **B17 fix final**: `_skip_disabled` para en PRIMER item válido
  - Preamp ↓ se queda en Preamp (no salta a bands)
  - eq_enabled ↓ llega a eq_preset (no salta a Preamp)
- **B16**: `_cycle_eq_preset` guarda/restaura custom_bands al cambiar preset
- **B13**: Listen hints toggle con `;`
- **B18/B19**: Help hints actualizados
- **Cleanup**: eliminado `r` reset de Config/Audio (conflicto con shuffle global)

## Módulos del sistema
| Módulo | Archivos | Estado |
|--------|----------|--------|
| Core | app.py, audio.py | Estable + EQ |
| Config | config.py | Estable + custom_bands |
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
