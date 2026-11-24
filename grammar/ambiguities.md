# Open issues

Each item needs a decision, and where possible a test. Status is `open`
unless marked.

| ID | Issue | Needs |
|----|-------|-------|
| A-01 | Case folding: what is folded and where (file names, strings, `.control`). | Tests per context |
| A-02 | Unit letters that collide with scale letters (`1A`, `1F`). **Resolved for ngspice 42:** they are scale factors. Needs checking in other tools. | LEX-001; HSPICE docs |
| A-03 | Order of comment removal and continuation joining; comment lines between a line and its `+` line. | Tests |
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
| A-15 | `R`, `C`, `L`: value versus model name in the first field. | Rule: parses as number or not |
| A-16 | `Q` with 3, 4 or 5 nodes: needs a model symbol table. | Decision: allow semantic lookup |
| A-17 | Order and optionality of `DC`, `AC`, `DISTOF`, function on V/I sources. | Tests |
| A-18 | `X` call: where nodes end and `params:` begins. | Manual 2.9.3 |
| A-19 | PWL `r`, `td` on current sources. | Test |
| A-20 | AM source formula versus implementation. | Test |
| A-21 | Precedence of unary minus versus `^` (`-2^2`, `2^-2`). | Test |
| A-22 | Function domains and `log` base. | Tests |
| A-23 | Suffixes `a`, `mil`, `t` inside expressions. | Test |
| A-24 | `.dc` sweeps of temperature, parameters and model parameters. | Manual 15.3.2 |

## Cross-tool items

Every row above needs the same question asked of Xyce and HSPICE. That has
not been done: only ngspice has been consulted. Rows A-02, A-04, A-07, A-17
and A-21 are the most likely to differ.
