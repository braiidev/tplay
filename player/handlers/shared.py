from __future__ import annotations

import curses
import os
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from ..file_utils import is_media as _is_media_file
from ..file_utils import is_url as _is_url
from ..stack import StackItem

if TYPE_CHECKING:
    from player.app import PlayerApp


def _prompt(app: PlayerApp, label: str, callback: Callable[..., None],
            initial: str = "") -> None:
    app.dialog = {"type": "prompt", "label": label, "buf": initial,
                  "callback": callback, "scroll": 0, "cursor_pos": len(initial)}
    curses.curs_set(1)
    curses.flushinp()


def _toast(app: PlayerApp, msg: str) -> None:
    app.toast(msg)


def _confirm(app: PlayerApp, label: str, callback: Callable[..., None]) -> None:
    app.dialog = {"type": "confirm", "label": label, "callback": callback}
    curses.flushinp()


def _clamp_scroll(cursor: int, scroll: int, list_h: int) -> int:
    if cursor < scroll:
        return cursor
    if cursor >= scroll + list_h:
        return cursor - list_h + 1
    return scroll


def _page_size(app: PlayerApp) -> int:
    h, _ = app.stdscr.getmaxyx()
    return int(max(1, h - app.LIST_H))


def _play_file_direct(app: PlayerApp, path: str) -> None:
    if not os.path.isfile(path):
        return
    app.stack.items = [StackItem(path=path, name=os.path.basename(path))]
    app.audio.play_file(path)
    app.current_view = app.V_LISTEN


def _do_clear_stack(app: PlayerApp) -> None:
    app._push_snapshot()
    app.audio.stop()
    app.stack.clear()


def _save_stack_as_playlist_cb(app: PlayerApp, name: str) -> None:
    if name and name not in app.playlist_data:
        app.playlist_data[name] = [(item.name, item.path) for item in app.stack.items]
        from ..playlist import save_all as _save_all
        _save_all(app.playlist_data, app.active_name)
        _toast(app, f"Lista '{name}' creada desde pila")


def _export_as_m3u(app: PlayerApp, filename: str) -> None:
    if not app.stack.items:
        _toast(app, "Stack vacío, nada que exportar")
        return
    filename = filename.strip()
    if not filename:
        return
    if not filename.endswith(".m3u"):
        filename += ".m3u"
    music_dir = app.config.get("music_dir", os.path.expanduser("~/Music"))
    dest = os.path.join(music_dir, filename)
    try:
        lines: list[str] = ["#EXTM3U\n"]
        for item in app.stack.items:
            lines.append(f"#EXTINF:-1,{item.name}\n")
            lines.append(f"{item.path}\n")
        with open(dest, "w", encoding="utf-8") as f:
            f.writelines(lines)
        _toast(app, f"Exportado a {filename}")
    except Exception as e:
        _toast(app, f"Error al exportar: {e}")


def _prompt_export_m3u(app: PlayerApp) -> None:
    _prompt(app, "Exportar pila como M3U", _export_as_m3u, "tplay_stack.m3u")


def _parse_m3u(filepath: str) -> list[str]:
    paths: list[str] = []
    base = os.path.dirname(os.path.abspath(filepath))
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if _is_url(line):
                paths.append(line)
            else:
                p = line if os.path.isabs(line) else os.path.normpath(os.path.join(base, line))
                if os.path.isfile(p):
                    paths.append(p)
    return paths


def _parse_pls(filepath: str) -> list[str]:
    paths: list[str] = []
    base = os.path.dirname(os.path.abspath(filepath))
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line.lower().startswith("file"):
                _, _, val = line.partition("=")
                val = val.strip()
                if val:
                    if _is_url(val):
                        paths.append(val)
                    else:
                        p = val if os.path.isabs(val) else os.path.normpath(os.path.join(base, val))
                        if os.path.isfile(p):
                            paths.append(p)
    return paths


