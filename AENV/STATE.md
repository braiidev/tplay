# STATE — tplay

## Versión actual
- **v1.5.45** (último tag: `v1.5.45`)
- **Último commit**: `dae0c98` — docs: actualizar AGENTS, KEYBINDINGS, TODO con v1.5.38-v1.5.45

## Estado del código
- **Compila**: ✅ (mypy strict pasa)
- **Tests**: ⚠️ No hay tests unitarios
- **Último fix**: v1.5.46 — Explorer read-only fuera del directorio raíz

## Features activos
| ID | Feature | Estado |
|----|---------|--------|
| F2 | Ecualizador gráfico (VLC API) | Pendiente |
| F4 | Exportar/Importar M3U/PLS | ✅ Hecho |
| F8 | Cover art (chafa/viu) | Descartado |
| F28 | Streaming/Radio | ✅ Hecho |

## Módulos del sistema
| Módulo | Archivos | Estado |
|--------|----------|--------|
| Core | app.py, audio.py | Estable |
| Config | config.py | Estable |
| Handlers | handlers/ (8 archivos) | Estable |
| Views | views.py | Estable |
| UI | ui.py | Estable |
| State | state.py, stack.py | Estable |
| Data | playlist.py, favorites.py, radios.py | Estable |
| Utils | file_utils.py, metadata.py, keybindings.py | Estable |

## Deuda técnica conocida
- Sin tests unitarios
- `mutagen.File` usa `# type: ignore[attr-defined]`
- handlers/__init__.py re-exporta 65 símbolos

## Próximo paso sugerido
- F2 — Ecualizador gráfico (VLC API)
