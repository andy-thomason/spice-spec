"""Pass 1: physical lines to logical lines (grammar/01-lexical.md, P1-P11).

Simplifications, chosen here and not specified (see the open issues):
- End-of-line comment characters are recognized outside double quotes only;
  inside braces they still start a comment (A-06, A-29).
- `.include` is expanded only when a loader is supplied (A-28).
- `.lib file name` is not expanded.
- Anything after `.end` is kept; a missing `.end` is a diagnostic.
"""
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from .dialect import NGSPICE, Dialect


@dataclass
class Diag:
    severity: str
    code: str
    message: str
    file: str
    line: int


@dataclass
class Seg:
    start: int      # offset in the logical line where this piece begins
    file: str
    line: int       # 1-based physical line
    col: int        # 1-based column of the piece's first character


@dataclass
class LogicalLine:
    text: str
    segs: List[Seg]

    def origin(self, offset):
        s = self.segs[0]
        for seg in self.segs:
            if seg.start <= offset:
                s = seg
        return (s.file, s.line, s.col + offset - s.start)


@dataclass
class Pass1Result:
    title: str
    lines: List[LogicalLine]
    diagnostics: List[Diag] = field(default_factory=list)


def _strip_eol_comment(s, d):
    inq = False
    i = 0
    while i < len(s):
        c = s[i]
        if c == '"':
            inq = not inq
        elif not inq:
            if c in d.eol_chars or (d.eol_slashes and s.startswith("//", i)):
                return s[:i].rstrip()
        i += 1
    return s.rstrip()


def _decode(data, file, diags):
    if isinstance(data, str):
        return data
    try:
        return data.decode("utf-8")                       # P1
    except UnicodeDecodeError as e:
        diags.append(Diag("error", "invalid-utf8", str(e), file, 0))
        return data.decode("utf-8", errors="replace")


def _process(text, file, d, diags, loader, depth):
    out: List[LogicalLine] = []
    cur: Optional[LogicalLine] = None
    open_backslash = False
    for n, raw in enumerate(text.replace("\r\n", "\n").split("\n"), start=1):
        line = raw
        if not line.strip():                                # blank lines
            continue
        col = 1
        if line[0] in " \t":                                # P3
            if d.leading_ws_comment and not line.lstrip().startswith("+"):
                continue
            stripped = line.lstrip()
            col = len(line) - len(stripped) + 1
            line = stripped
        c0 = line[0]
        if c0 == "*":                                       # P5
            continue
        if d.special_leading and c0 in d.special_leading:   # P4
            diags.append(Diag("warning", "special-leading-char",
                              "line starts with %r; treated as a comment" % c0, file, n))
            continue
        if c0 == "+" and not open_backslash:                # P6
            if cur is None:
                diags.append(Diag("error", "stray-continuation",
                                  "continuation with nothing to continue", file, n))
                continue
            rest = _strip_eol_comment(line[1:], d)
            lead = len(rest) - len(rest.lstrip())
            cur.segs.append(Seg(len(cur.text) + 1, file, n, col + 1 + lead))
            cur.text += " " + rest.strip()
        elif open_backslash and cur is not None:            # P7, second half
            rest = _strip_eol_comment(line, d)
            cur.segs.append(Seg(len(cur.text) + 1, file, n, col))
            cur.text += " " + rest
        else:
            cur = LogicalLine(_strip_eol_comment(line, d), [Seg(0, file, n, col)])
            out.append(cur)
        open_backslash = False
        if d.backslash_continuation and cur.text.endswith("\\\\"):
            cur.text = cur.text[:-2].rstrip()
            open_backslash = True
    return out


def _expand_includes(lines, d, diags, loader, depth):
    if loader is None:
        return lines
    out = []
    for ll in lines:
        parts = ll.text.split(None, 1)
        if parts and parts[0].lower() == ".include":        # P9 (optional)
            f, _, ln = ll.origin(0)
            if depth >= 32:
                diags.append(Diag("error", "include-depth", "include nesting too deep", f, ln))
                continue
            path = parts[1].strip().strip('"\'') if len(parts) > 1 else ""
            try:
                body = loader(path)
            except OSError as e:
                diags.append(Diag("error", "include-missing", "%s: %s" % (path, e), f, ln))
                continue
            inner = _process(body, path, d, diags, loader, depth + 1)
            out += _expand_includes(inner, d, diags, loader, depth + 1)
        else:
            out.append(ll)
    return out


def pass1(data, file="<input>", dialect: Dialect = NGSPICE,
          loader: Optional[Callable[[str], str]] = None) -> Pass1Result:
    diags: List[Diag] = []
    text = _decode(data, file, diags)
    rows = text.replace("\r\n", "\n").split("\n")
    title = rows[0] if rows else ""                          # P2
    body = "\n".join([""] + rows[1:])                        # keep numbering
    lines = _process(body, file, dialect, diags, loader, 0)
    lines = _expand_includes(lines, dialect, diags, loader, 0)
    kept = []
    for ll in lines:
        if ll.text.split(None, 1)[:1] == [".title"] or ll.text.lower().startswith(".title "):
            title = ll.text[len(".title"):].strip()          # P10
        else:
            kept.append(ll)
    if not kept or kept[-1].text.strip().lower() != ".end":  # P11
        diags.append(Diag("error", "missing-end", "the last line must be .end", file, 0))
    return Pass1Result(title, kept, diags)
