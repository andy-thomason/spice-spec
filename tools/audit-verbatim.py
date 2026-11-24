#!/usr/bin/env python3
"""Report runs of N or more consecutive words shared between this repo's
text and reference documents. A shared run is not proof of copying (short
syntax such as `.ac dec nd fstart fstop` is a fact), but every hit must be
reviewed and reworded or justified.

Usage: audit-verbatim.py [-n 8] REFERENCE_TEXT... -- REPO_FILE...
Reference texts are never stored in the repo. Run with `python3 -I`.
"""
import re, sys

def words(text):
    return re.findall(r"[a-z0-9]+(?:[.'][a-z0-9]+)*", text.lower())

def main(argv):
    n = 8
    if argv and argv[0] == "-n":
        n = int(argv[1]); argv = argv[2:]
    if "--" not in argv:
        sys.exit(__doc__)
    i = argv.index("--")
    refs, files = argv[:i], argv[i + 1:]
    grams = {}
    for r in refs:
        w = words(open(r, errors="replace").read())
        for k in range(len(w) - n + 1):
            grams.setdefault(tuple(w[k:k + n]), r)
    hits = 0
    for f in files:
        w = words(open(f, errors="replace").read())
        k = 0
        while k <= len(w) - n:
            g = tuple(w[k:k + n])
            if g in grams:
                j = k + n
                while j < len(w) and tuple(w[j - n + 1:j + 1]) in grams:
                    j += 1
                print("%s: %d words match %s: %s" % (f, j - k, grams[g], " ".join(w[k:j])[:160]))
                hits += 1
                k = j
            else:
                k += 1
    print("%d shared run(s) of >= %d words" % (hits, n))
    return 1 if hits else 0

sys.exit(main(sys.argv[1:]))
