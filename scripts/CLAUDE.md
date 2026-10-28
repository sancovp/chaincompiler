# scripts/ — the repository's own tools

What builds, checks and releases ChainCompiler, run from the repository root (`DESIGN.md` §16 · §17 · §18 · §19):

| script | what it does |
|---|---|
| `update_site.py` | renders `roadmap.json` and the README changelog into the roadmap SVG, `site/data.json` and the board |
| `check_changelog.py` | the deploy gate: the README changelog parses, and in CI carries a new entry |
| `build_meta_ape_skills.py` | writes the eight capability skills into `skills/`, each with its uv line |
| `build_blog.py` | builds the site's development log |
| `uvline.py` | the one wording of a shipped skill's uv line, read by the generators and the version gate |
| `set_version.py` | writes one release version into every version line and pin |
| `check_versions.py` | the gate on the one version line, the build files' declarations, the skills' uv lines and every copy |
| `upload_release.py` | the upload of a release's fifteen packages to PyPI from a clone at its publish commit, in dependency order, within PyPI's daily quota of new projects, resuming from PyPI's state |
| `plugin_proof.py` · `plugin-proof-task.md` | the plugin proof: a signed-out install at a clean seat, then a headless session there given that task, graded |
| `whereimport.py` | a pytest plugin that prints where each named package resolved inside a test session — the proof that a check ran against an install, never a clone's source |
| `validate_registry.py` · `promote.py` | the marketplace registry's contribution gate and its promotion (§15) |

Their tests are in `tests/` (`python3 -m pytest scripts/tests`).
