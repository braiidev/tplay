# COMPACT_SPEC.md — tplay v0.3.x

> Documento único de consenso. Última palabra del proyecto.
> Construido mediante entrevista directa entre dev + opencode.

---

## 1. IDENTIDAD

| Campo         | Valor                                                                       |
| ------------- | --------------------------------------------------------------------------- |
| **Nombre**    | tplay                                                                       |
| **Versión**   | 1.4.26 (semver: x = etapa, y = cambios/avances, z = sub-etapas)             |
| **Propósito** | Reproductor multimedia TUI completo. Video se reproduce solo track de audio |
| **Frase**     | Terminal Player — tu música en la terminal                                  |

---

## 2. STACK TECNOLÓGICO

| Componente   | Tecnología                               |
| ------------ | ---------------------------------------- |
| Lenguaje     | Python 3.10+                             |
| TUI          | `curses` (stdlib)                        |
| Motor        | `python-vlc` (≥3.0.0), `--no-video`      |
| Metadatos    | `mutagen` (≥1.46.0)                      |
| Persistencia | JSON en `~/.config/tplay/data/`          |
| Formateo     | black (Python), prettier (JS si hubiera) |
| LSP          | pyright                                  |
| Testing      | pytest                                   |

### Formatos soportados

| Tipo  | Extensiones                                 |
| ----- | ------------------------------------------- |
| Audio | `.mp3`, `.flac`, `.wav`, `.ogg`             |
| Video | `.mp4`, `.mkv`, `.avi`, `.mov` (solo audio) |

---

## 3. VISTAS

| ID  | Nombre        | Tecla | Descripción                                         |
| --- | ------------- | ----- | --------------------------------------------------- |
| 0   | **Config**    | `0`   | Preferencias, keybindings, temas                    |
| 1   | **Listen**    | `1`   | Vista principal. Reproducción activa + Stack toggle |
| 2   | **Explorer**  | `2`   | Navegación de directorios, ops de archivo           |
| 3   | **Playlist**  | `3`   | Gestión de playlists (CRUD)                         |
| 4   | **Historial** | `4`   | Últimos 100 reproducidos, con contador              |
| 5   | **Radio**     | `5`   | Radios guardadas, CRUD, export M3U                  |
| 6   | **Favoritos** | `6`   | Acceso rapido a favoritos con <f>                   |

### Acciones transversales (funcionan en cualquier vista)

| Tecla    | Acción                                            |
| -------- | ------------------------------------------------- |
| `Space`  | Play / Pause toggle                               |
| `S`      | Stop (desde cualquier vista)                      |
| `n` / `b`| Siguiente / anterior track                        |
| `+` / `-`| Volumen +5 / -5                                   |
| `0-6`    | Cambiar vista                                     |
| `?` / `F1`| Help overlay con pestañas por vista              |
| `q`      | Salir (guarda todo)                               |
| `Esc`    | Cancelar/cerrar overlay (Stack, Goto, KB, DirPicker, Help). En Historial: volver a Listen |

---

## 4. MATRIZ DE TECLAS POR VISTA

### Vista 1 — Listen

| Tecla     | Acción                                          |
| --------- | ----------------------------------------------- |
| `Space`   | Play / Pause toggle                             |
| `S`       | Stop (global, desde cualquier vista)            |
| `s`       | Stop (solo en Listen)                           |
| `n`       | Siguiente item en Stack                         |
| `b`       | Anterior item en Stack                          |
| `+`       | Volumen +5                                      |
| `k`       | Volumen +5                                      |
| `-`       | Volumen -5                                      |
| `j`       | Volumen -5                                      |
| `m`       | Mute toggle                                     |
| `r`       | Shuffle toggle (global, afecta todo el Stack)   |
| `R`       | Repeat toggle (global, loop infinito del Stack) |
| `t`       | Sleep timer toggle (on/off)                     |
| `T`       | Sleep timer config (prompt minutos)             |
| `g`       | Goto (seek dentro del track actual)             |
| `f`       | Agregar/quitar playhead a Favoritos             |
| `h` / `l` | Seek -5s / +5s                                  |
| `Tab`     | Toggle Stack sub-vista (contenido del Slot)     |

#### Sub-vista Stack (Tab dentro de Listen)

