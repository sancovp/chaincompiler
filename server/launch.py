"""launch.py — the self-interpreter's launcher, what the plugin's `.mcp.json` runs (DESIGN.md §16).

Claude Code gives an MCP server thirty seconds to answer `initialize`, and a plugin cannot lengthen that. The real
server, `si-server` from the PyPI distribution `chaincompiler-si`, is run through uv; on a machine whose uv cache is empty
uv first installs its seventy-odd packages, and its first answer comes a minute or more later. So this launcher, which
needs nothing but the standard library, answers the connection itself and starts the real server behind it:

- `initialize` is answered at once, as the real server would answer it — the protocol version the client asks for, or
  the newest the real server speaks when the client asks for a newer one, and the capability it serves, its tools —
  from `initialize.json` beside it; `tools/list` and `ping` are answered at once, the list from `tools.json`. Both files
  are written from the real server's own answers by `scripts/build_server_tools.py`.
- `server/discover`, the probe a newer client sends before `initialize`, is refused at once as a method this connection
  does not serve, so the client goes straight to `initialize` instead of waiting out its probe.
- The real server is started with the arguments the launcher was given, through `uv tool run --compile-bytecode`. Once
  it has answered its own `initialize`, every message passes through unchanged, both ways, as bytes — the real
  server's transport is UTF-8, and nothing here decodes or re-encodes what passes. One thread writes to the server, in
  the order the messages came, so the thread reading its answers never blocks on it.
- A request that arrives before then waits for it. Every request the launcher cannot deliver is answered with an error
  that says why: one held when the real server ends before it answers, one held when the client closes first, one the
  server's input refuses. A server that ends after it has served ends the launcher with it.

    uv run --no-project --quiet <plugin>/server/launch.py --from chaincompiler-si==<release> si-server
"""
from __future__ import annotations

import json
import os
import queue
import shutil
import subprocess
import sys
import threading
from collections import deque
from pathlib import Path

HERE = Path(__file__).resolve().parent
OWN_INIT = "server/launch.py:initialize"   # the id of the launcher's own initialize, never a client's


def release(args: list[str]) -> str:
    """The release the arguments pin (`chaincompiler-si==<release>`), for the answer's serverInfo."""
    for a in args:
        if a.startswith("chaincompiler-si=="):
            return a.split("==", 1)[1]
    return ""


def server_command(args: list[str]) -> list[str]:
    """The real server's command: the arguments run by `uv tool run --compile-bytecode` — the uv that ran this launcher
    when uv says which (`UV`), else the first `uv` on the PATH, else `uvx`. Bytecode is compiled once, at install, so
    every later start imports fast."""
    uv = os.environ.get("UV") or shutil.which("uv")
    return [uv, "tool", "run", "--compile-bytecode", *args] if uv else ["uvx", "--compile-bytecode", *args]


def negotiate(asked: object, newest: str) -> str:
    """The version the real server answers: the one asked for when it speaks it, else its newest (versions are dates)."""
    return asked if isinstance(asked, str) and asked and asked <= newest else newest


