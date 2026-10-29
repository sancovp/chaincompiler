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
published plugin pins a version PyPI does not hold, so the upload is the first thing done after the merge · a package
on PyPI whose sibling is not there installs for no one, and its metadata names a sibling anyone could publish under
that name, so the upload goes in dependency order and a release is whole only when PyPI holds all fifteen at its
version · an install proves what it installed only when every check imports that install, never a clone's source ·
the plugin's server is reached through its launcher, which answers Claude Code before the real server is installed, so
what Claude Code is shown at connect time — the launcher's own answers, from `server/initialize.json` and
`server/tools.json` — is what the session
keeps, and each must be what the real server at the release would have answered; once the real server is up the
launcher is a pipe that loses, reorders and re-encodes nothing, and a request it cannot deliver is answered with an
error, never dropped]

## RETRIEVE (in this order; whole file unless a section or a function is named — read that whole)

| what | where |
|---|---|
| the design the release must keep true | `DESIGN.md` §0 · §2 · §8 · §16 · §17 · §18 · §19 · §20 · plus every section the change touches |
| the same-change discipline | `.claude/rules/00-keeping-roadmap-and-backlog-current.md` |
| the mint flow, when a skill or chain is minted | `.claude/rules/22-seq-mint-attention-chain.md` |
| the release surface | `README.md` badge line (anchor `badge/tests-`) · `## Quickstart` · `## Changelog` head and newest entry · `## Status` table · `BACKLOG.md` · `roadmap.json` · `ROADMAP.md` · the generated board `.claude/rules/chaincompiler_states.md` |
| the version line and its gate | `scripts/set_version.py` · `scripts/check_versions.py` (its `LAZY` and `OUTSIDE` tables, `check_copies`) · `scripts/uvline.py` · `scripts/tests/test_check_versions.py` · what they write and read: `.claude-plugin/plugin.json` `version` · `.claude-plugin/marketplace.json` `plugins[].version` · `packages/*/pyproject.toml` (`version`, `readme`, `license`, the `setuptools` build requirement, every dependency and optional extra) · each `__version__` · `.mcp.json` · every uv line in `skills/` |
| the install path | `install.sh` (the PyPI line and the `PKGS` list; it installs the fifteen with `--no-build-isolation`, so the environment's own setuptools builds them) · `.mcp.json` (uv running `server/launch.py --from chaincompiler-si==<release> si-server`, `scripts/uvline.py`'s `server_launch`) · `scripts/set_version.py`'s rewrite of that pin |
| the plugin's server, as Claude Code meets it | `server/launch.py` whole (`Launcher.run` · `start` · `to_server` · `pump_out` · `pump_err` · `go` · `fail`, `server_command`, `release`, `negotiate`) · `server/initialize.json`, `server/tools.json` and `scripts/build_server_tools.py` whole · `scripts/tests/test_server_launch.py` whole · `packages/si/src/si/server.py` (what the real server registers: tools only) · `packages/si/pyproject.toml` (its `fastmcp` requirement, which decides the `tools/list` a user's install answers) · the real server's stdio transport, the installed `mcp` package's `server/stdio.py` (it reads and writes UTF-8 whatever the locale) · what Claude Code sends a stdio server and what the real server answers, MEASURED at this tip, never recalled: the tee probe of THE PROOF below logs the first client message (Claude Code's MCP client opens with `server/discover` in the 2026-07-28 envelope and falls back to `initialize` when that is refused or unanswered), the `initialize` params (`protocolVersion`, `capabilities`), and the real server's own answer to the launcher's `initialize`, read from the real server's output, which the probe's wrapper logs beside the launcher's two streams; the real server's own answers to `server/discover` and `prompts/list` are asked of `python3 -m si.server` directly over stdio, the way `scripts/build_server_tools.py` asks it, because the launcher forwards neither |
| the generators and what they write | `scripts/update_site.py` (`parse_changelog`, `render_board`, `main`) → `site/data.json`, `assets/roadmap.svg`, `.claude/rules/chaincompiler_states.md` · `scripts/build_meta_ape_skills.py` (`APE_RUN`, `CC_RUN`, `CC_CAPABILITIES`, `with_run_line`) → the eight capability skills in `skills/` · `skills/bigdog/build.py` (`build_grade_legend`) → `skills/bigdog/GRADE-LADDER.md` · `packages/chainaios/src/chainaios/gba.py` (`_BCS_SKILL`, `default_rule_blocks`, `_portable`/`_resolved`, `_apply_tree`) → every GBA under `personas/` · `packages/chainaios/src/chainaios/hba.py` · `packages/chainaios/src/chainaios/cog.py` |
| what git does not carry | `.gitignore` (its `dist/` line drops every `personas/.<name>.src/dist/` except the two un-ignored root packages; the derived `.index.db`) |
| the public repository's gates | `.github/workflows/deploy.yml` · `scripts/check_changelog.py` · `.github/workflows/contribute.yml` · `scripts/validate_registry.py` |
| the checks | `examples/_all/run_all.py` · `examples/_all/bandit_self.py` · `examples/_all/test_all.py` · `examples/nutrition/build.py` · `examples/nutrition/test_nutrition_aios.py` · `scripts/tests/` · `scripts/whereimport.py` · `.importlinter` |
| the plugin proof | `scripts/plugin_proof.py` (`new`, `install`, `run`, `grade`, `remove`; `CAPABILITIES`, `KEEP_ENV`; the `<transcript>.env.json` sidecar `run` writes twice — before its pre-check, then `started_at` just before the session — and `grade` reads) · `scripts/plugin-proof-task.md` · `scripts/tests/test_plugin_proof.py` · the clean seat it keeps: CompiloApe's `DESIGN.md` §1 THE CLEAN SEAT |
| the release check and the upload driver | `scripts/release_check.py` whole (`extract` · `tree_diff` · `part_generated` · `part_frontmatter` · `history_line` · `part_sentences` · `part_publish` · `WRAPPER` · `read_tee_log` · `part_tee`) · `scripts/tests/test_release_check.py` whole · `scripts/upload_release.py` whole (`fetch` · `max_age` · `uploaded_at` · `held` · `indexed` · `whole` · `run`) · `scripts/tests/test_upload_release.py` whole · and what each part stands in for, read beside it: the public repository's `.github/workflows/deploy.yml` (its staleness gate fails a generated file that differs AND one that is untracked) · `scalable-publishing/bin/publish_unit.sh` and `scalable-publishing/bin/generate_unit_readme.py` (the published README is the source README with a managed badge block) · `server/launch.py`'s `handle`, `pump_out`, `go` and `to_server` (the launcher swallows the client's `notifications/initialized` and sends its own only once the real server answered its `initialize`) · the README's section order (its history is `## Changelog` up to the next `## ` heading; `## Status` and `## License` come after it and are current text) |
| the publish pipeline (in the source home's repository, outside this folder) | `scalable-publishing/publish-manifest.json` — the `chaincompiler` unit, the fifteen `chaincompiler-pkg-*` units and the `sancrev-marketplace` unit (its `watch_paths`) · `.github/workflows/publish-on-main.yml` · `.github/workflows/publish-subdir.yml` · `scalable-publishing/bin/select_units_for_paths.py` · `scalable-publishing/bin/publish_unit.sh` · `scalable-publishing/bin/publish_package.sh` (it builds a copy of one package folder in a fresh environment and refuses a version PyPI holds) · `scalable-publishing/bin/generate_unit_readme.py` · `scalable-publishing/bin/generate_marketplace.py` · `scalable-publishing/bin/generate_publish_paths.py` · `scalable-publishing/templates/readme-refresh.yml` · its edit flow, the skill `scalable-publishing/skills/edit-scalable-publishing` |
| PyPI's state of the fifteen | `https://pypi.org/pypi/<name>/<version>/json` for whether PyPI holds a version (200 once it does, 404 before) and when its files were uploaded (`urls[].upload_time_iso_8601`) · `https://pypi.org/simple/<name>/`, which pip and uv read, in both its forms — the HTML page and the JSON form pip and uv ask for first (`Accept: application/vnd.pypi.simple.v1+json`) — for whether an install can find the version's files · `https://pypi.org/pypi/<name>/json` for which versions it holds and each held release's `requires_dist` — each served through a cache that can still answer as before an upload: the simple index for up to its `cache-control` max-age (600 s), its two forms cached apart, and a version's JSON 404 for up to 72 s after v0.3.3's uploads, so one reader can see a new version the next does not (scalable-publishing `DESIGN.md` §4) |
| an agent built on this one | CompiloApe's forge flow `base/compiloape/.claude/rules/22-seq-forge-compiloape.md`, whenever the change touches `make_gba`, `construct_into`, `_apply_tree`, `default_rule_blocks`, `check_gba`, `roll_up_algebra` or the `bandit-chain-system` skill |
| the records above the folder | the source home's project registry, section `base/chaincompiler` · the source home's root `CHANGELOG.md` tail · `scalable-publishing/CHANGELOG.md` tail · THE TOP-LEVEL DESIGN's publishing bridge (the list of published units) · every other project that installs or names the fifteen (the steward project's build file, stack and messages) |
| every other copy of what the change edits | `git grep -n '<name, path or sentence changed>' HEAD -- .` across the whole source home — each hit's file read whole, a package's own `.claude/` (`packages/glyphsteer/.claude/rules/` and `.claude/skills/glyphsteer/`) among them; for a shipped skill, every `SKILL.md` carrying its `name` and every generator that writes it |

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
   - `python3 scripts/build_meta_ape_skills.py`, on every release (each capability's uv line carries the release; it
     reads the release from the `chaincompiler` its `python3` imports, so run it in the editable environment
     `./install.sh` built from this tree);
   - `python3 scripts/build_server_tools.py`, in that environment, on every release — it writes `server/initialize.json`
     and `server/tools.json` from the real server's own answers to `initialize` (asking for a protocol version newer than
     any, so it answers its newest) and `tools/list` — with that environment's `fastmcp` first brought to the newest release
     PyPI's JSON names inside the bound `si`'s build file gives it, because a plugin install resolves `fastmcp` afresh
     and Claude Code is shown the stored list, never its own server's, for the whole session;
   - each committed GBA under `personas/`, re-applied through `_apply_tree` from its own `gba.json` with its sibling
     `.<name>.src/` present, on every release (the `bandit-chain-system` skill it carries holds the release's uv line)
     and whenever `gba.py`, `hba.py`, `cog.py` or SkillTree changed.
4. MAKE EVERY COPY ONE. The `bandit-chain-system` skill's source is `chainaios`'s package data
   (`packages/chainaios/src/chainaios/data/bandit-chain-system/SKILL.md`); the plugin's `skills/` copy, the working copy
   in `.claude/skills/` and each GBA's copy equal it byte for byte, each a file and never a link. Every other `SKILL.md`
   in the folder whose frontmatter `name` is a shipped skill's — the working copies of `glyphsteer`, `glyphsteer-dense`
   and `report-missed-skill` in `.claude/skills/`, and the glyphsteer package's own
   `packages/glyphsteer/.claude/skills/glyphsteer/` — equals that shipped skill byte for byte, a file of its own and
   never reached through a linked folder, whether the link is the skill's own folder or any folder above it (a linked
   `.claude/skills/`). When one sentence moves, grep for it across the source home and move it in every copy, in every
   document of a package's own `.claude/`, and in every generator that writes it, including the GBA rule blocks.
   `scripts/check_versions.py` refuses a copy on its list that differs, is a link or is reached through a linked
   folder at any depth.
5. CUT ONE VERSION LINE, in the same change:
   - a new `### vX.Y.Z — date` entry at the head of the README `## Changelog` — the release version — with its suite
     line at the counts the suites give, and the README badge and `## Status` table at the same counts;
   - `python3 scripts/set_version.py X.Y.Z`, which writes it into every package's `version` and every `__version__` a
     package defines, both plugin manifests, `.mcp.json`'s pin and every uv-line pin in `skills/`, `.claude/skills/` and
     the package data, and pins every dependency among the fifteen, an optional extra's included, with `==`;
   - then step 3's regenerations — the GBAs re-applied, since `set_version.py` does not touch `personas/` — and
     `python3 scripts/check_versions.py` exits 0.
   Every release moves the whole line, whether or not a package changed. Update the skill enumeration in `plugin.json`
   and `marketplace.json` whenever the shipped `skills/` changed.
6. KEEP EVERY SHIPPED SKILL RUNNABLE FROM A PLUGIN INSTALL: a skill that has an agent run code from one of the fifteen,
   or from `agent-prompt-engineering` or `agent-skilltree`, states its uv line once, before its first code block, in
   `scripts/uvline.py`'s words, naming every distribution the code it runs imports (a lazy reach through `LAZY` in
   `check_versions.py` included); a step that needs the repository's source says it needs a clone. A new import or a
   new lazy edge goes into the build files and, when a skill can reach it, into `check_versions.py`'s tables. Each
   Python block of a capability skill runs on its own, as the uv line says it is run — piped in alone, in an empty
   folder — so a block that needs what another skill made says so and makes it.
