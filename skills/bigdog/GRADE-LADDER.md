# GRADE-LADDER — correspondence grading as a glyphsteer vocabulary

Every correspondence claim (`X ↔ Y`, "X is Y", "X maps to Y") carries a grade.
The glyph is the **dense** marker (steers an embedding); the tag is the **lexical**
facet (rare, max-IDF). Both are **stripped from the returned text** — they steer
retrieval/display, the reader never sees them. **Never round up.**

Bands: **G0–G3 proven** · **G4–G7 mapped-under-R (state R + the promoting check)** · **G8–G9 salience only (inspiration, never evidence)**.

| Grade | glyph | tag | meaning |
|---|---|---|---|
| **G0** | 🟰 | `gsxg0` | Identity — literally the same object |
| **G1** | 🔗 | `gsxg1` | Isomorphism — same up to renaming (+ inverse) |
| **G2** | 🟢 | `gsxg2` | Equivalence — same behavior/category |
| **G3** | 🔄 | `gsxg3` | Automorphism — same object, internal transform |
| **G4** | 🧩 | `gsxg4` | Homomorphism — some operations preserved |
| **G5** | 🔀 | `gsxg5` | Functor/interp — system-to-system translation |
| **G6** | 🟡 | `gsxg6` | Simulation — one system models another |
| **G7** | 🟠 | `gsxg7` | Rule-mediated — under R, this maps to that |
| **G8** | 🔴 | `gsxg8` | Aesthetic — looks structurally similar (salience) |
| **G9** | 🌫️ | `gsxg9` | Vibe — associative cloud, nothing guaranteed |

Usage (glyphsteer): annotate a chain corpus so search can facet by grade and
display the badge, body stays clean:

```python
from glyphsteer import Chunk, build_index, search
# each claim-chunk annotated with its grade glyph (e.g. 🟢=gsxg2, 🔴=gsxg8)
hits = search(con, 'correspondence', facet='gsxg8')  # audit: show only salience-grade claims
```
