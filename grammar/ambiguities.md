# Open issues

Each item needs a decision, and where possible a test. Status is `open`
unless marked.

| ID | Issue | Needs |
|----|-------|-------|
| A-01 | Case folding: what is folded and where (file names, strings, `.control`). | Tests per context |
| A-02 | Unit letters that collide with scale letters (`1A`, `1F`). ngspice 42 reads `a` as atto (tested). SPICE3 has no atto; Xyce reads `a` as amperes unless `-hspice-ext units`; HSPICE accepts atto (second-hand, `XYC-REF` 6.2). | LEX-001; HSPICE docs; Xyce run |
| A-03 | Order of comment removal and continuation joining; comment lines between a line and its `+` line. **ngspice 42:** a `+` line continues the card across comment lines and blank lines (P1-CONT-1). Other tools not checked. | Tests on other tools |
| A-04 | `=` is a separator, so `name=value` and two positional fields look alike. Grammar needs keyword tables. | Decision |
| A-05 | Node names in batch versus interactive/control mode; numeric-looking names. | Tests |
| A-06 | `$ % [ ]` allowed in parameter names but also separators or comment markers. | Tests |
| A-07 | Three expression contexts (braced, quoted, bare). Which elements allow which. | Table |
| A-08 | `.control` blocks: in or out of the spec? Proposal: out, listed as `dialect:ngspice`. | Decision |
| A-09 | `.ends` without a name closes all open `.subckt`. | Test |
| A-10 | Unbraced expressions with spaces in `.param`. | Tests, decision |
| A-11 | File names with spaces or quotes in `.include`, `.lib`. | Tests |
| A-12 | Which cards are allowed inside `.if` blocks. | Manual 2.13 and tests |
| A-13 | `U` means URC line or XSPICE digital block. | Disambiguation rule |
| A-14 | `POLY` coefficient ordering and node-pair counting. | Spec page |
| A-15 | `R`, `C`, `L`: value versus model name in the first field. **ngspice 42:** a bare word that names a parameter is also replaced by its value (EX-PARAM-1), so a word can be value, model or parameter; the AST keeps it as `Ident`. | Rule: number, else look up |
| A-16 | `Q` with 3, 4 or 5 nodes: needs a model symbol table. | Decision: allow semantic lookup |
| A-17 | Order and optionality of `DC`, `AC`, `DISTOF`, function on V/I sources. | Tests |
| A-18 | `X` call: where nodes end and `params:` begins. | Manual 2.9.3 |
| A-19 | PWL `r`, `td` on current sources. | Test |
| A-20 | AM source formula versus implementation. **Partly resolved for ngspice 42:** `va*(vo+sin(2*pi*mf*t))*sin(2*pi*fc*t)`, delayed by `td`; role of `phases` still open. | RAD-002; a test for `phases` |
| A-21 | Precedence of unary minus versus `^` (`-2^2`, `2^-2`). | Test |
| A-22 | Function domains. `log` is base 10 in Xyce, natural in PSpice and in Xyce with `-hspice-ext math` (`XYC-REF` 6.1.14, 3.1); ngspice lists `ln, log` together. | Test `log(10)` on ngspice |
| A-23 | Suffixes `a`, `mil`, `t` inside expressions. | Test |
| A-24 | `.dc` sweeps of temperature, parameters and model parameters. | Manual 15.3.2 |

| A-25 | Leading white space: comment in SPICE3 and Xyce, ignored in ngspice. | Test; decision on the spec baseline |
| A-26 | ngspice element forms contain many parameters not in SPICE3 (`m`, `scale`, `tc1`, ...). Spec needs a per-parameter provenance tag. | Table in `spec/03-elements/` |
| A-27 | `DISTOF1`/`DISTOF2` on a source: documented with an optional magnitude, but ngspice 42 rejects the keyword with no value (AN-DISTO-2). | Check the SPICE3 and Xyce docs; decide which is the rule |
| A-28 | Where `.include` and `.lib` are expanded: before parsing (ngspice inserts the text) or as an `Include` node inlined later (07-ast.md). Differences: line numbers, continuation across the boundary. | Decision and a test |
| A-29 | Does `{` inside a word (`abc{1k}`) start a group? | Test |
| A-30 | Decimal-to-double rounding of number values. | Decision |
| A-31 | Whether comments are retained in the tree. | Decision |

## Cross-tool items

SPICE3 (`SP3-UG`) and Xyce (`XYC-REF`) documentation has now been read for
the lexical rules, source functions and a few element forms. The rest of the
rows still only have ngspice evidence. HSPICE has not been read. Rows A-02,
A-04, A-07, A-17, A-21 and A-25 are the most likely to differ.
