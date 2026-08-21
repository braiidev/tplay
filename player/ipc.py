"""IPC: control externo de tplay via Unix domain socket.

Permite play/pausa/stop/next/prev/volumen/status desde fuera (tmux,
scripts) con `tplay --ctl <cmd>`. El server corre en un daemon thread;
los comandos mutantes se encolan y el main loop los ejecuta (nunca se
toca curses ni VLC desde este thread).
"""
from __future__ import annotations

import os
import socket
import threading
from typing import Callable

COMMANDS: frozenset[str] = frozenset({
    "toggle", "play", "pause", "stop", "next", "prev",
    "vol+", "vol-", "status",
})
MAX_CMD_LEN = 64
RECV_TIMEOUT = 2.0
RESP_BUF = 256


def socket_path() -> str:
    """Path del socket: $XDG_RUNTIME_DIR (ideal, 0700) o ~/.local/state."""
    runtime = os.environ.get("XDG_RUNTIME_DIR", "")
    if runtime:
        base = os.path.join(runtime, f"tplay-{os.getuid()}")
    else:
        base = os.path.expanduser("~/.local/state/tplay")
    return os.path.join(base, "ctl.sock")


def is_valid_command(cmd: str) -> bool:
    """Whitelist exacta + 'vol <0-100>'."""
    if not cmd or len(cmd) > MAX_CMD_LEN:
        return False
    if cmd in COMMANDS:
        return True
    if cmd.startswith("vol "):
        arg = cmd[4:]
        return arg.isdigit() and len(arg) <= 3
    return False


def dispatch_command(
    cmd: str, on_command: Callable[[str], str],
) -> str:
    """Valida y despacha. Retorna respuesta para el cliente."""
    if not cmd:
        return "ERR: comando vacío"
    if len(cmd) > MAX_CMD_LEN:
        return f"ERR: comando demasiado largo (max {MAX_CMD_LEN})"
    if not is_valid_command(cmd):
        return f"ERR: comando desconocido '{cmd[:32]}'"
    try:
        return on_command(cmd)
    except Exception:
        return "ERR: error interno"


class IpcServer:
    """Server Unix socket — un comando por conexión."""

    def __init__(
        self, srv: socket.socket, path: str,
        on_command: Callable[[str], str],
    ) -> None:
        self._srv: socket.socket = srv
        self._path: str = path
        self._on_command: Callable[[str], str] = on_command
        self._running: bool = True
        self._thread: threading.Thread = threading.Thread(
            target=self._serve_loop, daemon=True,
        )

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        try:
            self._srv.close()
        except OSError:
            pass
        try:
            os.unlink(self._path)
        except OSError:
            pass

    def _serve_loop(self) -> None:
        self._srv.settimeout(1.0)
        while self._running:
            try:
                conn, _ = self._srv.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            self._handle_conn(conn)

    def _handle_conn(self, conn: socket.socket) -> None:
        try:
            conn.settimeout(RECV_TIMEOUT)
            data = conn.recv(MAX_CMD_LEN + 1)
            cmd = data.decode("utf-8", errors="replace").strip()
            resp = dispatch_command(cmd, self._on_command)
            conn.sendall(resp.encode("utf-8"))
        except (OSError, UnicodeDecodeError):
            pass
        finally:
            try:
                conn.close()
            except OSError:
                pass


def _ensure_dir(path: str) -> None:
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    try:
        os.chmod(d, 0o700)
    except OSError:
        pass


def start_server(
    path: str, on_command: Callable[[str], str],
) -> IpcServer:
    """Crea y arranca el server. Lanza OSError si no puede bind."""
    _ensure_dir(path)
    try:
        os.unlink(path)
    except OSError:
        pass
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(path)
    srv.listen(2)
    server = IpcServer(srv, path, on_command)
    server.start()
    return server


def send_command(cmd: str, path: str | None = None) -> str:
    """Cliente: envía un comando y retorna la respuesta.

    Raises:
        FileNotFoundError: tplay no está corriendo (socket inexistente).
        ConnectionRefusedError: socket stale.
        OSError: otros errores de red.
    """
    p = path if path is not None else socket_path()
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(RECV_TIMEOUT)
    try:
        s.connect(p)
        s.sendall(cmd.encode("utf-8")[:MAX_CMD_LEN + 1])
        resp = s.recv(RESP_BUF)
    finally:
        s.close()
    return resp.decode("utf-8", errors="replace").strip()
