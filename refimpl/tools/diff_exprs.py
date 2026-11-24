#!/usr/bin/env python3
"""Differential test: reference expression evaluator against ngspice.

Generates random expressions (mostly without parentheses, to exercise
precedence and associativity), evaluates them with the reference, and asks
ngspice (through `listing expand`) for the same. Needs ngspice.

  python3 diff_exprs.py --ngspice PATH [--count 600] [--seed 1] [--show-errors]
"""
import argparse, os, random, re, subprocess, sys, tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from spicelex import NGSPICE
from spicelex.expr import Env, ExprError, Unsupported, evaluate, parse_expr

BIN = ["+", "-", "*", "/", "**", "^", "%", "\\", "==", "!=", "<=", ">=", "<", ">", "&&", "||"]
UN = ["-", "!", "+"]
F1 = ["abs", "sqrt", "exp", "ln", "log", "log10", "sin", "cos", "atan", "tanh", "int", "nint", "floor", "ceil", "sgn"]
F2 = ["min", "max", "pow", "pwr"]


def operand(r, depth):
    c = r.random()
    if c < 0.45:
        return str(r.randint(0, 9))
    if c < 0.60:
        return "%g" % (r.randint(1, 99) / 8)
    if c < 0.68:
        inner = operand(r, depth)
        op = r.choice(UN)
        if inner.startswith("-") and op == "-":      # `--2**2` quirk, not modelled
            op = "!"
        return op + inner
    if depth > 0 and c < 0.82:
        return "(" + expr(r, depth - 1) + ")"
    if depth > 0 and c < 0.92:
        return "%s(%s)" % (r.choice(F1), expr(r, depth - 1))
    if depth > 0:
        return "%s(%s,%s)" % (r.choice(F2), expr(r, depth - 1), expr(r, depth - 1))
    return str(r.randint(1, 9))


def expr(r, depth=2):
    s = operand(r, depth)
    for _ in range(r.randint(0, 3)):
        s += r.choice(BIN) + operand(r, depth)
    if r.random() < 0.1:
        s += "?%s:%s" % (operand(r, depth), operand(r, depth))
    return s


def ngspice_values(ngspice, exprs):
    deck = ["diff exprs"] + ["R%d a%d 0 {%s}" % (i, i, e) for i, e in enumerate(exprs)]
    deck += [".control", "listing expand", ".endc", ".end"]
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "d.cir"), "w").write("\n".join(deck) + "\n")
        p = subprocess.run([ngspice, "-n", "-b", "d.cir"], cwd=d, capture_output=True, text=True, timeout=120)
    return {int(m.group(1)): float(m.group(2))
            for m in re.finditer(r"^\s*\d+ : r(\d+) a\d+ 0\s+(\S+)", p.stdout, re.M)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ngspice", required=True)
    ap.add_argument("--count", type=int, default=600)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--show-errors", action="store_true")
    a = ap.parse_args()
    r = random.Random(a.seed)
    es = []
    while len(es) < a.count:
        e = expr(r)
        if e not in es:
            es.append(e)
    env = Env(lambda n: None, {}, NGSPICE)
    mism = agree = skipped = 0
    for lo in range(0, len(es), 60):
        chunk = es[lo:lo + 60]
        got = ngspice_values(a.ngspice, chunk)
        if len(got) != len(chunk):
            got = {}
            for i, e in enumerate(chunk):
                g = ngspice_values(a.ngspice, [e])
                if 0 in g:
                    got[i] = g[0]
        for i, e in enumerate(chunk):
            try:
                want = evaluate(parse_expr(e, NGSPICE), env)
            except Unsupported:                       # ngspice quirk, not modelled
                skipped += 1
                continue
            except ExprError as ex:
                if i in got:
                    print("REFERENCE REJECTS %-34s (%s) ngspice=%.12g" % (e, ex, got[i]))
                    mism += 1
                else:
                    agree += 1
                continue
            if i not in got:
                print("NGSPICE REJECTS   %-34s reference=%.12g" % (e, want))
                mism += 1
            elif abs(got[i] - want) > 1e-9 * abs(want) + 1e-12:
                print("MISMATCH          %-34s ngspice=%.12g reference=%.12g" % (e, got[i], want))
                mism += 1
            else:
                agree += 1
    print("%d expressions: %d agree, %d problems, %d skipped" % (len(es), agree, mism, skipped))
    return 1 if mism else 0


if __name__ == "__main__":
    sys.exit(main())
