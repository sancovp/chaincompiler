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
(`.mcp.json`). The plugin's program is the fifteen Python packages under `packages/`, at one version: a plugin
install runs them from PyPI through uv, with nothing installed by hand (§16), and a clone installs them editable
with `./install.sh`. The repository and the packages are published on every release (§18).

**How to read this document.** One section per part, in dependency order; §2 is the map of the whole.
`ASPIRATIONAL:` marks what is designed and not built. `⚠ OWED:` marks a known defect in what is built,
with its task in `BACKLOG.md`.

**How to change it.** Rewrite the section a change touches in the same commit as the change, so this
document always states the current design and nothing else. What changed, what it replaced and why go in
the README's `## Changelog` — the project's one history, gated by `scripts/check_changelog.py`.

**Where work state lives.** `roadmap.json` holds the phases (P0–P10; rendered to the roadmap SVG, the site and
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
| `packages/*/README.md` | each package's own reference, and its page on PyPI (§18) |

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
                    archetype · skill2framework · si §12 · §13 · §14
```

`.importlinter` enforces the six-layer chain `chainaios > sccc > corcc > accc > chaincompiler >
prompt_engineering`; `lint-imports` keeps it. The base never imports a chain compiler, and no chain
compiler imports the agent tier — that is what lets each tier be made from the one below it. sccc
imports accc and corcc inside its functions only. Beside the tiers, personacc imports the chain tier and the base,
personapack imports personacc and corcc, archetype imports the base inside its functions, skill2framework imports
SkillTree, si imports SkillTree and its server library at its top and the agent tier, the chain tier and the base
inside its functions,
and goldenreq imports nothing; the stack's §4 draws every edge, from the AST walk `scripts/check_versions.py` makes of
each package's `src/`. The packages beside the tiers are not under the contract (ASPIRATIONAL: widen it to cover them).
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
⚠ OWED: a scope snapshot imported by merge — `rulecatcher import-scope` without `--replace-scope`, the default — keeps
the target's own status for a rule both scopes hold while it imports the snapshot's decisions for that rule, so the
rule's history can say it was adopted while its status is pending. Which status a merge keeps for such a rule — the
target's, the snapshot's, or its latest decision's — is not stated; state it, then make the status and the history
agree (BACKLOG).

**honeyc** (`packages/honeyc`) compiles the Dense Rune-Chain notation (`[Entity]`, `|Bounded|`, `⇒`, `⇔`,
relation markers, scopes, placeholders): a Lark grammar parses it to an AST, `normalize` flattens it to
triples, and lenses render it readable, as triples, as prose, as Prolog text or as Cypher text; `check`
warns of an unbounded term in a mediator's place and suggests the whole chain, in its source spelling, with that one
term bounded — what it suggests parses back to the chain's own statements plus the bounding and the mediation.
**dietc**, in the same package, is a nutrition compiler built on honeyc — the proof that a domain compiler can ride on
it (`packages/honeyc/DIETC.md`); a safety field it does not know is kept as a note, and what it writes uses only
markers the grammar reads as it means them: the rune's gap watches its caps through a relation leaf, and the block it
passes through honeyc writes each step as a scope holding its chain. Each user's
notation is that user's own configuration (§1: a notation is minted from its user's examples); for this repository's
own Dense Rune-Chain notation, its README, its examples, its grammar, its code and its tests state one reading of every
marker the grammar defines: the README's `Core notation` table gives each marker its reading, an example and the
triples the example gives, and `tests/test_readme_notation.py` checks every row against the code and every grammar
marker against the table. A relation is written `A -rel-> B` or `A <rel- B`, two spellings of `rel(A, B)`, and
`A <rel> B` states it both ways; the parser keeps the spelling, and the readable lens writes back the spelling it read.
The spelling is never part of a term's identity: a transform's id names its chain, whichever way a relation in it is
spelled.
A bounded term between two backbone links is an inferred mediator, carrying its target; a relation an author names
`mediates` is an ordinary relation, and every lens and emitter tells the two apart through `normalize.is_mediation`.
`check` descends into assignments and transforms. The Prolog it emits declares the predicates its base rules read and
closes `linked/2` over `equiv/2` with a visited list, so a false query fails — on a program with no equivalence too — and
an open one enumerates every node reached.

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
that count as evidence it was performed; the last move is the held convergence. A move that carries no cue phrase (a
persona recovered without them, as personapack's SamayaReviewer and ParamitaReader are) is cued by its own name in the
paragraph skeleton, so every persona packages and seats. `forge_persona` forges
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
⚠ OWED: SCCC resolves each step to a `SKILL.md` of that name anywhere under the skills folder, the organizing tree a
roll-up writes there included, so a system minted again into a folder that holds its tree can resolve a step to the
tree's node copy and describe it by the node's placeholder (agent-rts's WoomEngineer rollup: steps 4 and 5 read
"attend (woom)"). Resolve to the package itself, never a tree's node copy (BACKLOG).

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
- **The `bandit-chain-system` skill** every GBA receives is package data of `chainaios`
  (`data/bandit-chain-system/SKILL.md`), read through `importlib.resources` (`gba.py`'s `_BCS_SKILL`) and written into
  the GBA byte for byte, so an installed `chainaios` carries it as an editable one does. The repository's
  `.claude/skills/` copy and the plugin's `skills/` copy equal it, each a file and not a link, and
  `scripts/check_versions.py` refuses a copy that differs (§16). `test_make_gba_is_a_persistent_aios` finds it in a GBA
  and compares its bytes with the package data's, whichever way `chainaios` was installed.

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
⚠ OWED: SkillTree's search hands a query's words to FTS5 unquoted, so `skilltree search` raises on a query with no word
in it (`"` gives `unterminated string`) and on an operator word (`NOT` gives `syntax error near "NOT"`); ChainCompiler's
doors to it, `si_search` and `chaincompiler gba search`, send it the query's words alone, lowercased, and answer a query
with no word with nothing. The fix belongs in SkillTree (BACKLOG).

## §11 Retrieval steering — glyphsteer

**glyphsteer** (`packages/glyphsteer`, roadmap P8, research) annotates a corpus with a compiled glyph
vocabulary that steers retrieval twice over — lexically, as a rare ASCII tag that becomes an exact facet,
and densely, as an emoji whose embedding direction nudges the chunk — and strips the markers from the
returned text. Its built-in `GRADE` vocabulary is the grade legend the agent tier writes into every
persona. Its own design is `packages/glyphsteer/README.md`, `implementation_plan.md` and
`packages/glyphsteer/.claude/rules/`. A vocabulary may hold a glyph that is part of another (a skin tone, a variation
selector): one matcher takes the longest glyph first and never two that overlap, and every reader of a code or a text
goes through it — parsing, stripping, the hide check, the HoneyC bridge and the grammar's order check. Stripping removes
the separator with its space and repeats until nothing is left to remove; the HoneyC bridge keeps the code's own order;
merging legends keeps the last author on a clash of name, glyph or derived tag and every entry that clashes with
nothing; the grammar's `lint` refuses whatever in a code is neither a vocabulary glyph nor
the separator before it builds the tag chain rulecatcher reads; and a search query with no word finds nothing.

## §12 The archetype compiler

**archetype** (`packages/archetype`) compiles an archetype as a state machine rather than a name: Persona,
Shadow (the persona's denied inverse), Self (holding both), Odyssey (a succession of journeys, one per
other archetype met, ending in a post-return journey) and Becoming (the next archetype). From one seed it
infers the missing aspects, builds the Odyssey, validates constraints C1–C6 and emits readable text,
triples, Prolog, Cypher, JSON or a `SKILL.md`.
⚠ OWED: its specification, `ARCHETYPE-COMPILER.md` (cited throughout the package), and its companion
correspondence map are not in this repository.

## §13 The chapter rung — skill2framework

Roadmap P9 turns a finished agent into a chapter of its author's SkillTome. `chains/skill2framework.chain`
compiles to the `skills/skill2framework/` rollup: two prompt stages write the narrative post and the
deep-dive post, then deterministic operations in the package **skill2framework** (`packages/skill2framework`)
assemble the chapter (`assemble_chapter`), write the volume skill, package a plugin (`package_plugin`, which repaths
the chapter links into the bundle and checks they resolve) and fold the framework into the tome
(`fold_into_tome`, SkillTree's `tome.fold`). The chain and the package carry one name: the package's folder, its
distribution on PyPI and its import name are all `skill2framework`. The SkillTome is its own project, built on
ChainCompiler.

## §14 The self-interpreter — si

**si** (`packages/si`) runs the chain dialect: Python with ChainCompiler's operations injected as names
(`forge_ac`, `forge_cor`, `forge_sc`, `construct_language`, `SkillTree`, `materialize`, `walk`,
`build_exchange`, `tree_to_mcp`, …). `walk` and `reachable` traverse a materialized tree by its
breadcrumbs, resolving each relative breadcrumb at its node's folder; `read_skill` finds a skill by name
anywhere in the tree, with or without its coordinate prefix. `tree_to_mcp` turns a tree into
an MCP server launcher, and `scaffold_repo` stamps a federated node repository from a tree. `si.server` is
the MCP server the plugin registers — `si_interpret`, `si_walk`, `si_reachable`, `si_read_skill`,
`si_tree_to_mcp`, `si_search` — and the console command `si-server` (`chaincompiler-si`) runs it, the command the
plugin's launcher starts through uv (§16).
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
`bigdog`, and the `skill2framework` set; `.mcp.json` registers the self-interpreter (below). The plugin's
version (`plugin.json`, `marketplace.json`) is the release version (§18), so it moves on every release: an installed
plugin updates only when it does.
⚠ OWED: `skills/bigdog/build.py` exports rulecatcher's scope with each decision's `created_at`, so two builds of the
same inputs differ in those stamps alone; the export should carry none, as a compiled skillchain carries no compile
date (BACKLOG).

The plugin carries no `CLAUDE.md` at its root — a plugin install does not load one. An agent the plugin delivers
(an AIOS — an agent in its own folder) ships as an **install skill**: the agent's `CLAUDE.md` is one of the skill's
resources, and the skill's script makes a new folder, named by whoever installs it, that holds that `CLAUDE.md`, and
injects the rules and skills the agent needs. The folder is that installer's own instance, filled out by its
configuration (§20).

**How a plugin install gets its Python: from PyPI, through uv, pinned to the release.** uv is the plugin's one
prerequisite, and nothing is installed into the user's own Python:
- `.mcp.json` launches the self-interpreter through the plugin's own launcher, `server/launch.py`, as
  `uv run --no-project --quiet ${CLAUDE_PLUGIN_ROOT}/server/launch.py --from chaincompiler-si==<release> si-server`
  (`scripts/uvline.py`'s `server_launch`). Claude Code gives a server thirty seconds to answer `initialize`, a plugin
  cannot lengthen that, and the real server cannot meet it on a new machine: there uv first installs its seventy-odd
  packages, so `si-server` answers more than a minute after it is started. The launcher needs nothing but the standard
  library, so uv starts it at once, and what it answers before the real server is up is what the real server would
  answer: `initialize` with the protocol version the client asks for, or the real server's newest when the client asks
  for a newer one, and the one capability it serves, its tools; `tools/list` from the stored list; `ping`. Both stored
  answers, `server/initialize.json` and `server/tools.json`, are the real server's own, written by
  `scripts/build_server_tools.py` (whose `--check` refuses a stale one), and `si`'s build file bounds `fastmcp` to the
  major they were written under. The probe a newer Claude Code opens with, `server/discover`, is refused at once, so it
  goes straight to `initialize` instead of waiting out the probe. The launcher starts the real server behind it as
  `uv tool run --compile-bytecode --from chaincompiler-si==<release> si-server`, in an environment uv resolves from PyPI
  at the release's version (§18), compiles once and caches. Once the real server has answered its own `initialize`,
  every message passes through unchanged, both ways, as bytes — the real server's transport is UTF-8 and nothing in the
  launcher decodes what passes, so no locale or Windows code page touches it — written to the server by one thread in
  the order it came, never by the thread reading the server's answers. A request that arrives before then waits for it;
  every request the launcher cannot deliver is answered with an error naming why — the server ended before it answered,
  the client closed first, the server's input refused it — and a line that is not one JSON object is answered with an
  error; a server that ends after serving ends the launcher with it.
- Every shipped skill that has an agent run code from one of the fifteen, or from an outside distribution they rest
  on (`agent-prompt-engineering`, `agent-skilltree`), names how a plugin install runs it, once, before its first code
  block, covering every block and command in the skill: `uv run --no-project --with <distribution>==<release>
  python3` for its Python, and `uvx --from <distribution>==<release> <command>` for a console command (a command a
  distribution installs). The line names every distribution the code it runs imports, a lazy or optional import
  included (`roll_up_algebra` writes its legend only with `glyphsteer` present), an outside one at the lower bound
  §18 states. The same line says that from a clone where `./install.sh` ran, the clone's `python3` runs it, so the copy
  a GBA carries (§8) is true in both places. The wording is `scripts/uvline.py`'s, which the two skill generators
  (`scripts/build_meta_ape_skills.py`, `skills/bigdog/build.py`) write from and the hand-written skills carry.
- A step that needs this repository's source — a script under `packages/*/experiments`, the dense sidecar's compose
  file, a package's test run — says it needs a clone of the public repository.
- A shipped skill that has a working copy under the repository's own `.claude/skills/` (`bandit-chain-system`,
  `glyphsteer`, `glyphsteer-dense`, `report-missed-skill`) keeps that copy byte for byte, a file of its own and not a
  link nor reached through a linked folder, and so does every other
  `SKILL.md` under a `.claude/skills/` folder or a package's own folder that carries a shipped skill's name (the
  glyphsteer package keeps one in its own `.claude/skills/`).
- The plugin's manifests describe how it gets its Python — through uv, from PyPI — and not as `./install.sh`.
- `scripts/check_versions.py` (§18) refuses a shipped skill whose code has no such line, or whose line misses a
  distribution the code it runs imports — the lazy reaches it knows are in its `LAZY` table.

**The proof of the plugin**, `scripts/plugin_proof.py`, given the task `scripts/plugin-proof-task.md`, runs on every
release once its packages are on PyPI (§18). It keeps THE CLEAN SEAT's discipline (CompiloApe's `DESIGN.md` §1): a marked seat in scratch space outside
any folder holding a `CLAUDE.md` or a `.claude/rules/`, an environment holding only `HOME`, `USER`, `LOGNAME`, `PATH`,
`LANG`, `TERM` and `TMPDIR` — the seat's own `UV_CACHE_DIR`, empty, added — the user's settings out, every grade read
from a transcript and the files, never from the session's account.
- **The install** — with an empty `CLAUDE_CONFIG_DIR`, signed out: `claude plugin marketplace add sancovp/chaincompiler`
  and `claude plugin install chaincompiler@chaincompiler` exit 0, `claude plugin list` names the plugin enabled at the
  release's version, and its cached copy holds every shipped skill, the launcher with its `initialize.json` and
  `tools.json`, and a `.mcp.json` launching it pinned to that release.
- **The run** — a headless session on the user's own login (the install's configuration is signed out), whose only
  addition is that cached copy (`--plugin-dir`), and whose `python3` imports none of the fifteen (checked in the same
  environment before the session). The plugin's server connects — the session's start lists it connected, or still
  connecting (`pending`) and the session is then offered or answered one of its tools, and no note of Claude Code's,
  in a tool search's result, says it failed to connect; that proves the launcher answered, and only one of the
  server's tools answering without an error proves the self-interpreter behind it. Any other MCP server Claude Code
  loads at the seat is named in the proof and granted no tool. The session calls one of the server's tools and gets a
  result that is not an error — on the seat's empty uv cache, after uv installs the server, the seconds from the
  session's start, which `run` records beside the transcript, to that answer recorded with the grade — and it follows one of the eight capability skills, whose Python runs through
  its uv line into the skill dir the task asks for, as that capability packages it — its name, its kind and its chain
  — written by no tool, shell write or Python of the session's own.