7. KEEP THE PLUGIN'S SERVER CONNECTING, AND KEEP ITS LAUNCHER A PIPE. Whatever `server/launch.py` answers before the
   real server is up is what the real server at the release answers to the same message: `initialize` with the
   `protocolVersion` the real server negotiates for the client's request (the one asked for when it is no newer than
   the real server's newest, read from it into `server/initialize.json`; else that newest) and capabilities that are a
   subset of the real server's, every list they advertise answered at once from what is stored — `tools/list`
   from `server/tools.json` — and `ping`; and a message Claude Code sends first to probe for a newer protocol era
   (`server/discover`) is refused at once with a JSON-RPC error, so Claude Code falls back to `initialize` without
   waiting on a server that is still installing. Every other message waits and is delivered in the order it came. Both
   streams are UTF-8 whatever the machine's locale, as the real server's own transport is (Windows' default code page
   cannot decode every UTF-8 byte), the held messages are written by a thread that is not the one reading the real
   server's output, a request that cannot be delivered — the server ended, the client closed its input first, a write
   failed — is answered with an error naming why, and a line that is JSON but not an object is answered with an error,
   never a crash. The launch line lives only in `scripts/uvline.py`'s `server_launch`.
8. KEEP THE BUILD FILES TRUE: every package's `pyproject.toml` declares every distribution its source imports — a lazy
   import as an optional extra — its folder's `README.md` as `readme` and `license = "MIT"`, and a new outside module
   goes into `check_versions.py`'s `OUTSIDE` table with its distribution. `si`'s build file bounds `fastmcp` to the
   major `server/tools.json` was written under, because Claude Code shows the session that list and a user's install
   resolves its own `fastmcp`. `install.sh` installs the build backend the
   build files require (`setuptools` at their lower bound) in its first `pip install`, before the editable installs,
   because it builds them without isolation and a fresh environment carries no setuptools, or an older one.
