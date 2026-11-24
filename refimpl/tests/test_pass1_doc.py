"""Compare reference pass 1 with the ngspice `listing logical` output
recorded in the doctests (P1-* in grammar/01-lexical.md).

`listing` adds conventions that are not pass 1 (lower case, a `.global gnd`
line after the title); they are applied to our output here, not to the
reference implementation."""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _docs
from spicelex import NGSPICE, pass1


def norm(s):
    return " ".join(s.split())


class Pass1Doc(unittest.TestCase):
    def test_logical_listings(self):
        cases = [t for t in _docs.examples() if t.get("listing") == "logical"]
        self.assertGreaterEqual(len(cases), 8)
        for t in cases:
            with self.subTest(t["id"]):
                files = t["files"]
                uses = [u for u in t.get("uses", "").split(",") if u]
                loader = lambda p: files[p]
                r = pass1("\n".join(t["body"]) + "\n", "deck.cir", NGSPICE, loader if uses else None)
                got = [norm(r.title).lower(), ".global gnd"] + [norm(l.text).lower() for l in r.lines]
                want = [norm(x) for x in t["expected_listing"] if x.strip()]
                self.assertEqual(got, want)
                self.assertEqual([d for d in r.diagnostics if d.severity == "error"], [])


class Pass1Behavior(unittest.TestCase):
    def test_spice3_leading_white_space_is_comment(self):
        from spicelex import SPICE3
        r = pass1("t\n R1 a 0 1k\nR2 a 0 1k\n+ tc1=1\n  + tc2=2\n.end\n", "x", SPICE3)
        self.assertEqual([l.text for l in r.lines], ["R2 a 0 1k tc1=1 tc2=2", ".end"])

    def test_ngspice_special_leading_char(self):
        r = pass1("t\n%oops\nR1 a 0 1k\n.end\n")
        self.assertEqual([l.text for l in r.lines], ["R1 a 0 1k", ".end"])
        self.assertEqual(r.diagnostics[0].code, "special-leading-char")

    def test_missing_end_and_stray_plus(self):
        r = pass1("t\n+ x\nR1 a 0 1k\n")
        self.assertEqual({d.code for d in r.diagnostics}, {"stray-continuation", "missing-end"})

    def test_bad_utf8(self):
        r = pass1(b"t\nR1 a 0 \xff\n.end\n")
        self.assertIn("invalid-utf8", {d.code for d in r.diagnostics})


if __name__ == "__main__":
    unittest.main()
