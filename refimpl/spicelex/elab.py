"""Reference elaboration: Deck AST -> flat Netlist (grammar/08-elaboration.md).

Naming of flattened devices, nodes and models follows what ngspice 42 prints
(`r.x1.r1`, `x1.m`, `x1:dm`); the spec treats names as implementation
policy. The ngspice quirk for subcircuits *defined inside* another
subcircuit (`r.x9.r.x1.r1`) is not reproduced.
"""
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from .ast import Node
from .dialect import NGSPICE, Dialect
from .expr import Env, ExprError, evaluate, parse_expr
from .parser import parse

MAX_DEPTH = 64
RUNTIME_DOT = {"control"}


@dataclass
class EVal:
    kind: str                 # "num", "name", "expr" (run-time, left as text)
    text: Optional[str] = None
    value: Optional[float] = None
    computed: bool = False    # produced by evaluating a parameter or expression


@dataclass
class EParam:
    name: str
    value: Optional[EVal]
    more: List[EVal] = field(default_factory=list)


@dataclass
class EItem:
    kind: str                 # "element", "model", "directive"
    name: str = ""
    letter: str = ""
    nodes: List[str] = field(default_factory=list)
    rest: List[EVal] = field(default_factory=list)
    params: List[EParam] = field(default_factory=list)
    source: Optional[dict] = None
    poly: Optional[dict] = None
    model_type: str = ""
    node: Optional[Node] = None    # the AST node, for directives
    origin: str = ""               # instance path it came from


@dataclass
class Netlist:
    title: str
    items: List[EItem]
    diagnostics: List[Node]
    params: Dict[str, float]


class Scope:
    def __init__(self, parent=None):
        self.vars: Dict[str, float] = {}
        self.parent = parent

    def get(self, name):
        s = self
        while s is not None:
            if name in s.vars:
                return s.vars[name]
            s = s.parent
        return None


class Frame:
    """One level of hierarchy: the top deck or one subcircuit instance."""

    def __init__(self, path, scope, parent=None, portmap=None):
        self.path: List[str] = path
        self.scope: Scope = scope
        self.parent: Optional[Frame] = parent
        self.portmap: Optional[Dict[str, str]] = portmap
        self.defs: Dict[str, Node] = {}           # subcircuits and libs defined at this level
        self.models: Dict[str, str] = {}          # local model name -> flat name
        self.names: set = set()                   # instance names used at this level

    def prefix(self):
        return ".".join(self.path)