9. KEEP THE BACKLOG TRUE, without deleting work:
   - tick a `BACKLOG.md` item when it is done;
   - add an item when work is found;
   - never delete an open `[ ]` item. Move it, or tick it with the reason;
   - every `roadmap.json` phase still `in_progress` keeps at least one open task in `BACKLOG.md`.
10. REWRITE `DESIGN.md` where the design changed. Every factual sentence must be checked against the code at this tip
    before it is written, and none states a fact about this release that only its own after-merge proof makes true.
    Every known defect is `⚠ OWED` with its BACKLOG task; an `⚠ OWED` that counts something (names free on PyPI, tests)
    states the count PyPI or the suite gives at this tip. A number measured on an earlier release and stated in any
    document of the change (a seconds count, a lag, a suite count) names that release and the record holding it — a
    goal proof committed with the change, or a release proof's field — and that record is reachable from this tip.
11. MOVE THE RECORDS ABOVE THE FOLDER when the release changes what they state, each checked against PyPI and the code
    at this tip, never ahead of the upload:
    - the publish manifest's `chaincompiler` unit `readme.description`;
    - the source home's project registry section — PyPI's state of the fifteen as measured (which names it holds, at
      which version), rewritten again once the upload is whole;
    - THE TOP-LEVEL DESIGN's publishing bridge, through its own write procedure;
    - every other project's reading of the fifteen found by the grep in RETRIEVE (the steward project's "not on PyPI"),
      changed in that project's own change and named in this release's PR;
    - for every file outside the folder that the change touched, an entry in the `CHANGELOG.md` of the project that owns
      that file (`scalable-publishing/CHANGELOG.md` for scalable-publishing's), or in the source home's root
      `CHANGELOG.md` for a file no project owns.

## COHERENCE SET (what changes when this changes)

- Every release moves the whole version line: every package, both plugin manifests, `.mcp.json`, every uv line, and so
  every capability skill, the `bandit-chain-system` copies and every GBA under `personas/` that carries one.
- A change to the `bandit-chain-system` skill re-applies every GBA's copy and moves the plugin's and the working copy.
- A generator's output text changes (a rollup's header, a rule block, a uv line), so every committed output it wrote is
  regenerated through it — `skills/`, and the bodies under `personas/.<name>.src/` with each GBA re-applied — and the
  old sentence is grepped to 0.
