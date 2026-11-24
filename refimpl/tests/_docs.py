"""Load examples and illustrations from the grammar documents."""
import importlib.util, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "refimpl"))


def load_doctest_module():
    spec = importlib.util.spec_from_file_location("spice_doctest", os.path.join(ROOT, "tools", "doctest.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def examples():
    dt = load_doctest_module()
    tests, _ = dt.collect([os.path.join(ROOT, "grammar")])
    return tests


def token_illustrations():
    """(source line, expected token rendering) pairs from 00-tokens.md."""
    text = open(os.path.join(ROOT, "grammar", "00-tokens.md"), encoding="utf-8").read()
    sec = text.split("## Tokenization, shown", 1)[1]
    block = re.search(r"```text\n(.*?)```", sec, re.S).group(1).split("\n")
    pairs, i = [], 0
    while i < len(block):
        src = block[i]
        if src and not src.startswith(" "):
            j = i + 1
            exp = None
            while j < len(block) and block[j].startswith("  "):
                if not block[j].startswith("  ("):
                    exp = block[j].strip()
                j += 1
            if exp:
                pairs.append((src, exp))
            i = j
        else:
            i += 1
    return pairs
