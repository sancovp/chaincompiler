# Rule: the auto-load mechanism (VERIFIED 2026-06-18 — the substrate fact everything rests on)

The entire SkillTree exists to exploit *one* API behavior. For months it was assumed; on 2026-06-18
it was **observed directly against the live Claude Code runtime** (the substrate is the oracle). This
rule records exactly what is true, with the evidence, so it is never re-guessed.

## What loads, when (verified)

> **Your context + Skill-tool menu = (`~/.claude`, ALWAYS, one layer) + (for every project dir you
> *read into*: that dir's `CLAUDE.md` + `.claude/rules/*` + `.claude/skills/*`, injected dynamically,
> one layer each).** Nested-below does NOT load until you read *into that dir*. Dirs outside your
> project root do NOT trigger it.

The trigger is the **Read tool entering a directory** (not a Bash `cd` — the shell resets, but the
harness tracks where you read). It is **dynamic and in-session**, not frozen at session start.

**CRITICAL: the trigger is the Read TOOL, not `cat`.** Verified 2026-06-18: Reading a file with the
Read tool injects that dir's `.claude`; a Bash `cat` of the *same file* injects **nothing** (the
harness hooks the Read tool's path argument; a shell `cat` is opaque to it). **Consequence: the
generated breadcrumbs must instruct the Read tool, NOT `cat`** — a literal `cat <path>` in Bash sees
the menu text but **silently fails to load the child's persona/rules/skills.** (`materialize`'s and
`cohere`'s `_CRUMB` currently say `cat …` — that wording is a latent descent bug; it must say "Read".)

## The evidence (metaformal observation — copy of the real run)

- **Rules inject:** reading `~/fable_test/SSRI/SSRI-RESEARCH-SYSTEMS-FIXMAP.md` caused
  `SSRI/CLAUDE.md` + all four `SSRI/.claude/rules/*.md` to appear in context — none were there before.
- **Skills inject:** a marker skill `zzz-marker-probe` planted at `~/fable_test/SSRI/cam/.claude/skills/`
  was ABSENT from the menu; after reading `cam/ARCHITECTURE-ASCII.md`, it appeared in the Skill-tool
  list (and `cam/CLAUDE.md` injected too).
- **Project-scoped:** reading `~/.claude/skills/gameworld-generator/modes/base/game.json` (a dir
  *outside* the project root) injected **nothing** — confirming the trigger is project-bounded.
- **One layer:** a `.claude/skills` nested *below* the dir you're in does not load until you read into
  *that* dir (the gameworld nested `deity`/`execute_in_game` stayed absent while rooted elsewhere).

## Why this is the whole game

1. **Descent is real and in-session.** "Going to a node" = **reading a file in that node's dir** →
   its persona (`CLAUDE.md`) + rules + child skills load *right then*. You **become the lord of that
   subtree by reading into it.** There is **no need to spawn a container/subagent** for descent
   (the earlier "container problem" was an artifact of the wrong "frozen at start" assumption).
2. **`cat`-breadcrumbs are the map, the Read is the move.** The menu's `cat <child>` links tell you
   *which dir to read into* to descend; the Read is what actually injects the child layer.
3. **Two melts, two fixes:**
   - **user level** (`~/.claude/skills`) auto-loads its top layer in *every* session — so a flat 133
     always melts. Fix = treeify it so only a *root* lives at the top (everything else nested, reached
     by reading down).
   - **project tree** progressively discloses *as you read into it* — already correct by construction;
     just keep each node one-layer with breadcrumbs.

## Triggers
- Any reasoning about what skills/rules are "available" — it depends on *where you've read*, not just
  session start. Don't assert the menu is static.
- Designing descent/navigation — descent = read into the node dir; don't invent subagent containers
  for what a Read already does.
- If this ever seems false, re-run the probe (plant a marker skill in a project subdir, read a sibling
  file, check the menu) before trusting any claim — the substrate is the oracle.
