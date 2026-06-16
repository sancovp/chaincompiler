# Rule: ChainCompiler architecture — component diagrams

The static structure of the system. Every aspect has a component diagram here;
when you change the architecture, update the matching diagram in the same change.

The whole system is **a closed algebra over one type — the skill dir**
(`<name>/SKILL.md`, the unit any agent auto-loads). Every layer produces or
consumes only that type, so composition closes and recurses.

---

## 1. The full stack

```mermaid
flowchart TB
    subgraph ORG["Organization"]
        ST["SkillTree<br/>cat-breadcrumbs · coords · forest · exchange · federation"]
    end
    subgraph LAYERS["Compiler layers — each PRODUCES a skill dir"]
        direction LR
        ACCC["ACCC<br/>attention chains"] --> CORCC["CORCC<br/>chains of reasoning"] --> SCCC["SCCC<br/>skill chains"]
    end
    subgraph SUB["Substrate"]
        CC["ChainCompiler<br/>learn→gate→compile · construct_language() · SKILL.md packager"]
        SKC["skillchain<br/>rollup"]
    end
    subgraph ENG["Engine"]
        RC["rulecatcher<br/>linter / the gate"]
        HC["honeyc<br/>compiler (+ dietc)"]
    end
    SI["SI<br/>self-interpreter MCP (also a skill)<br/>execute · tree_to_mcp · scaffold_repo"]
    TYPE(["THE ONE TYPE<br/>skill dir = name/SKILL.md"])

    ORG --> LAYERS --> SUB --> ENG
    CC --> RC & HC
    SCCC --> SKC
    LAYERS -. produces .-> TYPE
    SKC -. composes .-> TYPE
    ST -. organizes .-> TYPE
    SI -. runs / emits .-> TYPE
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

---

## 4. Package dependency graph (monorepo)

```mermaid
flowchart BT
    rulecatcher["rulecatcher<br/>(external repo)"]
    honeyc["honeyc (+ dietc)"]
    chaincompiler --> honeyc
    chaincompiler --> rulecatcher
    accc --> chaincompiler
    corcc --> accc
    sccc --> accc
    sccc --> corcc
    sccc --> skillchain
    si --> sccc
    si --> skilltree
    classDef ext fill:#f6f6f5,stroke:#9a9a96;
    class rulecatcher ext;
```

(Arrows point from a package to what it depends on. `chaincompiler` also re-exports
`construct_language`; `accc`/`corcc`/`sccc`/`si` all build on it.)

`rulecatcher` is an **external** dependency (its own repo); everything else is a
package in this monorepo under `packages/`.
