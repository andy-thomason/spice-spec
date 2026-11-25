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
| A-20 | AM source. **Resolved for ngspice 42** (spec/06-sources/waveforms.md): the formula is `va*(vo+sin(2*pi*mf*(t-td)))*sin(2*pi*fc*(t-td))`, `phases` is accepted and ignored, and fewer than four parameters give a zero source. Other tools not checked. | Tests on other tools |
| A-21 | Precedence of unary minus versus `^` (`-2^2`, `2^-2`). **Resolved for ngspice 42** (05-expressions.md rules 1 to 5): unary minus is looser than power and product; power is left-associative; `**` drops the sign of its base. Other tools not checked. | Tests on other tools |
| A-22 | Function domains. `log` is base 10 in Xyce, natural in PSpice and in Xyce with `-hspice-ext math` (`XYC-REF` 6.1.14, 3.1). **ngspice 42: `log` is natural** (EXPR-12). Arithmetic is IEEE and only a non-finite final value is an error (EXPR-10, EXPR-11). | Test on Xyce |
| A-23 | Suffixes `a`, `mil`, `t` inside expressions. | Test |
| A-24 | `.dc` sweeps of temperature, parameters and model parameters. | Manual 15.3.2 |

| A-25 | Leading white space: comment in SPICE3 and Xyce, ignored in ngspice. | Test; decision on the spec baseline |
| A-26 | ngspice element forms contain many parameters not in SPICE3 (`m`, `scale`, `tc1`, ...). Spec needs a per-parameter provenance tag. | Table in `spec/03-elements/` |
| A-27 | `DISTOF1`/`DISTOF2` on a source: documented with an optional magnitude, but ngspice 42 rejects the keyword with no value (AN-DISTO-2). | Check the SPICE3 and Xyce docs; decide which is the rule |
| A-28 | Where `.include` and `.lib` are expanded: before parsing (ngspice inserts the text) or as an `Include` node inlined later (07-ast.md). Differences: line numbers, continuation across the boundary. | Decision and a test |
| A-29 | Does `{` inside a word (`abc{1k}`) start a group? | Test |
| A-30 | Decimal-to-double rounding of number values. | Decision |
| A-31 | Whether comments are retained in the tree. | Decision |
| A-32 | Which words are flags and which are positional (`off` for D, Q, J, Z, M is a flag; `on`/`off` on S and W stay in `rest`). The list is a parser decision, not observed. | Test per device |
| A-33 | Which keyword parameters take expressions (`r`, `c`, `q`, `l`, `v`, `i`, `vol`, `cur`). Parser decision. | Check each tool's manual |
| A-34 | Expression forms ngspice 42 accepts but no simple rule explains: `--2**2` is -4, `2*--2` is -4, a minus after `?` or `:` before a non-number (`1?-(2):3` is 2). A tool may reject them. | Decision |
| A-35 | Which naming form for flattened items a conforming tool must produce, if any (08-elaboration.md). | Decision |
| A-36 | A bare name in a value slot that is both a local model and a parameter: which wins. | Test |
| A-37 | Subcircuit call parameters that have no default: set or error. | Test |
| A-38 | `.lib` sections that call each other; `.include` inside a subcircuit. | Test |
| A-39 | Where the documents differ from measured source behavior: `SIN` before its delay, the `AM` formula and `fc` default, `np` on `PULSE` (spec/06-sources/waveforms.md). | Tests on other tools |
| A-40 | A zero `tr`/`tf` on `PULSE` is replaced by `tstep`: the print step or an internal limit. | Test with a different `tmax` |
| A-41 | `.dc` step with the wrong sign for the range. ngspice: no points. Xyce: warning, one point. | Spec treats as an error. `spec/07-analyses/analyses.md` section 3. |
| A-42 | `.ic` with `.op` and element `ic=` without `uic`. ngspice ignores both. Xyce applies both. | Not portable; no defined effect. Section 2 and 6. |
| A-43 | `.ac` point set when `FSTOP/FSTART` is not a whole number of decades or octaves. ngspice rescales `dec` spacing to end at `FSTOP`, not `oct`. Xyce keeps the nominal ratio. | Implementation-defined. Section 4. |
| A-44 | Several analysis cards in one deck: order, and which results are kept. | Not yet measured. |
| A-45 | `DC` keyword followed directly by a waveform (`V1 a 0 dc pulse(...)`). Both tools accept it. The source grammar requires a value after `DC`. | Evidence: `seen` in sky130 and gf180mcu, `measured` on ngspice and Xyce (LIB-DC-1). Grammar to be extended. |
| A-46 | `.option scale=S`: which parameters it multiplies. Both tools scale MOS `w` and `l`; the rest is unmeasured. | `seen` in sky130 (165 uses); `measured` for `w`, `l` (LIB-SCALE-1). |
| A-47 | Model binning (`name.N` with `lmin` `lmax` `wmin` `wmax`): which model kinds support it and the boundary rule. ngspice: BSIM3 and BSIM4 only (level 1 is an error). Xyce: picks `lmin <= l < lmax` even for level 1, with a warning. | `seen` in three libraries; `documented` (`NGS-42` 3.2.3); `measured` in part. No doctest runs on both. |
| A-48 | Diode diffusion capacitance (`tt`) with no junction capacitance. ngspice includes it. Xyce 7.10 gives none in AC unless `cj0` is non-zero. | `measured` (EL-CAP-D-1, EL-CAP-D-2); spec follows the documents, which give `C = tt * gd` unconditionally. |
| A-49 | Level 1 MOSFET temperature behavior with `gamma` not 0, and the forms of `kp(T)` and `vto(T)` that the documents do not print. Fitted to measurements at `gamma = 0` only. | `measured` (TMP-M-1, TMP-M-2). |

## Cross-tool items

SPICE3 (`SP3-UG`) and Xyce (`XYC-REF`) documentation has now been read for
the lexical rules, source functions and a few element forms. The rest of the
rows still only have ngspice evidence. HSPICE has not been read. Rows A-02,
A-04, A-07, A-17, A-21 and A-25 are the most likely to differ.

Xyce 7.10 has now been run on the doctest examples (spec/11-compat/): the
number tail rule, `=` as a separator, expression precedence and associativity
(`^` is a logical xor, `**` is right-associative), `log`, rounding of `nint`,
time-zero source values, `.if`, `.temp`, and the unsupported analyses all differ
from ngspice.