- A tool of `si.server` changes, or `fastmcp`'s newest release inside `si`'s bound lists one differently, so
  `server/tools.json` is written again by `scripts/build_server_tools.py`; a prompt or a resource added to `si.server`
  changes the real server's capabilities, which `build_server_tools.py --check` sees as a changed `server/initialize.json`,
  and moves the capabilities the launcher answers `initialize` with and the lists it answers itself. The launch line changes only in `scripts/uvline.py`'s `server_launch`, which `.mcp.json`,
  `set_version.py`'s pin rewrite, `check_versions.py` and `plugin_proof.py`'s install check all read.
- What Claude Code sends a stdio server first, or the protocol era it asks for, changes, or the real server's own answer
  to `initialize` or `server/discover` changes (a `fastmcp` or `mcp` release), so the set of messages the launcher
  answers itself, its tests and `DESIGN.md` §16 move together, re-measured by the tee probe below.
- A sentence about how the plugin's server starts or connects is grepped across the source home and moves in every
  place that states it: `DESIGN.md` §14 · §16 · §17 · §19, the README Quickstart and the release's changelog entry,
  `BACKLOG.md`, `roadmap.json`, `ROADMAP.md` P7, `server/CLAUDE.md`, `scripts/CLAUDE.md`, the SURFACE subgraph of
  `21-architecture-diagrams.md`, and the docstrings of `server/launch.py`, `scripts/uvline.py` and
  `scripts/check_versions.py`; older changelog entries keep their own words.
- A grader check that reads text in a transcript reads only where Claude Code writes that text: the failed-to-connect
  note only in a tool search's result naming the plugin's server, never a file the session read — the plugin's own
  `README.md` and `DESIGN.md`, which a session may read, carry both phrases. With the launcher answering at once, the
  init event's `connected` proves the launcher; the self-interpreter itself is proven only by one of its tools
  answering without an error.
- The README changelog changes, so `site/data.json` is regenerated.
- The public repository's `deploy.yml` staleness gate, a generator, or the README's section order changes, so
  `scripts/release_check.py`'s generated, publish and sentence parts change with it and compare what `deploy.yml`
  compares, the way it compares it (a differing file and an untracked one alike). A part added to or dropped from the
  release check moves THE PROOF's first bullet, the GATE's release-check clause, `DESIGN.md` §17 · §19,
  `scripts/CLAUDE.md`, `scripts/tests/CLAUDE.md` and the stack's RCHK box, whose arrows name everything it runs:
  `update_site.py` · `build_meta_ape_skills.py` · the GBA re-apply through `chainaios` · `build_server_tools.py` ·
  `plugin_proof.py`'s seat · `server/launch.py` · `publish_unit.sh`.
- `server/launch.py` changes which messages it answers itself or how it tells the real server the client is
  initialized (`go`, `to_server`), so the tee probe's wrapper and `read_tee_log`'s checks move with it.
- What PyPI answers on which page changes (a version's JSON, the project's JSON, the simple index), in which form, or
  for how long its cache serves it, so `upload_release.py`'s `held`, `indexed`, `max_age`, `uploaded_at` and `whole`,
  the stand-in PyPI in `scripts/tests/test_upload_release.py`, stage 1 below, `DESIGN.md` §18 and scalable-publishing's
  `DESIGN.md` §4 move together.
- `roadmap.json` changes, so `site/data.json`, `assets/roadmap.svg`, the board and `ROADMAP.md` move with it.
- A `gba.py`, `hba.py` or `cog.py` text change re-applies every committed GBA under `personas/`, every copy of the
  `bandit-chain-system` skill, and runs CompiloApe's forge flow whole.
- `scripts/build_meta_ape_skills.py` or APE changes, so the eight capability skills are regenerated.
- A moved name (`construct_language`, `roll_up_algebra`, `hierarchicalize`, `make_gba`, the `gba`/`hba`/`cog`/`bandit`
  modules) is grepped in `examples/`, `skills/`, `personas/`, `.claude/`, `scripts/` and the README above
  `## Changelog`; an entry point that reaches a lazy import is listed in `check_versions.py`'s `LAZY`.
- A package added or dropped changes `install.sh` `PKGS`, the README Status table, the manifest's `readme.description`
  and its `chaincompiler-pkg-*` units, `DESIGN.md` §0 and §2, `21-architecture-diagrams.md` §1 and §4,
  `.importlinter` when the package is in the tier chain, and THE UPLOAD's order below.
- An import edge changes the build file that owns it, `21-architecture-diagrams.md` §4 and DESIGN §2. Both state the real
  import graph, lazy imports included. A new dependency among the fifteen also moves THE UPLOAD's order.
- A build-system requirement changes `install.sh`'s first `pip install`, which installs that backend, and is proven by
  the clean install on the lowest and the newest Python the build files admit.
- A sentence about the fifteen's PyPI state or how they install is grepped across the whole source home — the glyphsteer
  package's own `.claude/` and the steward project carry such sentences — and every hit moves with it.
