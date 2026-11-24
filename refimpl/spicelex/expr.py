"""Expression parser and evaluator (grammar/05-expressions.md).

Everything below was measured on ngspice 42 with tools/diff_exprs.py; the
manual's operator table is not followed where it disagrees.

* Arithmetic is IEEE: 4/0 is infinity and 7==4/0 is 0. An error is reported
  only if the *final* value is not a finite number.
* Binary operators are left-associative, including ** and ^ (2^3^2 is 64).
  ** and ^ compute |x| to the power y ((-2)**3 is 8); pow() is C pow().
  \\ is trunc(|a|/|b|), a real division with both signs dropped ((-7)\\2 is
  3); % is fmod on real numbers (the sign of the dividend), computed as
  a - trunc(a/b)*b, so an infinite divisor is an error.
* Unary minus at the start of an expression, after ( , ? or :, is an operator
  that binds looser than power but tighter than * and +: -2**2 is -4.
* After a binary operator, a minus is accepted only directly before a number
  and then belongs to the number: 2*-2**2 is 8. Anything else there
  (2*-(3), 2+-sin(1)) is rejected by ngspice and is `Unsupported` here.
* A unary + is allowed only at the start of an expression, after ( or ,.
* ! binds tighter than ** (!1**0 is (!1)**0); its operand cannot start with - or +.
* Not modelled (`Unsupported`): `--2**2` (ngspice: -4), `2*--2` (-4),
  a minus after ? or : before anything but a number (`1?-(2):3` gives 2).
"""
import math
import re
from typing import Callable, Dict, List, Optional

from .ast import Node
from .dialect import Dialect
from .numbers import number


class ExprError(Exception):
    pass


class Unsupported(ExprError):
    """Syntax whose ngspice behavior is not explained by the rules above."""


_NUM = re.compile(r"(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?[A-Za-z_]*")
_ID = re.compile(r"[A-Za-z_][A-Za-z0-9_.]*")
_OPS = ["**", "==", "!=", "<>", "<=", ">=", "&&", "||"] + list("+-*/%\\^<>!?:(),")
_WORD_OPS = {"and": "&&", "or": "||", "not": "!", "div": "\\", "mod": "%"}
RUNTIME_NAMES = {"time", "temper", "hertz"}


def strip_delims(raw: str) -> str:
    raw = raw.strip()
    if len(raw) >= 2 and ((raw[0] == "{" and raw[-1] == "}") or (raw[0] == "'" and raw[-1] == "'")):
        return raw[1:-1]
    return raw


def tokenize(src: str, d: Dialect):
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c in " \t":
            i += 1
            continue
        m = _NUM.match(src, i) if (c.isdigit() or (c == "." and i + 1 < n and src[i + 1].isdigit())) else None
        if m:
            info = number(m.group(0), d)
            if info is None or info.error:
                raise ExprError("bad number %r" % m.group(0))
            out.append(("num", info.value, m.group(0)))
            i = m.end()
            continue
        m = _ID.match(src, i)
        if m:
            w = m.group(0)
            low = w.lower()
            out.append(("op", _WORD_OPS[low], w) if low in _WORD_OPS else ("id", low, w))
            i = m.end()
            continue
        for op in _OPS:
            if src.startswith(op, i):
                out.append(("op", op, op))
                i += len(op)
                break
        else:
            raise ExprError("unexpected character %r" % c)
    return out


