#!/usr/bin/env python3
"""build_server_tools.py — write what the plugin's launcher answers with, from the real server (DESIGN.md §16).

The launcher answers Claude Code's `initialize` and `tools/list` before the real server is up, so what it answers must
be the real server's own. This asks the self-interpreter over stdio, as a client does, with the `python3` running this
script: `initialize` asking for a protocol version newer than any — the real server answers its newest, and its
capabilities — then `notifications/initialized`, then `tools/list`. It writes `server/initialize.json` (that answer)
and `server/tools.json` (the tool list). Run it where `si` imports from this tree (`./install.sh`); `--check` writes
nothing and exits 1 when either stored file differs from the server's answer, or when the server stops serving tools.

    python3 scripts/build_server_tools.py [--check]
"""
from __future__ import annotations

import json
import queue
import subprocess
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERVER = ROOT / "server"
NEWER_THAN_ANY = "9999-12-31"


def live(timeout: float = 120) -> tuple[dict, dict]:
    """The self-interpreter's own answers to `initialize` (asking for a version newer than any) and `tools/list`."""
    p = subprocess.Popen([sys.executable, "-m", "si.server"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL)
    q: queue.Queue = queue.Queue()
    threading.Thread(target=lambda: [q.put(line) for line in p.stdout], daemon=True).start()

    def send(msg: dict) -> None:
        p.stdin.write((json.dumps(msg) + "\n").encode("utf-8"))
        p.stdin.flush()

    def wait(mid: int) -> dict:
        while True:
            msg = json.loads(q.get(timeout=timeout))
            if msg.get("id") == mid:
                return msg

    try:
        send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": NEWER_THAN_ANY, "capabilities": {}, "clientInfo": {"name": "build_server_tools", "version": "1"}}})
        init = wait(1)["result"]
        send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        return init, wait(2)["result"]
    finally:
        p.stdin.close()
        p.terminate()


def render(obj: dict) -> str:
    return json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv: list[str]) -> int:
    init, tools = live()
    if "tools" not in init.get("capabilities", {}):
        print("✗ the self-interpreter no longer serves tools — the launcher's answers cannot stand for it")
        return 1
    files = {SERVER / "initialize.json": render(init), SERVER / "tools.json": render(tools)}
    if "--check" in argv:
        stale = [f.relative_to(ROOT).as_posix() for f, text in files.items()
                 if not f.is_file() or f.read_text(encoding="utf-8") != text]
        if stale:
            print(f"✗ {' · '.join(stale)} differ from the self-interpreter's own answers — run scripts/build_server_tools.py")
            return 1
        print(f"✓ server/initialize.json and server/tools.json are the self-interpreter's own answers "
              f"(protocol {init['protocolVersion']}, {len(tools['tools'])} tools)")
        return 0
    for f, text in files.items():
        f.write_text(text, encoding="utf-8")
    print(f"✓ wrote server/initialize.json (protocol {init['protocolVersion']}) and server/tools.json "
          f"({len(tools['tools'])} tools)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
