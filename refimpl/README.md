# Reference pass 1 and tokenizer

**Not part of the specification.** Nothing in `grammar/`, `spec/` or
`conformance/` depends on this code or refers to it. The spec is the text; this
is a tool that checks the text.

**Not an implementation to build on.** It is a small Python program that lets
the spec authors find mistakes in the spec (see below). A separate
implementation project is planned under clean-room rules
([../docs/clean-room.md](../docs/clean-room.md)); its authors must not read
or reuse this directory. Anything they need must be in the spec.

Written from the spec text and from black-box observation of ngspice. No
simulator source code was read or used.

## What it is for

| Check | How |
|-------|-----|
| The tokenization illustrations in `grammar/00-tokens.md` are what the rules produce | `tests/test_tokens_doc.py` |
| Pass 1 gives the logical lines ngspice's `listing logical` shows, for every `P1-*` doctest | `tests/test_pass1_doc.py` |
| Every accepted doctest example parses; node shapes; the JSON illustrations in `grammar/07-ast.md` are what the parser produces | `tests/test_parser.py` |
| Elaboration gives the `listing expand` text for every `EX-*` doctest; scoping, parameters, errors | `tests/test_elab.py` |
| Expression semantics | `tests/test_expr.py` |
| `number()` matches ngspice on generated words | `tools/diff_numbers.py` (needs ngspice) |
| Expression evaluator matches ngspice on generated expressions | `tools/diff_exprs.py` (needs ngspice) |
| Number rules and dialect differences | `tests/test_numbers.py` |

A failure means the spec text, the examples, or this code is wrong. Fix the
spec first.

## Running

```
cd refimpl
python3 -m unittest discover -s tests                      # no ngspice needed
python3 tools/diff_numbers.py --ngspice /path/to/ngspice   # random words vs ngspice
python3 tools/diff_exprs.py   --ngspice /path/to/ngspice   # random expressions vs ngspice
python3 cli.py pass1  deck.cir [--dialect ngspice|spice3|xyce] [--include]
python3 cli.py tokens deck.cir
python3 cli.py ast    deck.cir [--dialect ...]
```

Python 3, standard library only.

## What it implements

- `spicelex.elab.elaborate`: the flat netlist of `grammar/08-elaboration.md`
  (`cli.py elab`), with a text form in the style of ngspice's `listing expand`.
- `spicelex.expr`: expression parser and evaluator, written to ngspice 42's
  measured behavior (`grammar/05-expressions.md`).
- `spicelex.parse`: the AST of `grammar/07-ast.md` (nodes, JSON form via
  `to_json`), including the decisions in the "Parsing rules" section.
  `python3 cli.py ast deck.cir` prints the JSON.

- `spicelex.pass1`: steps P1 to P11 of `grammar/01-lexical.md`, with dialect
  switches (`spicelex.dialect`). `.include` is expanded only if a loader is
  given.
- `spicelex.tokenize`: the token kinds of `grammar/00-tokens.md`, with origin
  spans that survive line joining.
- `spicelex.number`: the numeric-word classification.

## Simplifications (not specified, chosen here)

- End-of-line comment characters are recognized outside double quotes only.
- `{` inside a word is an ordinary character (A-29).
- `.lib` is not expanded; `.include` expansion is optional (A-28).
- Elaboration does not reproduce ngspice's double prefix for subcircuits defined
  inside subcircuits, and the expression evaluator rejects (`Unsupported`) a
  few forms ngspice accepts but no simple rule explains (A-34).
- The parser follows only the AST spec; it does not check names, counts of
  source-function arguments, or model types (that is elaboration).
- The SPICE3 and Xyce dialect presets use documented behavior only and have
  not been compared with running those tools.
