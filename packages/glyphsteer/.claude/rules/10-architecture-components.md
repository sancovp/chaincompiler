# GlyphSteer — Component Architecture

> Static structure. Update with every module/boundary change (rule 00). Arrows = depends-on.

## Whole-package component diagram

```mermaid
flowchart TB
    subgraph lang["Language layer (the controlled vocabulary)"]
        vocab["vocab.py<br/>Axis(glyph, tag) · Vocabulary<br/>validate · code · code_tags · strip<br/>_matches: longest glyph first, never overlapping"]
        legend["legend.py<br/>author · save/load · merge (last author wins<br/>on a name, glyph or tag clash) · render"]
    end

    subgraph gate["Syntax gate (optional extra)"]
        grammar["grammar.py<br/>GlyphGrammar.lint: foreign residue → syntax_break<br/>· order via in_code_order → orthogonal"]
    end

    subgraph ext["ChainCompiler (not ours — its seam)"]
        rc["chaincompiler.bridge · rulecatcher<br/>SEAM: learn / gate (imported lazily)"]
    end

    subgraph annot["Annotation layer (writes the sidecar)"]
        annotate["annotate.py<br/>RuleAnnotator · LLMAnnotator<br/>(judge → glyph code)"]
    end

    subgraph core["Encode layer (the sidecar split — KEYSTONE)"]
        encode["encode.py<br/>Chunk · indexed_form (dense input)<br/>returned_form (CLEAN) · annotate_chunk<br/>check_hidden (the HIDE invariant)"]
    end

    subgraph lex["Lexical regime (zero deps)"]
        index["index.py<br/>FTS5/BM25 · facet on ASCII tag<br/>returns CLEAN text"]
    end

    subgraph dense["Dense regime (optional extra)"]
        denseM["dense.py<br/>embed · measure_anchor<br/>(the sidecar, or lazy fastembed / sentence-transformers)"]
        steer["steer.py<br/>sim_eff = cos + Σ wₖ⟨q,âₖ⟩⟨d,âₖ⟩<br/>(pure numpy)"]
    end

    subgraph evalL["Evaluation"]
        evalm["eval.py<br/>magnitude_probe (Q1-Q3)<br/>retrieval_lift_lexical (Q4)"]
    end

    cli["cli.py — annotate / query / vocab"]

    vocab --> annotate
    vocab --> encode
    vocab --> legend
    vocab --> grammar
    grammar -.lazy.-> rc
    encode -.grammar=.-> grammar
    annotate --> encode
    encode --> index
    encode --> evalm
    vocab --> index
    denseM --> steer
    denseM --> evalm
    steer --> evalm
    encode -.dense input.-> denseM
    index --> cli
    encode --> cli

    classDef key fill:#ffd,stroke:#aa0,stroke-width:2px;
    class encode key;
```

## The dual-rendering of one axis (the central finding)

```mermaid
flowchart LR
    axis["Axis<br/>name: negative"]
    axis -->|dense marker| glyph["glyph 😡<br/>(emoji: learned direction;<br/>embedder tokenizes it)"]
    axis -->|lexical marker| tag["tag gsxnegative<br/>(ASCII sentinel: FTS5 tokenizes it;<br/>emoji are DROPPED by unicode61)"]
    glyph --> dpath["dense regime<br/>vector nudge / anchor reshape"]
    tag --> lpath["lexical regime<br/>maximal-IDF exact-match facet"]
    classDef find fill:#fdd,stroke:#a00;
    class tag find;
```

## The dense sidecar (containerized neural runtime)

The heavy neural runtime lives OFF the host, in a container; the host calls it over HTTP.

```mermaid
flowchart LR
    subgraph host["Host process (dependency-light)"]
        denseH["dense.py<br/>backend: remote (urllib, stdlib)<br/>fastembed / st = local fallbacks"]
        steerH["steer.py · eval.py<br/>(pure numpy on returned vectors)"]
    end
    subgraph container["glyphsteer-serve (Docker image, ~888MB, NO torch)"]
        api["app.py — FastAPI<br/>/health /info /embed"]
        fe["fastembed → onnxruntime"]
        weights["model weights<br/>(GLYPHSTEER_MODEL, pre-cached at build)"]
        api --> fe --> weights
    end
    denseH -->|"POST /embed {texts}"| api
    api -->|"{vectors}"| denseH
    denseH --> steerH
    classDef ext fill:#eef,stroke:#558;
    class container ext;
```

- Swapping the embedding model = one env var (`GLYPHSTEER_MODEL`) → rebuild. This is what
  made the emoji-collapse failure (see DW-6) discoverable and fixable.
- The container is **embeddings-only**; all steer/probe math stays host-side on the vectors.

## Boundary notes
- `vocab._matches` is the **only** way a glyph is found in text: left to right, at each place the
  longest glyph that starts there, never two that overlap. `parse`, `glyphs_in`, `code_tags`,
  `strip`, `in_code_order`, `to_honeyc` and the grammar's order check all read through it, so a
  vocabulary may hold a glyph that is part of another (an emoji and its VS16 or skin-tone form).
- `encode.py` is the **only** place the indexed-form/returned-form split is defined; the
  HIDE invariant (`check_hidden`, `index.assert_hidden`) is enforced at every read boundary.
- `grammar.py` imports ChainCompiler's bridge and rulecatcher inside `_deps()`, so importing
  GlyphSteer never needs them; its `lint` refuses foreign content itself, before the tag chain
  rulecatcher reads is built.
- `dense.py` is the **only** import of an embedding runtime (`fastembed`, `sentence-transformers`), each lazy, so the
  whole left side runs with the package installed from its folder and no extra (`pip install -e packages/glyphsteer`;
  glyphsteer is not on PyPI — ChainCompiler `DESIGN.md` §18).
- `steer.py` is **pure numpy** — it takes vectors, never the model, so the metric math is
  testable without any download.