| Tecla             | Acción                                                |
| ----------------- | ----------------------------------------------------- |
| `hjkl` / `arrows` | Navegar items                                         |
| `Enter`           | Mover playhead al item (sin overwrite)                |
| `f`               | Agregar/quitar item a favoritos                       |
| `d`               | Eliminar item (con confirmación)                      |
| `x`               | Limpiar todo el Stack (con confirmación)              |
| `s`               | Guardar Stack como playlist (prompt nombre)           |
| `J` / `K`         | Reordenar (mover abajo / arriba)                      |
| `r` / `R`         | Alternar modo del item: Normal → Repeat 1x → Repeat ∞ |
| `g` / `G`         | Ir al inicio / fin                                    |
| `Tab` / `Esc`     | Cerrar Stack                                          |

> **Audio al vaciar Stack**: al eliminar el último item (`d` o `x`), se detiene la reproducción automáticamente.

##### Modos por item (Stack)

| Modo          | Comportamiento                                                         |
| ------------- | ---------------------------------------------------------------------- |
| **Normal**    | Item suena 1 vez, avanza al siguiente                                  |
| **Repeat 1x** | Item suena 2 veces, luego avanza                                       |
| **Repeat ∞**  | Item loopea hasta que el usuario lo cambie manualmente o salte de item |

##### Modos globales (Listen, fuera del Stack)

| Modo              | Ámbito        | Comportamiento                                     |
| ----------------- | ------------- | -------------------------------------------------- |
| **Shuffle** (`r`) | Todo el Stack | Orden aleatorio. Se desactiva al vaciarse el Stack |
| **Repeat** (`R`)  | Todo el Stack | Loop infinito del Stack completo                   |

---

### Vista 2 — Explorer

| Tecla                   | Acción                                                           |
| ----------------------- | ---------------------------------------------------------------- |
| `Enter`                 | **Dir**: navegar dentro. **File**: overwrite Stack + reproducir  |
| `h` / `←` / `Backspace` | Ir al directorio padre                                           |
| `~`                     | Ir al home (`~`)                                                 |
| `g` / `G`               | Ir al inicio / fin del listado                                   |
| `a`                     | Añadir item al **final** del destino (presiona `s`=Stack, `p`=Playlist activa, `Esc`=cancelar) |
| `A`                     | Añadir item **tras el playhead** del destino (`s`=Stack, `p`=Playlist activa, `Esc`=cancelar) |
| `C`                     | Copiar archivo/directorio (navegar destino + Enter confirma)     |
| `V`                     | Mover archivo/directorio (navegar destino + Enter confirma)      |
| `E`                     | Renombrar archivo/directorio (prompt)                            |
| `I`                     | Editar tags ID3 del track (prompt: title → artist → album)       |
| `d`                     | Eliminar archivo/carpeta vacía (con confirmación)                |
| `M`                     | Crear directorio (prompt nombre)                                 |
| `P`                     | Reproducir carpeta (carga todos los tracks al Stack)             |
| `F5`                    | Refresh (recargar listado del directorio actual)                 |
| `/`                     | Búsqueda inline (filtro por nombre)                              |
| `f`                     | Agregar/Quitar item a favoritos                                  |
| `F`                     | Abre vista [6] Favoritos                                         |


---

### Vista 3 — Playlist

| Tecla     | Acción                                                          |
| --------- | --------------------------------------------------------------- |
| `Enter`   | Overwrite Stack con toda la playlist + reproducir desde track 1 |
| `d`       | Eliminar item de la playlist (con confirmación)                 |
| `x`       | Limpiar toda la playlist (con confirmación)                     |
| `c`       | Crear nueva playlist (prompt nombre)                            |
| `E`       | Renombrar item en la playlist (prompt nuevo nombre)             |
| `R`       | Renombrar playlist (prompt nuevo nombre)                        |
| `D`       | Eliminar playlist (con confirmación)                            |
| `J` / `K` | Reordenar item (mover abajo / arriba)                           |
| `[` / `]` o `h` / `l` | Playlist anterior / siguiente                                   |
| `s`       | Guardar playlist                                                |
| `g` / `G` | Ir al inicio / fin                                              |
| `/`       | Búsqueda inline (filtro por nombre/path)                        |
| `f`       | Agregar/Quitar item a favoritos                                 |

> **Nota**: No existe playlist "default". Si no hay playlists, se muestra helper instructivo.

---

### Vista 4 — Historial

| Tecla     | Acción                                                  |
| --------- | ------------------------------------------------------- |
| `Enter`   | Overwrite Stack con ese track + reproducir              |
| `d`       | Eliminar entrada del historial (con confirmación)       |
| `x`       | Limpiar todo el historial (con confirmación)            |
| `a`       | Añadir al **final** del destino (solo Stack, sin prompt) |
| `A`       | Añadir **tras el playhead** del destino (solo Stack) |
| `g` / `G` | Ir al inicio / fin                                      |
| `f`       | Agregar/Quitar item a favoritos                         |