- A breadcrumb or descent wording changes rules 01 and 02, `.claude/skills/skilltree/SKILL.md`, the si docstrings and
  MCP tool descriptions, and the GBA, COG and HBA generated texts. Descent is the Read tool, never `cat`.
- A test count changes the README badge, the README Status table and the changelog entry's suite line.
- A manifest edit also republishes `sancrev-marketplace` through its `watch_paths`. Confirm its catalog render is the
  one intended — `generate_marketplace.py` on the new manifest against the render on the default branch's.
- Every check that runs against an install — the wheel proof, the install from PyPI — imports that install, shown by
  `scripts/whereimport.py` inside the test session; a conftest or a path insert that reaches a clone's source is a
  defect.

## THE PROOF (per store, before and after; run every gate BARE and read its output)

- THE RELEASE CHECK, on the committed tip, before the release's PR is opened: with `git status --porcelain -- .`
  printing nothing (the frontmatter sweep and the tee probe read the working tree, and every generator runs from the
  editable install) and with a `python3` whose `chainaios`, `chaincompiler` and `si` resolve into this tree's
  `packages/` (`importlib.util.find_spec(<module>).origin`, printed), `python3 scripts/release_check.py --replaced <a
  file of every reading the change rewrote away, one per line, taken from the lines the change's diff removes from a
  document>` exits 0. It runs, and names every finding of, five of the stores below — the generated files, the skill
  loader's frontmatter, one sentence one meaning with the configurable greps, the publish dry run and the tee probe;
  each is still read below for what it holds, and the rest of this proof runs beside it. Without `--replaced` it
  checks only the flow's own readings and proves nothing about the readings the change replaced.
- the source tree, in an environment `./install.sh` built:
  - `pytest packages` passes, with the same count the README Status table states, SWI-Prolog on the path;
  - `python examples/_all/run_all.py` shows all checks ✓;
  - `python examples/_all/bandit_self.py` shows all checks ✓;
  - `pytest examples/nutrition` passes;
  - `pytest scripts/tests` passes — the version gate's planted refusals, the plugin grader's negative controls and the
    launcher's tests against a fake `uv`;
  - `lint-imports` reports the contract KEPT;
  - `python3 scripts/check_changelog.py` exits 0;
  - `python3 scripts/check_versions.py` exits 0, naming the release;
  - the board gate (the `state-file` skill's `check_state_files.py`), run bare on the board's absolute path, passes.
- generated files: in a copy of the tree as committed,
  - run `scripts/update_site.py`, which exits 0, then `diff` `site/data.json`, `assets/roadmap.svg` and the board
    against the committed files. They must be empty, and a generated file the commit lacks is a finding, as the public
    `deploy.yml` fails an untracked one;
  - run `scripts/build_meta_ape_skills.py`, then `diff -r skills/` against the committed files. It must be empty;
  - `skills/bigdog/build.py`'s `build_grade_legend()` equals the committed `skills/bigdog/GRADE-LADDER.md` (call the
    function; running the whole script rewrites `bigdog.rulecatcher.json`'s stamps);
  - re-apply each GBA under `personas/` with `_apply_tree(_resolved(gba.json))`, then `diff -r` against the committed
    copy, excluding `.index.db`. It must be empty;
  - count `SKILL.md` bodies reading `SkillTree <kind> node \`` (stubs). The count must equal the count before the
    re-apply.
- the plugin's server, each store measured on the default branch's tree (before) and on this tip (after), every
  command run with `PYTHONDONTWRITEBYTECODE=1` and pytest's `-p no:cacheprovider` when the editable install points into
  a tree another process is using:
  - `.mcp.json` — before: `git show <default>:<folder>/.mcp.json`; after: its `self-interpreter` entry equals
    `uvline.server_launch(<release>)` (`check_versions.py` exits 0), and in a copy of the tree
    `set_version.py 9.9.9` changes exactly the one pin in it (`diff`).
  - `server/initialize.json` · `server/tools.json` — the environment's `fastmcp` (`pip show fastmcp`) is the newest
    release PyPI's JSON names inside `si`'s bound, and `build_server_tools.py --check` exits 0;
    `git diff <default> -- server/` shows only the changes the release intends.
  - the launcher's stdio, against a fake `uv` (`scripts/tests/test_server_launch.py`): `initialize`, `tools/list` and
    `ping` answered before a slow server is up; `server/discover` refused at once with an error; `initialize`'s
    `protocolVersion` and capabilities what the real server answers to the same request; a burst of requests across
    the moment the server becomes ready each delivered once, in order; held requests larger than a pipe, to a server
    that answers each before reading the next, all answered; a non-ASCII and an astral-plane argument and result
    (`é`, `⇒`, `🐉`) relayed byte for byte with every text stream of the launcher put in `cp1252`, Windows' default;
    a request held when the client closes its input answered with an error; a JSON line that is not an object
    answered with an error; a server that ends before it answers turning every call into an error naming why.
  - the launcher with Claude Code, THE TEE PROBE: in a marked seat, an environment holding only `HOME`, `USER`,
    `LOGNAME`, `PATH`, `LANG`, `TERM` and `TMPDIR`, a headless `claude -p` on a small model with
    `--strict-mcp-config --mcp-config <scratch config> --setting-sources project,local`, whose server is a scratch
    wrapper that loads this tree's `server/launch.py`, logs both of its streams and the real server's output with
    timestamps, and starts the real server (`python3 -m si.server` of the editable environment) after a sleep longer
    than Claude Code's thirty seconds, asked to call `si_interpret` with `1+1`: the init event lists the server
    `connected`; the log shows the first client message — a `server/discover`, when it is that message, refused with
    an error within one second of it — `initialize` answered within one second of that first message, `tools/list`
    answered from `server/tools.json`, the `tools/call` written to the real server only after the real server's own
    answer to the launcher's `initialize` appears in the log (so never before the sleep ends), and answered with
    `{"result":"2"}`, and every client request id answered exactly once; the session's result, stripped, is the
    tool's answer in either form the tool returns it — its text `2` or its structured content `{"result":"2"}`.
  - the grader (`scripts/tests/test_plugin_proof.py`): besides its controls, a passing session that also reads the
    plugin's `README.md` and `DESIGN.md` still passes, and a session whose server never came up behind the launcher
    (connected at the start, every call of its tools an error naming why) fails.
- skill loader: every `SKILL.md` under `skills/`, `.claude/skills/`, `personas/` and `packages/` of the committed tree
  is checked with `yaml.safe_load` on its frontmatter. Each must give a mapping with string `name` and `description`,
  found with a recursive walk that enters dot-directories, and every failure is named. Every `SKILL.md` whose `name`
  is a shipped skill's is byte-compared with that shipped skill; every difference is named. `git ls-files -s -- .claude
  packages` lists no entry of mode `120000` (a link) on this tip — before: `git ls-files -s` on the default branch's
  tree, naming each link it held — and `check_versions.py` refuses a link planted at a skill's folder and at a folder
  above it (`scripts/tests/test_check_versions.py`).
- the plugin's manifests: `claude plugin validate --strict .`, `claude plugin validate --strict
  .claude-plugin/plugin.json` and `claude plugin validate --strict skills` each exit 0.
- one sentence, one meaning: every sentence the change rewrote is found across the whole source home's tracked text
  in its new reading only — searched with whitespace flattened, since the documents wrap their prose and a
  line-by-line `git grep` misses a reading split across two lines. Only the histories are excepted: every
  `CHANGELOG.md`, the README's `## Changelog` section up to the next `## ` heading (its `## Status` table and
  `## License` are current text), `site/data.json` (which renders that changelog and `roadmap.json`, both checked at
  their source), and every goal file and goal proof under `.claude/goals/` (a merged goal's conditions are never
  reworded). In particular, `git grep -n 'Promote a chain to golden' HEAD -- base/chaincompiler` returns 0 lines
  outside those histories, and so does `` git grep -nE '`cat ' `` across `packages/*/src` and `.claude/` — save, for
  these two greps alone, a line that states the grep with its pattern quoted and rule 02's own statement that descent is
  the Read tool, NOT `cat`, and, for them as for the configurable greps below, `scripts/release_check.py` and its tests,
  which carry every pattern they search for and plant them.
