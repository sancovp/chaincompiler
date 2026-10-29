# scripts/ — the repository's own tools

What builds, checks and releases ChainCompiler, run from the repository root (`DESIGN.md` §16 · §17 · §18 · §19):

| script | what it does |
|---|---|
| `update_site.py` | renders `roadmap.json` and the README changelog into the roadmap SVG, `site/data.json` and the board |
| `check_changelog.py` | the deploy gate: the README changelog parses, and in CI carries a new entry |
| `build_meta_ape_skills.py` | writes the eight capability skills into `skills/`, each with its uv line |
| `build_blog.py` | builds the site's development log |
| `uvline.py` | the one wording of a shipped skill's uv line and of the plugin's server launch (`server_launch`), read by the generators, the version gate and the plugin proof |
| `build_server_tools.py` | writes `server/initialize.json` and `server/tools.json`, what the plugin's launcher answers with, from the real server's own answers to `initialize` and `tools/list`; `--check` refuses a stale one |
| `set_version.py` | writes one release version into every version line and pin |
| `check_versions.py` | the gate on the one version line, the build files' declarations, the skills' uv lines and every copy |
| `upload_release.py` | the upload of a release's fifteen packages to PyPI from a clone at its publish commit, in dependency order, within PyPI's quota of four new projects in any 86,400 s, resuming from PyPI's state; `--whole` reads whether PyPI holds the release, from each version's JSON, both forms of its simple index list it, and its cache life has passed since each upload |
| `release_check.py` | a release's own checks on its tip, before its PR: the generated files, the frontmatter sweep, the greps for every replaced reading and for a machine path, the publish dry run into a local bare copy, the tee probe of the plugin's launcher; exit 1 naming each finding |
| `plugin_proof.py` · `plugin-proof-task.md` | the plugin proof: a signed-out install at a clean seat, then a headless session there given that task, graded |
| `whereimport.py` | a pytest plugin that prints where each named package resolved inside a test session — the proof that a check ran against an install, never a clone's source |
| `validate_registry.py` · `promote.py` | the marketplace registry's contribution gate and its promotion (§15) |

Their tests are in `tests/` (`python3 -m pytest scripts/tests`).
