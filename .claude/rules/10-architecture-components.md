# Rule: ChainCompiler architecture — component diagrams

The static structure of the system. Every aspect has a component diagram here;
when you change the architecture, update the matching diagram in the same change.

The whole system is **a closed algebra over one type — the skill dir**
(`<name>/SKILL.md`, the unit any agent auto-loads). Every layer produces or
consumes only that type, so composition closes and recurses.

---

## 1. The full stack

Arrows = dependency (who imports whom). Drawn from `DESIGN.md` §2; every package is a box, and the
mint dev flow sits on the tiers it runs through.

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
        FW["framework"]
        SI["si — MCP server + skill"]
    end
    TYPE(["THE ONE TYPE — skill dir = name/SKILL.md"])
    MINT["22-seq-mint-attention-chain — the mint dev flow"]

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
    CHAIN -. produces .-> TYPE
    ST -. organizes .-> TYPE
    MINT -. runs through .-> CHAIN
    MINT -. runs through .-> CA
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
source; dotted = optional or lazy).

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
    si --> chainaios
    si --> sccc
    si --> corcc
    si --> accc
    si --> chaincompiler
    si --> ST
    archetype --> chaincompiler
    framework --> ST
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
