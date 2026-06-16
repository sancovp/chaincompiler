"""AST dataclasses for Dense Rune-Chain Notation."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Entity:
    id: str


@dataclass
class Glyph:
    id: str
    name: str | None = None


@dataclass
class Symbol:
    name: str


@dataclass
class TypeAnn:
    term: object
    type_name: str


@dataclass
class Bounded:
    term: object


@dataclass
class Placeholder:
    kind: str = "drilldown"


@dataclass
class Connector:
    kind: str          # equiv | produces | compiles | maps | arrow | trans | runtime | rel
    value: str         # the surface glyph or relation name


@dataclass
class Chain:
    terms: list[object]
    connectors: list[Connector]


@dataclass
class Scope:
    owner: object
    body: list[object]


@dataclass
class Transform:
    chain: object       # Chain or a single term


@dataclass
class Assignment:
    left: object
    right: object


@dataclass
class Program:
    statements: list[object] = field(default_factory=list)
