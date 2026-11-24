"""Tokenizer (grammar/00-tokens.md). Context-free: no modes."""
from dataclasses import dataclass
from typing import List, Optional, Tuple

from .dialect import NGSPICE, Dialect
from .numbers import NumberInfo, number
from .pass1 import LogicalLine

SEPARATORS = " \t,=()"


@dataclass
class Token:
    kind: str                  # Word Equals LParen RParen Comma Braced Quoted DQuoted Unterminated
    text: str
    start: int
    end: int
    space_before: bool
    origin: Tuple[str, int, int]       # file, line, col of start
    number: Optional[NumberInfo] = None


def tokenize(line: LogicalLine, dialect: Dialect = NGSPICE) -> List[Token]:
    s = line.text
    toks: List[Token] = []
    i, n = 0, len(s)
    space = False

    def add(kind, a, b, num=None):
        toks.append(Token(kind, s[a:b], a, b, space, line.origin(a), num))

    while i < n:
        c = s[i]
        if c in " \t":
            space = True
            i += 1
            continue
        if c == ",":
            add("Comma", i, i + 1); i += 1
        elif c == "=":
            add("Equals", i, i + 1); i += 1
        elif c == "(":
            add("LParen", i, i + 1); i += 1
        elif c == ")":
            add("RParen", i, i + 1); i += 1
        elif c == "{":
            depth, j = 0, i
            while j < n:
                if s[j] == "{":
                    depth += 1
                elif s[j] == "}":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            if j < n:
                add("Braced", i, j + 1); i = j + 1
            else:
                add("Unterminated", i, i + 1); i = n
        elif c in "'\"":
            j = s.find(c, i + 1)
            if j < 0:
                add("Unterminated", i, i + 1); i = n
            else:
                add("Quoted" if c == "'" else "DQuoted", i, j + 1); i = j + 1
        else:
            j = i
            # A '{' inside a word is an ordinary character (A-29: unspecified).
            while j < n and s[j] not in SEPARATORS:
                j += 1
            add("Word", i, j, number(s[i:j], dialect))
            i = j
        space = False
    return toks


def render(tokens: List[Token]) -> str:
    """The notation used in 00-tokens.md: W(x) N(x) Equals Braced(...)."""
    out = []
    for t in tokens:
        if t.kind == "Word":
            out.append(("N(%s)" if t.number else "W(%s)") % t.text)
        elif t.kind == "DQuoted":
            out.append('DQuoted("%s")' % t.text[1:-1])
        elif t.kind == "Quoted":
            out.append("Quoted(%s)" % t.text)
        elif t.kind == "Braced":
            out.append("Braced(%s)" % t.text)
        elif t.kind == "Unterminated":
            out.append("Unterminated(%s)" % t.text)
        else:
            out.append(t.kind)
    return " ".join(out)
