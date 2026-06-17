# glyphsteer-serve

A thin **ONNX embedding sidecar** for GlyphSteer's dense regime. It holds the neural
runtime (fastembed → onnxruntime, **no torch**) and the model weights, and exposes
embeddings over HTTP. The host `glyphsteer` package stays dependency-light and calls
this container; the steer/probe math runs host-side on the returned vectors.

## Run

```bash
cd packages/glyphsteer/serve
docker compose up --build -d           # builds image, pre-caches model, serves :8088
curl localhost:8088/health             # {"status":"ok","model":"BAAI/bge-small-en-v1.5"}
curl localhost:8088/info               # {"model":..., "dim":384}
```

Point the host package at it and the dense regime "just works":

```bash
export GLYPHSTEER_EMBED_URL=http://localhost:8088
python -c "from glyphsteer import dense; print(dense.embed(['hello','😡']).shape)"
python experiments/magnitude_probe.py  # now runs against the container
```

## Swap models (the emoji-tokenization experiment)

The whole point of the sidecar: trying a different embedding model is a one-env-var
change. Some tokenizers collapse emoji to `[UNK]` (no usable direction); byte-level /
multilingual ones represent them distinctly. Compare:

```bash
GLYPHSTEER_MODEL=BAAI/bge-small-en-v1.5      docker compose up --build -d   # English BERT-ish
GLYPHSTEER_MODEL=intfloat/multilingual-e5-small docker compose up --build -d # byte-aware, better for emoji
```

Run the magnitude probe against each and compare `Q1_separation` / `Q2_delta_cos`.

## Endpoints
- `GET /health` → `{status, model}`
- `GET /info` → `{model, dim}`
- `POST /embed` `{texts:[...]}` → `{model, dim, vectors:[[...]]}`
