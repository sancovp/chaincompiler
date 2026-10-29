# 21 — THE STACK (ChainCompiler): the components and the flows

<docsys kind="arch-map" role="instance"/>

TRIGGER:[a change to `DESIGN.md` that adds, removes, renames or re-orders a layer, a package or an import edge (⇒
redraw §1 and §4 the same change) · a new dev flow (⇒ place it on §1) · a changed runtime flow (⇒ its sequence
diagram, §5–§10)]
DO:[draw every diagram from `DESIGN.md` · keep one diagram per altitude, a section each, in this one file · end
every external dependency at its seam · place every dev flow (`22-seq-*`) on the boxes it runs through]
NOT:[draw a box the design does not name · let the design and these diagrams disagree after any change]

The whole system is **a closed algebra over one type — the skill dir** (`<name>/SKILL.md`, the unit any agent
auto-loads). Every layer produces or consumes only that type, so composition closes and recurses.

---

## 1. The full stack

Arrows = dependency (who imports whom). Drawn from `DESIGN.md` §2 and §16–§18; every package is a box, and each dev
flow sits on the boxes it runs through.

```mermaid
flowchart TB
    subgraph AGENT["Agent tier"]
        CA["chainaios<br/>construct_language · roll_up_algebra · GBA · COG · HBA<br/>(installs the chaincompiler CLI)"]
    end
    subgraph CHAIN["Chain tier — each PRODUCES a skill dir"]
        direction LR
        ACCC["accc<br/>attention chains"] --> CORCC["corcc<br/>chains of reasoning"] --> SCCC["sccc<br/>skill chains"]
    end
    subgraph BASE["Base"]
        CC["chaincompiler<br/>forge · gate · grammar · package · prime · persona"]
    end
    subgraph ENG["Engine (in this repo)"]
        RC["rulecatcher — the gate"]
        HC["honeyc (+ dietc) — the compiler"]
        SKC["skillchain — the rollup writer"]
    end
    subgraph DEP["From PyPI — their internals are not ours"]
        APE["agent-prompt-engineering · SEAM: prompt engine, grammar seam, write_skill"]
        PSC["pydantic-stack-core · SEAM: the blocks under APE"]
        ST["agent-skilltree · SEAM: materialize · validate · search · exchange · federation · tome"]
    end
    subgraph BESIDE["Beside the tiers"]
        PCC["personacc → personapack"]
        GR["goldenreq"]
        GS["glyphsteer"]
        ARC["archetype"]
        FW["skill2framework"]
        SI["si — MCP server + skill"]
    end
    subgraph SURFACE["The project surface — DESIGN §16 · §17 · §18 · §19"]
        PLUG["the plugin — plugin.json · marketplace.json · skills/ · .mcp.json; an agent ships as an install skill"]
        UVL["the plugin's Python from PyPI through uv — .mcp.json: uv runs server/launch.py --from chaincompiler-si==release si-server · every shipped skill's uv line, in uvline.py's words"]
        LAUNCH["server/launch.py — standard library only: answers initialize and tools/list at once (server/tools.json, written by build_server_tools.py from the real server), starts si-server through uv tool run, then passes every message through"]
        VER["one version line — set_version.py writes it; check_versions.py refuses a tree where any line, pin, build-file declaration, uv line or copy is off"]
        PPROOF["plugin_proof.py — the signed-out install from the marketplace, then a headless session at a clean seat given plugin-proof-task.md, graded from its transcript and files"]
        UPL["upload_release.py — the fifteen to PyPI from a clone at the publish commit, in dependency order (the self-interpreter's closure first), a package only once its siblings are held, within PyPI's four new projects in any 86,400 s, resuming from PyPI's state; --whole: each version's JSON holds the release, both forms of the simple index list it, and the index's cache life has passed since each upload"]
        GEN["update_site.py → roadmap SVG · site/data.json · the board (all from roadmap.json + the README changelog)"]
        RCHK["release_check.py — on a release's committed tip, its own packages imported, before its PR: the generated files regenerated in a copy, the frontmatter sweep, the replaced-sentence and configurable greps, the publish dry run into a local bare copy, the tee probe reading the real server's own output; every finding named"]
    end
    subgraph PUBX["Outside this folder — DESIGN §18"]
        PUB["scalable-publishing · SEAM: publish_unit.sh mirrors the folder to the public repository, with deletes · publish_package.sh uploads each of the fifteen, a chaincompiler-pkg-* manifest unit, built from a clone at the publish commit"]
        PYPI["PyPI · SEAM: the fifteen at each release's version, uploaded right after its publish commit; uv resolves the plugin's environments from it"]
    end
    TYPE(["THE ONE TYPE — skill dir = name/SKILL.md"])
    MINT["22-seq-mint-attention-chain — the mint dev flow"]
    REL["22-seq-chaincompiler-release — the release dev flow"]

    CA --> CHAIN
    CA --> CC
    CA --> ST
    CHAIN --> CC
    SCCC --> SKC
    CC --> APE
    CC --> RC
    CC --> HC
    APE --> PSC
    PCC --> CHAIN
    FW --> ST
    SI --> CA
    SI --> ST
    ARC --> CC
    GS -.-> CC
    CC -.-> GS
    PLUG --> LAUNCH
    LAUNCH --> SI
    PLUG -.-> UVL
    UVL -.-> PYPI
    VER -.-> PLUG
    PPROOF -.-> PLUG
    PUB -.-> PYPI
    UPL -.->|"publish_package.sh, one package at a time"| PUB
    CHAIN -. produces .-> TYPE
    ST -. organizes .-> TYPE
    MINT -. runs through .-> CHAIN
    MINT -. runs through .-> CA
    REL -. runs through .-> GEN
    REL -. runs through .-> PLUG
    REL -. runs through .-> PUB
    REL -. runs through .-> VER
    REL -. runs through .-> PPROOF
    REL -. runs through .-> UPL
    REL -. runs through .-> RCHK
    RCHK -.-> GEN
    RCHK -.-> LAUNCH
    RCHK -.->|"the tee probe's seat"| PPROOF
    RCHK -.->|"re-applies the GBAs"| CA
    RCHK -.->|"publish_unit.sh into a local bare copy"| PUB
```