> Formato entrada: nombre_archivo (visible), path + contador (interno).
> Si el archivo ya no existe: muestra "Archivo Inexistente" sin interrumpir nada.

---

### Vista 5 — Radio

| Tecla     | Acción                                                  |
| --------- | ------------------------------------------------------- |
| `Enter`   | Reproducir radio (carga en Stack + cambia a Listen)     |
| `a`       | Agregar radio (prompt nombre → prompt URL)              |
| `d`       | Eliminar radio (con confirmación)                       |
| `E`       | Editar radio (ciclo: nombre → URL, Enter guarda) |
| `s`       | Guardar radios a archivo                                |
| `X`       | Exportar como M3U                                       |
| `j` / `k` | Cursor abajo / arriba                                   |
| `g` / `G` | Ir al inicio / fin                                      |
| `f`       | Agregar/Quitar item a favoritos                         |

> Las radios se guardan en `radios.json`. Al reproducir, se añade al historial automáticamente.

---

### Vista 0 — Config

| Tecla                   | Acción                                       |
| ----------------------- | -------------------------------------------- |
| `↑` `↓` / `k` `j`      | Navegar items de configuración               |
| `←` `→` / `Enter`      | Cambiar valor del item seleccionado          |
| `[` `]` / `H` `L`       | Navegar pestañas de configuración            |
| `Enter` en Keybindings  | Abrir sub-vista de keybindings               |
| `Enter` en music_dir    | Abrir selector de directorio (DirPicker)     |
| `Esc` / `q`             | Volver a Listen (o salir si es `q` global)   |

> Pestañas posicionales: `◀ [general] │ apariencia │ sistema ▶`
> La pestaña activa se marca con `[...]`, se navega con `[`/`]` o `H`/`L` (Shift).

> Items de configuración (ordenados por tipo):
>
> 1. Directorio de música (path) — abre DirPicker con Enter
> 2. Volumen (int)
> 3. Tema (choice: clásico, mono, cálido, alto_contraste, custom)
> 4. Sleep timer minutos (int)
> 5. Modo keybindings (custom/default)
> 6. Keybindings (acción → abre subvista)
> 7. Actualizacion [Comprobar]

#### Sub-vista DirPicker

| Tecla                   | Acción                                       |
| ----------------------- | -------------------------------------------- |
| `j` / `k` / `↑` `↓`    | Cursor abajo / arriba                        |
| `h` / `←` / `Backspace`| Ir al directorio padre                       |
| `l` / `→` / `Enter`    | Entrar directorio / seleccionar              |
| `~`                     | Ir a home                                    |
| `g` / `G`               | Ir al inicio / fin                           |
| `Esc`                   | Cancelar                                     |

---

## 5. STACK DE REPRODUCCIÓN (Slot)

### Concepto

```
Fuentes (CDs)          Stack (Slot)          Reproductor
┌──────────┐          ┌──────────────┐       ┌──────────┐
│ Track    │──Enter──→│ [t1, t2, t3, │──────→│  Listen  │
│ Playlist │──Enter──→│  t4, t5, t6] │       │  (VLC)   │
│ Carpeta  │──(fut.)→│ └──────────────┘       └──────────┘
└──────────┘                ↑
                        Tab para ver
                        y gestionar
```

### Reglas del Stack

- **Único**: solo existe un Stack global
- **Overwrite total** con `Enter` en cualquier fuente: se vacía y se llena con la nueva fuente
- **Append** con `a`: agrega al final
- **Insert** con `A`: agrega **inmediatamente después del playhead**
- **No se eliminan items consumidos** — los items viven hasta que el Stack se libera o se vacía manualmente
- Al terminar el último item (sin Repeat): Stack se libera, reproducción se detiene

### Estados del Stack

| Situación                        | Comportamiento                                             |
| -------------------------------- | ---------------------------------------------------------- |
| Stack vacío + sin reproducción   | Listen muestra helper "Nada sonando. Abrí [2] Explorer..." |
| Enter en track suelto            | Stack = [track], playhead = 0, reproduce                   |
| Enter en playlist (N tracks)     | Stack = [t1, t2, ..., tN], playhead = 0, reproduce t1      |
| Termina último item (Repeat off) | Stack se vacía, stop                                       |
| Termina último item (Repeat on)  | Loop al inicio del Stack                                   |
| Tab desde Listen                 | Muestra contenido del Stack para gestionar                 |

---

## 6. PLAYBACK ENGINE

| Acción      | Implementación                                        |
| ----------- | ----------------------------------------------------- |
| Play        | `python-vlc`, `--no-video`                            |
| Seek        | `player.set_time()`                                   |
| Sleep timer | `time.monotonic()` en loop principal. Stop al expirar |
| Goto        | Modo inline en Listen con mm:ss, Enter salta          |

