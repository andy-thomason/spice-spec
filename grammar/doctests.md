# Doctests

The grammar files end with examples. Every production has at least one.
Examples are **non-normative**: they illustrate the rules and are checked
against ngspice, but they do not define the language. If an example and the
rule text disagree, the rule text is the specification and the example is a
bug to investigate (or a recorded tool difference). A passing example is not
evidence that a rule is right, and a failing one does not change the rule.

All examples are original and written for this project (see
[../docs/clean-room.md](../docs/clean-room.md)).

## Format

An example is a fenced block with the language `spice-test`:

````
```spice-test id=EL-R-1 covers=resistor,r-simple dialect=ngspice
I1 0 a 1m
R1 a 0 1k
* expect: v(a) = 1
```
````

Attributes on the opening line:

| Attribute | Meaning |
|-----------|---------|
| `id` | Unique ID. |
| `covers` | Comma list of grammar rule names the example exercises. |
| `dialect` | Where it is expected to work (`ngspice`, or omitted for tools in general). Informative. |
| `expect` | `accept` (default), `warn` (runs but the tool warns and ignores something), or `reject` (the tool reports an error). |
| `deck` | `cards` (default): the runner adds a title line, `.end`, and `.op` if there is no analysis card. `full`: the block is a whole deck ending in `.end`. |
| `uses` | Comma list of `spice-file` blocks in the same document to write next to the deck. |
| `needs` | `xspice` if the example needs XSPICE code models (for example `POLY`). Run with `--codemodels DIR`; skipped without it. |
| `skip` | Reason the example is not run. |
| `timeout` | Seconds (default 120). |

A line `* expect: EXPR = VALUE [tol=REL] [atol=ABS]` is a check. It is a
comment to every simulator. The runner evaluates `EXPR` after the analysis
and compares the last point to `VALUE` (default `tol=1e-6`, `atol=1e-12`).
`EXPR` must be real: use `mag()` or `db()` for AC results.

A block with language `spice-file name=FILE` supplies an auxiliary file for
`.include` and `.lib` examples.

### Listing examples (observed behavior)

An example with `listing=logical` or `listing=expand` (and `deck=full`)
does not run an analysis. The runner asks ngspice to print the processed
deck with its `listing` command and compares the text with the block
```` ```spice-listing for=ID ````. Comparison ignores line numbers and
runs of white space. `logical` shows the result of pass 1; `expand` shows
subcircuits flattened and parameters evaluated. The expected text is what
ngspice printed, not what any manual states, and it includes ngspice-only
conventions (lower case, `.global gnd`, the `r.x1.r1` naming). The modes
`physical` and `deck` did not reproduce the original text in batch mode, so
they are not used.

## Running

```
python3 -I tools/doctest.py --ngspice /path/to/ngspice grammar
python3 -I tools/doctest.py --coverage grammar
```

The runner calls `ngspice -n -b` on a generated deck. `--coverage` lists
grammar rules without an example, and `covers=` names that do not match a
rule. Rules without an example are not accepted.

The runner uses ngspice's `.control` language to run the analysis and write
values. That is a property of the runner, not of the examples, which stay
portable cards.
