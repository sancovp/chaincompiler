# 22-seq — CUT A CHAINCOMPILER RELEASE from its source home: one version line, every generated file regenerated, every copy coherent, proven from wheels before the merge and from PyPI and a clean Claude Code after it

<docsys kind="dev-flow" role="instance"/>

TRIGGER:[any change under the source home `base/chaincompiler` that will merge to the source home's default branch ·
a change to the `chaincompiler` unit or a `chaincompiler-pkg-*` unit in the source home's
`scalable-publishing/publish-manifest.json` · a change to the publish machinery those units run through] · a PROCEDURE
flow: every stage runs every time

PRINCIPLE:[the source home is the only place ChainCompiler is edited · ChainCompiler is published, so every merge that
touches it is a release, because the publish pipeline mirrors the folder to the public repository on that merge, with
deletes · the public repository's own gate requires a NEW README changelog version on every publish commit, so a merge
without one turns the public deploy red · one version line: the release version is every package's version, both
plugin manifests and every pin, so every release moves the whole line and every release's fifteen packages go to PyPI ·
a version that does not move keeps every installed plugin on the old payload, because Claude Code pins an installed
plugin to its `plugin.json` version until that version changes · between the publish commit and the upload the
published plugin pins a version PyPI does not hold, so the upload is the first thing done after the merge · an install
proves what it installed only when every check imports that install, never a clone's source]

## RETRIEVE (in this order; whole file unless a section or a function is named — read that whole)

| what | where |
|---|---|
| the design the release must keep true | `DESIGN.md` §0 · §2 · §8 · §16 · §17 · §18 · §19 · §20 · plus every section the change touches |
| the same-change discipline | `.claude/rules/00-keeping-roadmap-and-backlog-current.md` |
| the mint flow, when a skill or chain is minted | `.claude/rules/22-seq-mint-attention-chain.md` |
| the release surface | `README.md` badge line (anchor `badge/tests-`) · `## Quickstart` · `## Changelog` head and newest entry · `## Status` table · `BACKLOG.md` · `roadmap.json` · `ROADMAP.md` · the generated board `.claude/rules/chaincompiler_states.md` |
| the version line and its gate | `scripts/set_version.py` · `scripts/check_versions.py` (its `LAZY` and `OUTSIDE` tables) · `scripts/uvline.py` · `scripts/tests/test_check_versions.py` · what they write and read: `.claude-plugin/plugin.json` `version` · `.claude-plugin/marketplace.json` `plugins[].version` · `packages/*/pyproject.toml` (`version`, every dependency and optional extra) · each `__version__` · `.mcp.json` · every uv line in `skills/` |
| the install path | `install.sh` (the PyPI line and the `PKGS` list) · `.mcp.json` (`uvx --from chaincompiler-si==<release> si-server`) |
| the generators and what they write | `scripts/update_site.py` (`parse_changelog`, `render_board`, `main`) → `site/data.json`, `assets/roadmap.svg`, `.claude/rules/chaincompiler_states.md` · `scripts/build_meta_ape_skills.py` (`APE_RUN`, `CC_RUN`, `with_run_line`) → the eight capability skills in `skills/` · `skills/bigdog/build.py` (`build_grade_legend`) → `skills/bigdog/GRADE-LADDER.md` · `packages/chainaios/src/chainaios/gba.py` (`_BCS_SKILL`, `default_rule_blocks`, `_portable`/`_resolved`, `_apply_tree`) → every GBA under `personas/` · `packages/chainaios/src/chainaios/hba.py` · `packages/chainaios/src/chainaios/cog.py` |
| what git does not carry | `.gitignore` (its `dist/` line drops every `personas/.<name>.src/dist/` except the two un-ignored root packages; the derived `.index.db`) |
| the public repository's gates | `.github/workflows/deploy.yml` · `scripts/check_changelog.py` · `.github/workflows/contribute.yml` · `scripts/validate_registry.py` |
| the checks | `examples/_all/run_all.py` · `examples/_all/bandit_self.py` · `examples/_all/test_all.py` · `examples/nutrition/build.py` · `examples/nutrition/test_nutrition_aios.py` · `scripts/tests/` · `scripts/whereimport.py` · `.importlinter` |
| the plugin proof | `scripts/plugin_proof.py` (`new`, `install`, `run`, `grade`, `remove`; `CAPABILITIES`, `KEEP_ENV`) · `scripts/plugin-proof-task.md` · `scripts/tests/test_plugin_proof.py` · the clean seat it keeps: CompiloApe's `DESIGN.md` §1 THE CLEAN SEAT |
| the publish pipeline (in the source home's repository, outside this folder) | `scalable-publishing/publish-manifest.json` — the `chaincompiler` unit, the fifteen `chaincompiler-pkg-*` units and the `sancrev-marketplace` unit (its `watch_paths`) · `.github/workflows/publish-on-main.yml` · `.github/workflows/publish-subdir.yml` · `scalable-publishing/bin/select_units_for_paths.py` · `scalable-publishing/bin/publish_unit.sh` · `scalable-publishing/bin/publish_package.sh` · `scalable-publishing/bin/generate_unit_readme.py` · `scalable-publishing/bin/generate_marketplace.py` · `scalable-publishing/bin/generate_publish_paths.py` · `scalable-publishing/templates/readme-refresh.yml` · its edit flow, the skill `scalable-publishing/skills/edit-scalable-publishing` |
| an agent built on this one | CompiloApe's forge flow `base/compiloape/.claude/rules/22-seq-forge-compiloape.md`, whenever the change touches `make_gba`, `construct_into`, `_apply_tree`, `default_rule_blocks`, `check_gba`, `roll_up_algebra` or the `bandit-chain-system` skill |
| the records above the folder | the source home's project registry, section `base/chaincompiler` · the source home's root `CHANGELOG.md` tail · `scalable-publishing/CHANGELOG.md` tail · THE TOP-LEVEL DESIGN's publishing bridge (the list of published units) |
| every other copy of what the change edits | `git grep -n '<name, path or sentence changed>' HEAD -- base/chaincompiler` — each hit's file read whole; for a shipped skill, every copy of it and every generator that writes it |

## THE CHANGE (obligations, in order)

1. EDIT ONLY THE SOURCE HOME. Never edit the public repository. A file that exists only there is deleted at the next
   publish, except `CHANGELOG.md`, `.github/scripts/generate_unit_readme.py` and `.github/workflows/readme-refresh.yml`,
   which the publisher owns. Never add a `CHANGELOG.md` to the source folder: the mirror excludes that name, so it would
   never publish. The project's history is the README's `## Changelog`.
2. CHANGE THE CODE AND THE GENERATOR, NEVER ONLY THE OUTPUT. When an instruction, a description or a skill body is
   wrong, fix the code that writes it — `gba.py`'s `default_rule_blocks`, `hba.py`, `cog.py`, `bandit.py`,
   `scripts/build_meta_ape_skills.py`, `skills/bigdog/build.py` — and then regenerate the committed outputs from it. A
   hand fix to a generated file is a defect that the next regeneration undoes.
3. REGENERATE EVERY GENERATED FILE in the same change:
   - `python3 scripts/update_site.py`, which writes `site/data.json`, `assets/roadmap.svg` and the board
     `.claude/rules/chaincompiler_states.md`;
   - `python3 scripts/build_meta_ape_skills.py`, on every release (each capability's uv line carries the release);
   - each committed GBA under `personas/`, re-applied through `_apply_tree` from its own `gba.json` with its sibling
     `.<name>.src/` present, on every release (the `bandit-chain-system` skill it carries holds the release's uv line)
     and whenever `gba.py`, `hba.py`, `cog.py` or SkillTree changed.
4. MAKE EVERY COPY ONE. The `bandit-chain-system` skill's source is `chainaios`'s package data
   (`packages/chainaios/src/chainaios/data/bandit-chain-system/SKILL.md`); the plugin's `skills/` copy, the working copy
   in `.claude/skills/` and each GBA's copy equal it byte for byte, each a file and never a link. The working copies of
   `glyphsteer` and `glyphsteer-dense` in `.claude/skills/` equal their shipped skills. When one sentence moves, grep for
   it and move it in every copy and in every generator that writes it, including the GBA rule blocks.
   `scripts/check_versions.py` refuses a copy that differs or is a link.
5. CUT ONE VERSION LINE, in the same change:
   - a new `### vX.Y.Z — date` entry at the head of the README `## Changelog` — the release version;
   - `python3 scripts/set_version.py X.Y.Z`, which writes it into every package's `version` and every `__version__` a
     package defines, both plugin manifests, `.mcp.json`'s pin and every uv-line pin in `skills/`, `.claude/skills/` and
     the package data, and pins every dependency among the fifteen, an optional extra's included, with `==`;
   - then step 3's regenerations, and `python3 scripts/check_versions.py` exits 0.
   Every release moves the whole line, whether or not a package changed. Update the skill enumeration in `plugin.json`
   and `marketplace.json` whenever the shipped `skills/` changed.
6. KEEP EVERY SHIPPED SKILL RUNNABLE FROM A PLUGIN INSTALL: a skill that has an agent run code from one of the fifteen,
   or from `agent-prompt-engineering` or `agent-skilltree`, states its uv line once, before its first code block, in
   `scripts/uvline.py`'s words, naming every distribution the code it runs imports (a lazy reach through `LAZY` in
   `check_versions.py` included); a step that needs the repository's source says it needs a clone. A new import or a
   new lazy edge goes into the build files and, when a skill can reach it, into `check_versions.py`'s tables.
7. KEEP THE BUILD FILES TRUE: every package's `pyproject.toml` declares every distribution its source imports — a lazy
   import as an optional extra — and a new outside module goes into `check_versions.py`'s `OUTSIDE` table with its
   distribution.
8. KEEP THE BACKLOG TRUE, without deleting work:
   - tick a `BACKLOG.md` item when it is done;
   - add an item when work is found;
   - never delete an open `[ ]` item. Move it, or tick it with the reason;
   - every `roadmap.json` phase still `in_progress` keeps at least one open task in `BACKLOG.md`.
9. REWRITE `DESIGN.md` where the design changed. Every factual sentence must be checked against the code at this tip
   before it is written, and none states a fact about this release that only its own after-merge proof makes true.
   Every known defect is `⚠ OWED` with its BACKLOG task.
10. MOVE THE RECORDS ABOVE THE FOLDER when the release changes what they state:
    - the publish manifest's `chaincompiler` unit `readme.description`;
    - the source home's project registry section;
    - THE TOP-LEVEL DESIGN's publishing bridge, through its own write procedure;
    - a source-home `CHANGELOG.md` entry for every file outside the folder that the change touched.

## COHERENCE SET (what changes when this changes)

- Every release moves the whole version line: every package, both plugin manifests, `.mcp.json`, every uv line, and so
  every capability skill, the `bandit-chain-system` copies and every GBA under `personas/` that carries one.
- A change to the `bandit-chain-system` skill re-applies every GBA's copy and moves the plugin's and the working copy.
- A generator's output text changes (a rollup's header, a rule block, a uv line), so every committed output it wrote is
  regenerated through it — `skills/`, and the bodies under `personas/.<name>.src/` with each GBA re-applied — and the
  old sentence is grepped to 0.
- The README changelog changes, so `site/data.json` is regenerated.
- `roadmap.json` changes, so `site/data.json`, `assets/roadmap.svg`, the board and `ROADMAP.md` move with it.
- A `gba.py`, `hba.py` or `cog.py` text change re-applies every committed GBA under `personas/`, every copy of the
  `bandit-chain-system` skill, and runs CompiloApe's forge flow whole.
- `scripts/build_meta_ape_skills.py` or APE changes, so the eight capability skills are regenerated.
- A moved name (`construct_language`, `roll_up_algebra`, `hierarchicalize`, `make_gba`, the `gba`/`hba`/`cog`/`bandit`
  modules) is grepped in `examples/`, `skills/`, `personas/`, `.claude/`, `scripts/` and the README above
  `## Changelog`; an entry point that reaches a lazy import is listed in `check_versions.py`'s `LAZY`.
- A package added or dropped changes `install.sh` `PKGS`, the README Status table, the manifest's `readme.description`
  and its `chaincompiler-pkg-*` units, `DESIGN.md` §0 and §2, `21-architecture-diagrams.md` §1 and §4, and
  `.importlinter` when the package is in the tier chain.
- An import edge changes the build file that owns it, `21-architecture-diagrams.md` §4 and DESIGN §2. Both state the real
  import graph, lazy imports included.
- A breadcrumb or descent wording changes rules 01 and 02, `.claude/skills/skilltree/SKILL.md`, the si docstrings and
  MCP tool descriptions, and the GBA, COG and HBA generated texts. Descent is the Read tool, never `cat`.
- A test count changes the README badge, the README Status table and the changelog entry's suite line.
- A manifest edit also republishes `sancrev-marketplace` through its `watch_paths`. Confirm its catalog render is the
  one intended — `generate_marketplace.py` on the new manifest against the render on the default branch's.
- Every check that runs against an install — the wheel proof, the install from PyPI — imports that install, shown by
  `scripts/whereimport.py` inside the test session; a conftest or a path insert that reaches a clone's source is a
  defect.

## THE PROOF (per store, before and after; run every gate BARE and read its output)

- the source tree, in an environment `./install.sh` built:
  - `pytest packages` passes, with the same count the README Status table states, SWI-Prolog on the path;
  - `python examples/_all/run_all.py` shows all checks ✓;
  - `python examples/_all/bandit_self.py` shows all checks ✓;
  - `pytest examples/nutrition` passes;
  - `pytest scripts/tests` passes — the version gate's planted refusals and the plugin grader's negative controls;
  - `lint-imports` reports the contract KEPT;
  - `python3 scripts/check_changelog.py` exits 0;
  - `python3 scripts/check_versions.py` exits 0, naming the release;
  - the board gate, run bare on the board's absolute path, passes.
- generated files: in a copy of the tree,
  - run `scripts/update_site.py`, then `diff` `site/data.json`, `assets/roadmap.svg` and the board against the
    committed files. They must be empty;
  - run `scripts/build_meta_ape_skills.py`, then `diff -r skills/` against the committed files. It must be empty;
  - `skills/bigdog/build.py`'s `build_grade_legend()` equals the committed `skills/bigdog/GRADE-LADDER.md`;
  - re-apply each GBA under `personas/` with `_apply_tree(_resolved(gba.json))`, then `diff -r` against the committed
    copy, excluding `.index.db`. It must be empty;
  - count `SKILL.md` bodies reading `SkillTree <kind> node \`` (stubs). The count must equal the count before the
    re-apply.
- skill loader: every `SKILL.md` under `skills/`, `.claude/skills/` and `personas/` is checked with
  `yaml.safe_load` on its frontmatter. Each must give a mapping with string `name` and `description`, found with a
  recursive walk that enters dot-directories, and every failure is named.
- the plugin's manifests: `claude plugin validate --strict .`, `claude plugin validate --strict
  .claude-plugin/plugin.json` and `claude plugin validate --strict skills` each exit 0.
- one sentence, one meaning: `git grep -n '<every sentence the change rewrote>' HEAD -- base/chaincompiler` returns
  the new reading only. In particular, `git grep -n 'Promote a chain to golden' HEAD -- base/chaincompiler` returns
  0 lines outside the README history, and so does `` git grep -nE '`cat ' `` across `packages/*/src` and `.claude/`.
- configurable: across `git ls-files` there are no matches for
  `grep -nIE '/Users/[A-Za-z]|/home/[A-Za-z]|/private/(tmp|var)/|/var/folders'` except this rule's own line stating
  the pattern, no `~/<name>` other than `~/.claude`, and no person named as the user. An author credit is allowed.
- versions: the new README changelog version is not in the public README, and `plugin.json`'s `version` there
  (`gh api repos/<owner>/<name>/contents/.claude-plugin/plugin.json`) is an older one.
- the publish dry run, which writes only under a scratch directory and never pushes to the network:
  1. Clone the public repository read-only.
  2. Make a local bare copy of it.
  3. Run `scalable-publishing/bin/publish_unit.sh base/chaincompiler <bare copy> <short sha> <owner/name>
     "<the unit's readme JSON>"` from a clean checkout of the source home at the tip being released.
  4. Clone the bare copy.
  5. In that clone, `python3 scripts/check_changelog.py --require-new` must exit 0 and report a new entry.
  6. `python3 scripts/update_site.py`, then `git diff --quiet -- site/data.json assets/roadmap.svg
     .claude/rules/chaincompiler_states.md` must exit 0.
  7. Every symlink resolves (`find . -type l ! -exec test -e {} \; -print` prints nothing).
  8. `git show --stat HEAD` lists exactly the intended files.
- unit selection: `git diff --name-only <merge-base>..<tip> | python3 scalable-publishing/bin/select_units_for_paths.py
  --manifest scalable-publishing/publish-manifest.json` names `chaincompiler` and every other unit the change is meant
  to republish, and no other — a `chaincompiler-pkg-*` unit never. `generate_publish_paths.py --manifest
  scalable-publishing/publish-manifest.json --workflow .github/workflows/publish-on-main.yml --check` exits 0 — without
  `--workflow` it prints the paths and checks nothing.
- the clean install: in a fresh venv, where `command -v python3` is checked to be that venv in the same command,
  clone the dry-run result. Run `./install.sh`, then the full source-tree proof above. Also run
  `python3 -c "import si.server"`, the module the plugin's MCP launches.
- THE WHEEL PROOF, before the merge, from the dry-run clone: `scalable-publishing/bin/publish_package.sh
  packages/<folder> --dry-run` for each of the fifteen passes `twine check` and finds the version not yet on PyPI;
  `python -m build --wheel` builds each into a folder the proof keeps; a fresh venv, checked to be the `python3` in use,
  installs the fifteen non-editable from those wheels (`--find-links`) with the outside dependencies from PyPI;
  `pip check` is clean; and the source-tree proof's checks run from the clone against that venv, each with no failure,
  `WHEREIMPORT=<the fifteen's modules> PYTHONPATH=scripts … -p whereimport` printing every module inside the venv.
- after the merge, in this order:
  1. THE UPLOAD, first: once `git ls-remote` shows the `Publish base/chaincompiler (<sha>)` commit whose `<sha>` is the
     merge, clone the public repository at that commit and run `scalable-publishing/bin/publish_package.sh
     packages/<folder>` for each of the fifteen; a pass run again reads a refusal of a version PyPI already holds at
     the release's own version as that package uploaded; PyPI's JSON (`https://pypi.org/pypi/<name>/json`) names the
     release for all fifteen.
  2. THE INSTALL FROM PYPI: a fresh venv, checked, `pip install --no-cache-dir --report <file>` of `chaincompiler-si`,
     `glyphsteer`, `framework`, `personapack`, `chaincompiler-archetype` and `goldenreq` at `==<release>` with no index
     but PyPI; the report shows every one of the fifteen downloaded from PyPI; `pip check` is clean; the source-tree
     proof's checks run from a clean clone at the publish commit against it, each with no failure, every module
     resolving into the venv.
  3. THE PLUGIN PROOF: `scripts/plugin_proof.py new <root>` (a scratch root outside the world dir), `install <seat>
     --version <release>` passing every check, `run <seat> --prompt-file scripts/plugin-proof-task.md --out <t>.jsonl
     --allowed-tools Skill Read 'Bash(uv:*)' 'Bash(uvx:*)' mcp__plugin_chaincompiler_self-interpreter__si_interpret`
     exiting 0, `grade` passing every check, then `remove`; every proof names the seat `<seat>`.
  4. the public repository: `gh run list -R <owner>/<name>` shows `deploy-site` succeeded on the publish commit, and a
     clean clone of it passes the clean-install proof.
  5. when the release touched what CompiloApe's forge reads, CompiloApe's forge flow runs whole against it.

NOT:[edit the public repository · add a `CHANGELOG.md` to the source folder · put a `CLAUDE.md` at the folder's root
(the plugin carries none; an agent it delivers ships inside its install skill, `DESIGN.md` §16) · hand-edit a generated
file (site data, roadmap SVG, the board, capability skills, the grade ladder, GBA output) · fix a shipped instruction in
one copy while its generator or another copy keeps the old reading · move one version line without the others ·
merge a change to the folder without a new README changelog version · upload a package built from anything but a
clone of the public repository at the release's publish commit · run anything else in the after-merge proof before the
upload · reuse a version PyPI holds · let a check against an install import a clone's source · run the plugin proof's
session with the user's settings or outside a marked seat · delete an open backlog task · claim a GBA rebuilds from a
copy whose `skill_src` resolves outside the copied folder or into an ignored `dist/` · trust `validate()` as proof a
rebuild kept its bodies (it checks frontmatter and breadcrumbs, not content) · write `cat` as the way to descend into a
node · push the dry run anywhere · pip install into an environment without checking which `python3` it is]

COMPOSES:[`.claude/rules/00-keeping-roadmap-and-backlog-current.md` — the same-change discipline this flow runs at
release grain · `.claude/rules/22-seq-mint-attention-chain.md` — the flow for minting what a release ships ·
`.claude/rules/02-the-autoload-mechanism.md` — why descent is the Read tool · scalable-publishing's edit flow and its
`DESIGN.md` §4 — how a package inside this folder reaches PyPI · CompiloApe's forge flow — the agent built on this one ·
the source home's publishing rule — the manifest is the allowlist, and the public repository is a delete-enabled mirror]

GATE (what would detect a violation):[`scripts/check_versions.py` — the version line, the build files' declarations,
the skills' uv lines and every copy · `scripts/plugin_proof.py grade` — a plugin install that does not work · and a
script still owed in `scripts/` that runs the generated-file diffs, the frontmatter sweep, the grep for each rewritten
sentence and the publish dry run, exiting non-zero on any finding, before the release's PR is opened]
