# TEST — tplay

## Framework
_No hay tests unitarios implementados._

## Testing manual

### Setup
```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
python -m player.app
# o
python app.py
```

### Casos de prueba manuales

#### Reproducción básica
1. Navegar a un archivo de audio en Explorer
2. Presionar Enter → debe iniciar reproducción
3. Presionar Espacio → pausar/reanudar
4. Presionar `s` → stop

#### Stack/Cola
1. Seleccionar múltiples archivos con `m`
2. Presionar `a` → agregar a stack
3. Verificar que la cola se muestra en Listen (vista 1)

#### Playlists
1. Ir a Playlist (vista 3)
2. `n` → crear nueva playlist
3. `Enter` → agregar archivo seleccionado
4. `d` → eliminar entrada
5. `[]` → cambiar entre playlists

#### Favoritos
1. En cualquier vista, presionar `f` → toggle favorito
2. Ir a Favoritos (vista 6)
3. `Enter` → reproducir
4. `d` → eliminar de favoritos

#### Configuración
1. Ir a Config (vista 5)
2. `←/→` → cambiar tema
3. `w/W` → cambiar volumen
4. Verificar que los cambios persisten en config.json

#### Undo/Redo
1. Hacer cambios en Explorer (mover, renombrar, eliminar)
2. `u` → undo
3. `U` → redo

### Verificar en diferentes tamaños de terminal
- 80x24 (mínimo)
- 120x40 (normal)
- 200x60 (grande)

### Verificar
- [ ] No hay errores en error.log
- [ ] Colores se aplican correctamente
- [ ] Scroll funciona en todas las vistas
- [ ] Resize (SIGWINCH) no rompe la UI
