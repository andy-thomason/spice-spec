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
| `number()` matches ngspice on generated words | `tools/diff_numbers.py` (needs ngspice) |
| Number rules and dialect differences | `tests/test_numbers.py` |

A failure means the spec text, the examples, or this code is wrong. Fix the
spec first.

## Running

```
cd refimpl
python3 -m unittest discover -s tests                      # no ngspice needed
python3 tools/diff_numbers.py --ngspice /path/to/ngspice   # random words vs ngspice
python3 cli.py pass1  deck.cir [--dialect ngspice|spice3|xyce] [--include]
python3 cli.py tokens deck.cir
```

Python 3, standard library only.

## What it implements

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
- The SPICE3 and Xyce dialect presets use documented behavior only and have
  not been compared with running those tools.
