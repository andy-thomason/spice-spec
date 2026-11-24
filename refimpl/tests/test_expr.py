import math, os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from spicelex import NGSPICE
from spicelex.expr import Env, ExprError, evaluate, parse_expr


def ev(s, params=None, funcs=None):
    p = params or {}
    return evaluate(parse_expr(s, NGSPICE), Env(lambda n: p.get(n), funcs or {}, NGSPICE))


class Expr(unittest.TestCase):
    def test_values_observed_on_ngspice(self):
        # Each pair was measured on ngspice 42 with `listing expand` (see
        # tools/diff_exprs.py for the randomized comparison).
        cases = {
            "-2**2": -4, "-2^2": -4, "2**-2": 0.25, "2^3^2": 64, "2**3**2": 64, "-2**0.5": -math.sqrt(2),
            "5\\3": 1, "7\\2": 3, "-7\\2": -3, "5%3": 2, "-5%3": -2, "-7%3": -1,
            "!0": 1, "!2": 0, "1<2<3": 1, "3>2>1": 0, "1?2:3": 2, "1+1?3:4": 3,
            "1&&0||1": 1, "1||0&&0": 1, "3-2-1": 0, "8/2/2": 2, "2*3%4": 2, "2*-3": -6, "2- -2": 4,
            "log(100)": math.log(100), "ln(100)": math.log(100), "log10(100)": 2,
            "pow(2,3)": 8, "pwr(-2,2)": 4, "pwr(2,0.5)": math.sqrt(2), "nint(2.5)": 2, "nint(3.5)": 4,
            "int(-2.7)": -2, "floor(-2.7)": -3, "ceil(-2.2)": -2, "sgn(-3)": -1, "min(1,2)": 1,
            "max(1,2)": 2, "abs(-3)": 3, "atan(1)": math.pi / 4, "arctan(1)": math.pi / 4,
            "exp(1)": math.e, "2k*3": 6000, "1/3": 1 / 3, "(-8)**2": 64, "2^0.5": math.sqrt(2),
            "(-2)**3": 8, "(-2)**-3": 0.125, "pow(-2,3)": -8, "pow(-2,-3)": -0.125, "pwr(-2,3)": 8,
            "5.5\\2": 2, "7\\0.5": 14, "-5.9\\3": -1, "5.5%2": 1.5, "-5.5%2": -1.5, "5.5%-2": 1.5,
            "7%2.5": 2, "5%3.9": 1.1, "0**0": 1, "2**-2**2": 0.0625, "2**0.5**2": 2,
            "max(+1,2)": 2, "+2*3": 6, "+-2": -2, "1+(+2)": 3, "-!2": 0, "!(-2)": 0, "!!!2": 0, "2--2": 4,
            "2*-2**2": 8, "!1**0": 1, "!0**2": 1, "-3*3\\2": -4, "-2**2*2": -8, "-!0*5": -5, "--2": 2, "-2+3": 1, "!1+1": 1, "!1==0": 1, "1?-2:3": -2, "0?3:-2": -2, "7\\-2": 3, "(-7)\\2": 3, "-7\\-2": -3, "3\\-0.5": 6,
            "7==4/0": 0, "(1/0)>1": 1, "ln(0)>1": 0, "!(1/0)": 0, "7\\0.5": 14, "2**-2": 0.25,
        }
        for s, want in cases.items():
            with self.subTest(s):
                self.assertAlmostEqual(ev(s), want, places=12)

    def test_word_operators(self):
        self.assertEqual(ev("1 and 0 or 1"), 1)
        self.assertEqual(ev("not 0"), 1)
        self.assertEqual(ev("7 div 2"), 3)
        self.assertEqual(ev("7 mod 4"), 3)

    def test_errors(self):
        for s in ["sqrt(-4)", "1/0", "7\\0", "7%0", "log(0)", "foo", "pow(-8,1/3)", "time", "1 +", "(1", "min(1)",
                  "nosuch(1)", "2++2", "2*+3", "-+2", "2^+2", "!+2", "!-2", "1?+2:3", "0^-1", "2**2000", "exp(1000)",
                  "2*-(3)", "2+-sin(1)"]:
            with self.subTest(s):
                with self.assertRaises(ExprError):
                    ev(s)

    def test_unsupported_syntax_is_flagged(self):
        from spicelex.expr import Unsupported
        for s in ["2*-(3)", "2+-sin(1)", "2*--2", "1?-(2):3", "0?3:-(2)", "1?-sin(1):3"]:
            with self.subTest(s):
                with self.assertRaises(Unsupported):
                    ev(s)

    def test_names_and_functions(self):
        self.assertEqual(ev("a*2+b", {"a": 3, "b": 1}), 7)
        funcs = {"double": (["x"], parse_expr("2*x+k", NGSPICE), lambda n: {"k": 1}.get(n))}
        self.assertEqual(ev("double(3)", funcs=funcs), 7)
        with self.assertRaises(ExprError):
            ev("double(1,2)", funcs=funcs)

    def test_tree(self):
        t = parse_expr("{a ? b : c+1}", NGSPICE)
        self.assertEqual(t.kind, "Ternary")
        self.assertEqual(parse_expr("-2**2", NGSPICE).kind, "Unary")      # minus is outside the power
        self.assertEqual(parse_expr("f(1,2)", NGSPICE).args[1].value, 2)


if __name__ == "__main__":
    unittest.main()
