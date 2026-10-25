"""whereimport.py — a pytest plugin that prints, at the end of a session, where each named package resolved from inside
it (DESIGN.md §18 · §19: every check run against an install must import that install, never a clone's source).

    WHEREIMPORT=rulecatcher,honeyc PYTHONPATH=scripts python3 -m pytest -p whereimport packages/rulecatcher/tests

prints one `[whereimport] <name> -> <file>` line per name.
"""
from __future__ import annotations

import importlib
import os
import sys


def pytest_sessionfinish(session, exitstatus):
    for name in filter(None, os.environ.get("WHEREIMPORT", "").split(",")):
        module = sys.modules.get(name) or importlib.import_module(name)
        print(f"\n[whereimport] {name} -> {module.__file__}", flush=True)