---

## 2. The closed algebra (one type, three operations)

```mermaid
flowchart LR
    NOTATION["raw notation<br/>(examples)"] -->|"*CC constructs"| SKILL(["skill dir"])
    SKILL -->|"skillchain composes"| SKILL
    SKILL -->|"SkillTree organizes"| TREE["tree of skill dirs"]
    TREE -->|"exchange / federation"| FOREST["forest of trees<br/>(marketplaces federate)"]
    classDef t fill:#e9f7ef,stroke:#16a34a;
    class SKILL t;
```

`*CC`s are **constructors** (lift notation into the type); `skillchain` is the
**composition operator** (closed: an SC can chain an SC); `SkillTree`/exchange/
federation are the **arrangement**. Validators do what the substrate won't.

---

## 3. Skill OS (P6) — three rings over the global namespace

```mermaid
flowchart TB
    subgraph ORGANIZE["① Organize"]
        COORD["coords / metadata / schema<br/>over ~/.claude/skills"]
        LINK["link_tree / build_forest<br/>(symlink up to the top)"]
    end
    subgraph OBSERVE["② Observe"]
        HOOK["usage hook<br/>(PostToolUse on Skill)"]
        FE["frontend<br/>tree + analytics + problem-marking"]
    end
    subgraph IMPROVE["③ Improve"]
        REP["report-missed-skill<br/>+ reports store"]
        IMP["improver agent<br/>skill-improver / create"]
    end
    ORGANIZE --> OBSERVE --> IMPROVE -->|"new / better skills"| ORGANIZE
    HOOK --> REP
    FE --> REP
    REP --> IMP
```

The system **grows from its own gaps**: usage + reports feed improvement, which
feeds back into the organized namespace. Same closure, one ring higher.
Built: coordinates and the reports store (`report-missed-skill`). ASPIRATIONAL: the usage hook, the
frontend and the improver agent (`BACKLOG.md` P6).

---

## 4. Package dependency graph

Arrows point from a package to what it depends on (declared in its `pyproject.toml` and imported in its
source; dotted = imported only inside a function, a lazy import — declared as an optional extra when the build file
does not need it whole, `DESIGN.md` §18). Drawn from an AST walk of each package's `src/`, the walk
`scripts/check_versions.py` makes.

```mermaid
flowchart BT
    APE["agent-prompt-engineering"]
    PSC["pydantic-stack-core"]
    ST["agent-skilltree"]
    APE --> PSC
    chaincompiler --> APE
    chaincompiler --> honeyc
    chaincompiler --> rulecatcher
    accc --> chaincompiler
    accc --> honeyc
    corcc --> accc
    corcc --> chaincompiler
    sccc --> chaincompiler
    sccc --> rulecatcher
    sccc --> skillchain
    sccc -.-> accc
    sccc -.-> corcc
    chainaios --> chaincompiler
    chainaios --> accc
    chainaios --> corcc
    chainaios --> sccc
    chainaios --> ST
    chainaios -.-> glyphsteer
    personacc --> accc
    personacc --> corcc
    personacc --> chaincompiler
    personapack --> personacc
    personapack --> corcc
    si --> ST
    si -.-> chainaios
    si -.-> sccc
    si -.-> corcc
    si -.-> accc
    si -.-> chaincompiler
    archetype -.-> chaincompiler
    skill2framework --> ST
    glyphsteer -.-> chaincompiler
    glyphsteer -.-> rulecatcher
    chaincompiler -.-> glyphsteer
    classDef ext fill:#f6f6f5,stroke:#9a9a96;
    class APE,PSC,ST ext;
```

