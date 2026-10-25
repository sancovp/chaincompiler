# scripts/tests/ — the tests of the repository's own tools

`test_check_versions.py` plants each refusal of `../check_versions.py` in a copy of the tree and sees it caught, the
tree itself passing; `test_plugin_proof.py` holds the plugin proof's grader to its negative controls — a baseline
transcript passes, and one planted failure each fails exactly its check (`DESIGN.md` §16 · §19). Run them from the
repository root: `python3 -m pytest scripts/tests`.
