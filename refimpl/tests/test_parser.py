"""Reference parser tests: every doctest example must parse; structure of the
main node types; the JSON illustrations in grammar/07-ast.md must be a subset
of what the parser produces."""
import json, os, re, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _docs
from spicelex import NGSPICE, SPICE3, parse, to_json


def deck(body, dialect=NGSPICE, title="t"):
    return parse("%s\n%s\n.end\n" % (title, body), "deck.cir", dialect)


def first(body, **kw):
    return deck(body, **kw).items[0]


def errors(d):
    return [g for g in d.diagnostics if g.severity == "error"]


class Examples(unittest.TestCase):
    def test_every_example_parses(self):
        """No error diagnostics for any example that is expected to be accepted
        (or that only warns). Reject examples are tool-level rejections, which
        a syntactic parser need not reproduce."""
        n = 0
        for t in _docs.examples():
            if t.get("expect", "accept") == "reject" or "skip" in t:
                continue
            body = "\n".join(t["body"])
            text = body + "\n" if t.get("deck") == "full" else "title\n" + body + "\n.end\n"
            with self.subTest(t["id"]):
                d = parse(text, "ex.cir", NGSPICE)
                self.assertEqual([(g.code, g.message) for g in errors(d)], [])
                bad = [i for i in d.items if i.kind == "Invalid"]
                if t.get("expect") == "warn":
                    self.assertTrue(bad)
                else:
                    self.assertEqual([i.raw for i in bad], [])
            n += 1
        self.assertGreater(n, 80)

    def test_reject_examples_that_are_token_errors(self):
        for text in ["t\nV1 a 0 {2 * 3\n.end\n", "t\nV1 a 0 1D-3\nR1 a 0 1k\n.end\n"]:
            self.assertTrue(errors(parse(text)), text)