def encode(msg: dict) -> bytes:
    return (json.dumps(msg, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def request_id(line: bytes):
    """The id of a request (a message with a method and an id) — the messages that are owed an answer; else None."""
    try:
        msg = json.loads(line)
    except ValueError:
        return None
    return msg.get("id") if isinstance(msg, dict) and msg.get("method") and "id" in msg else None


class Launcher:
    def __init__(self, args: list[str], tools: dict, init: dict, inp=None, out=None):
        self.args, self.tools, self.init = args, tools, init
        self.inp = inp or sys.stdin.buffer
        self.out = out or sys.stdout.buffer
        self.write_lock = threading.Lock()   # one writer to the client at a time
        self.state = threading.Lock()        # guards ready / failed / closed / held together
        self.ready, self.failed, self.closed, self.held = False, "", False, []
        self.outbox: queue.Queue = queue.Queue()   # lines for the server, written in order by pump_in alone
        self.err_tail: deque[str] = deque(maxlen=12)
        self.proc: subprocess.Popen | None = None
        self.threads: list[threading.Thread] = []

    # ---- the client side
    def emit(self, line: bytes) -> None:
        with self.write_lock:
            self.out.write(line if line.endswith(b"\n") else line + b"\n")
            self.out.flush()

    def answer(self, msg: dict) -> None:
        self.emit(encode(msg))

    def error(self, mid, why: str, code: int = -32603) -> None:
        self.answer({"jsonrpc": "2.0", "id": mid, "error": {"code": code, "message": why}})

    # ---- the server side
    def start(self) -> None:
        env = dict(os.environ)
        env.pop("VIRTUAL_ENV", None)                   # the environment uv ran this launcher in is not the server's
        try:
            self.proc = subprocess.Popen(server_command(self.args), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE, env=env)
        except OSError as e:
            self.fail(f"the self-interpreter's server could not be started: {e}")
            return
        for target in (self.pump_in, self.pump_out, self.pump_err):
            t = threading.Thread(target=target, daemon=True, name=target.__name__)
            t.start()
            self.threads.append(t)

    def to_server(self, line: bytes) -> None:
        self.outbox.put(line if line.endswith(b"\n") else line + b"\n")

    def pump_in(self) -> None:
        """The one writer to the server, in order; a request it cannot deliver is answered with an error."""
        while True:
            line = self.outbox.get()
            if line is None:
                break
            try:
                self.proc.stdin.write(line)
                self.proc.stdin.flush()
            except (OSError, ValueError) as e:
                mid = request_id(line)
                if mid is not None:
                    self.error(mid, f"the self-interpreter's server could not take the request: {e}")
        try:
            self.proc.stdin.close()
        except OSError:
            pass

    def pump_err(self) -> None:
        for line in self.proc.stderr:
            self.err_tail.append(line.decode("utf-8", "replace").rstrip())
            sys.stderr.buffer.write(line)
            sys.stderr.buffer.flush()

    def pump_out(self) -> None:
        for line in self.proc.stdout:
            try:
                msg = json.loads(line)
            except ValueError:
                msg = None
            if isinstance(msg, dict) and msg.get("id") == OWN_INIT:
                if "error" in msg:
                    self.fail(f"the self-interpreter's server refused initialize: {msg['error']}")
                else:
                    self.go()
                continue
            self.emit(line)
        code = self.proc.wait()
        with self.state:
            served = self.ready
        if served:                                     # it served and ended: end with it, so the client sees it close
            for t in self.threads:
                if t.name == "pump_err":               # the server's last error lines, before the process ends
                    t.join(timeout=2)
            with self.write_lock:
                self.out.flush()
            sys.stderr.flush()
            os._exit(code)
        tail = " · ".join(t for t in self.err_tail if t)[-600:]
        self.fail(f"the self-interpreter's server ended (exit {code}) before it could answer" + (f": {tail}" if tail else ""))

    def go(self) -> None:
        """The real server answered: tell it the client is initialized, then queue what was held, in order."""
        with self.state:
            self.to_server(encode({"jsonrpc": "2.0", "method": "notifications/initialized"}))
            for line in self.held:
                self.to_server(line)
            self.held, self.ready = [], True

    def fail(self, why: str) -> None:
        with self.state:
            if self.failed:
                return
            self.failed, held, self.held = why, self.held, []
        for line in held:
            mid = request_id(line)
            if mid is not None:
                self.error(mid, why)

    # ---- the loop
    def handle(self, line: bytes) -> None:
        try:
            msg = json.loads(line)
        except ValueError:
            self.error(None, "the launcher takes one JSON-RPC message per line; this line is not JSON", -32700)
            return
        if not isinstance(msg, dict):
            self.error(None, "the launcher takes one JSON-RPC object per line, never a batch", -32600)
            return
        method, mid = msg.get("method"), msg.get("id")
        with self.state:
            ready = self.ready
        if ready:
            self.to_server(line)
        elif method == "server/discover" and mid is not None:
            self.error(mid, "server/discover is not served on this connection; use initialize", -32601)
        elif method == "initialize" and mid is not None:
            params = msg.get("params") or {}
            self.answer({"jsonrpc": "2.0", "id": mid, "result": {
                "protocolVersion": negotiate(params.get("protocolVersion"), self.init["protocolVersion"]),
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "self-interpreter", "version": release(self.args)}}})
            self.to_server(encode({"jsonrpc": "2.0", "id": OWN_INIT, "method": "initialize", "params": params}))
        elif method == "notifications/initialized":
            pass                                       # sent to the real server once it has answered its own
        elif method == "tools/list" and mid is not None:
            self.answer({"jsonrpc": "2.0", "id": mid, "result": self.tools})
        elif method == "ping" and mid is not None:
            self.answer({"jsonrpc": "2.0", "id": mid, "result": {}})
        else:
            with self.state:                           # held until the real server answers, or refused if it cannot
                failed = self.failed
                if self.ready:
                    self.to_server(line)
                elif not failed:
                    self.held.append(line)
            if failed and method and mid is not None:
                self.error(mid, failed)

    def close(self) -> None:
        """The client closed: what is held can never be delivered, so it is answered; the rest reaches the server, whose
        last answers reach the client before the launcher ends."""
        with self.state:
            held, self.held, self.closed = self.held, [], True
        for line in held:
            mid = request_id(line)
            if mid is not None:
                self.error(mid, "the client closed the connection before the self-interpreter's server was ready")
        self.outbox.put(None)
        if self.proc is not None:
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.terminate()
            for t in self.threads:
                t.join(timeout=2)

    def run(self) -> int:
        self.start()
        for line in self.inp:
            if line.strip():
                self.handle(line)
        self.close()
        return 0


def main(argv: list[str]) -> int:
    tools = json.loads((HERE / "tools.json").read_text(encoding="utf-8"))
    init = json.loads((HERE / "initialize.json").read_text(encoding="utf-8"))
    return Launcher(argv, tools, init).run()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