- configurable: across `git ls-files` there are no matches for
  `grep -nIE '/Users/[A-Za-z]|/home/[A-Za-z]|/private/(tmp|var)/|/var/folders'`, no `~/<name>` other than `~/.claude`,
  and no person named as the user — save a line stating the machine-path pattern itself, as this rule's does, and
  `scripts/release_check.py` and its tests. An author credit is allowed.
- versions: the new README changelog version is not in the public README, and `plugin.json`'s `version` there
  (`gh api repos/<owner>/<name>/contents/.claude-plugin/plugin.json`) is an older one.
- the publish dry run, which writes only under a scratch directory and never pushes to the network:
  1. Clone the public repository read-only.
  2. Make a local bare copy of it.
  3. Run `scalable-publishing/bin/publish_unit.sh base/chaincompiler <bare copy> <short sha> <owner/name>
     "<the unit's readme JSON>"` from a clean checkout of the source home at the tip being released.
  4. Clone the bare copy.
  5. In that clone, `python3 scripts/check_changelog.py --require-new` must exit 0 and report a new entry.
  6. `python3 scripts/update_site.py` exits 0, then `git diff --quiet -- site/data.json assets/roadmap.svg
     .claude/rules/chaincompiler_states.md` exits 0 and `git ls-files --others --exclude-standard --` on the same three
     prints nothing — both halves of the public `deploy.yml`'s staleness gate.
  7. Every symlink resolves (`find . -type l ! -exec test -e {} \; -print` prints nothing).
  8. `git show --stat HEAD` lists exactly the intended files.
- unit selection: `git diff --name-only <merge-base>..<tip> | python3 scalable-publishing/bin/select_units_for_paths.py
  --manifest scalable-publishing/publish-manifest.json` names `chaincompiler` and every other unit the change is meant
  to republish, and no other — a `chaincompiler-pkg-*` unit never. `generate_publish_paths.py --manifest
  scalable-publishing/publish-manifest.json --workflow .github/workflows/publish-on-main.yml --check` exits 0 — without
  `--workflow` it prints the paths and checks nothing.
- the clean install: clone the dry-run result. In a fresh venv made by `python3 -m venv` and given nothing by hand,
  where `command -v python3` is checked to be that venv in the same command, run `./install.sh`, then the full
  source-tree proof above — once on Python 3.11 and once on the newest Python uv offers, since the build files admit
  every Python from 3.11 and a plugin install's uv takes whichever one the machine has. Also run
  `python3 -c "import si.server"`, the module the plugin's launcher starts.