class Elements(unittest.TestCase):
    def test_resistor_forms(self):
        e = first("R1 a 0 1k")
        self.assertEqual((e.letter, e.name.text, [n.text for n in e.nodes]), ("R", "R1", ["a", "0"]))
        self.assertEqual(e.rest[0].kind, "NumberLit")
        e = first("R1 a 0 rm l=10u w=1u")
        self.assertEqual([r.kind for r in e.rest], ["Ident"])
        self.assertEqual([p.name.lower for p in e.params], ["l", "w"])
        e = first("R1 a 0 r='1k+1k' tc1=2m")
        self.assertEqual(e.params[0].value.form, "quoted")
        e = first("R1 a 0 r=v(a)*2 tc1=2m")
        self.assertEqual((e.params[0].value.form, e.params[0].value.raw), ("bare", "v(a)*2"))
        self.assertEqual(e.params[1].name.lower, "tc1")
        e = first("R1 a 0 {2*3}")
        self.assertEqual(e.rest[0].form, "braced")

    def test_invalid_line_is_recorded(self):
        d = deck("R1 a b\nR2 a 0 1k")
        self.assertEqual([i.kind for i in d.items], ["Invalid", "Element"])
        self.assertEqual(d.items[0].severity, "warning")
        self.assertEqual(deck("R1 a b", dialect=SPICE3).items[0].severity, "error")
        self.assertEqual(deck("R1 a").items[0].kind, "Invalid")        # too few nodes

    def test_values_decided_by_lexical_class(self):
        e = first("D1 a b dm area=2 off")
        self.assertEqual([r.text for r in e.rest], ["dm"])
        self.assertEqual([(p.name.lower, p.has_equals) for p in e.params], [("area", True), ("off", False)])
        e = first("C1 a 0 1u ic=0")
        self.assertEqual(e.params[0].value.text, "0")

    def test_multi_valued_param(self):
        e = first("Q1 c b e qm ic=0.6, 5.0")
        self.assertEqual([m.text for m in [e.params[0].value] + e.params[0].more], ["0.6", "5.0"])

    def test_bjt_keeps_open_fields_in_rest(self):
        e = first("Q1 c b e sub qm 2")
        self.assertEqual(([n.text for n in e.nodes], [r.text for r in e.rest]), (["c", "b", "e"], ["sub", "qm", "2"]))
        e = first("M1 d g s b nm w=1u l=1u")
        self.assertEqual(([n.text for n in e.nodes], [r.text for r in e.rest]), (["d", "g", "s"], ["b", "nm"]))

    def test_x_call(self):
        e = first("X1 a b c sub params: r=2k")
        self.assertEqual(([n.text for n in e.nodes], [r.text for r in e.rest]), ([], ["a", "b", "c", "sub"]))
        self.assertTrue(e.get("params_marker"))
        self.assertEqual(e.params[0].name.lower, "r")

    def test_dependent_sources(self):
        e = first("E1 b 0 a 0 2")
        self.assertEqual([r.text for r in e.rest], ["a", "0", "2"])
        e = first("E1 b 0 poly(1) a 0 0 3")
        self.assertEqual((e.poly.dim.text, [i.text for i in e.poly.items], e.rest), ("1", ["a", "0", "0", "3"], []))
        e = first("E1 b 0 vol='v(a)*2'")
        self.assertEqual(e.params[0].value.form, "quoted")
        e = first("B1 b 0 v=v(a)+1")
        self.assertEqual(e.params[0].value.raw, "v(a)+1")
        e = first("F1 0 b V1 3")
        self.assertEqual([r.text for r in e.rest], ["V1", "3"])

    def test_source_specs(self):
        s = first("V1 a 0 5").source
        self.assertEqual((s.dc.text, s.has_dc_keyword, s.get("function")), ("5", False, None))
        s = first("V1 a 0 dc 2 ac 1 90").source
        self.assertEqual((s.dc.text, s.ac.mag.text, s.ac.phase.text), ("2", "1", "90"))
        s = first("V1 a 0 pulse(0 1 0 1n 1n 5u 10u)").source
        self.assertEqual((s.function.name.lower, len(s.function.args), s.function.has_parens), ("pulse", 7, True))
        s = first("V1 a 0 sin 0 1 1k").source
        self.assertEqual((s.function.has_parens, len(s.function.args)), (False, 3))
        s = first("V1 a 0 pwl(0 0 1m 2) r=0 td=1u").source
        self.assertEqual(([p.name.lower for p in s.function.params], len(s.function.args)), (["r", "td"], 4))
        s = first("I1 0 a ac 1 sin(0 1 1k)").source
        self.assertEqual((s.get("dc"), s.ac.mag.text, s.function.name.text), (None, "1", "sin"))


