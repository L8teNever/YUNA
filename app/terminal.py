import os
import pty
import fcntl
import termios
import struct
import select
import eventlet


class TerminalSession:
    def __init__(self, sid, socketio):
        self.sid = sid
        self.socketio = socketio
        self.fd = None
        self.pid = None
        self._alive = False

    def start(self, cols=80, rows=24):
        self.pid, self.fd = pty.fork()
        if self.pid == 0:
            env = os.environ.copy()
            env["TERM"] = "xterm-256color"
            env["COLORTERM"] = "truecolor"
            os.execvpe("/bin/bash", ["/bin/bash", "--login"], env)
        else:
            self._resize(cols, rows)
            self._alive = True
            self.socketio.start_background_task(self._read_loop)

    def write(self, data: str):
        if self.fd and self._alive:
            try:
                os.write(self.fd, data.encode())
            except OSError:
                self._alive = False

    def resize(self, cols: int, rows: int):
        if self.fd and self._alive:
            self._resize(cols, rows)

    def _resize(self, cols: int, rows: int):
        winsize = struct.pack("HHHH", rows, cols, 0, 0)
        fcntl.ioctl(self.fd, termios.TIOCSWINSZ, winsize)

    def _read_loop(self):
        while self._alive:
            try:
                r, _, _ = select.select([self.fd], [], [], 0.05)
                if r:
                    data = os.read(self.fd, 4096)
                    if not data:
                        break
                    self.socketio.emit(
                        "output",
                        {"data": data.decode("utf-8", errors="replace")},
                        room=self.sid,
                    )
                else:
                    eventlet.sleep(0)
            except (OSError, ValueError):
                break
        self._alive = False
        try:
            self.socketio.emit("disconnect_terminal", {}, room=self.sid)
        except Exception:
            pass

    def kill(self):
        self._alive = False
        try:
            os.close(self.fd)
        except OSError:
            pass
        try:
            os.waitpid(self.pid, os.WNOHANG)
        except (ChildProcessError, OSError):
            pass


_sessions: dict[str, TerminalSession] = {}


def create_session(sid, socketio, cols=80, rows=24) -> TerminalSession:
    session = TerminalSession(sid, socketio)
    session.start(cols, rows)
    _sessions[sid] = session
    return session


def get_session(sid) -> TerminalSession | None:
    return _sessions.get(sid)


def remove_session(sid):
    session = _sessions.pop(sid, None)
    if session:
        session.kill()
