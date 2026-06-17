"""glyphsteer-serve — a thin ONNX embedding sidecar for GlyphSteer's dense regime.

One job: turn text into vectors over HTTP, using fastembed (ONNX runtime, NO torch).
The steer/probe math stays in the host package (pure numpy on the returned vectors);
this container only holds the neural runtime + model weights. Model is chosen by the
GLYPHSTEER_MODEL env var so the same image can serve any fastembed-supported model —
which is exactly what makes the emoji-tokenization question (does the model represent
emoji distinctly, or collapse them?) a one-env-var experiment.
"""
from __future__ import annotations

import os

from fastapi import FastAPI
from fastembed import TextEmbedding
from pydantic import BaseModel

MODEL = os.environ.get("GLYPHSTEER_MODEL", "BAAI/bge-small-en-v1.5")

app = FastAPI(title="glyphsteer-serve",
              summary="ONNX embedding sidecar for GlyphSteer's dense regime")
_model: TextEmbedding | None = None


def model() -> TextEmbedding:
    global _model
    if _model is None:
        _model = TextEmbedding(MODEL)
    return _model


class EmbedReq(BaseModel):
    texts: list[str]


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model": MODEL}


@app.get("/info")
def info() -> dict:
    vec = next(iter(model().embed(["x"])))
    return {"model": MODEL, "dim": int(len(vec))}


@app.post("/embed")
def embed(req: EmbedReq) -> dict:
    vecs = [v.tolist() for v in model().embed(list(req.texts))]
    return {"model": MODEL, "dim": (len(vecs[0]) if vecs else 0), "vectors": vecs}
