"""The plugin's server launcher (`server/launch.py`, DESIGN.md §16), held to what Claude Code needs of it.

Claude Code gives a server thirty seconds to answer `initialize`. The launcher answers it, and `tools/list`, before the
real server is up, then passes every message through once it is — unchanged, as bytes — and answers every request it
cannot deliver with an error. Here a fake `uv` stands in for `uv tool run`: it records the arguments it was given and
every message it receives, waits before it serves (an install), ends without serving (a failed install), or answers
with a large result; like the real server's transport it reads and writes UTF-8 whatever the locale. The launcher's
stored answers are the real server's own, checked against the self-interpreter installed in this environment. Run from
the repository root: `python3 -m pytest scripts/tests`.
"""
from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
LAUNCH = REPO / "server" / "launch.py"
ARGS = ["--from", "chaincompiler-si==9.9.9", "si-server"]
NEWEST = json.loads((REPO / "server" / "initialize.json").read_text())["protocolVersion"]

FAKE = r'''
import json, os, sys, time
sys.stdin.reconfigure(encoding="utf-8"); sys.stdout.reconfigure(encoding="utf-8")   # as the real transport does
log = open(os.environ["FAKE_LOG"], "a", encoding="utf-8")
log.write(json.dumps({"argv": sys.argv[1:]}) + "\n"); log.flush()
if os.environ.get("FAKE_FAIL"):
    sys.stderr.write("could not install: " + os.environ["FAKE_FAIL"] + "\n"); sys.exit(3)
time.sleep(float(os.environ.get("FAKE_DELAY", "0")))
pad = "x" * int(os.environ.get("FAKE_BIG", "0"))
for line in sys.stdin:                    # one message at a time, answered before the next is read
    m = json.loads(line)
    log.write(json.dumps({"got": m.get("method"), "params": m.get("params")}, ensure_ascii=False) + "\n"); log.flush()
    if m.get("id") is None:
        continue
    if m["method"] == "initialize":
        r = {"protocolVersion": m["params"]["protocolVersion"], "capabilities": {"tools": {}}, "serverInfo": {"name": "fake"}}
    elif m["method"] == "tools/call":
        r = {"content": [{"type": "text", "text": "echo " + json.dumps(m["params"]["arguments"], ensure_ascii=False) + pad}],
             "isError": False}
    else:
        r = {}
    sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": m["id"], "result": r}, ensure_ascii=False) + "\n"); sys.stdout.flush()
'''


class Client:
    """The launcher run as Claude Code runs it, over stdio in UTF-8, with `uv` the fake."""

    def __init__(self, tmp: Path, **env: str):
        fake = tmp / "fake_server.py"
        fake.write_text(FAKE)
        uv = tmp / "uv"
        uv.write_text(f"#!/bin/sh\nexec {sys.executable} {fake} \"$@\"\n")
        uv.chmod(0o755)
        self.log = tmp / "fake.log"
        e = dict(os.environ, UV=str(uv), FAKE_LOG=str(self.log), **env)
        self.t0 = time.time()
        self.p = subprocess.Popen([sys.executable, str(LAUNCH), *ARGS], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, env=e, text=True, encoding="utf-8", bufsize=1)
        self.q: queue.Queue = queue.Queue()
        threading.Thread(target=lambda: [self.q.put(json.loads(l)) for l in self.p.stdout], daemon=True).start()

    def send(self, msg) -> None:
        self.p.stdin.write((msg if isinstance(msg, str) else json.dumps(msg, ensure_ascii=False)) + "\n")
        self.p.stdin.flush()

    def wait(self, mid, limit: float = 30) -> dict:
        end = time.time() + limit
        while time.time() < end:
            try:
                m = self.q.get(timeout=0.2)
            except queue.Empty:
                continue
            if m.get("id") == mid:
                return m
        raise AssertionError(f"no answer to {mid!r} within {limit}s")

    def open(self, version: str = "2025-06-18") -> tuple[dict, dict, float]:
        self.send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                   "params": {"protocolVersion": version, "capabilities": {}, "clientInfo": {"name": "t"}}})
        init = self.wait(1)
        self.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        self.send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        tools = self.wait(2)
        return init, tools, time.time() - self.t0

    def call(self, mid, args: dict) -> None:
        self.send({"jsonrpc": "2.0", "id": mid, "method": "tools/call", "params": {"name": "si_interpret", "arguments": args}})

    def logged(self) -> list[dict]:
        return [json.loads(l) for l in self.log.read_text(encoding="utf-8").splitlines()] if self.log.exists() else []

    def close(self) -> int:
        self.p.stdin.close()
        return self.p.wait(timeout=20)


