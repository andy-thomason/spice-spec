"""The tokenization illustrations in grammar/00-tokens.md must be what the
reference tokenizer produces. (Both were written from the same rules; a
mismatch means the text or the code is wrong.)"""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _docs
from spicelex import NGSPICE, pass1, render, tokenize


class TokensDoc(unittest.TestCase):
    def test_illustrations(self):
        pairs = _docs.token_illustrations()
        self.assertGreaterEqual(len(pairs), 5)
        for src, want in pairs:
            with self.subTest(src):
                r = pass1("title\n" + src + "\n.end\n")
                got = render(tokenize(r.lines[0], NGSPICE))
                self.assertEqual(got, want)

    def test_spans_and_space(self):
        r = pass1("t\nR1 a 0 r={1k}\n.end\n", "x.cir")
        toks = tokenize(r.lines[0])
        self.assertEqual([t.space_before for t in toks], [False, True, True, True, False, False])
        self.assertEqual(toks[1].origin, ("x.cir", 2, 4))
        self.assertEqual(toks[-1].kind, "Braced")

    def test_continuation_origin(self):
        r = pass1("t\nR1 a 0 1k\n+ tc1=0.001\n.end\n", "x.cir")
        toks = tokenize(r.lines[0])
        tc = [t for t in toks if t.text == "tc1"][0]
        self.assertEqual(tc.origin[:2], ("x.cir", 3))
        self.assertEqual(tc.origin[2], 3)


if __name__ == "__main__":
    unittest.main()
