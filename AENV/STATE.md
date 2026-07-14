# STATE — tplay

## Versión actual
- **v1.5.48**
- **Último commit**: `375f4b0` — docs: B12 symlinks fix + CHANGELOG + DEVLOG

## Estado del código
- **Compila**: ✅ (mypy strict pasa)
- **Tests**: ⚠️ No hay tests unitarios
- **Último fix**: v1.5.48 — Explorer no ve symlinks-to-dirs (regresión P1)

## Features activos
| ID | Feature | Estado |
|----|---------|--------|
| F2 | Ecualizador gráfico (VLC API) | Pendiente |
| F4 | Exportar/Importar M3U/PLS | ✅ Hecho |
| F8 | Cover art (chafa/viu) | Descartado |
| F28 | Streaming/Radio | ✅ Hecho |

## Sesión actual (v1.5.46-v1.5.48)
- Setup AENV (migración tracking)
- Explorer read-only fuera del root
- 9 extensiones nuevas (.m4a .aac .opus .weba .wma .aiff .aif .flv .wmv)
- Fix symlinks-to-dirs en Explorer

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