def test_it_answers_at_once_while_the_server_installs_then_passes_a_call_through(tmp_path):
    c = Client(tmp_path, FAKE_DELAY="3")
    init, tools, took = c.open()
    assert took < 2.5, f"initialize and tools/list took {took:.1f}s — they must not wait for the server"
    assert init["result"]["serverInfo"] == {"name": "self-interpreter", "version": "9.9.9"}
    assert init["result"]["protocolVersion"] == "2025-06-18"
    assert tools["result"] == json.loads((REPO / "server" / "tools.json").read_text())
    c.call(3, {"source": "1+1"})
    assert c.wait(3)["result"]["content"][0]["text"] == 'echo {"source": "1+1"}'
    c.close()
    log = c.logged()
    assert log[0] == {"argv": ["tool", "run", "--compile-bytecode", *ARGS]}   # the real server, as the plugin pins it
    got = [m["got"] for m in log[1:]]
    assert got == ["initialize", "notifications/initialized", "tools/call"]   # its own handshake first, then the call
    assert log[1]["params"]["clientInfo"] == {"name": "t"}                    # the client's own initialize, passed on


def test_a_newer_client_s_discover_probe_is_refused_at_once_and_never_reaches_the_server(tmp_path):
    c = Client(tmp_path, FAKE_DELAY="3")
    c.send({"jsonrpc": "2.0", "id": 0, "method": "server/discover", "params": {}})
    refused = c.wait(0, limit=2)
    assert refused["error"]["code"] == -32601
    c.open()
    c.call(3, {"source": "1"})
    c.wait(3)
    c.close()
    assert "server/discover" not in [m.get("got") for m in c.logged()]


def test_it_answers_the_version_the_real_server_would(tmp_path):
    c = Client(tmp_path)
    init, _, _ = c.open(version="2099-01-01")              # newer than the real server speaks: its newest instead
    assert init["result"]["protocolVersion"] == NEWEST
    c.close()


def test_text_passes_unchanged_whatever_the_locale(tmp_path):
    # a Windows code page or a C locale must not touch what passes: the streams are bytes, the real transport UTF-8
    words = "café ⇒ 🐉 Привет 漢字"
    c = Client(tmp_path, PYTHONIOENCODING="cp1252", PYTHONUTF8="0", LC_ALL="C")
    c.open()
    c.call(3, {"source": words})
    assert words in c.wait(3)["result"]["content"][0]["text"]
    c.call(4, {"source": "1+1"})                                # and the connection still serves
    assert c.wait(4)["result"]["content"][0]["text"] == 'echo {"source": "1+1"}'
    c.close()


def test_held_input_larger_than_a_pipe_reaches_a_server_that_answers_one_at_a_time(tmp_path):
    c = Client(tmp_path, FAKE_DELAY="2", FAKE_BIG="200000")
    c.open()
    for i in range(3, 7):
        c.call(i, {"source": "y" * 100_000})
    for i in range(3, 7):
        assert len(c.wait(i, limit=60)["result"]["content"][0]["text"]) > 300_000
    c.close()


def test_a_burst_across_the_moment_the_server_is_ready_arrives_once_each_in_order(tmp_path):
    c = Client(tmp_path, FAKE_DELAY="0.5")
    c.open()
    ids = list(range(10, 310))
    for i in ids:                                              # sent while the server comes up, and after
        c.call(i, {"source": str(i)})
        if i == 160:
            time.sleep(0.5)
    answered = [c.wait(i)["id"] for i in ids]
    assert answered == ids
    c.close()
    calls = [m["params"]["arguments"]["source"] for m in c.logged() if m.get("got") == "tools/call"]
    assert calls == [str(i) for i in ids]                      # the server got each once, in the order sent


def test_once_the_server_is_up_every_message_passes_through(tmp_path):
    c = Client(tmp_path)
    c.open()
    c.call(3, {"root_dir": "."})
    c.wait(3)
    c.send({"jsonrpc": "2.0", "id": 4, "method": "tools/list", "params": {}})
    assert c.wait(4)["result"] == {}                                           # the fake's own answer, not the stored list
    c.close()


def test_a_server_that_ends_before_it_answers_turns_every_call_into_an_error_saying_why(tmp_path):
    c = Client(tmp_path, FAKE_FAIL="no network")
    init, tools, _ = c.open()
    assert "result" in init and "result" in tools                              # Claude Code still connects
    c.call(3, {"source": "1"})
    err = c.wait(3)["error"]["message"]
    assert "exit 3" in err and "could not install: no network" in err
    c.close()


def test_a_request_held_when_the_client_closes_is_answered_with_an_error(tmp_path):
    c = Client(tmp_path, FAKE_DELAY="5")
    c.open()
    c.call(3, {"source": "1"})
    c.p.stdin.close()
    err = c.wait(3, limit=15)["error"]["message"]
    assert "closed the connection before" in err
    c.p.wait(timeout=20)


def test_a_line_that_is_not_one_json_object_is_answered_and_the_connection_goes_on(tmp_path):
    c = Client(tmp_path)
    c.open()
    c.send("[]")
    assert c.wait(None, limit=5)["error"]["code"] == -32600
    c.send("not json")
    assert c.wait(None, limit=5)["error"]["code"] == -32700
    c.call(3, {"source": "1"})
    assert "result" in c.wait(3)
    c.close()


def test_the_stored_answers_are_the_real_servers_own():
    pytest.importorskip("si.server")
    r = subprocess.run([sys.executable, str(REPO / "scripts" / "build_server_tools.py"), "--check"],
                       capture_output=True, text=True, timeout=180)
    assert r.returncode == 0, r.stdout + r.stderr
