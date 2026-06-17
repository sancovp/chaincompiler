"""The dense backend selector + the remote (container) client — mocked, no GPU/model.

We never import torch/onnx here: we stub the HTTP layer to prove the host talks to the
sidecar correctly and that steer.py composes with whatever vectors come back.
"""
import io
import json

import numpy as np
import pytest

from glyphsteer import dense, sim_eff


def test_backend_resolves_remote_when_env_set(monkeypatch):
    monkeypatch.setenv("GLYPHSTEER_EMBED_URL", "http://localhost:8088")
    assert dense._default_backend() == "remote"


def test_remote_embed_posts_and_parses(monkeypatch):
    captured = {}

    def fake_urlopen(req, timeout=0):
        captured["url"] = req.full_url
        captured["body"] = json.loads(req.data.decode())
        resp = json.dumps({"model": "m", "dim": 3,
                           "vectors": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]}).encode()
        return io.BytesIO(resp)

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    out = dense.embed(["a", "b"], backend="remote", url="http://svc:8088")
    assert captured["url"] == "http://svc:8088/embed"
    assert captured["body"] == {"texts": ["a", "b"]}
    assert out.shape == (2, 3)
    assert np.allclose(out[0], [1.0, 0.0, 0.0])


def test_measure_anchor_feeds_steer(monkeypatch):
    def fake_urlopen(req, timeout=0):
        return io.BytesIO(json.dumps({"vectors": [[1.0, 0.0]]}).encode())
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    anchor = dense.measure_anchor("\U0001F621", backend="remote", url="http://x")
    docs = np.array([[1.0, 0.0], [0.0, 1.0]])
    q = np.array([1.0, 0.0])
    steered = sim_eff(q, docs, anchors=anchor[None, :], weights=[1.0])
    assert steered[0] > steered[1]      # the on-anchor doc wins


def test_unknown_backend_raises():
    with pytest.raises(ValueError):
        dense.embed(["x"], backend="nope")