- **The grader's negative controls** — `scripts/tests/test_plugin_proof.py` (§19): a baseline transcript passes, and
  so do one whose server was still connecting at the start and then answered and one that also read the plugin's own
  README; one whose server failed to connect or timed out connecting, whose server never came up behind the launcher,
  whose tool call returned an error, whose skill ran its Python without its uv line, whose skill dir was written by hand
  (a tool, a shell write or a write from Python) or is not the capability's output fails exactly that check. The
  launcher's own tests, `scripts/tests/test_server_launch.py`, run it against a fake `uv`: it answers before a slow
  server is up and then passes a call through; refuses `server/discover` at once; answers the version the real server
  would; relays text unchanged under a Windows code page and a C locale; delivers held input larger than a pipe to a
  server that answers one message at a time; delivers a burst across the moment the server is ready once each, in
  order; answers with an error a request held when the server ends first or the client closes first, and a line that
  is not one JSON object; and its stored answers are the real server's.

## §17 The project surface

`README.md` is the public face and holds the changelog. `roadmap.json` is the source of the phases;
`scripts/update_site.py` renders it into `assets/roadmap.svg`, `site/data.json` and the board
`.claude/rules/chaincompiler_states.md` — generated files are never edited by hand, and `deploy.yml` fails a push
whose generated files are stale — and `ROADMAP.md` mirrors it in prose. `site/` is the GitHub Pages site (the roadmap, a workbench, and
the development log built by `scripts/build_blog.py`). `server/` holds the plugin's server launcher and its tool list
(§16). `scripts/` also holds the release's own tools — `set_version.py`, `check_versions.py` and `upload_release.py`
(§18), `uvline.py`, `build_server_tools.py` and `plugin_proof.py` (§16), `whereimport.py` (§19), and `release_check.py`,
which a release runs on its tip before its PR is opened: the generated files regenerated in a copy and compared, the
frontmatter of every `SKILL.md`, the greps for every reading the release replaced and for a machine path, the publish
dry run into a local bare copy, and the tee probe of the plugin's launcher (§16, §18) — with their tests in
`scripts/tests/`, each listed in `scripts/CLAUDE.md`. `.claude/` is the working surface for an agent
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
The public repository's three branches — the two bug sweeps `fix/bug-sweep` and `fix/confirmed-bug-sweep` (its pull
requests #1 and #2) and the backup of its history from before the rewrite — were ported home and closed: the sweeps'
fixes are in honeyc, dietc, glyphsteer and corcc (§3 · §11), each with a regression test, released as v0.1.64; the
whole history of all three, as git bundles, and the files of the backup held in no other form are in
`not-unified/chaincompiler-internal`; each pull request is closed with a comment naming the merge and the publish that
carry its work, and the branches are deleted. The public repository holds `main` alone.