class DotCards(unittest.TestCase):
    def test_subckt_nesting_and_ends(self):
        d = deck(".subckt outer p q\n.subckt inner a b\nR1 a b 1k\n.ends\nX1 p q inner\n.ends outer\nX9 u v outer")
        self.assertEqual([i.kind for i in d.items], ["Subckt", "Element"])
        outer = d.items[0]
        self.assertEqual([i.kind for i in outer.items], ["Subckt", "Element"])
        self.assertEqual(outer.ends_name.text, "outer")
        self.assertEqual([i.kind for i in outer.items[0].items], ["Element"])
        self.assertEqual(errors(d), [])

    def test_subckt_ports_and_params(self):
        s = first(".subckt s in out params: r=1k c=1p\n.ends").__class__ and deck(".subckt s in out params: r=1k c=1p\n.ends").items[0]
        self.assertEqual(([p.text for p in s.ports], [p.name.lower for p in s.params], s.get("params_marker")),
                         (["in", "out"], ["r", "c"], True))

    def test_param_forms(self):
        c = first(".param a=1 b={a+1} c='a*2' d=2*3 e=rv")
        kinds = [(p.name.lower, p.value.kind, p.value.get("form")) for p in c.assignments]
        self.assertEqual(kinds, [("a", "NumberLit", None), ("b", "Expr", "braced"), ("c", "Expr", "quoted"),
                                 ("d", "Expr", "bare"), ("e", "Ident", None)])

    def test_func_global_temp_include_lib(self):
        f = first(".func double(x) {2*x}")
        self.assertEqual((f.name.text, [a.text for a in f.args], f.body.form), ("double", ["x"], "braced"))
        self.assertEqual([n.text for n in first(".global vdd gnd").nodes], ["vdd", "gnd"])
        self.assertEqual(first(".temp 50").value.value, 50.0)
        i = first('.include "my inc.cir"')
        self.assertEqual((i.path, i.form), ("my inc.cir", "double_quoted"))
        self.assertEqual(first(".include a.cir").form, "bare")
        u = first(".lib l.lib sec")
        self.assertEqual((u.kind, u.path, u.section.text), ("LibUse", "l.lib", "sec"))
        l = deck(".lib sec\nR1 a 0 1k\n.endl sec\nR2 a 0 1k").items
        self.assertEqual(([i.kind for i in l], [i.kind for i in l[0].items]), (["LibDef", "Element"], ["Element"]))

    def test_if_blocks(self):
        d = deck(".if (1 > 2)\nR1 a 0 1k\n.elseif (2 > 1)\nR1 a 0 2k\n.else\nR1 a 0 3k\n.endif\nR9 a 0 1k")
        self.assertEqual([i.kind for i in d.items], ["If", "Element"])
        br = d.items[0].branches
        self.assertEqual(([b.cond.raw if b.cond else None for b in br]), ["(1 > 2)", "(2 > 1)", None])
        self.assertTrue(all(len(b.items) == 1 for b in br))

    def test_control_block_is_raw(self):
        d = deck("R1 a 0 1k\n.control\nrun\nplot v(a)\n.endc")
        self.assertEqual([i.kind for i in d.items], ["Element", "OtherDot"])
        self.assertEqual(d.items[1].raw, "run\nplot v(a)")

    def test_unknown_dot_card_is_kept(self):
        o = first(".print tran v(a) i(v1)")
        self.assertEqual((o.name, o.raw), ("print", ".print tran v(a) i(v1)"))

    def test_analyses(self):
        t = first(".tran 10u 1m 0 1u uic")
        self.assertEqual((t.tstep.text, t.tstop.text, t.tstart.text, t.tmax.text, t.uic), ("10u", "1m", "0", "1u", True))
        a = first(".ac dec 10 1 1meg").sweep
        self.assertEqual((a.variation, a.points.text, a.fstop.value), ("dec", "10", 1e6))
        dc = first(".dc V1 0 5 1 V2 0 1 0.5")
        self.assertEqual([(s.source.text, s.step.text) for s in dc.sweeps], [("V1", "1"), ("V2", "0.5")])
        n = first(".noise v(out,ref) Vin dec 5 10 1k")
        self.assertEqual((n.output.args[0].text, n.reference.text, n.source.text), ("out", "ref", "Vin"))
        self.assertEqual(first(".tf v(5,3) VIN").output.args[1].text, "3")
        p = first(".pz a 0 b 0 vol pol")
        self.assertEqual(([x.text for x in p.nodes], p.pz_kind, p.mode), (["a", "0", "b", "0"], "vol", "pol"))
        self.assertEqual(first(".sens v(out) ac dec 10 100 100k").ac.variation, "dec")
        self.assertEqual(first(".disto dec 2 100 1k 0.9").f2overf1.text, "0.9")
        ic = first(".ic v(a)=2 v(b)=0")
        self.assertEqual([(i.target.args[0].text, i.value.text) for i in ic.items], [("a", "2"), ("b", "0")])
        self.assertEqual(first(".nodeset all=5").all.text, "5")
        o = first(".options reltol=1e-4 noacct")
        self.assertEqual([(p.name.lower, p.has_equals) for p in o.items], [("reltol", True), ("noacct", False)])

    def test_end_and_diagnostics(self):
        d = parse("t\nR1 a 0 1k\n")
        self.assertIn("missing-end", [g.code for g in d.diagnostics])
        d = parse("t\n.subckt s a\nR1 a 0 1k\n.end\n")
        self.assertIn("unclosed-block", [g.code for g in d.diagnostics])
        d = parse("t\nR1 a 0 1k\n.end\nR2 a 0 1k\n")
        self.assertEqual(len(d.items), 1)
        self.assertIsNotNone(d.end)

    def test_dialect_extension_diagnostic(self):
        d = parse("t\n.param x=1\nV1 a 0 am(1 0 1k 1meg)\nY1 a b 0 m\n.end\n", "x", SPICE3)
        self.assertEqual(sorted(g.code for g in d.diagnostics), ["dialect-extension"] * 3)
        self.assertEqual([g.code for g in parse("t\n.param x=1\n.end\n").diagnostics], [])


