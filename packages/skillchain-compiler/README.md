# skillchain — a skillchain compiler

Compose Claude Code **skills** into a validated, packaged **chain**.

A skillchain is an ordered list of steps of two kinds:
- **skill** — invoke a named skill (the compiler validates it exists on disk).
- **cor** — an **Attention-Chain / Chain-of-Reasoning** bridge between skills: an explicit
  reasoning step that routes one skill's output into the next.

The compiler **(1)** indexes every skill under `~/.claude/skills` + `~/.claude/plugins`,
**(2)** validates every referenced skill exists (errors listing any missing), **(3)** wires
the CoR bridges, **(4)** exports a **skill package** (`<out>/<name>/SKILL.md` + `chain.json`)
that, when invoked, executes the chain in order.

## Use
```bash
python3 skillchain.py list                       # list indexed skills
python3 skillchain.py validate examples/offer_builder.chain
python3 skillchain.py compile  examples/offer_builder.chain --out dist
python3 skillchain.py compile  examples/offer_builder.chain --install   # -> ~/.claude/skills
```
`--install` writes the compiled package straight into `~/.claude/skills/<name>/` so it becomes
an invokable skill (after a reload). Otherwise it lands in `./dist/<name>/`.

## Spec formats
Two interchangeable formats; both parse to the same internal spec.

### `.chain` text DSL (ergonomic)
```
name: my_chain
description: one line
> skill-a : args for skill-a        # '>' = skill step  (skill : args)
= result_a                          # '=' = capture last result as a var
~ Given {result_a}, reason about X, then produce Y.   # '~' = CoR / AttentionChain bridge
> skill-b : use {result_a} and Y
```

### `.json` (canonical)
```json
{
  "name": "my_chain",
  "description": "one line",
  "steps": [
    {"skill": "skill-a", "args": "args for skill-a", "capture": "result_a"},
    {"cor": "Given {result_a}, reason about X, then produce Y."},
    {"skill": "skill-b", "args": "use {result_a} and Y"}
  ]
}
```

## What "compile" produces
`<out>/<name>/SKILL.md` — a real skill whose body is the ordered orchestration: each skill
step says *"invoke skill X with …, capture as …"*, each CoR step is an explicit reason-then-carry
bridge, and the header lists the validated dependencies. Plus `chain.json`, the canonical spec.

## Validation guarantees
`compile` refuses to emit a package if **any** referenced skill is missing — so a compiled
chain only ever composes skills that actually exist. `validate` exits non-zero on any problem
(missing skill, no name, malformed step), so it can gate CI.
