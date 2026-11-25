#!/usr/bin/env python3
"""Count the syntax features used by a corpus of SPICE model libraries.

    python3 -I tools/scan-syntax.py --name NAME --root DIR [--ext .spice,.lib]
        [--max-bytes N] [--parse] --out results.json

The output holds only counts and short keywords (card names, element
letters, number suffixes, function names, option names, parser error codes).
No library text is stored, so the result can be committed. The library
files themselves stay outside the repository (see docs/hspice-corpus.md).

With --parse each file is also run through the reference parser in refimpl/
(pass 1 plus parser, ngspice presets, no title line) and the diagnostics are
counted by code.
"""
import argparse
import collections
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "refimpl"))

NUM_TAIL = re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?([a-z][a-z0-9_]*)$")
FUNC = re.compile(r"\b([a-z_][a-z0-9_]*)\s*\(")
ELEMENT_LETTERS = set("rclkdqjmvievfghbstuwxoyzpna")
SKIP_FUNCS = {"v", "i", "pwl", "pulse", "sin", "exp", "sffm", "am"}


def bump(d, k, n=1):
    d[k] = d.get(k, 0) + n


def scan_lines(lines, acc):
    for text in lines:
        t = text.strip()
        if not t:
            continue
        low = t.lower()
        first = low.split(None, 1)[0]
        acc["logical_lines"] += 1
        if first.startswith("."):
            bump(acc["dot_cards"], first)
            card_features(low, first, acc)
        elif first[0] in ELEMENT_LETTERS and first[0].isalpha():
            bump(acc["elements"], first[0])
        else:
            bump(acc["other_first"], first[0])
        for tok in re.split(r"[\s,()=]+", low):
            m = NUM_TAIL.match(tok)
            if m:
                bump(acc["number_tails"], m.group(1))
        for q in re.findall(r"'([^']*)'", low) + re.findall(r"\{([^}]*)\}", low):
            acc["quoted_or_braced_exprs"] += 1
            for f in FUNC.findall(q):
                if f not in SKIP_FUNCS:
                    bump(acc["expr_functions"], f)
            for op in ("**", "^", "&&", "||", "?", "!=", "==", ">=", "<=", "!"):
                if op in q:
                    bump(acc["expr_operators"], op)


def card_features(low, card, acc):
    f = low.split()
    if card == ".model" and len(f) >= 3:
        mtype = re.split(r"[(\s]", f[2])[0]
        bump(acc["model_types"], mtype)
        m = re.search(r"\blevel\s*=\s*([0-9.]+)", low)
        if m:
            bump(acc["model_levels"], "%s:%s" % (mtype, m.group(1)))
        if re.search(r"\b(lmin|lmax|wmin|wmax)\s*=", low):
            acc["binned_models"] += 1
    elif card in (".lib", ".library"):
        bump(acc["lib_forms"], "args=%d" % (len(f) - 1))
    elif card in (".param", ".parameters"):
        for v in re.findall(r"=\s*(\S)", low):
            bump(acc["param_value_start"], {"'": "quote", "{": "brace"}.get(v, "bare"))
    elif card == ".subckt":
        if "params:" in low:
            acc["subckt_params_keyword"] += 1
        if "=" in low:
            acc["subckt_with_defaults"] += 1
    elif card in (".option", ".options", ".opt"):
        for k in re.findall(r"([a-z_][a-z0-9_]*)\s*(?:=|\s|$)", " ".join(f[1:])):
            bump(acc["option_names"], k)
    elif card in (".include", ".inc"):
        bump(acc["include_path_form"], "quoted" if re.search(r"[\"']", low) else "bare")