class Invariants(unittest.TestCase):
    def spans(self, x, out):
        from spicelex import Node
        if isinstance(x, Node):
            if "span" in x.f:
                out.append(x)
            for v in x.f.values():
                self.spans(v, out)
        elif isinstance(x, list):
            for v in x:
                self.spans(v, out)

    def test_items_in_source_order_with_spans(self):
        text = ("t\nR1 a 0 1k\n.subckt s p q\nR1 p q 1k\n.ends\nV1 a 0 sin(0 1 1k)\n"
                ".model dm d(is=1e-14)\nD1 a 0 dm\n.tran 1u 1m\n.end\n")
        d = parse(text, "x.cir")
        lines = [i.span.line for i in d.items]
        self.assertEqual(lines, sorted(lines))
        nodes = []
        self.spans(d.items, nodes)
        src = text.split("\n")
        for n in nodes:
            sp = n.span
            self.assertGreaterEqual(sp.line, 2)
            self.assertLessEqual((sp.line, sp.col), (sp.end_line, sp.end_col))
            if sp.line == sp.end_line and n.kind in ("Ident", "NumberLit"):
                self.assertEqual(src[sp.line - 1][sp.col - 1:sp.end_col - 1].lower(), n.text.lower())

    def test_element_node_count_matches_table(self):
        from spicelex.parser import ELEMENTS
        for letter, (k, _) in ELEMENTS.items():
            if letter in "KX":
                continue
            line = "%s1 %s 1k" % (letter, " ".join("n%d" % i for i in range(k)))
            d = deck(line)
            it = d.items[0]
            self.assertEqual(len(it.nodes) if it.kind == "Element" else -1, k, letter)


class JsonIllustrations(unittest.TestCase):
    def subset(self, want, got, path=""):
        if isinstance(want, dict):
            self.assertIsInstance(got, dict, path)
            for k, v in want.items():
                self.assertIn(k, got, path + "." + k)
                self.subset(v, got[k], path + "." + k)
        elif isinstance(want, list):
            self.assertEqual(len(want), len(got), path)
            for i, (a, b) in enumerate(zip(want, got)):
                self.subset(a, b, "%s[%d]" % (path, i))
        else:
            self.assertEqual(want, got, path)

    def test_07_ast_examples(self):
        text = open(os.path.join(_docs.ROOT, "grammar", "07-ast.md"), encoding="utf-8").read()
        blocks = re.findall(r"```json\n(.*?)```", text, re.S)
        self.assertEqual(len(blocks), 3)
        d = parse("t\nR1 a 0 1k\nV1 a 0 dc 0 sin(0 1 1k)\nR1 a b\n.end\n", "deck.cir")
        got = json.loads(json.dumps(to_json(d)))["items"]
        for want, g in zip(blocks, got):
            self.subset(json.loads(want), g)


if __name__ == "__main__":
    unittest.main()
