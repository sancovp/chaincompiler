# 22-seq — CUT A CHAINCOMPILER RELEASE from its source home: one version, every generated file regenerated, every copy coherent, proven on a clean install of what publishes

<docsys kind="dev-flow" role="instance"/>

TRIGGER:[any change under the source home `base/chaincompiler` that will merge to the source home's default branch ·
a change to the `chaincompiler` unit in the source home's `scalable-publishing/publish-manifest.json` · a change to
the publish machinery that unit runs through] · a PROCEDURE flow: every stage runs every time

PRINCIPLE:[the source home is the only place ChainCompiler is edited · ChainCompiler is published, so every merge that
touches it is a release, because the publish pipeline mirrors the folder to the public repository on that merge, with
deletes · the public repository's own gate requires a NEW README changelog version on every publish commit, so a merge
without one turns the public deploy red · a version that does not move keeps every installed plugin on the old
payload, because Claude Code pins an installed plugin to its `plugin.json` version until that version changes]

## RETRIEVE (in this order; whole file unless a section or a function is named — read that whole)

| what | where |
|---|---|
| the design the release must keep true | `DESIGN.md` §0 · §2 · §8 · §16 · §17 · §18 · §19 · plus every section the change touches |
| the same-change discipline | `.claude/rules/00-keeping-roadmap-and-backlog-current.md` |
| the mint flow, when a skill or chain is minted | `.claude/rules/22-seq-mint-attention-chain.md` |
| the release surface | `README.md` badge line (anchor `badge/tests-`) · `## Quickstart` · `## Changelog` head and newest entry · `## Status` table · `BACKLOG.md` · `roadmap.json` · `ROADMAP.md` · the generated board `.claude/rules/chaincompiler_states.md` |
| the version lines | `.claude-plugin/plugin.json` `version` · `.claude-plugin/marketplace.json` `plugins[].version` · `packages/*/pyproject.toml` line `version =` · each package's `__version__` |
| the install path | `install.sh` (the PyPI line and the `PKGS` list) · `.mcp.json` |
| the generators and what they write | `scripts/update_site.py` (`parse_changelog`, `render_board`, `main`) → `site/data.json`, `assets/roadmap.svg`, `.claude/rules/chaincompiler_states.md` · `scripts/build_meta_ape_skills.py` → the eight capability skills in `skills/` · `packages/chainaios/src/chainaios/gba.py` (`_BCS_SKILL`, `_rule_blocks`, `_portable`/`_resolved`, `_apply_tree`) → every GBA under `personas/` · `packages/chainaios/src/chainaios/hba.py` · `packages/chainaios/src/chainaios/cog.py` |
| what git does not carry | `.gitignore` (its `dist/` line drops every `personas/.<name>.src/dist/` except the two un-ignored root packages; the derived `.index.db`) |
| the public repository's gates | `.github/workflows/deploy.yml` · `scripts/check_changelog.py` · `.github/workflows/contribute.yml` · `scripts/validate_registry.py` |
| the checks | `examples/_all/run_all.py` · `examples/_all/bandit_self.py` · `examples/_all/test_all.py` · `examples/nutrition/build.py` · `examples/nutrition/test_nutrition_aios.py` · `.importlinter` |
| the publish pipeline (in the source home's repository, outside this folder) | `scalable-publishing/publish-manifest.json` — the `chaincompiler` unit and the `sancrev-marketplace` unit (its `watch_paths`) · `.github/workflows/publish-on-main.yml` · `.github/workflows/publish-subdir.yml` · `scalable-publishing/bin/select_units_for_paths.py` · `scalable-publishing/bin/publish_unit.sh` · `scalable-publishing/bin/generate_unit_readme.py` · `scalable-publishing/bin/generate_marketplace.py` · `scalable-publishing/bin/generate_publish_paths.py` · `scalable-publishing/templates/readme-refresh.yml` |
| the records above the folder | the source home's project registry, section `base/chaincompiler` · the source home's root `CHANGELOG.md` tail · `scalable-publishing/CHANGELOG.md` tail · THE TOP-LEVEL DESIGN's publishing bridge (the list of published units) |
| every other copy of what the change edits | `git grep -n '<name, path or sentence changed>' HEAD -- base/chaincompiler` — each hit's file read whole; for a shipped skill, every `bandit-chain-system/SKILL.md` and every rule block `gba.py` writes |

## THE CHANGE (obligations, in order)

1. EDIT ONLY THE SOURCE HOME. Never edit the public repository. A file that exists only there is deleted at the next
   publish, except `CHANGELOG.md`, `.github/scripts/generate_unit_readme.py` and `.github/workflows/readme-refresh.yml`,
   which the publisher owns. Never add a `CHANGELOG.md` to the source folder: the mirror excludes that name, so it would
   never publish. The project's history is the README's `## Changelog`.
2. CHANGE THE CODE AND THE GENERATOR, NEVER ONLY THE OUTPUT. When an instruction, a description or a skill body is
   wrong, fix the code that writes it — `gba.py`'s `_rule_blocks`, `hba.py`, `cog.py`, `bandit.py`,
   `scripts/build_meta_ape_skills.py` — and then regenerate the committed outputs from it. A hand fix to a generated
   file is a defect that the next regeneration undoes.
3. REGENERATE EVERY GENERATED FILE in the same change:
   - `python3 scripts/update_site.py`, which writes `site/data.json`, `assets/roadmap.svg` and the board
     `.claude/rules/chaincompiler_states.md`;
   - `python3 scripts/build_meta_ape_skills.py`, when a capability or APE changed;
   - each committed GBA under `personas/`, re-applied through `_apply_tree` from its own `gba.json` with its sibling
     `.<name>.src/` present, whenever `gba.py`, `hba.py`, `cog.py`, the `bandit-chain-system` skill or SkillTree changed.
4. MAKE EVERY COPY ONE. The `bandit-chain-system` skill lives in four places: `.claude/skills/`, `skills/`, and each
   GBA's `.claude/skills/`. All four equal the bytes `_apply_tree` copies. When one sentence moves, grep for it and
   move it in every copy and in every generator that writes it, including the GBA rule blocks.
5. CUT ONE VERSION and write it everywhere a version lives, in the same change:
   - a new `### vX.Y.Z — date` entry at the head of the README `## Changelog`;
   - the `plugin.json` `version`;
   - the `marketplace.json` `plugins[].version`;
   - each package's `pyproject.toml` version and `__version__`, for the packages the change moved.
   Also update the skill enumeration in `plugin.json` and `marketplace.json` whenever the shipped `skills/` changed.
6. KEEP THE BACKLOG TRUE, without deleting work:
   - tick a `BACKLOG.md` item when it is done;
   - add an item when work is found;
   - never delete an open `[ ]` item. Move it, or tick it with the reason;
   - every `roadmap.json` phase still `in_progress` keeps at least one open task in `BACKLOG.md`.
7. REWRITE `DESIGN.md` where the design changed. Every factual sentence must be checked against the code at this tip
   before it is written. Every known defect is `⚠ OWED` with its BACKLOG task.
8. MOVE THE RECORDS ABOVE THE FOLDER when the release changes what they state:
   - the publish manifest's `chaincompiler` unit `readme.description`;
   - the source home's project registry section;
   - THE TOP-LEVEL DESIGN's publishing bridge, through its own write procedure;
   - a source-home `CHANGELOG.md` entry for every file outside the folder that the change touched.

## COHERENCE SET (what changes when this changes)

- A package version moves, so the README changelog version, `plugin.json`, `marketplace.json` and that package's
  `pyproject.toml` and `__version__` all move.
- Any change under `skills/` changes the plugin version and the skill enumeration in both plugin manifests.
- The README changelog changes, so `site/data.json` is regenerated.
- `roadmap.json` changes, so `site/data.json`, `assets/roadmap.svg`, the board and `ROADMAP.md` move with it.
- A `gba.py`, `hba.py` or `cog.py` text change re-applies every committed GBA under `personas/` and every copy of the
  `bandit-chain-system` skill.
- `scripts/build_meta_ape_skills.py` or APE changes, so the eight capability skills are regenerated.
- A moved name (`construct_language`, `roll_up_algebra`, `hierarchicalize`, `make_gba`, the `gba`/`hba`/`cog`/`bandit`
  modules) is grepped in `examples/`, `skills/`, `personas/`, `.claude/`, `scripts/` and the README above
  `## Changelog`.
- A package added or dropped changes `install.sh` `PKGS`, the README Status table, the manifest's `readme.description`,
  `DESIGN.md` §0 and §2, `21-architecture-diagrams.md` §1 and §4, and `.importlinter` when the package is in
  the tier chain.
- An import edge changes `21-architecture-diagrams.md` §4 and DESIGN §2. Both state the real import graph, lazy imports included.
- A breadcrumb or descent wording changes rules 01 and 02, `.claude/skills/skilltree/SKILL.md`, the si docstrings and
  MCP tool descriptions, and the GBA, COG and HBA generated texts. Descent is the Read tool, never `cat`.
- A test count changes the README badge, the README Status table and the changelog entry's suite line.
- A manifest edit also republishes `sancrev-marketplace` through its `watch_paths`. Confirm its catalog render is the
  one intended.

## THE PROOF (per store, before and after; run every gate BARE and read its output)

- the source tree, in an environment `./install.sh` built:
  - `pytest packages` passes, with the same count the README Status table states;
  - `python examples/_all/run_all.py` shows all checks ✓;
  - `python examples/_all/bandit_self.py` shows all checks ✓;
  - `pytest examples/nutrition` passes;
  - `lint-imports` reports the contract KEPT;
  - `python3 scripts/check_changelog.py` exits 0;
  - the board gate, run bare on the board's absolute path, passes.
- generated files: in a copy of the tree,
  - run `scripts/update_site.py`, then `diff` `site/data.json`, `assets/roadmap.svg` and the board against the
    committed files. They must be empty;
  - run `scripts/build_meta_ape_skills.py`, then `diff -r skills/` against the committed files. It must be empty;
  - re-apply each GBA under `personas/` with `_apply_tree(_resolved(gba.json))`, then `diff -r` against the committed
    copy, excluding `.index.db`. It must be empty;
  - count `SKILL.md` bodies reading `SkillTree <kind> node \`` (stubs). The count must equal the count before the
    re-apply.
- skill loader: every `SKILL.md` under `skills/`, `.claude/skills/` and `personas/` is checked with
  `yaml.safe_load` on its frontmatter. Each must give a mapping with string `name` and `description`, found with a
  recursive walk that enters dot-directories, and every failure is named.
- one sentence, one meaning: `git grep -n '<every sentence the change rewrote>' HEAD -- base/chaincompiler` returns
  the new reading only. In particular, `git grep -n 'Promote a chain to golden' HEAD -- base/chaincompiler` returns
  0 lines outside the README history, and so does `` git grep -nE '`cat ' `` across `packages/*/src` and `.claude/`.
- configurable: across `git ls-files` there are no matches for
  `grep -nIE '/Users/[A-Za-z]|/home/[A-Za-z]|/private/(tmp|var)/|/var/folders'` except this rule's own line stating
  the pattern, no `~/<name>` other than `~/.claude`, and no person named as the user. An author credit is allowed.
- versions: `plugin.json` `version` differs from the published one whenever `skills/` changed. Read it in the public
  repository with `gh api repos/<owner>/<name>/contents/.claude-plugin/plugin.json`. The new README changelog version
  is not in the public README.
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
  to republish, and no other. `generate_publish_paths.py --manifest scalable-publishing/publish-manifest.json --check`
  exits 0.
- the clean install: in a fresh venv, where `command -v python3` is checked to be that venv in the same command,
  clone the dry-run result. Run `./install.sh`, then the full source-tree proof above. Also run
  `python3 -c "import si.server"`, the module the plugin's MCP launches.
- after the merge, in the public repository:
  - `git ls-remote` shows a new `Publish base/chaincompiler (<sha>)` commit whose `<sha>` is the merge;
  - `gh run list -R <owner>/<name>` shows `deploy-site` succeeded on it;
  - a clean clone of it passes the clean-install proof.

NOT:[edit the public repository · add a `CHANGELOG.md` to the source folder · put a `CLAUDE.md` at the folder's root
(the plugin carries none; an agent it delivers ships inside its install skill, `DESIGN.md` §16) · hand-edit a generated
file (site data, roadmap SVG, the board, capability skills, GBA output) · fix a shipped instruction in one copy while
its generator or another copy keeps the old reading · change `skills/` without bumping the plugin version · merge a
change to the folder without a new README changelog version · delete an open backlog task · claim a GBA rebuilds from
a copy whose `skill_src` resolves outside the copied folder or into an ignored `dist/` · trust `validate()` as proof a
rebuild kept its bodies (it checks frontmatter and breadcrumbs, not content) · write `cat` as the way to descend into a
node · push the dry run anywhere · pip install into an environment without checking which `python3` it is]

COMPOSES:[`.claude/rules/00-keeping-roadmap-and-backlog-current.md` — the same-change discipline this flow runs at
release grain · `.claude/rules/22-seq-mint-attention-chain.md` — the flow for minting what a release ships ·
`.claude/rules/02-the-autoload-mechanism.md` — why descent is the Read tool · the source home's publishing rule — the
manifest is the allowlist, and the public repository is a delete-enabled mirror]

GATE (what would detect a violation):[a script in `scripts/` that runs the generated-file diffs, the frontmatter sweep,
the grep for each rewritten sentence, the version-line comparison and the publish dry run, and exits non-zero on any
finding — run before the release's PR is opened]
