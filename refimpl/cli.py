#!/usr/bin/env python3
"""Command line for the reference pass 1 and tokenizer.

  python3 cli.py pass1  FILE [--dialect ngspice|spice3|xyce] [--include]
  python3 cli.py tokens FILE [--dialect ...] [--include]
"""
import argparse, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spicelex import DIALECTS, pass1, render, tokenize


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=["pass1", "tokens"])
    ap.add_argument("file")
    ap.add_argument("--dialect", default="ngspice", choices=sorted(DIALECTS))
    ap.add_argument("--include", action="store_true", help="expand .include (paths relative to FILE)")
    a = ap.parse_args()
    d = DIALECTS[a.dialect]
    base = os.path.dirname(os.path.abspath(a.file))
    loader = (lambda p: open(os.path.join(base, p), encoding="utf-8").read()) if a.include else None
    r = pass1(open(a.file, "rb").read(), a.file, d, loader)
    print("title:", r.title)
    for ll in r.lines:
        f, ln, col = ll.origin(0)
        if a.command == "pass1":
            print("%s:%d: %s" % (os.path.basename(f), ln, ll.text))
        else:
            print("%s:%d: %s" % (os.path.basename(f), ln, render(tokenize(ll, d))))
    for g in r.diagnostics:
        print("%s: %s:%d: %s" % (g.severity, g.file, g.line, g.message), file=sys.stderr)
    return 1 if any(g.severity == "error" for g in r.diagnostics) else 0


if __name__ == "__main__":
    sys.exit(main())
