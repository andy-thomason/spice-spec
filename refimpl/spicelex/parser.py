"""Reference parser: tokens to the AST of grammar/07-ast.md.

Syntactic only (07-ast.md, principles 1 to 7). It never reads files,
evaluates, or resolves names. Where the AST spec was silent, the choice made
here is listed in the README and in the "Parsing rules" section it led to.
"""
import re
from typing import Callable, List, Optional

from .ast import Node, Span, to_json
from .dialect import NGSPICE, Dialect
from .pass1 import LogicalLine, pass1
from .tokens import Token, tokenize

SEP_KINDS = ("LParen", "RParen", "Comma")

# letter -> (fixed node count, flag words that are parameters without a value)
ELEMENTS = {
    "R": (2, ()), "C": (2, ()), "L": (2, ()), "K": (0, ()),
    "V": (2, ()), "I": (2, ()), "E": (2, ()), "G": (2, ()), "F": (2, ()), "H": (2, ()),
    "B": (2, ()), "D": (2, ("off",)), "Q": (3, ("off",)), "J": (3, ("off",)),
    "Z": (3, ("off",)), "M": (3, ("off",)), "S": (4, ()), "W": (2, ()),
    "T": (4, ()), "O": (4, ()), "U": (3, ()), "X": (0, ()),
}
# (letter, keyword) whose value is an expression, taken as raw text
EXPR_KEYS = {("R", "r"), ("C", "c"), ("C", "q"), ("L", "l"), ("B", "v"), ("B", "i"),
             ("E", "vol"), ("G", "cur")}
SOURCE_KEYWORDS = ("dc", "ac", "distof1", "distof2")
OPERATOR_CHARS = set("+-*/^%<>!&|?:")

# Constructs SPICE3 does not have (for the dialect-extension diagnostic).
NOT_IN_SPICE3_DOT = {"param", "func", "global", "csparam", "lib", "endl", "if", "elseif",
                     "else", "endif", "control", "endc", "meas", "measure", "pss", "sp", "optran"}
NOT_IN_SPICE3_ELEM = set("YPAN")


class _Fail(Exception):
    def __init__(self, reason):
        self.reason = reason


