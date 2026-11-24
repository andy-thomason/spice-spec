import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from spicelex import NGSPICE, SPICE3, number


class Numbers(unittest.TestCase):
    def v(self, w, d=NGSPICE):
        n = number(w, d)
        return None if n is None else n.value

    def test_values_observed_on_ngspice(self):
        # Words and values from the doctests (TOK-NUM-*, LEX-*); ngspice 42.
        for w, want in [("1k5", 1000), ("1_000", 1), ("0x10", 0), ("1.5.2", 1.5),
                        ("1e", 1), ("1e+", 1), ("1D3", 1000), ("1e-3k", 1), ("1e3x", 1000),
                        ("1m_eg", 1e-3), ("1mm", 1e-3), ("1MIL", 2.54e-5), ("1MEG", 1e6),
                        ("1MEGOHM", 1e6), ("1Mi", 1e-3), ("2MA", 2e-3), ("10Volts", 10),
                        ("1A", 1e-18), ("1F", 1e-15), ("1G", 1e9), ("1T", 1e12),
                        ("-1.5e-3", -1.5e-3), ("5mil", 1.27e-4), ("5eu", 5e-6), ("5e-u", 5e-6),
                        ("5e+meg", 5e6), ("1dk", 1000), ("10emil", 2.54e-4), (".5", 0.5), ("5.", 5),
                        ("+5", 5), ("-.5e1", -5)]:
            with self.subTest(w):
                self.assertAlmostEqual(self.v(w) / want if want else self.v(w), 1 if want else 0, places=12)

    def test_not_numeric(self):
        for w in ["a", "R1", "-", "+", ".", "abc", "e5", "_1", ""]:
            with self.subTest(w):
                self.assertIsNone(number(w, NGSPICE))

    def test_dialect_differences(self):
        self.assertEqual(self.v("1A", SPICE3), 1)        # no atto in SPICE3
        self.assertEqual(self.v("1D3", SPICE3), 1)       # d is not an exponent marker
        self.assertEqual(self.v("1A", NGSPICE), 1e-18)

    def test_signed_d_exponent_is_an_error(self):
        for w in ["1D-3", "1d+3", "1D-", "1d-k", "2.5D-2", "1kD-2", "5Vd-3", "1.5.2D-2"]:
            with self.subTest(w):
                self.assertEqual(number(w, NGSPICE).error, "signed-d-exponent")
        self.assertIsNone(number("1D3", NGSPICE).error)
        self.assertIsNone(number("1.5.2D3", NGSPICE).error)
        self.assertIsNone(number("1D3", SPICE3).error)

    def test_parts(self):
        n = number("1.5Meg_x", NGSPICE)
        self.assertEqual((n.mantissa, n.exponent, n.scale, n.tail), ("1.5", None, "Meg", "_x"))
        n = number("5e-u", NGSPICE)
        self.assertEqual((n.exponent, n.skipped, n.scale, n.tail), (None, "e-", "u", ""))
        n = number("2e-3k", NGSPICE)
        self.assertEqual((n.mantissa, n.exponent, n.scale, n.tail), ("2", "e-3", "k", ""))


if __name__ == "__main__":
    unittest.main()
