#!/usr/bin/env python3
"""Differential test: reference number() against ngspice.

Generates words that start with a number, puts each in a voltage source
value, asks ngspice for the node voltage, and compares. Needs ngspice.

  python3 diff_numbers.py --ngspice PATH [--count 400] [--seed 1] [--dialect ngspice]
"""
import argparse, os, random, re, subprocess, sys, tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from spicelex import DIALECTS, number

SIGNS = ["", "", "", "+", "-"]
MANT = ["1", "5", "10", "2.5", ".5", "5.", "0", "123", "0.001", "1.5.2"]
EXPO = ["", "", "", "e3", "E-3", "e+2", "d3", "D-2", "e", "e+", "e-"]
SCALE = ["", "", "", "k", "K", "meg", "MEG", "mil", "m", "M", "u", "n", "p", "f", "t", "g", "a", "A"]
TAIL = ["", "", "", "v", "Volts", "Hz", "ohm", "_x", "5", "k5", "7a", "x10", "%", "meg", "_1e3"]


def words(n, seed):
    rnd = random.Random(seed)
    seen, out = set(), []
    while len(out) < n:
        w = rnd.choice(SIGNS) + rnd.choice(MANT) + rnd.choice(EXPO) + rnd.choice(SCALE) + rnd.choice(TAIL)
        if w not in seen:
            seen.add(w)
            out.append(w)
    return out


def run(ngspice, ws):
    deck = ["diff numbers"]
    for i, w in enumerate(ws):
        deck += ["V%d n%d 0 %s" % (i, i, w), "R%d n%d 0 1k" % (i, i)]
    deck += [".op", ".control", "run", "print " + " ".join("v(n%d)" % i for i in range(len(ws))),
             ".endc", ".end"]
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "d.cir"), "w").write("\n".join(deck) + "\n")
        p = subprocess.run([ngspice, "-n", "-b", "d.cir"], cwd=d, capture_output=True, text=True, timeout=120)
    got = {}
    for m in re.finditer(r"^v\(n(\d+)\)\s*=\s*(\S+)\s*$", p.stdout, re.M):
        got[int(m.group(1))] = float(m.group(2))
    return got, p.stdout + p.stderr


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ngspice", required=True)
    ap.add_argument("--count", type=int, default=400)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--dialect", default="ngspice")
    a = ap.parse_args()
    d = DIALECTS[a.dialect]
    ws = words(a.count, a.seed)
    bad = 0
    for lo in range(0, len(ws), 100):
        chunk = ws[lo:lo + 100]
        got, log = run(a.ngspice, chunk)
        if len(got) != len(chunk):             # something made ngspice stop: go one by one
            got = {}
            for i, w in enumerate(chunk):
                g, _ = run(a.ngspice, [w])
                if 0 in g:
                    got[i] = g[0]
                else:
                    n = number(w, d)
                    if not (n and n.error):
                        print("ngspice gave no value for %r (reference: %s)" % (w, n and n.value))
                        bad += 1
        for i, w in enumerate(chunk):
            n = number(w, d)
            if i not in got:
                continue
            want = n.value if n else None
            if want is None or abs(got[i] - want) > 1e-9 * abs(want) + 1e-30:
                print("MISMATCH %-14s ngspice=%.12g reference=%s" % (w, got[i], want))
                bad += 1
    print("%d words, %d problems" % (len(ws), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
