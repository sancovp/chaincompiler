# ChainCompiler — DESIGN

## §0 What ChainCompiler is

ChainCompiler is a compiler-compiler for cognition. A language model thinks in whatever notation it is
given, so the useful machine is not one notation but a factory for them: ChainCompiler mints a notation
from examples, gates text against it so a model cannot malform it, compiles it into a skill any agent
loads, composes those skills, organizes them into a tree an agent walks, and builds agents out of them.
Every check it makes is about syntax and structure. It never judges whether a thought is good — that
boundary is deliberate, and every section below keeps it.

**What it ends as: a PLUGIN.** The public repository `github.com/sancovp/chaincompiler` carries a Claude
Code plugin (`.claude-plugin/`): the skills under `skills/` and the self-interpreter MCP server
(`.mcp.json`). The plugin's program is the fifteen Python packages under `packages/`, installed by
`./install.sh`. It is published there now (§18); installing it through Claude Code's plugin commands into
a clean Claude Code is not yet proven (§16).

**How to read this document.** One section per part, in dependency order; §2 is the map of the whole.
`ASPIRATIONAL:` marks what is designed and not built. `⚠ OWED:` marks a known defect in what is built,
with its task in `BACKLOG.md`.

**How to change it.** Rewrite the section a change touches in the same commit as the change, so this
document always states the current design and nothing else. What changed, what it replaced and why go in
the README's `## Changelog` — the project's one history, gated by `scripts/check_changelog.py`.

**Where work state lives.** `roadmap.json` holds the phases (P0–P9; rendered to the roadmap SVG, the site and
the board `.claude/rules/chaincompiler_states.md`, and mirrored in prose by `ROADMAP.md`) and `BACKLOG.md` holds
the tasks under them. Both move in the same change as the work
(`.claude/rules/00-keeping-roadmap-and-backlog-current.md`); the board is never edited by hand. A question only the
author can answer is a `BACKLOG.md` task marked as the author's call.

**Where the detail lives** — each is reference detail for the section that points to it:

| document | what it answers |
|---|---|
| `README.md` | the public face: the pitch, the quickstart, and the changelog (the history) |
| `ROADMAP.md` · `roadmap.json` · `BACKLOG.md` | the phases and the tasks (§17) |
| `REBUILD-SPEC.md` | the record of the rebuild that produced the layering in §2 |
| `FEDERATION.md` | the plan behind the marketplace federation (§15) |
| `DIETC-AIOS-REBUILD.md` | the record of rebuilding the nutrition compiler as an agent (§8, §19) |
| `.claude/rules/01-everything-is-a-tree.md` | the tree law (§10) |
| `.claude/rules/02-the-autoload-mechanism.md` | what Claude Code loads when an agent reads into a folder (§8, §10) |
| `.claude/rules/21-architecture-diagrams.md` | the stack, the component diagrams and the sequence diagrams of everything below, with every dev flow placed on the stack |
| `.claude/rules/22-seq-mint-attention-chain.md` | the procedure for minting an attention chain or a chain system (§5, §7) |
| `.claude/rules/22-seq-chaincompiler-release.md` | the procedure for cutting a release: one version everywhere, every generated file regenerated, every copy coherent, proven on a clean install of what publishes (§16, §18, §19) |
| `.claude/rules/chaincompiler_states.md` | the board, generated from `roadmap.json` — never edited by hand |
| `packages/*/README.md` | each package's own reference |

## §1 The one type and the closed algebra

Everything reduces to one type, the **skill dir**: a folder `<name>/` holding a `SKILL.md` with YAML
frontmatter, the unit Claude Code auto-loads. Every operation produces or consumes only that type, so
composition closes and recurses:

```
a constructor (*CC)   lifts a notation into a skill dir
a skillchain          composes skill dirs into one skill dir   (a chain of chains is a chain)
a SkillTree           arranges skill dirs into a walkable tree
a validator           checks each seam the platform does not check
```

Every constructor runs the same loop. **Forge**: learn a grammar from example chains into a named scope
(a *forged language*). **Gate**: lint a candidate against that grammar — clean, or a violation with a
suggested fix. **Package**: write the compiled body as `<name>/SKILL.md`. **Prime**: render a block that
teaches a model the grammar and shows one compiled example, so the model writes in shape and the gate
catches drift. A language forged shape-only (`strict=False`) admits any vocabulary in the right shape;
`strict=True` also pins the vocabulary.