class _P:
    def __init__(self, toks):
        self.t, self.i = toks, 0
        # token indices where an expression may begin
        self.starts = {0}
        self.plus_ok = {0}
        for j, (k, v, _) in enumerate(toks[:-1]):
            if k == "op" and v in ("(", ",", "?", ":"):
                self.starts.add(j + 1)
            if k == "op" and v in ("(", ","):
                self.plus_ok.add(j + 1)

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None, None)

    def eat(self, op=None):
        k, v, _ = self.peek()
        if k == "op" and (op is None or v == op):
            self.i += 1
            return True
        return False

    def expect(self, op):
        if not self.eat(op):
            raise ExprError("expected %r" % op)

    def expr(self):
        return self.ternary()

    def ternary(self):
        c = self.oror()
        if self.eat("?"):
            a = self.expr()
            self.expect(":")
            b = self.expr()
            return Node("Ternary", cond=c, then=a, **{"else": b})
        return c

    def binary(self, sub, ops):
        left = sub()
        while True:
            k, v, _ = self.peek()
            if k == "op" and v in ops:
                self.i += 1
                left = Node("Binary", op=v, left=left, right=sub())
            else:
                return left

    def oror(self):
        return self.binary(self.andand, ("||",))

    def andand(self):
        return self.binary(self.cmp, ("&&",))

    def cmp(self):
        return self.binary(self.sum, ("==", "!=", "<>", "<=", ">=", "<", ">"))

    def sum(self):
        return self.binary(self.signed, ("+", "-"))

    def signed(self):
        """A unary minus (or plus) covers a whole product: -3*3\\2 is -(3*3\\2)."""
        k, v, _ = self.peek()
        at = self.i
        if k == "op" and v == "+":
            if at not in self.plus_ok:
                raise ExprError("unexpected +")
            self.i += 1
            return Node("Unary", op="+", operand=self.signed())
        if k == "op" and v == "-" and at in self.starts:
            if at > 0 and self.t[at - 1][0] == "op" and self.t[at - 1][1] in ("?", ":"):
                if not (at + 1 < len(self.t) and self.t[at + 1][0] == "num"):
                    raise Unsupported("a minus after ? or : must be followed by a number")
            self.i += 1
            return Node("Unary", op="-", operand=self.signed())
        return self.term()

    def term(self):
        left = self.factor()
        while True:
            k, v, _ = self.peek()
            if k == "op" and v in ("*", "/", "%", "\\"):
                self.i += 1
                left = Node("Binary", op=v, left=left, right=self.factor())
            else:
                return left

    def factor(self):
        k, v, _ = self.peek()
        if k == "op" and v == "!":
            self.i += 1
            k2, v2, _ = self.peek()
            if k2 == "op" and v2 in ("-", "+"):
                raise ExprError("unexpected %s after !" % v2)
            return self.power_from(Node("Unary", op="!", operand=self.not_operand()))
        if k == "op" and v == "-":
            # not at the start of an expression: the minus belongs to a number
            k2, v2, raw2 = self.t[self.i + 1] if self.i + 1 < len(self.t) else (None, None, None)
            if k2 != "num":
                raise Unsupported("a minus here must be followed by a number")
            self.i += 2
            return self.power_from(Node("Num", value=-v2, text="-" + raw2))
        if k == "op" and v == "+":
            raise ExprError("unexpected +")
        return self.power()

    def not_operand(self):
        """! binds tighter than ** : !1**0 is (!1)**0."""
        k, v, _ = self.peek()
        if k == "op" and v == "!":
            self.i += 1
            k2, v2, _ = self.peek()
            if k2 == "op" and v2 in ("-", "+"):
                raise ExprError("unexpected %s after !" % v2)
            return Node("Unary", op="!", operand=self.not_operand())
        return self.atom()

    def pow_operand(self):
        k, v, _ = self.peek()
        if k == "op" and v == "-":
            k2, v2, raw2 = self.t[self.i + 1] if self.i + 1 < len(self.t) else (None, None, None)
            if k2 != "num":
                raise Unsupported("a minus here must be followed by a number")
            self.i += 2
            return Node("Num", value=-v2, text="-" + raw2)
        if k == "op" and v == "!":
            self.i += 1
            k2, v2, _ = self.peek()
            if k2 == "op" and v2 in ("-", "+"):
                raise ExprError("unexpected %s after !" % v2)
            return Node("Unary", op="!", operand=self.pow_operand())
        return self.atom()

    def power(self):
        return self.power_from(self.atom())

    def power_from(self, left):
        while True:
            k, v, _ = self.peek()
            if k == "op" and v in ("**", "^"):
                self.i += 1
                left = Node("Binary", op="**", left=left, right=self.pow_operand())
            else:
                return left

    def atom(self):
        k, v, raw = self.peek()
        if k == "num":
            self.i += 1
            return Node("Num", value=v, text=raw)
        if k == "id":
            self.i += 1
            if self.eat("("):
                args = []
                if not self.eat(")"):
                    while True:
                        args.append(self.expr())
                        if self.eat(")"):
                            break
                        self.expect(",")
                return Node("Call", func=v, args=args)
            return Node("Ref", name=v)
        if self.eat("("):
            e = self.expr()
            self.expect(")")
            return e
        raise ExprError("unexpected %s" % (raw or "end of expression"))


def parse_expr(src: str, d: Dialect) -> Node:
    p = _P(tokenize(strip_delims(src), d))
    if not p.t:
        raise ExprError("empty expression")
    e = p.expr()
    if p.i != len(p.t):
        raise ExprError("unexpected %s" % p.t[p.i][2])
    return e


INF, NAN = math.inf, math.nan


def _finite(x):
    if x != x or x in (INF, -INF):
        raise ExprError("result is not a finite number")
    return x


