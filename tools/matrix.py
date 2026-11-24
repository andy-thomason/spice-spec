#!/usr/bin/env python3
"""Merge per-simulator result files from `doctest.py --json` into a Markdown
table (one row per example, one column per simulator).

  matrix.py NAME=results.json NAME=results.json ... > table.md
"""
import json, sys

def main(argv):
    cols = []
    for a in argv:
        name, _, path = a.partition("=")
        cols.append((name, {r["id"]: r for r in json.load(open(path))}))
    ids = []
    for _, d in cols:
        for i in d:
            if i not in ids:
                ids.append(i)
    sym = {"PASS": "pass", "FAIL": "**differs**", "SKIP": "n/a"}
    print("| Example | " + " | ".join(n for n, _ in cols) + " | Note |")
    print("|---|" + "---|" * (len(cols) + 1))
    for i in ids:
        cells, note = [], ""
        for name, d in cols:
            r = d.get(i)
            if r is None:
                cells.append("")
                continue
            cells.append(sym[r["status"]] + (" (warns)" if r["message"].startswith("warning:") else ""))
            if r["message"] and not note and name != cols[0][0]:
                note = r["message"].replace("|", "/")[:160]
        print("| %s | %s | %s |" % (i, " | ".join(cells), note))
    for name, d in cols:
        c = {}
        for r in d.values():
            c[r["status"]] = c.get(r["status"], 0) + 1
        print("\n%s: %s" % (name, ", ".join("%d %s" % (v, sym[k]) for k, v in sorted(c.items()))))

main(sys.argv[1:])