def _import_m3u_pls_cb(app: PlayerApp, filepath: str) -> None:
    filepath = filepath.strip()
    if not filepath:
        return
    if not os.path.isfile(filepath):
        _toast(app, "Archivo no encontrado")
        return
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".pls":
        paths = _parse_pls(filepath)
    else:
        paths = _parse_m3u(filepath)
    if not paths:
        _toast(app, "No se encontraron canciones válidas")
        return
    items = [StackItem(path=p, name=os.path.basename(p)) for p in paths]
    if app.current_view == app.V_LISTEN:
        for item in items:
            app.stack.append(item)
        _toast(app, f"Importadas {len(items)} canciones al Stack")
    else:
        app._push_snapshot()
        app.playlist_data[app.active_name].extend([(item.name, item.path) for item in items])
        from ..playlist import save_all as _save_all
        _save_all(app.playlist_data, app.active_name)
        _toast(app, f"Importadas {len(items)} canciones a '{app.active_name}'")


def _prompt_import_m3u_pls(app: PlayerApp) -> None:
    music_dir = app.config.get("music_dir", os.path.expanduser("~/Music"))
    _prompt(app, "Importar M3U/PLS", _import_m3u_pls_cb, os.path.join(music_dir, ""))


def _rename_file(app: PlayerApp, full: str, name: str,
                 on_rename: Callable[..., None] | None = None) -> None:
    _, ext = os.path.splitext(name)

    def _do_rename(app: PlayerApp, old_path: str, new_path: str) -> None:
        try:
            app._push_snapshot()
            os.rename(old_path, new_path)
            if on_rename:
                on_rename(app, old_path, new_path)
        except Exception as e:
            _toast(app, f"Error al renombrar: {e}")

    def _cb(app: PlayerApp, buf: str) -> None:
        if not buf or buf == name:
            return
        if not os.path.splitext(buf)[1]:
            buf += ext
        new_path = os.path.join(os.path.dirname(full), buf)
        if new_path == full:
            return
        if os.path.exists(new_path):
            _confirm(app,
                     f"'{buf}' ya existe. Si continuas se sobreescribirá. ¿Continuar?",
                     lambda: _do_rename(app, full, new_path))
        else:
            _do_rename(app, full, new_path)

    _prompt(app, "Renombrar a", _cb, name)


def _update_refs_after_rename(app: PlayerApp, old_path: str, new_path: str) -> None:
    new_name = os.path.basename(new_path)
    for pl_name in app.playlist_data:
        songs = app.playlist_data[pl_name]
        for i, (n, p) in enumerate(songs):
            if p == old_path:
                songs[i] = (new_name, new_path)
    if app.active_name in app.playlist_data:
        from ..playlist import save_all as _save_all
        _save_all(app.playlist_data, app.active_name)
    for entry in app.history:
        if entry.get("path") == old_path:
            entry["path"] = new_path
            entry["name"] = new_name


def _open_tag_editor(app: PlayerApp, full: str) -> None:
    if not _is_media_file(full):
        _toast(app, "No es un archivo multimedia")
        return
    meta = app.meta_cache.get(full)
    app.meta_edit_file = full
    app.meta_edit_fields = [
        ('Título', 'title', (meta and meta.get('title')) or ''),
        ('Artista', 'artist', (meta and meta.get('artist')) or ''),
        ('Álbum', 'album', (meta and meta.get('album')) or ''),
        ('Género', 'genre', (meta and meta.get('genre')) or ''),
    ]
    app.meta_edit_changed = {}
    app.meta_edit_cursor = 0
    app.meta_edit_editing = False
    app.meta_edit_mode = True


def _handle_update(app: PlayerApp) -> None:
    app._check_updates()
    if app.update_available:
        n = app.update_behind
        s = "s" if n != 1 else ""
        _confirm(app, f"Actualización disp. ({n} commit{s}) ¿Descargar?", lambda: _do_update(app))
    else:
        _toast(app, "Sin actualizaciones disponibles")


def _do_update(app: PlayerApp) -> None:
    ok, msg = app._apply_updates()
    if ok:
        app.update_available = False
        _restart_app(app)
    else:
        _toast(app, msg)


def _restart_app(app: PlayerApp) -> None:
    import sys
    try:
        app._save_session()
        app.audio.player.stop()
        curses.endwin()
        app_path = os.path.join(app._repo_dir, "app.py")
        os.execv(sys.executable, [sys.executable, app_path])
    except Exception:
        _toast(app, "Error al reiniciar, reiniciá manualmente")
