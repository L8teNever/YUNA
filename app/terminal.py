import os
import pty
import fcntl
import termios
import struct
import threading


class TerminalSession:
    def __init__(self, sid, emit_fn):
        self.sid = sid
        self.emit_fn = emit_fn
        self.fd = None
        self.pid = None
        self._alive = False
        self._thread = None

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
            self._thread = threading.Thread(target=self._read_loop, daemon=True)
            self._thread.start()

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
                data = os.read(self.fd, 1024)
                if not data:
                    break
                self.emit_fn("output", {"data": data.decode("utf-8", errors="replace")}, to=self.sid)
            except OSError:
                break
        self._alive = False
        self.emit_fn("disconnect_terminal", {}, to=self.sid)

    def kill(self):
        self._alive = False
        try:
            os.close(self.fd)
        except OSError:
            pass
        try:
            os.waitpid(self.pid, os.WNOHANG)
        except ChildProcessError:
            pass


_sessions: dict[str, TerminalSession] = {}


def create_session(sid, emit_fn, cols=80, rows=24) -> TerminalSession:
    session = TerminalSession(sid, emit_fn)
    session.start(cols, rows)
    _sessions[sid] = session
    return session


def get_session(sid) -> TerminalSession | None:
    return _sessions.get(sid)


def remove_session(sid):
    session = _sessions.pop(sid, None)
    if session:
        session.kill()
