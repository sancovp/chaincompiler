"""CI guard: the _all example must run green end-to-end.

This is the dogfood test — it proves every package still composes on one domain.
If any package's public API drifts, this goes red before a user ever hits it.
"""
from run_all import main


def test_all_runs_green():
    assert main() == 0