Each package's distribution is named for its folder, save four whose bare names belong to other projects on PyPI:
`accc`, `archetype` and `si` publish as `chaincompiler-accc`, `chaincompiler-archetype` and `chaincompiler-si`, and
`skillchain` as `skillchain-compiler`; import names do not change. `rulecatcher` is held on PyPI already, as this
project's. In a clone, `install.sh` installs the fifteen editable with `--no-deps` and their outside dependencies —
`pydantic-stack-core`, `agent-prompt-engineering` ≥ 0.2.0, `agent-skilltree` ≥ 0.4.0 — from PyPI. A release is proven
by its release flow (`.claude/rules/22-seq-chaincompiler-release.md`): a clean clone of what publishes with
`./install.sh`, the wheel proof before the merge, and after it the install from PyPI and the plugin proof (§16, §19).
PyPI holds all fifteen names as this project's, every one at v0.3.1, the first whole version of the line, at v0.3.2
and at v0.3.3; v0.3.0 holds fourteen, short of `framework`, a name PyPI does not allow, which v0.3.1 carries as
`skill2framework` (§13).

**One version line.** A release's version, its README changelog entry, is every package's `version`,
every `__version__` a package defines, the plugin's version in `plugin.json` and `marketplace.json`, and the pin in
`.mcp.json` and in every shipped skill's uv line (§16) — the copies of the `bandit-chain-system` skill outside the GBAs
among them, the release re-applying every GBA under `personas/` so each carries the same bytes (§8). Every dependency
among the fifteen, an optional extra's included, is pinned to it exactly (`==`), so one pinned distribution brings the
whole release and nothing newer. Every build file declares every distribution its source imports — a lazy import as an
optional extra — and a build file that declares `agent-prompt-engineering` or `agent-skilltree` declares it at the
lower bound `install.sh` states (`>=0.2.0`, `>=0.4.0`); every other outside dependency keeps the bound its own build
file gives it. `scripts/set_version.py <version>` writes the version into every one of those places, and
`scripts/check_versions.py` refuses a tree in which any of them differs from the newest changelog entry, a dependency
among the fifteen is not pinned to it, a build file leaves an import of its source undeclared (an AST walk of each
`src/`, its outside modules mapped through the gate's `OUTSIDE` table), a build file does not give its package's page on
PyPI its folder's `README.md` (`readme`) and the repository's MIT license (`license = "MIT"`, under a `setuptools` build
requirement of at least 77, the first that reads a license written that way), a package folder lacks the repository's
`LICENSE` (each wheel ships it), a shipped skill's uv line is missing or incomplete (§16), or a copy of a shipped skill
differs; `scripts/tests/test_check_versions.py` plants each refusal. The
line starts at v0.3.0, the first version above everything the three lines held before it (the plugin was at 0.2.4), so
an installed plugin moves forward. Every release moves the whole line, whether or not a package changed.

**Publishing to PyPI.** Each of the fifteen is a unit of the publishing manifest — `chaincompiler-pkg-<folder>`, its
folder as `subdir`, `pypi` set, no public repository of its own, `auto_publish` off (scalable-publishing's `DESIGN.md`
§4) — `rulecatcher` among them, so a hand upload is never again a path. A release's packages go to PyPI after its merge:
as soon as the publish commit naming the merge is on the public repository, each of the fifteen is built from a clone
of the public repository at that commit and uploaded by `scripts/upload_release.py`, through scalable-publishing's
`bin/publish_package.sh`, which refuses a version PyPI already holds. That runs before anything else in the release's
after-merge proof, because between the publish commit and the upload the published plugin pins a version PyPI does not
hold. The driver uploads in dependency order — the self-interpreter's closure, then the packages the shipped skills'
uv lines name, then the rest — and uploads a package only once PyPI holds every sibling it requires, since a package
whose sibling is missing installs for no one and names in its metadata a sibling anyone could publish. PyPI lets one
account, and one address, create four new projects in any 86,400 seconds, counted from the creations themselves (its
`RateLimit-Policy` response header states the quota, `q=4;w=86400`; a refused try counts for nothing), and answers
`429 Too many new projects created` past it, while a version of a project it already holds uploads at once; so a
release that brings names PyPI does not hold yet takes as many runs of the driver as its new names need, each started
at least a day after the last creation of the run before and reading PyPI's state afresh, and reading a refusal of a
version PyPI holds at the release's own version as that package uploaded. PyPI also refuses some names outright — a
`400 Bad Request` on a new project whose build passed `twine check` — as it refused `framework`; no run uploads such a
name, so the package is renamed in the next release (§13). A failed upload is reported by the error lines twine and the
publish script printed — PyPI's own words after an `HTTPError` — never by the output's last line, which is the build's
progress. The next release merges only once PyPI holds this one whole, or holds every package of it but one whose name
PyPI refuses, that package renamed in the next release, which is then the line's next whole version: v0.3.0 is short
of `framework` for good, and v0.3.1 carries it as `skill2framework`. Whether PyPI holds the release is read from each
package's version JSON, never the project's JSON, and the install from PyPI starts only once both forms of the simple
index list the release's files — its HTML page and the JSON form pip and uv ask for first, which PyPI's cache keeps apart
(`Vary: Accept`) — and every package was uploaded longer ago than the index's cache life, its `cache-control` max-age
(600 s): `upload_release.py --whole` reads all of it. Each of PyPI's pages is served through a cache, so in the minutes
after an upload one reader can be served a page's answer from before it while the next is served the new one — the
simple index for up to its max-age, each form apart: v0.3.3's fifteen were named by each version's JSON and the HTML
pages within 72 seconds of each upload, while pip, about five minutes after `chaincompiler-si`'s upload, found no 0.3.3
(the goal `chaincompiler-distribution-whole`'s C26 proof). So a version that reads 404 in the minutes after its upload
is read again before it is uploaded again (scalable-publishing's `DESIGN.md` §4). Then a fresh environment installs the release from PyPI alone — pip's install report showing every
one of the fifteen downloaded from PyPI — and §19's checks pass from a clean clone at that commit, against those
installs; then the plugin proof runs (§16). In every proof against an install, each package the checks import
resolves into that environment, never into the clone's source.
Before the merge, the release is proven from wheels: from the publish dry run's clone, each of the fifteen is checked
by `publish_package.sh --dry-run` and built by `python -m build` — the same build — into a folder the proof keeps; the
fifteen are installed non-editable from those wheels with the outside dependencies from PyPI, and §19's checks pass
from that clone against them. So a packaging defect, such as a file a package reads
that its wheel lacks, is found before PyPI is asked to hold it.

## §19 Tests and proofs

| check | proves |
|---|---|
| `pytest packages` | each package's own suite |
| `pytest examples/_all/test_all.py` (or `python examples/_all/run_all.py`) | one domain through every package end to end — persona, compile, gate, construct, organize, steer, interpret |
| `python examples/_all/bandit_self.py` | the roll-up closes on a domain and on the system's own components |
| `pytest examples/nutrition` | the dietc rebuild: the agent closes, and a real day computes through the tools |
| `pytest scripts/tests` | the version gate's planted refusals, the plugin grader's negative controls, the server launcher against a fake `uv` and its tool list against the real server, every Python block of the eight capability skills and `bandit-chain-system` run alone in an empty folder, the upload driver against a stand-in PyPI, and the release check's planted findings |
| `python3 scripts/check_versions.py` | the one version line, the build files' declarations, the skills' uv lines and every copy (§16, §18) |
| `lint-imports` | the layer contract of §2 |

`examples/` sits outside `packages/`, so `pytest packages` alone does not run the examples; the nutrition example finds
its fixtures from its own file, so it runs against an installed dietc as against an editable one. A test reaches the
package under test through the environment's install, never a path insert into a clone's `src/`. Each release's counts
are in its changelog entry, and every check passes with no failure, with SWI-Prolog on the path, at the counts the
README's `## Status` states for the release.
Two proofs run these checks against installs, on every release (§16, §18): **the wheel proof**, from the publish dry
run's clone against the fifteen installed non-editable from their wheels, before the merge; and **the install from
PyPI**, from a clean clone at the publish commit against the fifteen installed from PyPI, after it — in each,
`scripts/whereimport.py` prints, inside the test session, where every package resolved, never in the clone. **The
plugin proof**, `scripts/plugin_proof.py`, follows the install from PyPI: the install into a clean Claude Code and a
headless session there, graded from its transcript and files.
⚠ OWED: the public repository's workflows run none of these; a release is checked by its release flow, run from the
source home.

## §20 The agent that knows ChainCompiler

ChainCompiler's own agent — the agent that knows ChainCompiler and makes agents and projects with it — is CompiloApe
(`base/compiloape` in the source home, its design `base/compiloape/DESIGN.md`): a separate project and a plugin of its
own that depends on this one. Its folder is built through ChainCompiler's own doors — a persona whose moves are this
package's operations performed on a task (Forge → Gate → Package → Compose → Arrange → Validate → Place), seated by
`make_gba` (§8) over five chains the chain compilers mint (§5), with `default_rule_blocks` extended by its user's
binding — and it climbs SkillTome's agent ladder: the folder, the agent definition in it, the launcher beside it that
runs it, its plugin, and the install wizard that teaches a base Claude to install all of it. The wizard is that
plugin's install skill, the delivery shape of §16: it installs this package from a checkout through `./install.sh`
into a Python environment it names, and runs the agent's forge,
so whoever installs it gets their own folder of the agent, filled out by their configuration. A host Claude makes use
of it through a skill the same plugin carries, which hands the installed agent a task and returns what it made, never
seating its persona in the host; the agent checks what it made with `chaincompiler gba check` and `skilltree validate`.
Its worked example is AEGIS, an agent made this way that mints further agents, whose personas personapack carries (§6).
An agent working in this repository gets the orientation skill `.claude/skills/chaincompiler` and the
`bandit-chain-system` skill.