## §2 The layers

Imports point down, with the one exception below. From the bottom:

```
foundation (PyPI)   pydantic-stack-core            blocks: every prompt is a MetaStack of RenderablePieces
                    agent-prompt-engineering (APE) the prompt engine, the grammar seam, the skill packager
engine (here)       rulecatcher · honeyc (+ dietc) · skillchain
organization (PyPI) agent-skilltree                SkillTree (§10)
base                chaincompiler                  imports APE · rulecatcher · honeyc (glyphsteer lazily)
chain tier          accc → corcc → sccc            each imports the ones below it and the base
agent tier          chainaios                      imports the chain tier, the base, SkillTree (glyphsteer if present)
beside the tiers    personacc → personapack        persona bundles (§6)
                    goldenreq                      the acceptance gate, stdlib only (§9)
                    glyphsteer                     retrieval steering (§11)
                    archetype · framework · si     §12 · §13 · §14
```

`.importlinter` enforces the six-layer chain `chainaios > sccc > corcc > accc > chaincompiler >
prompt_engineering`; `lint-imports` keeps it. The base never imports a chain compiler, and no chain
compiler imports the agent tier — that is what lets each tier be made from the one below it. The
packages beside the tiers are not under the contract (ASPIRATIONAL: widen it to cover them).
⚠ OWED: one lazy cycle sits outside the contract — the base's `persona` front end imports glyphsteer inside
its functions, and glyphsteer's grammar imports the base inside its own. Break it, so the base imports
nothing from beside the tiers.

The rebuild that produced this layering is recorded in `REBUILD-SPEC.md`; the prompt engine's own account
of it is `META-APE-ARCHITECTURE.md` in `github.com/sancovp/prompt-engineering`.

## §3 The engine — rulecatcher and honeyc

**rulecatcher** (`packages/rulecatcher`, no dependencies) is the gate. It learns rules from examples into
named scopes in a SQLite store — `next_kind` rules for shape, `next_token` rules for vocabulary — and
lints text against a scope. A violation is **orthogonal** (a known token in the wrong slot: steerable) or
**syntax_break** (a token foreign to the language: fatal). It has its own CLI and README.
⚠ OWED: a shape-only gate admits any bracketed chain, and on small corpora `strict=True` has not been shown
to reject an off-style chain of the right shape — the gate enforces form, and vocabulary enforcement is
unmeasured (BACKLOG).

