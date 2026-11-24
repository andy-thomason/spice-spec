#!/usr/bin/env python3
"""Run the examples embedded in the grammar documents against ngspice.

Examples are NON-NORMATIVE (see grammar/doctests.md). They illustrate the
rules; the rules are defined by the text. A failing example is a
discrepancy to investigate. It never redefines the language.

Usage:
  doctest.py [--ngspice PATH] [--id ID] [--list] [--coverage] FILE_OR_DIR...
"""
import argparse, os, re, subprocess, sys, tempfile

FENCE = re.compile(r"^```(\S*)\s*(.*)$")
ATTR = re.compile(r'(\w+)=("[^"]*"|\S+)')
ANALYSIS = re.compile(r"^\s*\.(op|dc|ac|tran|noise|tf|pz|sens|disto|pss|sp)\b", re.I | re.M)
EXPECT = re.compile(r"^\s*\*\s*expect:\s*(.+?)\s*=\s*(\S+)(.*)$")


def attrs(s):
    return {k: v.strip('"') for k, v in ATTR.findall(s)}


def parse_md(path):
    tests, files, rules, listings = [], {}, set(), {}
    lines = open(path, encoding="utf-8").read().split("\n")
    i = 0
    while i < len(lines):
        m = FENCE.match(lines[i])
        if not m or not m.group(1):
            i += 1
            continue
        kind, rest = m.group(1), m.group(2)
        j = i + 1
        while j < len(lines) and not lines[j].startswith("```"):
            j += 1
        body = lines[i + 1:j]
        if kind == "abnf":
            for ln in body:
                r = re.match(r"^([a-z][a-z0-9-]*)\s*=", ln)
                if r:
                    rules.add(r.group(1))
        elif kind == "spice-file":
            a = attrs(rest)
            files[a["name"]] = "\n".join(body) + "\n"
        elif kind == "spice-listing":
            listings[attrs(rest)["for"]] = body
        elif kind == "spice-test":
            a = attrs(rest)
            a["body"] = body
            a["file"] = path
            a["line"] = i + 1
            tests.append(a)
        i = j + 1
    return tests, files, rules, listings


def collect(paths):
    mds = []
    for p in paths:
        if os.path.isdir(p):
            for r, _, fs in os.walk(p):
                mds += [os.path.join(r, f) for f in sorted(fs) if f.endswith(".md")]
        else:
            mds.append(p)
    allt, allr = [], set()
    for md in sorted(mds):
        t, f, r, lst = parse_md(md)
        for x in t:
            x["files"] = f
            x["expected_listing"] = lst.get(x["id"])
        allt += t
        allr |= r
    return allt, allr


def build(t):
    body = list(t["body"])
    if "listing" in t and t.get("deck") != "full":
        raise SystemExit("%s: listing examples must use deck=full" % t["id"])
    checks = []
    for ln in body:
        m = EXPECT.match(ln)
        if m:
            checks.append((m.group(1).strip(), m.group(2), attrs(m.group(3))))
    text = "\n".join(body)
    if t.get("deck", "cards") == "full":
        out = body[:]
        while out and not out[-1].strip():
            out.pop()
        assert out[-1].strip().lower() == ".end", "full deck must end with .end"
        out = out[:-1]
    else:
        out = ["doctest " + t["id"]] + body
        if not ANALYSIS.search(text):
            out.append(".op")
    if "listing" in t:
        out += [".control", "listing " + t["listing"], ".endc"]
    elif "uses_control" not in t:
        out.append(".control")
        out.append("run")
        for k, (expr, _, _) in enumerate(checks):
            out.append("wrdata out%d.dat %s" % (k, expr))
        out.append(".endc")
    out.append(".end")
    return "\n".join(out) + "\n", checks


def norm(s):
    return " ".join(s.split())


def check_listing(t, log):
    """Compare the text of `listing MODE` output, ignoring line numbers and
    white-space runs, with the spice-listing block. The generated control
    lines are removed from the tail first."""
    want = t.get("expected_listing")
    if want is None:
        return "FAIL", "no spice-listing block for " + t["id"]
    got = []
    for ln in log.splitlines():
        m = re.match(r"^\s*\d+ : ?(.*)$", ln)
        if m:
            got.append(norm(m.group(1)))
    for drop in (".endc", "listing " + t["listing"], ".control"):
        for i in range(len(got) - 1, -1, -1):
            if got[i] == drop:
                del got[i]
                break
    want = [norm(x) for x in want if x.strip()]
    if got != want:
        return "FAIL", "listing differs:\n  got:  %s\n  want: %s" % (got, want)
    return "PASS", ""


