# 22-seq — MINT AN ATTENTION CHAIN / CHAIN SYSTEM through the door (dev-flow + rehydration protocol)

The feature: turn a style/domain "how to think" into forged AC language(s) + shipped
`skills/<name>/SKILL.md` package(s) — bare atom via `accc`, or the full rolled-up chain
system (ACs + persona CoR + SC + persona AIOS) via `chainaios.roll_up_algebra`. Through
the door, never by hand. This rule IS the read list for that work.

## THE CONTENT LAW (the author, 2026-08-12 — the correction that re-minted v0.1.47 as v0.1.48)

**The foci must be the OPERATIONS the style performs, not the topics it lands on.** A
topic-label chain (`[Dream] ⇒ [System] ⇒ …`) is a table of contents, not cognition. And a
single chain rarely reproduces a cognition — the unit that does is the LANGUAGE (several
chains covering the distinct maneuvers) + a bespoke `PersonaSpec` CoR whose Move cues pin
the spoken register (the melt-gauge). Recursion is expressed as a chain that re-enters
itself (`|RecurseOrClose|`), sequenced by the SC.

## RETRIEVE (read before minting — the execution boundary)

| what | where |
|---|---|
| the accc door (forge/gate/package/prime; strict semantics) | `packages/accc/src/accc/forge.py` (whole, ~88L) |
| AC parse + the injectable block | `packages/accc/src/accc/render.py` |
| corpus format precedent (one chain per line, exemplar first) | `packages/accc/src/accc/notation.py` + `packages/accc/examples/*.ac` |
| the generic forge core (scope `ac:<name>`) | `packages/chaincompiler/src/chaincompiler/forge.py` |
| the rollup lane (atoms dict · persona= · sequence= · closure) | `packages/chainaios/src/chainaios/bandit.py:161-225` (+ `construct.py` for the lighter `construct_language`) |
| the CoR persona model (Move cues = the melt-gauge) | `packages/corcc/src/corcc/{notation,forge,paragraph}.py` |
| the SC resolver/rollup | `packages/sccc/src/sccc/forge.py` |
| the REAL frontmatter writer — ⛔ NO YAML escaping | APE `prompt_engineering/skillpack.py` (installed): a `": "` in any description emits unparseable frontmatter; the *CC defaults are colon-free since v0.1.48, but caller-supplied descriptions must be too |
| WHO READS `skills/` — the plugin payload | `.claude-plugin/plugin.json` + `marketplace.json` (descriptions ENUMERATE the shipped skills; version must bump on payload change) |
| the same-change discipline | `.claude/rules/00-keeping-roadmap-and-backlog-current.md` + `scripts/{check_changelog,update_site}.py` |
| ⛔ THE TOPOLOGY | chaincompiler has ONE source home, where it is edited, and is published to `sancovp/chaincompiler` with a version and a changelog entry per release — edit only the source home, never the published repo |

## COHERENCE SET (what else moves when an AC / chain system is minted — same commit)

1. `packages/accc/examples/<name>.ac` — the corpus (the language is re-forgeable from it; the rulecatcher db is scratch).
2. `skills/<slug>/SKILL.md` — written by the door ONLY; a hand edit breaks the byte-reproducibility proof.
3. Rollup extras: persona AIOS under `personas/` (`persona_root=`), the `<domain>-tree` closure artifact beside the SC, `chain.json` in the SC dir.
3b. **GBA lane — seat the sub-domain personas deliberately.** `construct_into(g, name, atoms, persona=PersonaSpec(...))` makes that branch a **LORD** (its own `CLAUDE.md`, re-emitted from `gba.json`'s `_lord` after every materialize) — descending into its dir SEATS you as it. Omitting `persona=` deliberately leaves it the root lord's own region (rule 01's warrant clause). Verify a lord by DESCENT (Read into the dir; the persona + its scoped skill must inject), never by reading the emitter.
4. **Plugin surface**: `skills/` IS the plugin payload — update the skill enumeration in `.claude-plugin/plugin.json` + `marketplace.json`, bump the plugin version.
5. BACKLOG tick/row + README `## Changelog` new `### vX.Y.Z — date` block + `python3 scripts/update_site.py` (commit `site/data.json`). `roadmap.json` only if a phase moved.
6. **The topology line (never skip):** state in the commit/report where the change is homed — "monorepo-side; upstream sync pending the authoritative-source decision" — and never resolve that decision silently.

## THE CHANGE (the call sequence)

Bare atom: `accc.forge(name, corpus, db=<scratch>) → accc.gate(lang, every line) → accc.package(name, exemplar, out_dir="skills", description=<colon-free>)`.

Full system: `roll_up_algebra(domain, atoms={name: (chain, desc)}, persona=PersonaSpec(...), sequence="[ac:…] ⇒ [ac:…] ⇒ [cor:<persona-slug>] ⇒ |Held|", db=<scratch>, skills_dir="skills", out_dir="skills", persona_root="personas")` → assert `system.closed` (the closure proof: every artifact is a real skill dir AND the organizing SkillTree validates with zero violations).

## THE PROOF (per-store, before calling it done)

- **SKILL.md**: frontmatter passes `yaml.safe_load`; byte-compare a re-run of the door against the committed file (the hand-edit detector).
- **Gate**: every corpus line returns clean. ⚠ HONEST LIMIT (2026-08-12, measured): shape-only gates admit ANY bracketed chain, and `strict=True` did NOT reject off-style same-shape probes on the v0.1.48 corpora (single-atom and mixed both) — vocabulary teeth are an OPEN item (BACKLOG); do not claim "gated clean" implies style enforcement. The CoR's cue-pinned melt-gauge is the working style check.
- **Closure** (rollup lane): `system.closed == True`, `report.violations == 0`.
- **Suites**: `.venv/bin/python -m pytest packages/{accc,corcc,sccc,chainaios}/tests -q` → all green (36 at v0.1.48).
- **Changelog gate**: `scripts/check_changelog.py` exit 0 (local smoke — the real `deploy.yml` fires only in the public repo's CI).
- **Plugin surface**: plugin.json names the new skill; version bumped.
- **Topology**: the report carries the homing line.
