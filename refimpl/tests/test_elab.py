"""Elaboration tests: the `listing expand` doctests (EX-*), scoping, errors."""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _docs
from spicelex import NGSPICE, parse
from spicelex.elab import elaborate, render


def norm(s):
    return " ".join(s.split())


def el(text, loader=None):
    return elaborate(parse("t\n" + text + "\n.end\n", "d.cir"), NGSPICE, loader)


def lines(text, loader=None):
    return render(el(text, loader))[1:-1]


def codes(nl):
    return [d.code for d in nl.diagnostics]


class ListingExamples(unittest.TestCase):
    # ngspice names a device from a subcircuit that was defined *inside* another
    # one with a doubled prefix (`r.x9.r.x1.r1`). The spec treats names as policy
    # and this reference does not reproduce that; pinned here so a change shows.
    POLICY_DIFFERENCES = {"EX-ENDS-1": ["r.x9.x1.r1 u v 1k"]}

    def test_expand_listings(self):
        cases = [t for t in _docs.examples() if t.get("listing") == "expand"]
        self.assertGreaterEqual(len(cases), 10)
        for t in cases:
            with self.subTest(t["id"]):
                nl = elaborate(parse("\n".join(t["body"]) + "\n", "d.cir"), NGSPICE)
                self.assertEqual(codes(nl), [])
                got = [norm(x) for x in render(nl)]
                want = [norm(x) for x in t["expected_listing"] if x.strip()]
                if t["id"] in self.POLICY_DIFFERENCES:
                    want = [want[0]] + self.POLICY_DIFFERENCES[t["id"]] + [want[-1]]
                self.assertEqual(got, want)

    def test_duplicate_instance_names_differing_in_case(self):
        t = next(t for t in _docs.examples() if t["id"] == "EX-DUP-1")
        nl = elaborate(parse("title\n" + "\n".join(t["body"]) + "\n.end\n"), NGSPICE)
        self.assertIn("duplicate-name", codes(nl))


class Scoping(unittest.TestCase):
    def test_param_order_and_override(self):
        self.assertEqual(lines(".param a=2\n.param b={a*3}\nR1 x 0 {b}"), ["r1 x 0 6.000000000000000e+00"])
        self.assertEqual(lines(".param a=2\n.param a=5\nR1 x 0 {a}"), ["r1 x 0 5.000000000000000e+00"])
        self.assertIn("expression", codes(el("R1 x 0 {later}\n.param later=1")))

    def test_subckt_params(self):
        text = (".param base=10\n.subckt s a b params: r={base*2} c=1\nR1 a b {r}\nR2 a b {c}\n.ends\n"
                "X1 p q s\nX2 p q s r=7 c={base}\n")
        self.assertEqual(lines(text), [
            "r.x1.r1 p q 2.000000000000000e+01", "r.x1.r2 p q 1.000000000000000e+00",
            "r.x2.r1 p q 7.000000000000000e+00", "r.x2.r2 p q 1.000000000000000e+01"])

    def test_param_inside_subckt_is_local(self):
        text = ".subckt s a b\n.param k=5\nR1 a b {k}\n.ends\nX1 p q s\nR2 p q {k}"
        nl = el(text)
        self.assertEqual(lines(text)[0], "r.x1.r1 p q 5.000000000000000e+00")
        self.assertIn("expression", codes(nl))            # k is not visible outside

    def test_nested_subckt_calls_use_caller_scope(self):
        text = (".subckt inner a b params: v=1\nR1 a b {v}\n.ends\n"
                ".subckt outer a b params: w=3\nX1 a b inner v={w*2}\n.ends\nX9 p q outer w=4")
        self.assertEqual(lines(text), ["r.x9.x1.r1 p q 8.000000000000000e+00"])

    def test_models_are_local_to_the_instance(self):
        text = ".subckt s a b\n.model m d(is=1e-14)\nD1 a b m\n.ends\n.model m d(is=2e-14)\nD9 p q m\nX1 p q s\nX2 p q s"
        self.assertEqual(lines(text), [
            ".model m d(is=2e-14)", "d9 p q m",
            ".model x1:m d(is=1e-14)", "d.x1.d1 p q x1:m",
            ".model x2:m d(is=1e-14)", "d.x2.d1 p q x2:m"])

    def test_source_references_are_renamed(self):
        text = ".subckt s a b\nV1 a 0 1\nF1 0 b V1 3\nK1 L1 L2 0.5\n.ends\nX1 p q s"
        out = lines(text)
        self.assertIn("f.x1.f1 0 q v.x1.v1 3", out)
        self.assertIn("k.x1.k1 l.x1.l1 l.x1.l2 5e-1".replace("5e-1", "0.5"), out)

    def test_globals_and_ground(self):
        out = lines(".global vdd\n.subckt s a\nR1 vdd a 1k\nR2 a 0 1k\nR3 a gnd 1k\n.ends\nX1 p s")
        self.assertEqual(out, ["r.x1.r1 vdd p 1k", "r.x1.r2 p 0 1k", "r.x1.r3 p gnd 1k"])

    def test_if_uses_parameters_in_order(self):
        text = ".param sel=2\n.if (sel == 1)\nR1 a 0 1k\n.elseif (sel == 2)\nR1 a 0 2k\n.else\nR1 a 0 3k\n.endif"
        self.assertEqual(lines(text), ["r1 a 0 2k"])

    def test_func_sees_globals_at_definition(self):
        text = ".param k=3\n.func f(x) {x*k}\nR1 a 0 {f(2)}"
        self.assertEqual(lines(text), ["r1 a 0 6.000000000000000e+00"])

    def test_local_model_wins_over_a_parameter_of_the_same_name(self):      # A-36
        out = lines(".param m=5\n.subckt s a b\n.model m d(is=1e-14)\nD1 a b m\n.ends\nX1 p q s")
        self.assertEqual(out[-1], "d.x1.d1 p q x1:m")

    def test_call_parameter_without_a_default_is_set(self):                # A-37
        out = lines(".subckt s a b\nR1 a b {k}\n.ends\nX1 p q s k=3")
        self.assertEqual(out, ["r.x1.r1 p q 3.000000000000000e+00"])

    def test_definitions_may_follow_use(self):
        self.assertEqual(lines("X1 a b s\n.subckt s p q\nR1 p q 1k\n.ends"), ["r.x1.r1 a b 1k"])

    def test_inner_definition_is_local(self):
        text = ".subckt outer p q\n.subckt inner a b\nR1 a b 1k\n.ends\nX1 p q inner\n.ends\nX9 u v outer\nX2 u v inner"
        self.assertIn("unknown-subckt", codes(el(text)))


