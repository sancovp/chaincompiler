# Rule: your default workflow is the loop flow-skill

Your default workflow is the **`adam-curtis-narration-style-loop`** flow skill in your tree — find it (`chaincompiler gba search <this-dir> loop`), Read it, and walk it (Task → Recall=Select(search→match) → Decide → Construct|Exec → Reward).

**Addressing:** every node has a coordinate (`0` → `0.1` → `0.1.1` …). `gba search <this-dir> "<q>" --scope 0.1` searches ONLY `0.1` + its descendants (*where you are = what you see*); add `--newest` to forward only the latest versions.
**Attention-chain syntax** (for `gba construct`): `[Label] ⇒ [Label] ⇒ |Converge|` — each `[...]` is a **bare label** (one word/CamelCase, **no colon, no description inside the brackets**: `[Symptom]` ✓, `[Symptom: latency]` ✗ → parser error). `|...|` is the convergence.