class Elaborator:
    def __init__(self, dialect: Dialect = NGSPICE, loader: Optional[Callable[[str], str]] = None):
        self.d = dialect
        self.loader = loader
        self.items: List[EItem] = []
        self.diags: List[Node] = []
        self.funcs: Dict[str, tuple] = {}
        self.globals = {"0"}
        self.flat_names: set = set()
        self.calls: List[str] = []

    # ---- diagnostics ----------------------------------------------------------
    def err(self, code, msg, node=None, severity="error"):
        self.diags.append(Node("Diagnostic", severity=severity, code=code, message=msg,
                               span=getattr(node, "span", None) if node is not None else None))

    # ---- evaluation -----------------------------------------------------------
    def env(self, frame):
        return Env(frame.scope.get, self.funcs, self.d)

    def eval_text(self, raw, frame):
        return evaluate(parse_expr(raw, self.d), self.env(frame))

    def ev(self, v: Node, frame: Frame, expr_ctx=False) -> EVal:
        """Value node -> EVal. Braced and quoted expressions are evaluated now;
        bare ones are left for the analysis unless `expr_ctx`."""
        k = v.kind
        if k == "NumberLit":
            return EVal("num", v.text, v.value)
        if k == "Expr":
            if v.form == "bare" and not expr_ctx:
                return EVal("expr", v.raw)
            return EVal("num", None, self.eval_text(v.raw, frame), True)
        low = v.text.lower()
        if low in frame.models:
            return EVal("name", frame.models[low])
        val = frame.scope.get(low)
        if val is not None:
            return EVal("num", None, val, True)
        return EVal("name", low)

    def ev_safe(self, v, frame, expr_ctx=False):
        try:
            return self.ev(v, frame, expr_ctx)
        except ExprError as e:
            self.err("expression", str(e), v)
            return EVal("name", getattr(v, "raw", None) or getattr(v, "text", "?"))

    def eparams(self, params, frame, expr_ctx=False):
        out = []
        for p in params:
            out.append(EParam(p.name.lower,
                              self.ev_safe(p.value, frame, expr_ctx) if p.value is not None else None,
                              [self.ev_safe(m, frame, expr_ctx) for m in (p.get("more") or [])]))
        return out

    # ---- names ----------------------------------------------------------------
    def node(self, name: str, frame: Frame) -> str:
        n = name.lower()
        if frame.portmap is None:
            return n
        if n in frame.portmap:
            return frame.portmap[n]
        if n in self.globals or n == "gnd":
            return n
        return frame.prefix() + "." + n

    def device(self, name: str, frame: Frame) -> str:
        n = name.lower()
        if not frame.path:
            return n
        return n[0] + "." + frame.prefix() + "." + n

    # ---- the walk -------------------------------------------------------------
    def register(self, items, frame):
        for it in items:
            if it.kind == "Subckt":
                frame.defs[it.name.lower] = it
            elif it.kind == "LibDef":
                frame.defs["lib:" + it.name.lower] = it
            elif it.kind == "Global":
                for n in it.nodes:
                    self.globals.add(n.lower)

    def run(self, items, frame):
        self.register(items, frame)
        for it in items:
            try:
                self.item(it, frame)
            except ExprError as e:
                self.err("expression", str(e), it)

    def item(self, it, frame):
        k = it.kind
        if k in ("Subckt", "LibDef", "Global", "Invalid"):
            return
        if k in ("ParamCard", "Csparam"):
            for a in it.assignments:
                if a.value is None:
                    continue
                try:
                    frame.scope.vars[a.name.lower] = self.ev_value_number(a.value, frame)
                except ExprError as e:
                    self.err("expression", "%s: %s" % (a.name.text, e), a)
            return
        if k == "Func":
            body = parse_expr(it.body.raw if it.body.kind == "Expr" else it.body.text, self.d)
            self.funcs[it.name.lower] = ([a.lower for a in it.args], body, frame.scope.get)
            return
        if k == "If":
            for br in it.branches:
                if br.cond is None or self.eval_text(br.cond.raw, frame):
                    self.run(br.items, frame)
                    break
            return
        if k == "Include":
            self.include(it.path, None, frame, it)
            return
        if k == "LibUse":
            self.include(it.path, it.section.lower, frame, it)
            return
        if k == "Model":
            self.model(it, frame)
            return
        if k == "Element":
            self.element(it, frame)
            return
        if k == "OtherDot" and it.name in RUNTIME_DOT:
            return
        if not frame.path:
            self.items.append(EItem("directive", name=getattr(it, "name", None) and str(it.name) or it.kind.lower(),
                                    node=it))

    def ev_value_number(self, v, frame):
        r = self.ev(v, frame, expr_ctx=True)
        if r.value is None:
            raise ExprError("%s is not a number" % (r.text,))
        return r.value

    def include(self, path, section, frame, node):
        if self.loader is None:
            self.err("include", "no loader to read %s" % path, node)
            return
        try:
            text = self.loader(path)
        except OSError as e:
            self.err("include", "%s: %s" % (path, e), node)
            return
        deck = parse(text, path, self.d, None, has_title=False)
        items = deck.items
        if section is not None:
            lib = next((i for i in items if i.kind == "LibDef" and i.name.lower == section), None)
            if lib is None:
                self.err("include", "no library section %s in %s" % (section, path), node)
                return
            items = lib.items
        self.run(items, frame)

    def model(self, it, frame):
        name = it.name.lower
        flat = name
        if frame.path:
            flat = frame.prefix() + ":" + name
            frame.models[name] = flat
        self.items.append(EItem("model", name=flat, model_type=it.type.lower,
                                params=self.eparams(it.params, frame), origin=frame.prefix()))

    def element(self, it, frame):
        if it.letter == "X":
            self.call(it, frame)
            return
        name = self.device(it.name.text, frame)
        if name in self.flat_names:
            self.err("duplicate-name", "duplicate instance name %s" % name, it)
            return
        self.flat_names.add(name)
        e = EItem("element", name=name, letter=it.letter,
                  nodes=[self.node(n.text, frame) for n in it.nodes], origin=frame.prefix())
        rest = []
        for idx, v in enumerate(it.rest):
            if (it.letter in "FHW" and idx == 0) or (it.letter == "K" and idx < 2):
                rest.append(EVal("name", self.device(v.text, frame)))
            else:
                rest.append(self.ev_safe(v, frame))
        e.rest = rest
        e.params = self.eparams(it.params, frame)
        if it.get("source") is not None:
            s = it.source
            e.source = {"has_dc_keyword": s.has_dc_keyword}
            for key in ("dc",):
                if s.get(key) is not None:
                    e.source[key] = self.ev_safe(s.get(key), frame)
            for key in ("ac", "distof1", "distof2"):
                ph = s.get(key)
                if ph is not None:
                    e.source[key] = (self.ev_safe(ph.mag, frame) if ph.mag is not None else None,
                                     self.ev_safe(ph.phase, frame) if ph.phase is not None else None)
            fn = s.get("function")
            if fn is not None:
                e.source["function"] = {"name": fn.name.lower,
                                        "args": [self.ev_safe(a, frame) for a in fn.args],
                                        "params": self.eparams(fn.params, frame),
                                        "has_parens": fn.has_parens}
        if it.get("poly") is not None:
            e.poly = {"dim": self.ev_safe(it.poly.dim, frame),
                      "items": [self.ev_safe(v, frame) for v in it.poly.items]}
        self.items.append(e)

    def call(self, it, frame):
        words = it.rest
        if not words:
            self.err("subckt-call", "subcircuit call with no subcircuit name", it)
            return
        sub_name = words[-1].text.lower() if hasattr(words[-1], "text") else str(words[-1].raw).lower()
        args = [w.text for w in words[:-1]]
        inst = it.name.text.lower()
        if inst in frame.names:
            self.err("duplicate-name", "duplicate instance name %s" % inst, it)
            return
        frame.names.add(inst)
        d = None
        f = frame
        while f is not None and d is None:
            d = f.defs.get(sub_name)
            f = f.parent
        if d is None:
            self.err("unknown-subckt", "no subcircuit named %s" % sub_name, it)
            return
        if len(args) != len(d.ports):
            self.err("port-count", "%s has %d ports, called with %d" % (sub_name, len(d.ports), len(args)), it)
            return
        if len(self.calls) >= MAX_DEPTH:
            self.err("depth", "subcircuit nesting deeper than %d" % MAX_DEPTH, it)
            return
        if sub_name in self.calls:
            self.err("recursion", "subcircuit %s calls itself" % sub_name, it)
            return
        scope = Scope(frame.scope)
        given = {}
        for p in it.params:
            if p.value is not None:
                try:
                    given[p.name.lower] = self.ev_value_number(p.value, frame)
                except ExprError as e:
                    self.err("expression", "%s: %s" % (p.name.text, e), p)
        child = Frame(frame.path + [inst], scope, frame,
                      {x.lower(): self.node(a, frame) for x, a in zip((x.text for x in d.ports), args)})
        for p in d.params:
            if p.value is None:
                continue
            n = p.name.lower
            try:
                scope.vars[n] = given[n] if n in given else self.ev_value_number(p.value, child)
            except ExprError as e:
                self.err("expression", "%s: %s" % (p.name.text, e), p)
        for n, v in given.items():
            scope.vars.setdefault(n, v)
        self.calls.append(sub_name)
        try:
            self.run(d.items, child)
        finally:
            self.calls.pop()


