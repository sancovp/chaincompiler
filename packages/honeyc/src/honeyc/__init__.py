"""HoneyC — a compiler and CLI for Dense Rune-Chain Notation."""
from __future__ import annotations

__version__ = "0.1.0"

from .parser import parse_path, parse_text
from .normalize import normalize, Statement

__all__ = ["parse_path", "parse_text", "normalize", "Statement", "__version__"]
