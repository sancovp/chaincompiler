# scripts/tests/ — the tests of the repository's own tools

`test_check_versions.py` plants each refusal of `../check_versions.py` in a copy of the tree and sees it caught, the
tree itself passing; `test_plugin_proof.py` holds the plugin proof's grader to its negative controls — a baseline
transcript passes, and one planted failure each fails exactly its check — and to the seconds it records from the
session's start; `test_server_launch.py` runs the plugin's server launcher against a fake `uv` and checks its stored
answers against the real server; `test_skill_examples.py` runs every Python block of the eight capability skills and of
`bandit-chain-system` alone, piped into `python3 -` in an empty folder, as a skill's uv line says to;
`test_upload_release.py` holds the upload driver's order and its decisions against a stand-in PyPI, and its reading of
whether PyPI holds a release against a PyPI whose project JSON trails its version JSON; `test_release_check.py` plants
each kind of finding of `../release_check.py` and sees it named, each part finding nothing on a clean stand-in, and the
command itself exiting 1 naming a finding, 0 with none (`DESIGN.md` §16 · §17 · §18 · §19). Run them from the repository root: `python3 -m pytest scripts/tests`.