The grey boxes come from PyPI; every other box is a package under `packages/`. `goldenreq` depends on
nothing. The dotted pair `chaincompiler` ⇄ `glyphsteer` is a lazy import cycle (each imports the other inside
functions), outside the contract and owed a break (`DESIGN.md` §2). `.importlinter` enforces the six-layer chain `chainaios > sccc > corcc > accc > chaincompiler >
prompt_engineering` (`DESIGN.md` §2).

---

## 5. The compiler loop — how a `*CC` mints a skill

Every `*CC` (ACCC/CORCC/SCCC) runs the same loop on the engine.

```mermaid
sequenceDiagram
    participant U as caller
    participant CC as *CC layer
    participant RC as rulecatcher
    participant HC as honeyc
    participant FS as <name>/SKILL.md
    U->>CC: forge(name, examples)
    CC->>RC: catch grammar + adopt (ratify the shape)
    Note over RC: this is the only check — SYNTAX, never content
    U->>CC: gate / lint(candidate)
    CC->>RC: lint → orthogonal | syntax_break | clean
    U->>CC: package(...)
    CC->>HC: compile notation → markdown body
    CC->>FS: write <name>/SKILL.md (the one type)
```

---

## 6. `construct_language` — mint a whole domain language

```mermaid
sequenceDiagram
    participant U as user / agent
    participant CC as chainaios
    participant A as ACCC
    participant C as CORCC
    participant S as SCCC
    U->>CC: construct_language(domain, ac_chain, cor_persona)
    CC->>A: forge + package AC  →  ac/SKILL.md
    CC->>C: forge_persona + package CoR  →  cor/SKILL.md
    CC->>S: forge + package SC (chains ac + cor)  →  sc/SKILL.md
    CC-->>U: bundle{ac, cor, sc}  (three skill dirs)
```

---

## 7. SkillTree — surface up, then Read down (progressive disclosure)

A skill dir's nested `.claude/skills` is **not** auto-loaded (the scan is
non-recursive within `.claude/skills`). So entry points are symlinked UP to the
top, and the agent Reads DOWN the breadcrumbs (`02-the-autoload-mechanism.md`).

```mermaid
sequenceDiagram
    participant Dev as builder
    participant ST as skilltree
    participant User as ~/.claude/skills
    participant CC as Claude Code
    participant Ag as agent (session)
    Dev->>ST: materialize(tree, coords=True) + link_tree
    ST->>User: symlink root + branches (0-root, 0.1-…)
    Note over CC,User: session start → auto-loads ONLY the top entries
    CC->>Ag: available skills = root + first layer (coord-sorted)
    Ag->>Ag: Read the child's SKILL.md (its breadcrumb)  (= work in the child's folder)
    Note over Ag: on-demand load of that child's skills; leaves stay hidden until reached
```

---

## 8. Contribution gate — validate → queue → gated promote (P5)

The marketplace is a git repo; a contribution is a PR editing `registry.json`.
The gate is **fork-safe** and runs the BASE copy of itself, never the PR's.

```mermaid
sequenceDiagram
    participant C as contributor
    participant PR as PR (registry.json)
    participant CI as contribute.yml (read-only, no secrets)
    participant Q as registry.json
    participant M as maintainer
    C->>PR: add a DATA entry (pointer), not code
    PR->>CI: on pull_request
    CI->>CI: run BASE gate vs the PR's data
    alt invalid (self-promote / tamper / no provenance)
        CI-->>PR: ✗ rejected
    else valid
        CI->>Q: entry allowed as trust = unverified
        Q-->>M: queued
        M->>Q: promote → verified (manual, never automatic)
    end
```

---

## 9. Federation walk — a tree of marketplaces

```mermaid
sequenceDiagram
    participant App as caller
    participant F as walk_federation
    participant R as resolve(entry)
    App->>F: walk_federation(root_registry, resolve)
    loop each `registry`-kind entry (a child marketplace)
        F->>R: resolve child registry
        R-->>F: child registry.json
        F->>F: recurse (cycle-guarded)
    end
    F-->>App: nested tree of marketplaces<br/>(flatten → each skill tagged with its path)
```

---

## 10. The Skill OS loop — grow from your own gaps (P6)

```mermaid
sequenceDiagram
    participant Ag as agent / user
    participant RMS as report-missed-skill
    participant Store as ~/.claude/skill-reports.json
    participant Imp as improver agent
    participant NS as new / improved skill
    Ag->>RMS: "no skill for this" (or user: "you missed X, report it")
    RMS->>Store: report_missed / mark_problem  (status: open)
    Imp->>Store: read open queue (skilltree reports)
    Imp->>NS: skill-improver / create the missing skill
    Imp->>Store: resolve(report)
    Note over NS: lands in the namespace → organized → observed → … (loop)
```
