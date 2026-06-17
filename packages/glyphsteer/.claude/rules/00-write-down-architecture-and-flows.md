# Rule: Write Down ALL Architecture, Flows, and Discovered Dev Workflows

## Purpose
GlyphSteer is a research-grade package: its credibility depends on every structural
decision, runtime flow, and **empirically-discovered constraint** being written down at
the moment it is found — not reconstructed later. This rule is the harness that keeps the
docs == reality.

## Mandatory constraints

### 1. Every architectural layer gets a component diagram
When a module, boundary, or data path is added or changed, update
[`10-architecture-components.md`](10-architecture-components.md) with a Mermaid
`flowchart` (use `subgraph` for boundaries, arrows for dependency direction). No new
module ships without its node in the component diagram.

### 2. Every process boundary gets a sequence diagram
When a runtime flow is added or changed (annotate → encode → index → retrieve; the
dense magnitude probe; the steer reshape), update
[`20-architecture-flows.md`](20-architecture-flows.md) with a Mermaid `sequenceDiagram`.
The diagram must correspond to actual functions — no speculative steps.

### 3. **Development workflows are first-class — write them down as you discover them**
This is the part that is easy to skip and must not be. When building GlyphSteer you will
discover *how to build/verify GlyphSteer* — e.g. "FTS5 unicode61 drops emoji, so verify
any new marker with a 2-line sqlite probe before trusting it," or "the dense magnitude
must be probed before wiring the dense arm." **Each such discovered procedure is a dev
workflow** and goes into `20-architecture-flows.md` under "Development Workflows" as a
short sequence/checklist, the moment it is found. A discovered constraint that isn't
written down will be violated again.

### 4. The implementation plan is canonical
[`../../implementation_plan.md`](../../implementation_plan.md) is the single source of
structural truth. Empirical findings (e.g. the FTS5 emoji result, dense magnitude numbers)
are recorded there in the same change that discovers them, with the `ASPIRATIONAL:` prefix
for anything planned-but-unbuilt.

### 5. Findings carry their evidence
Any claim about behavior (tokenizer, embedding magnitude, retrieval lift) is written with
the command/test that established it, so it is reproducible and falsifiable — never an
unverified heuristic.

## Triggers
- Adding/changing any module, boundary, or data path → component diagram.
- Adding/changing any runtime flow → sequence diagram.
- **Discovering any procedure for building/verifying the system → write it down as a dev
  workflow immediately.**
- Any empirical finding → record in the implementation plan with its evidence.
