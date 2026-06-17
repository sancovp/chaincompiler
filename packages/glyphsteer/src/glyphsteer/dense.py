"""The dense layer — embeddings + anchor measurement, via a pluggable backend.

The heavy neural runtime is OFF the host by default: GlyphSteer talks to the
`glyphsteer-serve` container (ONNX/fastembed, no torch) over HTTP. The host import
stays dependency-light (the remote backend is stdlib-only urllib). Local backends
exist as fallbacks.

Backend resolution (override with `backend=`):
  1. "remote"    — POST to $GLYPHSTEER_EMBED_URL/embed  (default if the env var is set)
  2. "fastembed" — local ONNX runtime (`pip install glyphsteer[dense]`)
  3. "st"        — local sentence-transformers (`pip install glyphsteer[st]`, heavy)

`measure_anchor(glyph)` returns the glyph's learned direction — the â_k that
`steer.sim_eff` uses to reshape the metric, and what `eval.magnitude_probe` measures.
"""
from __future__ import annotations

import json
import os
import urllib.request
from functools import lru_cache

import numpy as np

_DEFAULT_MODEL = os.environ.get("GLYPHSTEER_MODEL", "BAAI/bge-small-en-v1.5")
_ENV_URL = "GLYPHSTEER_EMBED_URL"


def _default_backend() -> str:
    if os.environ.get(_ENV_URL):
        return "remote"
    try:
        import fastembed  # noqa: F401
        return "fastembed"
    except ImportError:
        return "st"


# ---- remote (the container; stdlib only) ------------------------------------
def _remote_embed(texts: list[str], url: str | None = None) -> np.ndarray:
    base = (url or os.environ[_ENV_URL]).rstrip("/")
    payload = json.dumps({"texts": list(texts)}).encode("utf-8")
    req = urllib.request.Request(base + "/embed", data=payload,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        out = json.load(r)
    return np.asarray(out["vectors"], dtype=np.float32)


# ---- fastembed (local ONNX) -------------------------------------------------
@lru_cache(maxsize=4)
def _fe(model: str):
    try:
        from fastembed import TextEmbedding
    except ImportError as e:  # pragma: no cover
        raise ImportError("backend 'fastembed' needs: pip install 'glyphsteer[dense]'") from e
    return TextEmbedding(model)


def _fastembed_embed(texts: list[str], model: str) -> np.ndarray:
    return np.asarray(list(_fe(model).embed(list(texts))), dtype=np.float32)


# ---- sentence-transformers (local, heavy) -----------------------------------
@lru_cache(maxsize=4)
def _st(model: str):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as e:  # pragma: no cover
        raise ImportError("backend 'st' needs: pip install 'glyphsteer[st]'") from e
    return SentenceTransformer(model)


def _st_embed(texts: list[str], model: str) -> np.ndarray:
    return np.asarray(_st(model).encode(list(texts), normalize_embeddings=False),
                      dtype=np.float32)


# ---- public API -------------------------------------------------------------
def embed(texts: list[str], *, backend: str | None = None,
          model: str = _DEFAULT_MODEL, url: str | None = None) -> np.ndarray:
    """Embed texts → (n, dim) float32 array, via the resolved backend."""
    backend = backend or _default_backend()
    if backend == "remote":
        return _remote_embed(texts, url)
    if backend == "fastembed":
        return _fastembed_embed(texts, model)
    if backend == "st":
        return _st_embed(texts, model)
    raise ValueError(f"unknown embed backend {backend!r} (remote|fastembed|st)")


def measure_anchor(glyph: str, **kw) -> np.ndarray:
    """The glyph's learned direction = its embedding (the â_k for steer.sim_eff)."""
    return embed([glyph], **kw)[0]


def measure_anchors(glyphs: list[str], **kw) -> np.ndarray:
    """Stack of anchor directions for a list of glyphs → (k, dim)."""
    return embed(list(glyphs), **kw)


def health(url: str | None = None) -> dict:
    """Ping the remote embedding service."""
    base = (url or os.environ[_ENV_URL]).rstrip("/")
    with urllib.request.urlopen(base + "/health", timeout=10) as r:
        return json.load(r)


def active_model(model: str = _DEFAULT_MODEL, url: str | None = None) -> str:
    """The model name actually serving embeddings, for honest reporting.

    With the remote backend the sidecar decides the model (the local `model` arg is
    ignored), so we ask it; otherwise the local model name is authoritative.
    """
    if _default_backend() == "remote":
        try:
            return health(url).get("model", model)
        except Exception:
            return model
    return model
