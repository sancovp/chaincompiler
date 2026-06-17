# GlyphSteer — Component Architecture

> Static structure. Update with every module/boundary change (rule 00). Arrows = depends-on.

## Whole-package component diagram

```mermaid
flowchart TB
    subgraph lang["Language layer (the controlled vocabulary)"]
        vocab["vocab.py<br/>Axis(glyph, tag) · Vocabulary<br/>validate · code · code_tags · strip"]
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
        denseM["dense.py<br/>embed · measure_anchor<br/>(lazy sentence-transformers)"]
        steer["steer.py<br/>sim_eff = cos + Σ wₖ⟨q,âₖ⟩⟨d,âₖ⟩<br/>(pure numpy)"]
    end

    subgraph evalL["Evaluation"]
        evalm["eval.py<br/>magnitude_probe (Q1-Q3)<br/>retrieval_lift_lexical (Q4)"]
    end

    cli["cli.py — annotate / query / vocab"]

    vocab --> annotate
    vocab --> encode
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
- `encode.py` is the **only** place the indexed-form/returned-form split is defined; the
  HIDE invariant (`check_hidden`, `index.assert_hidden`) is enforced at every read boundary.
- `dense.py` is the **only** import of `sentence-transformers`; it is lazy, so the whole
  left side runs with `pip install glyphsteer` (no extra).
- `steer.py` is **pure numpy** — it takes vectors, never the model, so the metric math is
  testable without any download.