class Parser:
    def __init__(self, dialect: Dialect, file: str, parse_exprs=False):
        self.d = dialect
        self.file = file
        self.diags: List[Node] = []

    # ---- spans and values -------------------------------------------------
    def span(self, ll: LogicalLine, a: int, b: int) -> Span:
        f, l1, c1 = ll.origin(a)
        f2, l2, c2 = ll.origin(max(a, b - 1))
        return Span(f, l1, c1, l2, c2 + 1)

    def diag(self, severity, code, message, span):
        self.diags.append(Node("Diagnostic", severity=severity, code=code, message=message, span=span))

    def ident(self, ll, t: Token):
        text = t.text[1:-1] if t.kind in ("DQuoted", "Quoted") else t.text
        return Node("Ident", text=text, lower=text.lower(), span=self.span(ll, t.start, t.end))

    def value(self, ll, t: Token):
        sp = self.span(ll, t.start, t.end)
        if t.kind == "Braced":
            return Node("Expr", form="braced", raw=t.text, span=sp)
        if t.kind == "Quoted":
            return Node("Expr", form="quoted", raw=t.text, span=sp)
        if t.kind == "Unterminated":
            self.diag("error", "unterminated", "unterminated %r" % t.text, sp)
            return Node("Ident", text=t.text, lower=t.text.lower(), span=sp)
        if t.kind == "Word" and t.number:
            n = t.number
            if n.error:
                self.diag("error", "number-error", "%s: %s" % (t.text, n.error), sp)
            return Node("NumberLit", text=t.text, mantissa=n.mantissa,
                        exponent=n.exponent, scale=n.scale, tail=n.tail, value=n.value, span=sp)
        return self.ident(ll, t)

    @staticmethod
    def simple(t: Token):
        """A token that can stand alone as a value in an expression context."""
        if t.kind in ("Braced", "Quoted", "DQuoted"):
            return True
        if t.kind != "Word":
            return False
        if t.number:
            return not (set(t.number.tail) & OPERATOR_CHARS)
        return re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.!#$%\[\]]*", t.text) is not None

    def group_value(self, ll, toks, expr_ctx):
        if len(toks) == 1 and (not expr_ctx or self.simple(toks[0])):
            return self.value(ll, toks[0])
        raw = ll.text[toks[0].start:toks[-1].end]
        return Node("Expr", form="bare", raw=raw, span=self.span(ll, toks[0].start, toks[-1].end))

    # ---- parameters -------------------------------------------------------
    def params(self, ll, toks, i, letter=None, expr_ctx=False, skip=()) -> List[Node]:
        out = []
        n = len(toks)
        while i < n:
            t = toks[i]
            if t.kind in SEP_KINDS:
                i += 1
                continue
            if t.kind != "Word":
                raise _Fail("unexpected %s %r where a parameter name was expected" % (t.kind, t.text))
            low = t.text.lower()
            if i + 1 < n and toks[i + 1].kind == "Equals":
                j = i + 2
                depth, group, groups = 0, [], []
                ex = expr_ctx or (letter, low) in EXPR_KEYS
                if not ex:
                    # one token, or tokens joined by commas (ic=0.6,5.0)
                    while j < n:
                        groups.append([toks[j]])
                        j += 1
                        if j < n and toks[j].kind == "Comma" and j + 1 < n:
                            j += 1
                            continue
                        break
                while ex and j < n:
                    u = toks[j]
                    if depth == 0 and u.kind == "Word" and j + 1 < n and toks[j + 1].kind == "Equals":
                        break
                    if u.kind == "LParen":
                        depth += 1
                    elif u.kind == "RParen":
                        depth -= 1
                    if depth == 0 and u.kind == "Comma":
                        groups.append(group)
                        group = []
                    else:
                        group.append(u)
                    j += 1
                if ex:
                    groups.append(group)
                groups = [g for g in groups if g]
                vals = [self.group_value(ll, g, ex) for g in groups]
                end = toks[j - 1].end if j - 1 > i + 1 else toks[i + 1].end
                out.append(Node("Param", name=self.ident(ll, t), value=vals[0] if vals else None,
                                more=vals[1:] or None, has_equals=True, span=self.span(ll, t.start, end)))
                i = j
            else:
                if low not in skip:
                    out.append(Node("Param", name=self.ident(ll, t), has_equals=False,
                                    span=self.span(ll, t.start, t.end)))
                i += 1
        return out

    # ---- elements ----------------------------------------------------------
    def element(self, ll, toks):
        name_t = toks[0]
        letter = name_t.text[0].upper()
        nnodes, flags = ELEMENTS.get(letter, (0, ()))
        if self.d.name == "spice3" and letter in NOT_IN_SPICE3_ELEM:
            self.diag("warning", "dialect-extension", "element %s is not in SPICE3" % letter,
                      self.span(ll, name_t.start, name_t.end))
        i, n = 1, len(toks)
        nodes = []
        while len(nodes) < nnodes:
            while i < n and toks[i].kind in SEP_KINDS:
                i += 1
            if i >= n or toks[i].kind != "Word":
                raise _Fail("too few nodes: %s needs %d" % (letter, nnodes))
            nodes.append(self.ident(ll, toks[i]))
            i += 1
        fields = dict(letter=letter, name=self.ident(ll, name_t), nodes=nodes)
        marker = False
        source = poly = None
        rest: List[Node] = []
        if letter in "VI":
            source, i = self.source_spec(ll, toks, i)
        else:
            if letter in "EGFH":
                j = i
                while j < n and toks[j].kind in SEP_KINDS:
                    j += 1
                if j < n and toks[j].kind == "Word" and toks[j].text.lower() == "poly":
                    j += 1
                    while j < n and toks[j].kind in SEP_KINDS:
                        j += 1
                    dim = self.value(ll, toks[j]) if j < n else None
                    i = j + 1
                    items = []
                    while i < n and not (toks[i].kind == "Word" and i + 1 < n and toks[i + 1].kind == "Equals"):
                        if toks[i].kind not in SEP_KINDS:
                            items.append(self.value(ll, toks[i]))
                        i += 1
                    poly = Node("Poly", dim=dim, items=items)
            if poly is None:
                while i < n:
                    t = toks[i]
                    if t.kind in SEP_KINDS:
                        i += 1
                        continue
                    if t.kind == "Word" and i + 1 < n and toks[i + 1].kind == "Equals":
                        break
                    if t.kind == "Word" and t.text.lower() in flags:
                        break
                    if t.kind == "Word" and t.text.lower() == "params:":
                        marker = True
                        i += 1
                        break
                    if t.kind == "Equals":
                        raise _Fail("stray '='")
                    rest.append(self.value(ll, t))
                    i += 1
        params = self.params(ll, toks, i, letter=letter, skip=("params:",))
        value_keys = {"R": ("r",), "C": ("c", "q"), "L": ("l",)}.get(letter, ())
        if letter in "RCL" and not rest and not any(
                p.name.lower in value_keys and p.value is not None for p in params):
            raise _Fail("%s needs a value or model" % {"R": "resistor", "C": "capacitor", "L": "inductor"}[letter])
        fields.update(rest=rest, params=params)
        if source is not None:
            fields["source"] = source
        if poly is not None:
            fields["poly"] = poly
        if marker:
            fields["params_marker"] = True
        fields["span"] = self.span(ll, name_t.start, toks[-1].end)
        return Node("Element", **fields)

    def source_spec(self, ll, toks, i):
        n = len(toks)
        spec = dict(has_dc_keyword=False)
        start = i

        def skipsep():
            nonlocal i
            while i < n and toks[i].kind in SEP_KINDS + ("Equals",):
                i += 1

        def optvalue():
            nonlocal i
            skipsep()
            if i < n and (toks[i].kind in ("Braced", "Quoted") or (toks[i].kind == "Word" and toks[i].number)):
                v = self.value(ll, toks[i])
                i += 1
                return v
            return None

        while True:
            skipsep()
            if i >= n:
                break
            t = toks[i]
            low = t.text.lower() if t.kind == "Word" else ""
            if low == "dc":
                spec["has_dc_keyword"] = True
                i += 1
                skipsep()
                if i < n:
                    spec["dc"] = self.value(ll, toks[i])
                    i += 1
            elif low in ("ac", "distof1", "distof2"):
                i += 1
                mag = optvalue()
                ph = optvalue() if mag is not None else None
                spec[low] = Node("Phasor", mag=mag, phase=ph)
            elif t.kind == "Word" and not t.number and not (i + 1 < n and toks[i + 1].kind == "Equals"):
                # a source function: any word in this position
                if self.d.name == "spice3" and low in ("am", "trnoise", "trrandom", "external"):
                    self.diag("warning", "dialect-extension", "source function %s is not in SPICE3" % t.text,
                              self.span(ll, t.start, t.end))
                paren = i + 1 < n and toks[i + 1].kind == "LParen"
                i += 1
                args, fparams = [], []
                depth = 1 if paren else 0
                if paren:
                    i += 1
                while i < n:
                    u = toks[i]
                    if u.kind == "LParen":
                        depth += 1
                        i += 1
                        continue
                    if u.kind == "RParen":
                        depth -= 1
                        i += 1
                        if paren and depth == 0:
                            break
                        continue
                    if u.kind == "Comma":
                        i += 1
                        continue
                    if u.kind == "Word" and u.text.lower() in SOURCE_KEYWORDS and not paren:
                        break
                    if u.kind == "Word" and i + 1 < n and toks[i + 1].kind == "Equals":
                        fparams += self.params(ll, toks, i)
                        i = n
                        break
                    args.append(self.value(ll, u))
                    i += 1
                if paren and i < n:       # keyword parameters may follow the parenthesis (pwl r= td=)
                    j = i
                    while j < n and toks[j].kind in SEP_KINDS:
                        j += 1
                    if j < n and toks[j].kind == "Word" and j + 1 < n and toks[j + 1].kind == "Equals":
                        fparams += self.params(ll, toks, j)
                        i = n
                spec["function"] = Node("SourceFunction", name=self.ident(ll, t), args=args,
                                        params=fparams, has_parens=paren)
            elif "dc" not in spec and not spec["has_dc_keyword"] and (t.kind in ("Braced", "Quoted") or t.number or t.kind == "Word"):
                spec["dc"] = self.value(ll, t)
                i += 1
            else:
                raise _Fail("unexpected %r in source specification" % t.text)
        return Node("SourceSpec", **spec), i

    # ---- dot cards ---------------------------------------------------------
    def outref(self, ll, toks, i):
        n = len(toks)
        if i < n and toks[i].kind == "Word" and toks[i].text.lower() in ("v", "i") \
                and i + 1 < n and toks[i + 1].kind == "LParen":
            k = toks[i].text.lower()
            j = i + 2
            args = []
            while j < n and toks[j].kind != "RParen":
                if toks[j].kind == "Word":
                    args.append(self.ident(ll, toks[j]))
                j += 1
            end = toks[j].end if j < n else toks[-1].end
            return Node("OutputRef", ref_kind=k, args=args, span=self.span(ll, toks[i].start, end)), j + 1
        raise _Fail("expected v(...) or i(...)")

    def words(self, ll, toks, i):
        return [t for t in toks[i:] if t.kind not in SEP_KINDS]

    def sweep(self, ll, ws):
        if len(ws) < 4 or ws[0].text.lower() not in ("dec", "oct", "lin"):
            raise _Fail("expected dec|oct|lin points fstart fstop")
        return Node("Sweep", variation=ws[0].text.lower(), points=self.value(ll, ws[1]),
                    fstart=self.value(ll, ws[2]), fstop=self.value(ll, ws[3]))

    def dot(self, ll, toks, st):
        t0 = toks[0]
        name = t0.text[1:].lower()
        sp = lambda: self.span(ll, t0.start, toks[-1].end)
        n = len(toks)
        if self.d.name == "spice3" and name in NOT_IN_SPICE3_DOT:
            self.diag("warning", "dialect-extension", ".%s is not in SPICE3" % name, sp())
        ws = self.words(ll, toks, 1)

        if name == "model":
            if len(ws) < 2:
                raise _Fail(".model needs a name and a type")
            return Node("Model", name=self.ident(ll, ws[0]), type=self.ident(ll, ws[1]),
                        params=self.params(ll, toks, toks.index(ws[1]) + 1), span=sp())
        if name == "subckt":
            if not ws:
                raise _Fail(".subckt needs a name")
            ports, i, marker = [], toks.index(ws[0]) + 1, False
            while i < n:
                u = toks[i]
                if u.kind in SEP_KINDS:
                    i += 1
                    continue
                if u.kind == "Word" and u.text.lower() == "params:":
                    marker = True
                    i += 1
                    break
                if u.kind == "Word" and i + 1 < n and toks[i + 1].kind == "Equals":
                    break
                ports.append(self.ident(ll, u))
                i += 1
            f = dict(name=self.ident(ll, ws[0]), ports=ports,
                     params=self.params(ll, toks, i, skip=("params:",)), items=[], span=sp())
            if marker:
                f["params_marker"] = True
            return Node("Subckt", **f)
        if name in ("param", "csparam"):
            return Node("ParamCard" if name == "param" else "Csparam",
                        assignments=self.params(ll, toks, 1, expr_ctx=True), span=sp())
        if name == "func":
            if not ws:
                raise _Fail(".func needs a name")
            i = toks.index(ws[0]) + 1
            args = []
            if i < n and toks[i].kind == "LParen":
                i += 1
                while i < n and toks[i].kind != "RParen":
                    if toks[i].kind == "Word":
                        args.append(self.ident(ll, toks[i]))
                    i += 1
                i += 1
            body = toks[i:]
            if not body:
                raise _Fail(".func needs a body")
            return Node("Func", name=self.ident(ll, ws[0]), args=args,
                        body=self.group_value(ll, body, True), span=sp())
        if name == "global":
            return Node("Global", nodes=[self.ident(ll, w) for w in ws], span=sp())
        if name == "temp":
            if not ws:
                raise _Fail(".temp needs a value")
            return Node("Temp", value=self.value(ll, ws[0]), span=sp())
        if name == "include":
            if len(toks) < 2:
                raise _Fail(".include needs a file name")
            t = toks[1]
            form = {"DQuoted": "double_quoted", "Quoted": "quoted"}.get(t.kind, "bare")
            path = t.text[1:-1] if t.kind in ("DQuoted", "Quoted") else t.text
            return Node("Include", path=path, form=form, span=sp())
        if name == "lib":
            if len(ws) == 1:
                return Node("LibDef", name=self.ident(ll, ws[0]), items=[], span=sp())
            if len(ws) >= 2:
                t = toks[1]
                form = {"DQuoted": "double_quoted", "Quoted": "quoted"}.get(t.kind, "bare")
                path = t.text[1:-1] if t.kind in ("DQuoted", "Quoted") else t.text
                return Node("LibUse", path=path, form=form, section=self.ident(ll, ws[1]), span=sp())
            raise _Fail(".lib needs a library name or a file and a section")
        if name in ("if", "elseif"):
            raw = ll.text[toks[1].start:].strip() if n > 1 else ""
            if not raw:
                raise _Fail(".%s needs a condition" % name)
            return Node("IfBranch", cond=Node("Expr", form="bare", raw=raw,
                                              span=self.span(ll, toks[1].start, toks[-1].end)),
                        items=[], span=sp())
        if name == "op":
            return Node("Op", span=sp())
        if name == "dc":
            if len(ws) < 4 or len(ws) % 4:
                raise _Fail(".dc needs groups of: source start stop step")
            sweeps = [Node("DcSweep", source=self.ident(ll, ws[k]), start=self.value(ll, ws[k + 1]),
                           stop=self.value(ll, ws[k + 2]), step=self.value(ll, ws[k + 3]))
                      for k in range(0, len(ws), 4)]
            return Node("Dc", sweeps=sweeps, span=sp())
        if name == "ac":
            return Node("Ac", sweep=self.sweep(ll, ws), span=sp())
        if name == "tran":
            uic = any(w.text.lower() == "uic" for w in ws)
            vals = [w for w in ws if w.text.lower() != "uic"]
            if len(vals) < 2:
                raise _Fail(".tran needs tstep and tstop")
            f = dict(tstep=self.value(ll, vals[0]), tstop=self.value(ll, vals[1]))
            if len(vals) > 2:
                f["tstart"] = self.value(ll, vals[2])
            if len(vals) > 3:
                f["tmax"] = self.value(ll, vals[3])
            return Node("Tran", uic=uic, span=sp(), **f)
        if name == "noise":
            out, i = self.outref(ll, toks, 1)
            rest = self.words(ll, toks, i)
            ref = None
            if len(out.args) == 2:
                out, ref = Node("OutputRef", ref_kind=out.ref_kind, args=out.args[:1], span=out.span), out.args[1]
            if len(rest) < 5:
                raise _Fail(".noise needs source and sweep")
            f = dict(output=out, reference=ref, source=self.ident(ll, rest[0]), sweep=self.sweep(ll, rest[1:5]))
            if len(rest) > 5:
                f["points_per_summary"] = self.value(ll, rest[5])
            return Node("Noise", span=sp(), **f)
        if name == "tf":
            out, i = self.outref(ll, toks, 1)
            rest = self.words(ll, toks, i)
            if not rest:
                raise _Fail(".tf needs a source")
            return Node("Tf", output=out, source=self.ident(ll, rest[0]), span=sp())
        if name == "pz":
            if len(ws) < 6:
                raise _Fail(".pz needs four nodes, cur|vol and pol|zer|pz")
            return Node("Pz", nodes=[self.ident(ll, w) for w in ws[:4]], pz_kind=ws[4].text.lower(),
                        mode=ws[5].text.lower(), span=sp())
        if name == "sens":
            out, i = self.outref(ll, toks, 1)
            rest = self.words(ll, toks, i)
            f = dict(output=out)
            if rest and rest[0].text.lower() == "ac":
                f["ac"] = self.sweep(ll, rest[1:5])
            return Node("Sens", span=sp(), **f)
        if name == "disto":
            f = dict(sweep=self.sweep(ll, ws))
            if len(ws) > 4:
                f["f2overf1"] = self.value(ll, ws[4])
            return Node("Disto", span=sp(), **f)
        if name in ("ic", "nodeset"):
            items, allv, i = [], None, 1
            while i < n:
                if toks[i].kind in SEP_KINDS:
                    i += 1
                    continue
                if toks[i].kind == "Word" and toks[i].text.lower() == "all" and i + 2 < n and toks[i + 1].kind == "Equals":
                    allv = self.value(ll, toks[i + 2])
                    i += 3
                    continue
                tgt, i = self.outref(ll, toks, i)
                if i + 1 >= n or toks[i].kind != "Equals":
                    raise _Fail("expected '=' and a value after v(...)")
                items.append(Node("Assignment", target=tgt, value=self.value(ll, toks[i + 1])))
                i += 2
            if name == "ic":
                return Node("Ic", items=items, span=sp())
            return Node("Nodeset", all=allv, items=items, span=sp())
        if name == "options" or name == "option":
            return Node("Options", items=self.params(ll, toks, 1), span=sp())
        return Node("OtherDot", name=name, words=[self.value(ll, w) for w in ws],
                    raw=ll.text, span=sp())

    # ---- deck ----------------------------------------------------------------
    def parse_lines(self, lines: List[LogicalLine]):
        top: List[Node] = []
        stack: List[dict] = []       # open blocks: {"kind", "node", "items"}
        end_span = None
        control: Optional[List[str]] = None
        control_head = None

        def cur():
            if stack:
                fr = stack[-1]
                return fr["items"]
            return top

        for ll in lines:
            toks = tokenize(ll, self.d)
            if not toks:
                continue
            for t in toks:
                if t.kind == "Unterminated":
                    self.diag("error", "unterminated", "unterminated %r" % t.text,
                              self.span(ll, t.start, t.end))
            t0 = toks[0]
            low = t0.text.lower() if t0.kind == "Word" else ""
            if control is not None:
                if low == ".endc":
                    cur().append(Node("OtherDot", name="control", words=[], raw="\n".join(control),
                                      span=control_head))
                    control = None
                else:
                    control.append(ll.text)
                continue
            if low == ".control":
                control, control_head = [], self.span(ll, t0.start, toks[-1].end)
                continue
            if low == ".end":
                end_span = self.span(ll, t0.start, toks[-1].end)
                break
            try:
                if t0.kind != "Word":
                    raise _Fail("a card must start with a name or a dot command")
                if low.startswith("."):
                    # block ends
                    if low == ".ends":
                        ws = self.words(ll, toks, 1)
                        fr = next((s for s in reversed(stack) if s["kind"] == "subckt"), None)
                        if fr is None:
                            raise _Fail(".ends without .subckt")
                        while stack[-1] is not fr:
                            stack.pop()
                            self.diag("error", "unclosed-block", "block closed by .ends", self.span(ll, t0.start, t0.end))
                        stack.pop()
                        if ws:
                            fr["node"].f["ends_name"] = self.ident(ll, ws[0])
                        continue
                    if low == ".endl":
                        fr = next((s for s in reversed(stack) if s["kind"] == "lib"), None)
                        if fr is None:
                            raise _Fail(".endl without .lib")
                        while stack[-1] is not fr:
                            stack.pop()
                        stack.pop()
                        continue
                    if low in (".else", ".elseif", ".endif"):
                        fr = stack[-1] if stack and stack[-1]["kind"] == "if" else None
                        if fr is None:
                            raise _Fail("%s without .if" % low)
                        if low == ".endif":
                            stack.pop()
                            continue
                        if low == ".elseif":
                            br = self.dot(ll, toks, stack)
                        else:
                            br = Node("IfBranch", cond=None, items=[], span=self.span(ll, t0.start, toks[-1].end))
                        fr["node"].f["branches"].append(br)
                        fr["items"] = br.f["items"]
                        continue
                    item = self.dot(ll, toks, stack)
                    cur().append(item)
                    if item.kind == "Subckt":
                        stack.append({"kind": "subckt", "node": item, "items": item.f["items"]})
                    elif item.kind == "LibDef":
                        stack.append({"kind": "lib", "node": item, "items": item.f["items"]})
                    elif item.kind == "IfBranch":     # .if opens an If with its first branch
                        ifn = Node("If", branches=[item], span=item.span)
                        cur().pop()
                        cur().append(ifn)
                        stack.append({"kind": "if", "node": ifn, "items": item.f["items"]})
                else:
                    cur().append(self.element(ll, toks))
            except _Fail as e:
                sev = "warning" if self.d.name == "ngspice" else "error"
                sp = self.span(ll, t0.start, toks[-1].end)
                cur().append(Node("Invalid", raw=ll.text, reason=e.reason, severity=sev, span=sp))
                self.diag(sev, "invalid-line", e.reason, sp)
        for fr in stack:
            self.diag("error", "unclosed-block", "%s not closed" % fr["kind"], fr["node"].span)
        if control is not None:
            self.diag("error", "unclosed-block", ".control not closed", control_head)
        return top, end_span


def parse(data, file="<input>", dialect: Dialect = NGSPICE, loader: Optional[Callable[[str], str]] = None):
    """Parse a deck. `loader` is only used by pass 1 if you want includes
    inlined into the line stream; leave it None to get Include nodes."""
    r = pass1(data, file, dialect, loader)
    p = Parser(dialect, file)
    items, end = p.parse_lines(r.lines)
    diags = []
    for g in r.diagnostics:
        if g.code == "missing-end" and end is not None:
            continue
        diags.append(Node("Diagnostic", severity=g.severity, code=g.code, message=g.message,
                          span=Span(g.file, g.line, 1, g.line, 1)))
    diags += p.diags
    return Node("Deck", dialect=dialect.name, title=r.title, items=items, end=end, diagnostics=diags)