def run_one(t, ngspice, codemodels=None):
    deck, checks = build(t)
    with tempfile.TemporaryDirectory(prefix="doctest-") as d:
        for name in filter(None, t.get("uses", "").split(",")):
            if name not in t["files"]:
                return "FAIL", "missing spice-file " + name
            open(os.path.join(d, name), "w").write(t["files"][name])
        open(os.path.join(d, "deck.cir"), "w").write(deck)
        env = dict(os.environ)
        if t.get("needs") == "xspice":
            if not codemodels:
                return "SKIP", "needs --codemodels DIR (XSPICE code models)"
            os.mkdir(os.path.join(d, "init"))
            with open(os.path.join(d, "init", "spinit"), "w") as f:
                f.write("codemodel %s\n" % os.path.join(codemodels, "spice2poly.cm"))
            env["SPICE_SCRIPTS"] = os.path.join(d, "init")
        try:
            p = subprocess.run([ngspice, "-n", "-b", "deck.cir"], cwd=d, capture_output=True,
                               text=True, env=env, timeout=int(t.get("timeout", "120")))
        except subprocess.TimeoutExpired:
            return "FAIL", "timeout"
        log = p.stdout + p.stderr
        errs = [l for l in log.splitlines() if l.startswith("Error")]
        warns = [l for l in log.splitlines() if l.startswith("Warning")]
        # A listing-only deck runs no simulation, and ngspice then exits with
        # status 1, so only error messages count for listing examples.
        bad_exit = p.returncode != 0 and "listing" not in t
        got = "reject" if (bad_exit or errs) else ("warn" if warns else "accept")
        want = t.get("expect", "accept")
        if want == "accept" and got == "warn":
            return "FAIL", "unexpected warning: " + warns[0]
        if want != got:
            return "FAIL", "expected %s, got %s %s" % (want, got, (errs or warns or [""])[0])
        if got == "reject":
            return "PASS", ""
        if "listing" in t:
            return check_listing(t, log)
        for k, (expr, val, a) in enumerate(checks):
            f = os.path.join(d, "out%d.dat" % k)
            if not os.path.exists(f):
                return "FAIL", "no output for " + expr
            row = [x for x in open(f).read().strip().splitlines()[-1].split()]
            v = float(row[-1])
            e = float(val)
            rtol = float(a.get("tol", "1e-6"))
            atol = float(a.get("atol", "1e-12"))
            if abs(v - e) > rtol * abs(e) + atol:
                return "FAIL", "%s = %.9g, expected %s" % (expr, v, val)
        return "PASS", ""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--ngspice", default=os.environ.get("NGSPICE", "ngspice"))
    ap.add_argument("--codemodels", default=os.environ.get("NGSPICE_CODEMODELS"),
                    help="directory holding spice2poly.cm, for examples with needs=xspice")
    ap.add_argument("--id")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--coverage", action="store_true")
    ap.add_argument("--exceptions", help="file of 'rule  reason' lines excluded from coverage")
    a = ap.parse_args()
    tests, rules = collect(a.paths)
    ids = [t["id"] for t in tests]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        sys.exit("duplicate example ids: " + ", ".join(sorted(dup)))
    if a.coverage:
        covered = set()
        for t in tests:
            covered |= set(filter(None, t.get("covers", "").split(",")))
        exc = {}
        if a.exceptions and os.path.exists(a.exceptions):
            for ln in open(a.exceptions):
                if ln.strip() and not ln.startswith("#"):
                    n, _, why = ln.strip().partition(" ")
                    exc[n] = why.strip()
        unk = covered - rules
        miss = sorted(rules - covered - set(exc))
        print("rules: %d, covered: %d, excepted: %d, uncovered: %d" %
              (len(rules), len(rules & covered), len(set(exc) & rules), len(miss)))
        for n in miss:
            print("  uncovered:", n)
        for n in sorted(unk):
            print("  covers= names no rule:", n)
        return 1 if miss or unk else 0
    if a.list:
        for t in tests:
            print(t["id"], t["file"], t["line"], t.get("covers", ""))
        return 0
    bad = 0
    n = {"PASS": 0, "FAIL": 0, "SKIP": 0}
    for t in tests:
        if a.id and t["id"] != a.id:
            continue
        if "skip" in t:
            st, msg = "SKIP", t["skip"]
        else:
            st, msg = run_one(t, a.ngspice, a.codemodels)
        n[st] += 1
        if st != "PASS":
            print("%s %s (%s:%d) %s" % (st, t["id"], t["file"], t["line"], msg))
    print("%d passed, %d failed, %d skipped" % (n["PASS"], n["FAIL"], n["SKIP"]))
    return 1 if n["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