**honeyc** (`packages/honeyc`) compiles the Dense Rune-Chain notation (`[Entity]`, `|Bounded|`, `⇒`, `⇔`,
relation markers, scopes, placeholders): a Lark grammar parses it to an AST, `normalize` flattens it to
triples, and lenses render it readable, as triples, as prose, as Prolog text or as Cypher text; `check`
suggests rewrites. **dietc**, in the same package, is a nutrition compiler built on honeyc — the proof
that a domain compiler can ride on it (`packages/honeyc/DIETC.md`). Each user's notation is that user's own
configuration (§1: a notation is minted from its user's examples); for this repository's own Dense Rune-Chain
notation, its README, its examples, its grammar, its code and its tests state one reading of every marker the grammar
defines. A relation is written `A -rel-> B` or `A <rel- B`, two
spellings of `rel(A, B)`, and `A <rel> B` states it both ways; the readable lens writes back the spelling it read.
⚠ OWED: the README's table calls `A <rel- B` the reverse of `A -rel-> B` and gives no reading for `⟶` or `⟼`, and
the readable lens writes both spellings as `<rel`, which the grammar does not parse (BACKLOG).

## §4 The base — the `chaincompiler` package

The base is the machine the chain compilers are made from. It imports APE, rulecatcher and honeyc; its
`persona` front end also imports glyphsteer, lazily (§2).

- **forge** — `Language(name, scope, db, rule_count)`; `forge(kind, name, examples, db=, strict=)` mints the
  scope `<kind>:<name>`; `gate_language`, `grammar` and `package_skill` gate against it, read it back and
  write a body as `<name>/SKILL.md`. A chain compiler adds only its kind, its parser and its renderer.
- **bridge** — `compile_chain` (a chain through honeyc into its lenses) and the grammar seam
  (`learn`, `gate`, `grammar_lines`, `foreign_tokens`), which lives in APE and is re-exported here.
- **prime** — `build_prime(scope, adopted_rows, example_chain)`, the re-injectable block of §1.
- **skillpack** — APE's `write_skill`, `skill_markdown` and `slugify`, re-exported.
  ⚠ OWED: `write_skill` writes the description unquoted, so a description containing `": "` makes
  unparseable frontmatter (SkillTree writes tree descriptions the same way); every description
  ChainCompiler generates is colon-free, and the quoting belongs in APE and SkillTree.
- **persona** — the front end for a glyph-persona program: its `[VarDefs]` become a GlyphSteer legend
  (`legend.json`), its numbered `⚙️` steps a workflow list, its `[ROLE]` header a `SKILL.md`, and a legend
  chain is gated through GlyphSteer's grammar. ASPIRATIONAL: executing the `⚙️` workflow.

The console command named `chaincompiler` is installed by the agent tier (§7).

## §5 The three chain compilers — ACCC, CORCC, SCCC

**ACCC** (`packages/accc`) compiles **attention chains**: `[Focus] ⇒ [Focus] ⇒ |Held|` — an inner, silent
template for how to think, converging on the held focus. `forge` (kind `ac`), `gate`, `grammar`,
`package` (a `SKILL.md` carrying the chain and its attention block) and `prime`; seed languages
`generic`, `debug` and `research`.

**CORCC** (`packages/corcc`) compiles **chains of reasoning**: a CoR is spoken — a paragraph that performs
ordered moves and ends in a decision. A `PersonaSpec` is the ordered `Move`s, each with the cue phrases
that count as evidence it was performed; the last move is the held convergence. `forge_persona` forges
the move chain as an attention-chain language, and `lint` gates the spoken CoR against it: drift out of
the syntax is the persona *melting* — the melt-gauge. `package` writes the CoR with its paragraph
skeleton (rendered through APE's `cor_skeleton`) and its inner attention chain. Seed personas: **BANDIT**
(`Task → Recall → Decide → Execute → Reward`, the ChainSelector — given a task it exploits a proven chain
or explores by constructing one; the default CoR everywhere), **EINSTEIN** and **FEYNMAN** (flavours: each
one proven chain).

**SCCC** (`packages/sccc`) compiles **skill chains**: `[ac:x] ⇒ [cor:y] ⇒ [skill:z] ⇒ |Result|` — a
sequence of attention chains, CoRs and ordinary skills, rolled up into one `SKILL.md`. It forges the
sequence grammar (scope `sc:<name>`), lints a sequence, resolves every step to a skill dir on disk (the
given skills folder first, then the user's `~/.claude/skills` and `~/.claude/plugins`) and refuses to
package while any step is missing. The rollup is written by the **skillchain** module
(`packages/skillchain-compiler`, import `skillchain`), which is also a standalone CLI with its own `.chain`
syntax: skill steps, captured results, and reasoning bridges between steps.

Minting a chain through these doors, never by hand, follows `.claude/rules/22-seq-mint-attention-chain.md`.

## §6 Personas — personacc and personapack

**personacc** (`packages/personacc`) compiles a whole persona. A `PersonaBundle` is description blocks + a
set of attention chains + at least one CoR that uses them. A `Block` is a kind (any string), a language
and a body; a body that parses as a chain in its language grades `chain` and is melt-gauged like a CoR,
anything else grades `prose` and is reported. `lint` checks the notation, `uses_them` checks that the
CoR's moves appear as foci in the bundle's chains (warnings by default, violations with `strict=True`),
`package` writes one `SKILL.md`, and `seat` returns the keyword arguments `make_gba` takes (§8).
ASPIRATIONAL: seating more than the first CoR.

**personapack** (`packages/personapack`) is a library of ready bundles. Each `PackEntry` carries the
bundle, its invocation terms, provenance, an activation grade — `seed` < `proven-in-forge` <
`tested-with-receipt` — the receipt behind the grade, and its domain. It holds ten: the three seed
personas, four proven in the AEGIS forge (Aegis, SdnaSynth, HormoziAegis, FrameBudgetGuardian), and three
tested with a live model (Bodhisattva, SamayaReviewer, ParamitaReader).
⚠ OWED: the forge script and the receipts behind the two upper grades live in the author's private
repositories, not in this repository, so a reader of a release cannot check them.

## §7 The agent tier — `chainaios`

`packages/chainaios` builds on the chain compilers and installs the `chaincompiler` command (`layers`,
`demo`, `persona`, `gba new|construct|search|check|hba`, `cog new|flow`).

- **`construct_language(domain, ac_chain=, cor_persona=)`** mints a domain's attention chain, its CoR (the
  BANDIT unless one is given) and a skill chain over both — three skill dirs in one call.
- **`roll_up_algebra(domain, atoms, persona=)`** mints one or more attention chains, a CoR (the BANDIT
  specialized to the domain, or the given persona), the skill-chain rollup, and a persona folder
  (`CLAUDE.md`, a GlyphSteer grade legend, `kb/`), then organizes them as a SkillTree and validates it. The
  result is a `BanditChainSystem`, and it is **closed** when every artifact is a skill dir and the tree
  validates with zero violations. The persona carries two standing instructions: keep a graded knowledge
  base of every run, and read it back through GlyphSteer to recall the best-graded chains — filing a
  goldenization request (§9) for a chain that earns the top grade twice, never promoting it itself.
- **`hierarchicalize(workdir=)`** applies that roll-up to every component the system is made of — accc,
  corcc, sccc, glyphsteer, skilltree, si, honeyc, rulecatcher — and assembles one master tree: the
  system's own granular view of itself.

## §8 The agent shapes — GBA, COG, HBA and the lattice

An agent shape is a folder an agent goes to and becomes: reading a file inside it makes Claude Code inject
that folder's `CLAUDE.md`, rules and skills (`.claude/rules/02-the-autoload-mechanism.md`). The shapes
were built in four stages.

**Stage 1 — the GBA** (General BanditAgent, `chainaios.gba`). `make_gba(domain, root, atoms=, persona=,
role_block=, rule_blocks=)` writes a persistent folder: `CLAUDE.md` (the role), `.claude/rules/` (the
loop, the law, the knowledge-base reward record, self-expansion), a coordinate-addressed SkillTree of the
gated chains, `kb/`, the `bandit-chain-system` skill, a rebuildable search index, and `gba.json` — the
manifest, which names every gated body relative to the folder. The bodies live in the sibling folder
`.<name>.src/`, so a GBA rebuilds wherever it is copied together with that sibling, and a rebuild refuses
when a body is missing rather than writing a stub in its place.
`construct_into` is the explore arm made to persist: it mints a new chain system, adds it to the tree,
re-materializes and re-indexes. `search` is BM25 over the tree, scoped by coordinate. Every tree change
goes through one path (`_apply_tree`), which keeps the knowledge base, the agent definitions and the
identity across the rebuild. The identity is the manifest's profile: `role_block=` and `rule_blocks=` persist
there, and a custom `rule_blocks=` REPLACES the four default blocks, so `default_rule_blocks(domain)` returns
them for a caller to extend (`{**default_rule_blocks(domain), "<its own>.md": …}`). `check_gba` — the
`chaincompiler gba check <root>` door — reads `closed` again on disk at any time: every body the manifest names
present; the materialized tree (`skilltree.json`) having the manifest's shape and validating with zero violations;
every `SKILL.md` in the folder a node of that tree or the `bandit-chain-system` copy, so a skill written into it by
hand is listed as unlisted; every `SKILL.md`'s frontmatter parsing. It exits non-zero when any fails. An agent made
inside the folder, with its `.<name>.src/` beside it, is checked on its own.
⚠ OWED: it does not compare a materialized body with its source, so a body edited by hand inside the tree passes.
⚠ OWED: a rebuild deletes the root folder and writes a new one, so a shell standing in it loses its working
directory and its next command fails until it starts afresh. Keep the root folder in place across a rebuild.
- **Lords.** A sub-domain constructed with its own persona gets its own `CLAUDE.md`, scoped to its
  branch, with the way back up to the domain frame — reading into it seats that persona. A sub-domain
  without one stays in the root's region. Lords grow on warrant, never one per leaf.
- ⚠ OWED: the GBA copies the `bandit-chain-system` skill from the source checkout; from a non-editable
  install that path does not exist and the GBA ships without it, silently. Ship it as package data.

**Stage 2 — the COG** (`chainaios.cog`). `make_cog` writes a Challenger · Generator · Observer flow: a
flow skill in the COG's tree, a role and a rule, and three seats `C/`, `G/`, `O/` — each a GBA — around a
shared `workspace/`. The Challenger mints the frames the Generator needs and places them in its tree, the
Generator uses them to produce, the Observer records what happened for the next cycle. There is no
runtime engine: the agent walks the folders.

**Stage 3 — the HBA** (`chainaios.hba`). `make_hba` writes a GBA whose loop dispatches instead of acting
inline: `.claude/agents/select-agent.md` decides between running a proven chain and constructing one, and
`.claude/agents/construct-agent.md` builds the missing chain in its own context window, so the
dispatching agent's context never fills with the material needed to build it. Claude Code's Agent tool
does the delegation at run time.

**Stage 4 — the lattice.** `make_cog(seats=)` makes any of the three seats an HBA — the eight `PATTERNS`,
from all GBAs to all HBAs.

**Worked agents.** `personas/chainforge` (diagram construction: a root persona and six branch lords) and
`personas/systemic-archive-narrator` (a root and five) were built through these doors, their bodies kept beside them in
`personas/.<name>.src/`; `examples/nutrition`
rebuilds the dietc compiler as a GBA whose chains call dietc's Python tools (`DIETC-AIOS-REBUILD.md`).

## §9 Goldenization — goldenreq

A gauge may detect quality; it may never certify itself. **goldenreq** (`packages/goldenreq`, stdlib only)
is the gate between them. A gauge files a request — kind `chain-golden`, `rule-adopt`, `template-promote`
or `pack-grade-bump`, the candidate, the evidence, the promotion asked for — onto an append-only queue. A
handler accepts or rejects it; a rejection must carry a reason; every verdict is appended to a verdicts
file in the acceptance-verdict shape, so the verdicts can later train an acceptance model. Only an accept
fires an effect: `chain-golden` appends an `ACCEPTED-BY` line to the knowledge-base note, `pack-grade-bump`
returns the next grade. ASPIRATIONAL: the `rule-adopt` and `template-promote` effects raise
`NotImplementedError` until there is a real target to call.

## §10 Organization — SkillTree and the tree law

SkillTree is its own package and project (`agent-skilltree` ≥ 0.4.0 on PyPI, import `skilltree`).
ChainCompiler uses it to materialize trees, validate them, address every node with a coordinate (`0` →
`0.1` → `0.1.1`), search them (scoped by coordinate), build exchanges, walk federations and fold
frameworks into a tome. A tree is portable: each breadcrumb names its child relative to the node's own
folder, and the manifest names its sources relative to itself; `skilltree relink --localize` writes
absolute paths after an install.

The law is `.claude/rules/01-everything-is-a-tree.md`: no bare forest — every set is rooted and every
region reachable from every other. The substrate fact it rests on is `.claude/rules/02-the-autoload-mechanism.md`:
Claude Code loads one layer of `.claude/skills/`, and descending is a Read into the child's folder.
⚠ OWED: this repository's own `.claude/skills/` is still a flat forest; rooting it waits on a layout
decision (BACKLOG).

## §11 Retrieval steering — glyphsteer

**glyphsteer** (`packages/glyphsteer`, roadmap P8, research) annotates a corpus with a compiled glyph
vocabulary that steers retrieval twice over — lexically, as a rare ASCII tag that becomes an exact facet,
and densely, as an emoji whose embedding direction nudges the chunk — and strips the markers from the
returned text. Its built-in `GRADE` vocabulary is the grade legend the agent tier writes into every
persona. Its own design is `packages/glyphsteer/README.md`, `implementation_plan.md` and
`packages/glyphsteer/.claude/rules/`. A vocabulary may hold a glyph that is part of another (a skin tone, a variation
selector): matching takes the longest glyph first and never two that overlap.
⚠ OWED: matching is by substring, so such a pair corrupts parsing and stripping while the hide check passes (BACKLOG).

## §12 The archetype compiler

**archetype** (`packages/archetype`) compiles an archetype as a state machine rather than a name: Persona,
Shadow (the persona's denied inverse), Self (holding both), Odyssey (a succession of journeys, one per
other archetype met, ending in a post-return journey) and Becoming (the next archetype). From one seed it
infers the missing aspects, builds the Odyssey, validates constraints C1–C6 and emits readable text,
triples, Prolog, Cypher, JSON or a `SKILL.md`.
⚠ OWED: its specification, `ARCHETYPE-COMPILER.md` (cited throughout the package), and its companion
correspondence map are not in this repository.

## §13 The chapter rung — framework and skill2framework

Roadmap P9 turns a finished agent into a chapter of its author's SkillTome. `chains/skill2framework.chain`
compiles to the `skills/skill2framework/` rollup: two prompt stages write the narrative post and the
deep-dive post, then deterministic operations in **framework** (`packages/framework`) assemble the chapter
(`assemble_chapter`), write the volume skill, package a plugin (`package_plugin`, which repaths the
chapter links into the bundle and checks they resolve) and fold the framework into the tome
(`fold_into_tome`, SkillTree's `tome.fold`). The SkillTome is its own project, built on ChainCompiler.

## §14 The self-interpreter — si

**si** (`packages/si`) runs the chain dialect: Python with ChainCompiler's operations injected as names
(`forge_ac`, `forge_cor`, `forge_sc`, `construct_language`, `SkillTree`, `materialize`, `walk`,
`build_exchange`, `tree_to_mcp`, …). `walk` and `reachable` traverse a materialized tree by its
breadcrumbs, resolving each relative breadcrumb at its node's folder; `read_skill` finds a skill by name
anywhere in the tree, with or without its coordinate prefix. `tree_to_mcp` turns a tree into
an MCP server launcher, and `scaffold_repo` stamps a federated node repository from a tree. `si.server` is
the MCP server the plugin registers: `si_interpret`, `si_walk`, `si_reachable`, `si_read_skill`,
`si_tree_to_mcp`, `si_search`.
⚠ `si_interpret` executes arbitrary Python with the permissions of the process running the server. It is
an execution surface: run only programs you trust.

## §15 Exchange, marketplace and federation

An exchange holds several skill trees under one master (SkillTree's exchange format). The marketplace is a
git repository: `registry.json` lists entries that point at trees, each `unverified` or `verified`. A
contribution is a pull request that adds an entry; `contribute.yml` runs the base branch's
`scripts/validate_registry.py` against the PR's data, read-only and without secrets, and admits a valid
entry as `unverified`. Only a maintainer promotes one (`scripts/promote.py`). A registry entry can itself
be a child registry, so marketplaces federate into a tree (SkillTree's `walk_federation`); the plan is
`FEDERATION.md`. ASPIRATIONAL: a hosted endpoint, cross-user discovery and a reputation tier.

## §16 The plugin

`.claude-plugin/plugin.json` and `marketplace.json` make the repository its own one-plugin marketplace.
The payload is `skills/`: the eight capability skills generated from the compiler build-functions by
`scripts/build_meta_ape_skills.py` (APE's four and the four `*CC`), `bandit-chain-system`, `glyphsteer`
and `glyphsteer-dense`, `report-missed-skill`, the two style chain systems minted through the doors
(`adam-curtis-narration-style`, `explain-something-fractally`, each with its parts and its tree),
`bigdog`, and the `skill2framework` set; `.mcp.json` registers the self-interpreter (`python3 -m
si.server`). The plugin's version (`plugin.json`, `marketplace.json`) moves with every change to the
payload: an installed plugin updates only when it does.

The plugin carries no `CLAUDE.md` at its root — a plugin install does not load one. An agent the plugin delivers
(an AIOS — an agent in its own folder) ships as an **install skill**: the agent's `CLAUDE.md` is one of the skill's
resources, and the skill's script makes a new folder, named by whoever installs it, that holds that `CLAUDE.md`, and
injects the rules and skills the agent needs. The folder is that installer's own instance, filled out by its
configuration (§20).
⚠ OWED: installing the plugin copies the skills and registers the MCP but installs no Python. The MCP
server and every skill that calls a package work only after `./install.sh` has run into the `python3` the
server launches, and the plugin install has not been proven in a clean Claude Code. Owed: an install path
that brings the packages with the plugin, and that proof.

## §17 The project surface

`README.md` is the public face and holds the changelog. `roadmap.json` is the source of the phases;
`scripts/update_site.py` renders it into `assets/roadmap.svg`, `site/data.json` and the board
`.claude/rules/chaincompiler_states.md` — generated files are never edited by hand, and `deploy.yml` fails a push
whose generated files are stale — and `ROADMAP.md` mirrors it in prose. `site/` is the GitHub Pages site (the roadmap, a workbench, and
the development log built by `scripts/build_blog.py`). `.claude/` is the working surface for an agent
developing this repository: the rules named in §0 and the skills `chaincompiler` (orientation),
`archetype-compiler`, `bandit-chain-system`, `glyphsteer`, `glyphsteer-dense`, `metaformal-self-test`
(test by observing real runs), `report-missed-skill` and `skilltree` (a copy of SkillTree's own skill).

## §18 Home, versions and publishing

The source home is the `base/chaincompiler` folder of the author's monorepo. `github.com/sancovp/chaincompiler`
is its published output, re-synced on every merge that touches the folder by a checksum-compared,
delete-enabled copy: anything that exists only in the public repository is removed at the next publish,
so every change is made at the source home. The public repository runs its own workflows — `deploy.yml`
(on every push to `main`: require a new changelog entry, regenerate the site and the board and fail if either is
stale, then publish Pages) and `contribute.yml` (§15). A branch of the public repository is never merged there: its
work is ported to the source home, and the branch is then closed.

The folder holds only what publishes. What the author keeps out of the public repository lives in the source home
outside this folder and is never published: the steward package, which the public repository's release pass removed,
is its own project, `not-unified/steward`; the internal design that pass relocated, the public repository's history
from before its rewrite, and every file of that history the source home holds in no other form are kept in
`not-unified/chaincompiler-internal`.
⚠ OWED: the public repository holds three branches whose work never reached the source home — two bug sweeps,
`fix/bug-sweep` and `fix/confirmed-bug-sweep` (its pull requests #1 and #2: fixes, each with a regression test, for
defects found in honeyc, dietc, glyphsteer and corcc), and the backup of its history from before the rewrite — and
the internal design and the steward package sit in a standalone folder outside the source home (BACKLOG).

ChainCompiler is not on PyPI; its outside dependencies — `pydantic-stack-core`, `agent-prompt-engineering`
≥ 0.2.0, `agent-skilltree` ≥ 0.4.0 — come from PyPI through `install.sh`. A release is proven by cloning the
public repository into an empty environment, running `./install.sh`, and running §19's checks green.
⚠ OWED: three version lines — the release line in the README changelog, the plugin's version in
`plugin.json`, and every package's own `pyproject.toml` version, never bumped. Owed: one line, the release
version stamped into the plugin and the packages.

## §19 Tests and proofs

| check | proves |
|---|---|
| `pytest packages` | each package's own suite |
| `pytest examples/_all/test_all.py` (or `python examples/_all/run_all.py`) | one domain through every package end to end — persona, compile, gate, construct, organize, steer, interpret |
| `python examples/_all/bandit_self.py` | the roll-up closes on a domain and on the system's own components |
| `pytest examples/nutrition` | the dietc rebuild: the agent closes, and a real day computes through the tools |
| `lint-imports` | the layer contract of §2 |

`examples/` sits outside `packages/`, so `pytest packages` alone does not run the examples. Each release's
counts are in its changelog entry.
⚠ OWED: the public repository's workflows run none of these; a release is checked only by the clean
install of §18.

## §20 The agent that knows ChainCompiler

ChainCompiler's own agent — the agent that knows ChainCompiler and makes agents and projects with it — is CompiloApe
(`base/compiloape` in the source home, its design `base/compiloape/DESIGN.md`): a separate project and a plugin of its
own that depends on this one. Its folder is built through ChainCompiler's own doors — a persona whose moves are this
package's operations performed on a task (Forge → Gate → Package → Compose → Arrange → Validate → Place), seated by
`make_gba` (§8) over five chains the chain compilers mint (§5), with `default_rule_blocks` extended by its user's
binding — and it climbs SkillTome's agent ladder: the folder, the agent definition in it, the launcher beside it that
runs it, its plugin, and the install wizard that teaches a base Claude to install all of it. The wizard is that
plugin's install skill, the delivery shape of §16: it installs this package from a checkout through `./install.sh`
(so every GBA gets its `bandit-chain-system` skill, §8) into a Python environment it names, and runs the agent's forge,
so whoever installs it gets their own folder of the agent, filled out by their configuration. A host Claude makes use
of it through a skill the same plugin carries, which hands the installed agent a task and returns what it made, never
seating its persona in the host; the agent checks what it made with `chaincompiler gba check` and `skilltree validate`.
Its worked example is AEGIS, an agent made this way that mints further agents, whose personas personapack carries (§6).
An agent working in this repository gets the orientation skill `.claude/skills/chaincompiler` and the
`bandit-chain-system` skill.
