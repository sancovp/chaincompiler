# Rule: ChainCompiler architecture — sequence diagrams

The runtime flows. Every key activity boundary has a sequence diagram here; when
you change a flow, update the matching diagram in the same change.

---

## 1. The compiler loop — how a `*CC` mints a skill

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

## 2. `construct_language` — mint a whole domain language

```mermaid
sequenceDiagram
    participant U as user / agent
    participant CC as ChainCompiler
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

## 3. SkillTree — surface up, then `cat` down (progressive disclosure)

A skill dir's nested `.claude/skills` is **not** auto-loaded (the scan is
non-recursive within `.claude/skills`). So entry points are symlinked UP to the
top, and the agent `cat`s DOWN the breadcrumbs.

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
    Ag->>Ag: cat <breadcrumb to child>  (= work in child subdir)
    Note over Ag: on-demand load of that child's skills; leaves stay hidden until reached
```

---

## 4. Contribution gate — validate → queue → gated promote (P5)

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

## 5. Federation walk — a tree of marketplaces

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

## 6. The Skill OS loop — grow from your own gaps (P6)

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