class Errors(unittest.TestCase):
    def test_errors(self):
        self.assertIn("unknown-subckt", codes(el("X1 a b nosuch")))
        self.assertIn("port-count", codes(el(".subckt s a b\n.ends\nX1 a s")))
        self.assertIn("recursion", codes(el(".subckt s a\nX1 a s\n.ends\nX1 p s")))
        self.assertIn("duplicate-name", codes(el("R1 a 0 1k\nr1 b 0 1k")))
        self.assertIn("expression", codes(el("R1 a 0 {1/0}")))

    def test_run_time_expressions_are_left_alone(self):
        nl = el("B1 a 0 v=v(b)*2\nR1 a 0 r=v(a)+1")
        self.assertEqual([i.rest for i in nl.items], [[], []])
        self.assertEqual(nl.diagnostics, [])

    def test_control_blocks_are_dropped_and_analyses_kept(self):
        nl = el("R1 a 0 1k\n.tran 1u 1m\n.control\nrun\n.endc")
        self.assertEqual([i.kind for i in nl.items], ["element", "directive"])


class Includes(unittest.TestCase):
    def test_include_and_lib(self):
        files = {"inc.cir": "R9 a 0 9k\n.param z=4", "l.lib": ".lib s1\nR1 a 0 1k\n.endl s1\n.lib s2\nR1 a 0 2k\n.endl s2"}
        loader = lambda p: files[p]
        self.assertEqual(lines(".include inc.cir\nR2 a 0 {z}", loader), ["r9 a 0 9k", "r2 a 0 4.000000000000000e+00"])
        self.assertEqual(lines(".lib l.lib s2", loader), ["r1 a 0 2k"])
        self.assertIn("include", codes(el(".include nosuch.cir", loader=lambda p: open("/nonexistent/" + p).read())))
        self.assertIn("include", codes(el(".include inc.cir")))                   # no loader
        self.assertIn("include", codes(el(".lib l.lib nosuch", loader)))


if __name__ == "__main__":
    unittest.main()