def raw_features(text, acc):
    for line in text.splitlines():
        s = line.lstrip()
        if line.startswith((" ", "\t")):
            acc["leading_whitespace_lines"] += 1
        if s.startswith("*"):
            acc["comment_star"] += 1
        elif s.startswith("//"):
            acc["comment_slashes"] += 1
        elif s.startswith(";"):
            acc["comment_semicolon_line"] += 1
        elif s.startswith("$"):
            acc["comment_dollar_line"] += 1
        elif s.startswith("+"):
            acc["continuation_lines"] += 1
        else:
            if re.search(r"\s\$", line):
                acc["eol_comment_dollar"] += 1
            if ";" in line:
                acc["eol_comment_semicolon"] += 1
            if "//" in line:
                acc["eol_comment_slashes"] += 1
        if "\t" in line:
            acc["lines_with_tab"] += 1
        if "\r" in line:
            acc["lines_with_cr"] += 1
    if text and not text.endswith("\n"):
        acc["files_without_final_newline"] += 1
    letters = [c for c in text if c.isalpha()]
    if letters and sum(c.isupper() for c in letters) > len(letters) / 2:
        acc["mostly_uppercase_files"] += 1


def new_acc():
    a = collections.defaultdict(int)
    for k in ("dot_cards", "elements", "other_first", "number_tails", "expr_functions", "expr_operators",
              "model_types", "model_levels", "lib_forms", "param_value_start", "option_names",
              "include_path_form", "parse_codes", "pass1_codes", "scan_errors"):
        a[k] = {}
    return a


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--ext", default=".spice,.lib,.pm,.ngspice,.inc,.sp,.cir,.mod")
    ap.add_argument("--max-bytes", type=int, default=2_000_000, help="skip bigger files (counted as skipped)")
    ap.add_argument("--parse", action="store_true")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    exts = tuple(a.ext.split(","))
    acc = new_acc()
    t0 = time.time()
    from spicelex.dialect import NGSPICE
    from spicelex.pass1 import pass1
    if a.parse:
        from spicelex.parser import parse
    for dp, dn, fn in os.walk(a.root):
        dn[:] = [d for d in dn if d != ".git"]
        for name in sorted(fn):
            if not name.lower().endswith(exts):
                continue
            path = os.path.join(dp, name)
            size = os.path.getsize(path)
            if size > a.max_bytes:
                acc["files_skipped_large"] += 1
                continue
            data = open(path, "rb").read()
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                acc["files_not_utf8"] += 1
                text = data.decode("latin-1")
            acc["files"] += 1
            acc["bytes"] += size
            raw_features(text, acc)
            try:
                r = pass1(text, name, NGSPICE, None, False)
                scan_lines([l.text for l in r.lines], acc)
                for g in r.diagnostics:
                    bump(acc["pass1_codes"], g.code)
            except Exception as ex:   # a scanner bug must not hide the corpus
                bump(acc["scan_errors"], type(ex).__name__)
                continue
            if a.parse:
                try:
                    deck = parse(text, name, NGSPICE, None, False)
                    acc["files_parsed"] += 1
                    errs = [d for d in deck.diagnostics if d.severity == "error"]
                    if errs:
                        acc["files_with_parse_errors"] += 1
                    for d in deck.diagnostics:
                        bump(acc["parse_codes"], "%s:%s" % (d.severity, d.code))
                except Exception as ex:
                    bump(acc["parse_codes"], "crash:" + type(ex).__name__)
    acc["seconds"] = round(time.time() - t0, 1)
    out = {"name": a.name, "extensions": list(exts), "max_bytes": a.max_bytes, "parsed": a.parse}
    out.update({k: v for k, v in acc.items()})
    for k, v in list(out.items()):
        if isinstance(v, dict):
            out[k] = dict(sorted(v.items(), key=lambda kv: -kv[1]))
    with open(a.out, "w") as f:
        json.dump(out, f, indent=1, sort_keys=False)
        f.write("\n")
    print("%s: %d files, %d logical lines, %s s" % (a.name, acc["files"], acc["logical_lines"], acc["seconds"]))


if __name__ == "__main__":
    main()
