"""AST nodes (grammar/07-ast.md): a generic record plus the JSON form."""
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class Span:
    file: str
    line: int
    col: int
    end_line: int
    end_col: int          # exclusive
    via: Optional["Span"] = None

    def __str__(self):
        s = "%s:%d:%d-%d:%d" % (self.file, self.line, self.col, self.end_line, self.end_col)
        return s + (" <- " + str(self.via) if self.via else "")


class Node:
    """A record with a `kind`; fields keep construction order."""

    def __init__(self, kind: str, **fields: Any):
        self.kind = kind
        self.f: Dict[str, Any] = fields

    def __getattr__(self, name):
        try:
            return self.__dict__["f"][name]
        except KeyError:
            raise AttributeError(name)

    def get(self, name, default=None):
        return self.f.get(name, default)

    def __repr__(self):
        return "Node(%s)" % self.kind


def to_json(x):
    """Canonical JSON form: `kind` tag, absent optionals omitted, span as text."""
    if isinstance(x, Node):
        out = {"kind": x.kind}
        for k, v in x.f.items():
            if v is None:
                continue
            out[k] = to_json(v)
        return out
    if isinstance(x, Span):
        return str(x)
    if isinstance(x, (list, tuple)):
        return [to_json(i) for i in x]
    if isinstance(x, float) and (x != x or x in (float("inf"), float("-inf"))):
        return None
    return x