- THE WHEEL PROOF, before the merge, from the dry-run clone: `scalable-publishing/bin/publish_package.sh
  packages/<folder> --dry-run` for each of the fifteen passes `twine check` and finds the version not yet on PyPI;
  `python -m build --wheel` builds each into a folder the proof keeps; a fresh venv, checked to be the `python3` in use,
  installs the fifteen non-editable from those wheels (`--find-links`, with `--report`, the report showing each of the
  fifteen taken from that folder) with the outside dependencies from PyPI; `pip check` is clean; the source-tree
  proof's checks run from the clone against that venv, each with no failure, `WHEREIMPORT=<the fifteen's modules>
  PYTHONPATH=scripts … -p whereimport` printing every module inside the venv; and in that venv each Python block of the
  eight capability skills, piped alone into its own empty scratch folder, exits 0.
- after the merge, in this order:
  0. THE PUBLISH: the source home's `publish-on-main.yml` makes the `Publish base/chaincompiler (<sha>)` commit on the
     merge. While GitHub Actions starts no job, the session runs that workflow's steps itself, from a clean checkout of
     the source home at the merge: the units `select_units_for_paths.py` names for the merge's diff, each — the
     marketplace unit's catalog rendered by `generate_marketplace.py` first — published with
     `bash scalable-publishing/bin/publish_unit.sh <subdir> https://github.com/<public_repo>.git <short merge sha>
     <public_repo> '<the unit's readme JSON>'`, `GITHUB_TOKEN` set from `gh auth token` for the README's badges.
  1. THE UPLOAD, first: once `git ls-remote` shows the `Publish base/chaincompiler (<sha>)` commit whose `<sha>` is the
     merge, clone the public repository at that commit — the clone kept until PyPI holds the whole release — and run
     `python3 scripts/upload_release.py --clone <the clone> --publish-package scalable-publishing/bin/publish_package.sh`
     (`--order` prints its order, `--dry-run` its plan), which uploads each of the fifteen through `publish_package.sh`
     in dependency order: a package only after every sibling its build file requires (its dependencies among the
     fifteen, not its extras) is on PyPI at the release. Three tiers, each in dependency order and then by name, exactly
     as `--order` prints: the self-interpreter's closure first — `honeyc` · `rulecatcher` · `chaincompiler` ·
     `chaincompiler-accc` · `corcc` · `skillchain-compiler` · `sccc` · `chainaios` · `chaincompiler-si` — then the packages
     the shipped skills run beside it, `glyphsteer` · `skill2framework`, then `chaincompiler-archetype` · `goldenreq` ·
     `personacc` · `personapack`; never the folders' alphabetical order. PyPI creates four new projects in any 86,400
     seconds for one account and one address, counted from the creations themselves (`429 Too many new projects
     created` past it, `q=4;w=86400` in its `RateLimit-Policy` header; a refused try counts for nothing), while a
     version of a project it holds uploads at once: after a 429 a later package still uploads only when PyPI holds its
     project and every sibling it requires, and every other name waits for the next batch, taken in the same order from
     the same clone — the driver run again no sooner than a day after the last creation of the run before, never at a
     fixed hour, reading PyPI's state afresh. A pass run again reads a refusal of a version PyPI already holds at the
     release's own version as that package uploaded. A `400 Bad Request` on a new name whose build passed `twine check`
     is PyPI refusing the name itself: no run uploads it, and the package is renamed in the next release (`DESIGN.md`
     §18). Before stage 2 starts, `python3 scripts/upload_release.py --clone <the clone> --whole` exits 0: it reads
     whether PyPI holds the release from each of the fifteen's version JSON (`https://pypi.org/pypi/<name>/<version>/json`),
     whether both forms of the simple index (`https://pypi.org/simple/<name>/`, its HTML page and the JSON form pip and uv
     ask for first) list the release's files, and whether each package was uploaded longer ago than the index's cache life
     (its `cache-control` max-age), the upload time read from the version's JSON. Before the upload it exits 4, every
     version JSON 404 (recorded as the store's before); after it, 0. Each of PyPI's pages is served through a cache that
     can still answer as before the upload — the simple index until its max-age (600 s) ends, each form apart, and a
     version's JSON 404 for up to 72 s after v0.3.3's uploads (scalable-publishing `DESIGN.md` §4) — so an exit 3,
     every version JSON 200 and a form of the simple index not listing them all or an upload still within its cache
     life, is read again a minute later, and so is an exit 4 in the minutes after an upload; an exit 4 that stands over
     readings several minutes apart names a package PyPI does not hold — an upload not run, failed or refused — and the
     upload driver runs again (`publish_package.sh` refuses a version PyPI holds), or the name is treated as refused. A
     release is never called short from the project's JSON.
  2. THE INSTALL FROM PYPI: a fresh venv, checked, `pip install --no-cache-dir --report <file>` of `chaincompiler-si`,
     `glyphsteer`, `skill2framework`, `personapack`, `chaincompiler-archetype` and `goldenreq` at `==<release>` with no index
     but PyPI; the report shows every one of the fifteen downloaded from PyPI; `pip check` is clean; the source-tree
     proof's checks run from a clean clone at the publish commit against it, each with no failure, every module
     resolving into the venv.
  3. THE PLUGIN PROOF: `scripts/plugin_proof.py new <root>` (a scratch root outside the world dir), `install <seat>
     --version <release>` passing every check, `run <seat> --prompt-file scripts/plugin-proof-task.md --out <t>.jsonl
     --allowed-tools Skill Read 'Bash(uv:*)' 'Bash(uvx:*)' mcp__plugin_chaincompiler_self-interpreter__si_interpret`
     exiting 0, `grade` passing every check, then `remove`; every proof names the seat `<seat>`. The seat's uv cache
     starts empty, so this is the cold start: the transcript's init event proves only that the launcher answered, the
     `si_interpret` answer of `2` proves the real server, and the grade records the seconds from the session's start to
     that answer — uv's install of the server — as `seconds_from_session_start_to_server_answer`, the start being the
     `started_at` `run` writes into the transcript's `.env.json` sidecar just before the session (before: the sidecar's
     keys without it; after: with it), since the init event carries no timestamp. A transcript whose sidecar has none —
     one `run` wrote before v0.3.3 — is graded from its first timestamped event, which is later than the session's
     start, and the grade names which start it used.
  4. the public repository: `gh run list -R <owner>/<name>` shows `deploy-site` succeeded on the publish commit, and a
     clean clone of it passes the clean-install proof.
  5. when the release touched what CompiloApe's forge reads, CompiloApe's forge flow runs whole against it.
  6. the records that state PyPI's state (step 11) are rewritten to it once stage 1 is whole.
  The next release merges only after this one is whole on PyPI and stages 2–5 have run, so every version PyPI holds is
  a whole, installable line — save a release short only of a package whose name PyPI refuses: stages 2–5, which need all
  fifteen, do not run for it, and the next release, which renames that package, merges and runs them (`DESIGN.md` §18).

