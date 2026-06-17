from __future__ import annotations

from dataclasses import dataclass
import re

# Keep contiguous symbol runs such as `=>`, `->`, and `::` together so the
# rule catcher learns syntax transitions instead of punctuation fragments.
TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|\d+|[^\sA-Za-z0-9_]+")

BOS = "<BOS>"
EOL = "<EOL>"
IDENTIFIER = "IDENTIFIER"
NUMBER = "NUMBER"
OPERATOR = "OPERATOR"
OPEN_DELIM = "OPEN_DELIM"
CLOSE_DELIM = "CLOSE_DELIM"
SEPARATOR = "SEPARATOR"
SYMBOL = "SYMBOL"
KEYWORD = "KEYWORD"

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_NUMBER_RE = re.compile(r"^\d+$")
_OPERATOR_RE = re.compile(r"^[=<>:+\-*/|&!?%~^]+$")
_OPEN_DELIMS = {"(", "[", "{"}
_CLOSE_DELIMS = {")", "]", "}"}
_SEPARATORS = {",", ";", "."}


@dataclass(frozen=True)
class Token:
    text: str
    line_no: int
    start: int
    end: int
    absolute_start: int
    absolute_end: int


@dataclass(frozen=True)
class TokenLine:
    line_no: int
    text: str
    start_offset: int
    tokens: tuple[Token, ...]


def tokenize_text(text: str) -> list[TokenLine]:
    token_lines: list[TokenLine] = []
    offset = 0
    for index, raw_line in enumerate(text.splitlines(keepends=True), start=1):
        line = raw_line.rstrip("\n")
        tokens = tuple(_tokenize_line(line, index, offset))
        token_lines.append(TokenLine(index, line, offset, tokens))
        offset += len(raw_line)

    if not text or text.endswith("\n"):
        return token_lines

    if "\n" not in text:
        return token_lines

    return token_lines


def line_token_texts(token_line: TokenLine) -> list[str]:
    return [BOS, *[token.text for token in token_line.tokens], EOL]


def line_token_kinds(token_line: TokenLine, keywords: frozenset[str] = frozenset()) -> list[str]:
    return [BOS, *[token_kind(token.text, keywords) for token in token_line.tokens], EOL]


def token_for_sequence_index(token_line: TokenLine, sequence_index: int) -> Token | None:
    if sequence_index <= 0:
        return None
    if sequence_index > len(token_line.tokens):
        return None
    return token_line.tokens[sequence_index - 1]


def _tokenize_line(line: str, line_no: int, line_start_offset: int) -> list[Token]:
    return [
        Token(
            text=match.group(0),
            line_no=line_no,
            start=match.start(),
            end=match.end(),
            absolute_start=line_start_offset + match.start(),
            absolute_end=line_start_offset + match.end(),
        )
        for match in TOKEN_RE.finditer(line)
    ]


def token_kind(text: str, keywords: frozenset[str] = frozenset()) -> str:
    if text in {BOS, EOL}:
        return text
    if text in keywords:
        return KEYWORD
    if _IDENTIFIER_RE.match(text):
        return IDENTIFIER
    if _NUMBER_RE.match(text):
        return NUMBER
    if text in _OPEN_DELIMS:
        return OPEN_DELIM
    if text in _CLOSE_DELIMS:
        return CLOSE_DELIM
    if text in _SEPARATORS:
        return SEPARATOR
    if _OPERATOR_RE.match(text):
        return OPERATOR
    return SYMBOL