def _div(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        if a != a or a == 0:
            return NAN
        return math.copysign(INF, a) * math.copysign(1.0, b)


def _fmod(a, b):
    q = _div(a, b)
    if q != q or q in (INF, -INF):
        return NAN
    return a - math.trunc(q) * b


def _cpow(x, y):
    """C pow(): NaN for a negative base with a non-integer exponent."""
    finite_y = y == y and y not in (INF, -INF)
    if x == 0 and y < 0:
        odd = finite_y and y == int(y) and int(y) % 2 != 0
        return -INF if (odd and math.copysign(1.0, x) < 0) else INF
    try:
        return math.pow(x, y)
    except OverflowError:
        neg = x < 0 and finite_y and y == int(y) and int(y) % 2 != 0
        return -INF if neg else INF
    except ValueError:
        return NAN


def _w(f, over=INF):
    def g(*a):
        try:
            return f(*a)
        except OverflowError:
            return over
        except (ValueError, ZeroDivisionError):
            return NAN
    return g


def _log(f):
    def g(x):
        if x == 0:
            return -INF
        return f(x) if x > 0 else NAN
    return g


def _round(f):
    def g(x):
        return x if (x != x or x in (INF, -INF)) else float(f(x))
    return g


def _atanh(x):
    if abs(x) == 1:
        return math.copysign(INF, x)
    return math.atanh(x) if abs(x) < 1 else NAN


BUILTINS: Dict[str, Callable] = {
    "sqrt": _w(math.sqrt), "sin": _w(math.sin), "cos": _w(math.cos), "tan": _w(math.tan),
    "sinh": lambda x: math.copysign(INF, x) if abs(x) > 710 else math.sinh(x),
    "cosh": lambda x: INF if abs(x) > 710 else math.cosh(x),
    "tanh": _w(math.tanh), "asin": _w(math.asin), "acos": _w(math.acos), "atan": _w(math.atan),
    "asinh": _w(math.asinh), "acosh": _w(math.acosh), "atanh": _w(_atanh),
    "arctan": _w(math.atan), "exp": _w(math.exp), "ln": _log(math.log), "log": _log(math.log),
    "log10": _log(math.log10), "abs": abs, "nint": _round(round), "int": _round(math.trunc),
    "floor": _round(math.floor), "ceil": _round(math.ceil),
    "pow": _cpow, "pwr": lambda x, y: _cpow(abs(x), y), "min": min, "max": max,
    "sgn": lambda x: float((x > 0) - (x < 0)),
    "ternary_fcn": lambda c, a, b: a if c else b,
}


class Env:
    """Names visible to an expression: parameters (a scope chain) and functions."""

    def __init__(self, lookup: Callable[[str], Optional[float]], funcs: Dict[str, tuple], dialect: Dialect):
        self.lookup, self.funcs, self.d = lookup, funcs, dialect


def evaluate(e: Node, env: Env) -> float:
    """Evaluate to a finite float, or raise ExprError."""
    return _finite(_eval(e, env, 0))


def _eval(e: Node, env: Env, depth: int) -> float:
    if depth > 100:
        raise ExprError("expression nesting or recursion too deep")
    k = e.kind
    if k == "Num":
        return e.value
    if k == "Ref":
        if e.name in RUNTIME_NAMES:
            raise ExprError("%s is only known during analysis" % e.name)
        v = env.lookup(e.name)
        if v is None:
            raise ExprError("undefined parameter %s" % e.name)
        return v
    if k == "Unary":
        x = _eval(e.operand, env, depth + 1)
        return -x if e.op == "-" else (x if e.op == "+" else float(not x))
    if k == "Ternary":
        return _eval(e.then if _eval(e.cond, env, depth + 1) else getattr(e, "else"), env, depth + 1)
    if k == "Binary":
        op = e.op
        if op == "&&":
            return float(bool(_eval(e.left, env, depth + 1)) and bool(_eval(e.right, env, depth + 1)))
        if op == "||":
            return float(bool(_eval(e.left, env, depth + 1)) or bool(_eval(e.right, env, depth + 1)))
        a, b = _eval(e.left, env, depth + 1), _eval(e.right, env, depth + 1)
        if op == "+": return a + b
        if op == "-": return a - b
        if op == "*": return a * b
        if op == "/": return _div(a, b)
        if op == "**": return _cpow(abs(a), b)            # the sign of the base is dropped
        if op == "%": return _fmod(a, b)
        if op == "\\":
            q = _div(abs(a), abs(b))
            return q if (q != q or q in (INF, -INF)) else float(math.trunc(q))
        if op == "==": return float(a == b)
        if op in ("!=", "<>"): return float(a != b)
        if op == "<=": return float(a <= b)
        if op == ">=": return float(a >= b)
        if op == "<": return float(a < b)
        if op == ">": return float(a > b)
        raise ExprError("unknown operator %s" % op)
    if k == "Call":
        args = [_eval(a, env, depth + 1) for a in e.args]
        if e.func in env.funcs:                          # user functions shadow built-ins
            params, body, lookup = env.funcs[e.func]
            if len(params) != len(args):
                raise ExprError("%s takes %d arguments" % (e.func, len(params)))
            local = dict(zip(params, args))
            sub = Env(lambda n: local[n] if n in local else lookup(n), env.funcs, env.d)
            return _eval(body, sub, depth + 1)
        f = BUILTINS.get(e.func)
        if f is None:
            raise ExprError("unknown function %s" % e.func)
        try:
            return float(f(*args))
        except TypeError:
            raise ExprError("wrong number of arguments to %s" % e.func)
    raise ExprError("cannot evaluate %s" % k)