NOT:[edit the public repository · add a `CHANGELOG.md` to the source folder · put a `CLAUDE.md` at the folder's root
(the plugin carries none; an agent it delivers ships inside its install skill, `DESIGN.md` §16) · hand-edit a generated
file (site data, roadmap SVG, the board, capability skills, the grade ladder, GBA output) · fix a shipped instruction in
one copy while its generator or another copy keeps the old reading · leave a second `SKILL.md` under a shipped skill's
name with other bytes · move one version line without the others · merge a change to the folder without a new README
changelog version · upload a package built from anything but a clone of the public repository at the release's publish
commit · run anything else in the after-merge proof before the upload · upload a package before every sibling it
requires is on PyPI at the release · merge the next release while this one is not whole on PyPI, a name PyPI refuses excepted, renamed in it · reuse a version PyPI
holds · call a release short from the project's JSON · let a
check against an install import a clone's source · prove the clean install only on an interpreter whose
venv happens to carry a new enough setuptools · run the plugin proof's session with the user's settings or outside a
marked seat · delete an open backlog task · claim a GBA rebuilds from a copy whose `skill_src` resolves outside the
copied folder or into an ignored `dist/` · trust `validate()` as proof a rebuild kept its bodies (it checks frontmatter
and breadcrumbs, not content) · write `cat` as the way to descend into a node · push the dry run anywhere · pip install
into an environment without checking which `python3` it is · state a record's PyPI fact ahead of the upload · let the
launcher answer what the real server would not (a protocol version it does not hold, a capability it lacks, a tool list
of another `fastmcp`) · hold a protocol-era probe until the real server is up · read or write either of the launcher's
streams in the machine's locale encoding · swallow a request the launcher cannot deliver · write held requests from the
thread that reads the real server's output · read "connected" at the session's start as proof of the self-interpreter ·
match a grader's failure phrase in a file the session read · write the launch line anywhere but `uvline.py` · run the
release check on a dirty tree, or with a `python3` that imports another tree's packages · except a line from the
replaced-reading grep because it mentions `git grep` · read the README below `## Status` as history · time the
launcher's `initialize` answer from anything but the client's first message · take the launcher's own
`notifications/initialized` as the only proof that the real server answered · upload a version again on a 404 read
in the minutes after its upload, before reading it again · start the install from PyPI before `--whole` exits 0 · read
the simple index in one form only]

COMPOSES:[`.claude/rules/00-keeping-roadmap-and-backlog-current.md` — the same-change discipline this flow runs at
release grain · `.claude/rules/22-seq-mint-attention-chain.md` — the flow for minting what a release ships ·
`.claude/rules/02-the-autoload-mechanism.md` — why descent is the Read tool · scalable-publishing's edit flow and its
`DESIGN.md` §4 — how a package inside this folder reaches PyPI · CompiloApe's forge flow — the agent built on this one ·
the source home's publishing rule — the manifest is the allowlist, and the public repository is a delete-enabled mirror]

GATE (what would detect a violation):[`scripts/check_versions.py` — the version line, the build files' declarations,
the skills' uv lines, and every copy of a shipped skill, every `SKILL.md` under a `.claude/skills/` folder or a
package's own folder that carries a shipped skill's name among them · `scripts/tests/test_skill_examples.py` — a
capability skill's Python block that does not run alone · `scripts/upload_release.py` — the upload in dependency order
from the kept clone, refusing a package whose sibling PyPI lacks, stopping its new names at PyPI's quota and resuming
from PyPI's state; its `--whole`, a release not yet held by each version's JSON (exit 4, read again in the minutes
after an upload, since a cache can hold a 404), not yet listed by both forms of the simple index, or uploaded within the
index's cache life (exit 3, read again) · `scripts/build_server_tools.py --check` — launcher answers (`initialize.json`, `tools.json`) that
are not the real server's under the environment's `fastmcp` · `scripts/tests/test_server_launch.py` — a launcher that waits where it must
answer, answers what the real server would not, loses, reorders or re-encodes a message, or leaves a request
unanswered · `scripts/plugin_proof.py grade` — a plugin install that does not work · `scripts/release_check.py` — a
stale or missing generated file, a frontmatter that does not parse, a replaced reading still read (one wrapped across
two lines, or sitting in the README's `## Status`, included), a machine path, a publish dry run that fails or whose
generated files differ or go untracked, a tee probe whose launcher waits (a held `server/discover` included), answers
wrongly, writes a call to the real server before the real server answered, or loses a request — run before the
release's PR is opened, on a clean tree with this tree's packages imported, its findings planted in
`scripts/tests/test_release_check.py` · `scripts/check_versions.py`'s linked-folder scan — a copy reached through a
linked folder at the skill's own folder or any folder above it]