---

## 7. DIÁLOGOS Y PROMPTS

### Confirmación

```
╭─────────────────╮
│ ¿Eliminar archivo?  │
│      s/N       │   ← s / S / Enter = sí | Esc = no
╰─────────────────╯
```

### Prompt de texto

```
╭──────────────────────╮
│ Nombre playlist: ____  │
╰──────────────────────╯
```

- Enter vacío = Esc (cancela)
- Max 60 caracteres
- Backspace borra

---

## 8. PERSISTENCIA

| Archivo         | Ruta                    | Contenido                                                                                  |
| --------------- | ----------------------- | ------------------------------------------------------------------------------------------ |
| `config.json`   | `~/.config/tplay/data/` | music_dir, volume, theme, custom_colors, sleep_timer_minutes, keybinding_mode, keybindings |
| `playlist.json` | ídem                    | `{active, playlists: [{name, songs}]}`                                                     |
| `state.json`    | ídem                    | `{playing, file, position}` para reanudación                                               |
| `history.json`  | ídem                    | `[{name, path, count}]` último 100                                                         |

---

## 9. UNDO / REDO

| Ámbito       | Push snapshot      | Acciones que guardan                                          |
| ------------ | ------------------ | ------------------------------------------------------------- |
| **Playlist** | Antes de modificar | Crear, eliminar, renombrar, reordenar, limpiar, eliminar item |
| **Stack**    | Antes de modificar | Eliminar item, limpiar, reordenar, guardar como playlist      |
| **Explorer** | Antes de modificar | Renombrar, eliminar, mover (copia no se deshace)              |

> Max 50 niveles. Redo se limpia al hacer un nuevo push.

---

## 10. ESTRUCTURA DEL PROYECTO

```
tplay/
├── app.py                    # Entry point: from player import main(); main()
├── COMPACT_SPEC.md           # Este documento
├── TODO.md                   # Pendientes
├── install.sh                # Instalación
├── requirements.txt          # python-vlc, mutagen
├── .gitignore
├── README.md
└── player/
    ├── __init__.py            # main() + CLI args
    ├── app.py                 # PlayerApp: init, run(), orquestación
    ├── audio.py               # AudioEngine: wrapper VLC
    ├── config.py              # Config, temas, colores
    ├── file_utils.py          # list_dir, is_media, time_str, etc.
    ├── handlers.py            # Input por vista
    ├── keybindings.py         # Sistema de bindings
    ├── metadata.py            # MetadataCache (mutagen)
    ├── playlist.py            # CRUD de playlists
    ├── stack.py               # Stack de reproducción
    ├── state.py               # Sesión (reanudar)
    ├── ui.py                  # Primitivas UI (box, nav, status, prompt, help)
    └── views.py               # Dibujado por vista
```

---

## 11. COMPORTAMIENTO ESPERADO (NO NEGOCIABLE)

| Situación                              | Debe hacer                                       |
| -------------------------------------- | ------------------------------------------------ |
| Primer inicio (sin data)               | Crear defaults, mostrar Listen vacío con helper  |
| Archivo de playlist/historial corrupto | Ignorar y empezar limpio                         |
| Archivo en historial ya no existe      | Mostrar "Archivo Inexistente", no interrumpir    |
| Enter en track suelto                  | Overwrite Stack inmediatamente                   |
| Enter en playlist (N tracks)           | Overwrite Stack con N tracks, play track 1       |
| Stack vacío y termina canción          | Detener reproducción, mostrar helper             |
| Prompt vacío + Enter                   | = Esc (cancelar)                                 |
| Borrar (d) en cualquier lista          | Confirmación previa obligatoria                  |
| Salir (q)                              | Guardar todo (config, playlists, state, history) |

---

## 12. FEATURES FUTUROS (REGISTRADOS)

| Feature                  | Descripción                                        |
| ------------------------ | -------------------------------------------------- |
| Ecualizador              | Vía API VLC                                        |
| Mouse support            | Clicks curses                                      |
| Cover art                | vía chafa/viu                                      |

> Se implemento Carpeta como Fuente (CD) -- Ver keybiding [Explorer] <P>
> Se implemento Exportar M3U -- Ver keybiding <X>
> Se implemento auto-import de M3U desde vista [Explorer]
> Se implemento vista Favoritos
> **Modo radio** (URL/stream) con vista unica desde [Radio]

---

_Este documento es la fuente de verdad. Cualquier discrepancia con el código
se resuelve a favor de COMPACT_SPEC.md._