def elaborate(deck: Node, dialect: Dialect = NGSPICE, loader: Optional[Callable[[str], str]] = None) -> Netlist:
    el = Elaborator(dialect, loader)
    top = Frame([], Scope())
    el.run(deck.items, top)
    return Netlist(deck.title, el.items, el.diags, dict(top.scope.vars))


# ---- text form, in the style of ngspice's `listing expand` (for tests) ------------

def _val(v: EVal) -> str:
    if v is None:
        return ""
    if v.kind == "num":
        return ("%.15e" % v.value) if v.computed else v.text.lower()
    return (v.text or "").lower()


def _param(p: EParam) -> str:
    if p.value is None:
        return p.name
    return "%s=%s" % (p.name, ",".join([_val(p.value)] + [_val(m) for m in p.more]))


def render(nl: Netlist) -> List[str]:
    out = [nl.title.lower()]
    for it in nl.items:
        if it.kind == "model":
            ps = " ".join(_param(p) for p in it.params)
            out.append(".model %s %s%s" % (it.name, it.model_type, "(%s)" % ps if ps else ""))
        elif it.kind == "element":
            parts = [it.name] + it.nodes
            if it.source is not None:
                s = it.source
                if "dc" in s:
                    parts += (["dc"] if s["has_dc_keyword"] else []) + [_val(s["dc"])]
                for key in ("ac", "distof1", "distof2"):
                    if key in s:
                        parts += [key] + [_val(x) for x in s[key] if x is not None]
                if "function" in s:
                    f = s["function"]
                    parts.append("%s(%s)" % (f["name"], " ".join(_val(a) for a in f["args"])))
            if it.poly:
                parts += ["poly(%s)" % _val(it.poly["dim"])] + [_val(v) for v in it.poly["items"]]
            parts += [_val(v) for v in it.rest] + [_param(p) for p in it.params]
            out.append(" ".join(parts))
        else:
            out.append(".%s" % it.name)
    out.append(".end")
    return out
