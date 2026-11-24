# 01 Lexical structure

Sources: `SP3-UG` (Circuit Description), `NGS-42` 2.1 and 2.3, `XYC-REF`
2.1.39. Registry and URLs: [../sources/README.md](../sources/README.md).
Each row or rule below gives its tag and sources.

## Pass 1: physical lines to logical lines

Pass 1 is a procedure, not a grammar. Apply these steps in order.

| Step | Rule | Notes |
|------|------|-------|
| P1 | Read the file as UTF-8. Stop with an error on invalid UTF-8. | `dialect:ngspice`. `NGS-42` 2.1.2.1. |
| P2 | The **first physical line is the title**, whatever it contains. | `core`. `SP3-UG` "Title Line"; `NGS-42` 2.1.1, 2.3.1. A leading `*` still works because the title is free text. |
| P3 | **Dialect split.** SPICE3 and Xyce: a line whose first character is white space is a comment, unless the next non-blank character is `+` (continuation). ngspice: leading white space is ignored and the line is parsed normally. Empty lines are dropped. | `SP3-UG` "Comments"; `XYC-REF` 2.1.39.1; `NGS-42` 2.1.1. A-25. |
| P4 | If a line's first character is one of `=[]?()&%$\"!:` (and `§`), replace it by `*` and warn. | ngspice 2.1.2.2. Treated as a comment. |
| P5 | A line starting with `*` is a comment. Drop it. | `core`/`common`. `SP3-UG` "Comments"; `NGS-42` 2.3.3; `XYC-REF` 2.1.39.1. |
| P6 | `core`/`common`. `SP3-UG` Description; `NGS-42` 2.3.5; `XYC-REF` 2.1.39.3. A line starting with `+` continues the previous logical line. Remove the `+` and join with a blank. | The continuation must directly follow. Comment lines between a line and its `+` line: **open, see A-03**. |
| P7 | A line ending in two backslashes (`\\`) is joined with the next line. | `dialect:ngspice`. `NGS-42` 2.1.4.1, 2.3.5. Not allowed for `.title`, `.lib`, `.include` (2.3.5). |
| P8 | Remove an end-of-line comment. `;` is `common` (`NGS-42` 2.3.4; `XYC-REF` 2.1.39.2). `$ ` and `//` are `dialect:ngspice` (`NGS-42` 2.3.4), and `$` is an ordinary character in ngspice's PSPICE compatibility mode. SPICE3 documents no end-of-line comment. | |
| P9 | Expand `.include` in place (before pass 2 sees the next line). | `.lib file name` selects a section. See 02-netlist.md. |
| P10 | A `.title text` line anywhere replaces the title. | ngspice 2.3.1. |
| P11 | The last logical line must be `.end`. | `core`. `SP3-UG` ".End line"; `NGS-42` 2.3.2; `XYC-REF` 2.1.6 (documented; wording not read). |

Case folding: node and device names are case-insensitive in batch mode. In
interactive or control mode, they follow the front end's rules (2.1.4.4).
**Open: A-01** on what is case-folded where, since file names and some
strings must keep their case.

Order of P6 and P8 matters: comments are removed from each physical line
before joining, so a `;` comment on a line does not swallow a following `+`
line. This follows the manual text for continuation lines (2.3.5), which
says end-of-line comments are ignored. **To confirm by test, A-03.**

## Separators

Tag `core`. Sources: `SP3-UG` Description (field separators), `NGS-42`
2.1.4.1. Not yet checked in `XYC-REF`. Fields are split at any run of blanks,
commas, equals signs and parentheses:

```abnf
SEP   = 1*( SP / HTAB / "," / "=" / "(" / ")" )
```

Consequences, which the spec must state explicitly because they surprise
people:

- `SIN(0 1 1k)`, `SIN 0 1 1k` and `SIN(0,1,1k)` are the same tokens.
- `r=5`, `r = 5` and `r 5` are the same tokens. A parameter assignment
  `name = value` therefore cannot be told from two positional fields by
  separators alone. The element rule decides, by position and by keyword.
  **Open: A-04.**
- `DC=3` and `DC 3` are the same (tested on ngspice 42, LEX-001).

Because `=` is a separator, the `=` is written as a literal token in rules
below for readability, and an implementation may treat it as optional.

## Numbers

Sources: `SP3-UG` Description ("Numbers"), `NGS-42` 2.1.4.2 and 2.1.4.3,
`XYC-REF` 3.1 and 6.2, test LEX-001. Tags are given per rule.

```abnf
number     = [ sign ] mantissa [ exponent ] [ scale ] *letter    ; LM
sign       = "+" / "-"
mantissa   = 1*DIGIT [ "." *DIGIT ] / "." 1*DIGIT
exponent   = "e" [ sign ] 1*DIGIT
scale      = "t" / "g" / "meg" / "k" / "mil" / "m" / "u" / "n" / "p" / "f"
           / a-atto                      ; dialect-dependent, see rule 5
a-atto     = "a"
letter     = ALPHA
```

Rules:

1. Case does not matter. `M` and `m` both mean milli. Mega is `meg`.
2. **Longest match** between `meg`, `mil` and `m`. `1Mi` is milli (1e-3),
   because `mi` is not `mil`; the trailing `i` is ignored.
3. Letters after the number that do not start a scale factor are ignored
   (`10V`, `10Volts`, `1Hz`). Letters after a scale factor are ignored
   (`1MEGOHM`, `2MA`).
4. Therefore a **unit letter that is also a scale letter is a scale
   factor**: `1A` is 1e-18 (atto), `1F` is 1e-15 (femto), `1G` is 1e9,
   `1T` is 1e12. `5V` is 5.

5. **The letter `a` differs between tools.** SPICE3's list has no `a`
   (`SP3-UG`), so `1A` is 1. ngspice reads `a` as atto (1e-18, tested in
   LEX-001). `XYC-REF` 6.2 says HSPICE accepts atto and Xyce does not, and
   3.1 says Xyce treats `a` as amperes unless started with
   `-hspice-ext units`. `a-atto` is therefore `dialect:ngspice`, and
   believed `dialect:hspice` (second-hand). Plain `core` is the list
   without it. A-02.

Rules 1 to 3 are `core` (`SP3-UG`, `NGS-42`). Rule 4's examples with `A` are
ngspice. Rules 3 and 4 were checked on ngspice 42 (test LEX-001).

| Text | Value |
|------|-------|
| `1k`, `1kHz`, `1000`, `1e3`, `1.0e3` | 1000 |
| `10Volts`, `10V`, `10` | 10 |
| `1Meg`, `1MEGOHM` | 1e6 |
| `1m`, `1Mi`, `2MA` | 1e-3, 1e-3, 2e-3 |
| `1mil` | 25.4e-6 |
| `1A` | 1e-18 in ngspice; 1 in SPICE3 (documented, untested) |
| `1F` | 1e-15 (`f` is femto in every tool listed) |

Dialect notes: LT compatibility mode accepts RKM notation
such as `2K7` and `100R` (manual 2.1.4.3). HSPICE is believed to use the
same suffixes but treats some unit words differently. Compare when HSPICE
documentation is read.

## Names

Sources: `SP3-UG` Description (name and node rules), `NGS-42` 2.1.4.4, 2.1.4.5. Device name and ground rules are
`core`; the `gnd` alias and the excluded characters are `dialect:ngspice`.

```abnf
device-name = LETTER *name-char          ; first letter selects element type
node-name   = 1*name-char                ; see node rules below
name-char   = any character except SEP and "=" "%" "(" ")" "," "[" "]" "<" ">" "~"
```

- Device names start with a letter (A to Z) and cannot contain separators.
- Node names are arbitrary strings, not evaluated as numbers: `0` and `00`
  are different nodes (manual 2.1.4.5).
- In batch mode a node name may start with a digit. In interactive or
  control mode, plain numbers are accepted but other names may not start
  with a number (2.1.4.4). **Open: A-05.**
- Ground is `0`. The name `gnd` is accepted and converted to `0` unless the
  option `no_auto_gnd` is set.

## Parameter names

`dialect:ngspice` and `common` with Xyce for `.param` itself (`NGS-42`
2.9.1; `XYC-REF` 2.1.26). SPICE3 has no `.param`. The character set below is
ngspice only.

```abnf
param-name = ALPHA *( ALPHA / DIGIT / "!" / "#" / "$" / "%" / "[" / "]" / "_" )
```

Manual 2.9.1. Some of these characters are also separators or comment
markers elsewhere (`$`, `%`, `[`, `]`), so the lexer needs the context
"inside `.param`" to read them. **Open: A-06.** Reserved names: `time`,
`temper`, `hertz`, `or`, `and`, `not`, `div`, `mod`, `defined`, and the
function names (manual 2.9.6).

## Expression tokens

`dialect:ngspice` (`NGS-42` 2.9.1, 2.9.7). `XYC-REF` 2.2 also allows braces
and single quotes ("best practice ... braces ... for compatibility,
single quotation marks"), which makes those two forms `common`.

An expression is written in one of three forms:

```abnf
braced     = "{" expr "}"        ; evaluated at netlist-expansion time
quoted     = "'" expr "'"        ; same time as braced
bare       = expr                ; run-time in B, E, G, R, L, C sources
```

Braced and quoted expressions are evaluated when the deck is expanded.
Bare expressions in behavioral elements are evaluated during analysis. See
05-expressions.md and **A-07**.

## Examples (non-normative)

Examples illustrate the rules above and are **not normative**: where an
example and the rule text disagree, the rule text is the specification and
the example is a bug to investigate. Examples run as doctests on ngspice
(`tools/doctest.py`; see [doctests.md](doctests.md)). All are original.


A signed number with a fraction and an exponent.

```spice-test id=LEX-NUM-1 covers=number,sign,mantissa,exponent,value
V1 a 0 -1.5e-3
R1 a 0 1k
* expect: v(a) = -1.5e-3
```

Scale factors; letters after a number or a scale factor are ignored.

```spice-test id=LEX-NUM-2 covers=scale,letter
V1 a 0 2k
V2 b 0 3MEGohm
V3 c 0 10Volts
V4 d 0 5mil
R1 a 0 1k
R2 b 0 1k
R3 c 0 1k
R4 d 0 1k
* expect: v(a) = 2000
* expect: v(b) = 3e6
* expect: v(c) = 10
* expect: v(d) = 1.27e-4
```

In ngspice `a` is atto. SPICE3 has no atto; Xyce reads `a` as amperes unless started with `-hspice-ext units`.

```spice-test id=LEX-NUM-3 covers=a-atto dialect=ngspice
V1 a 0 3a
R1 a 0 1k
* expect: v(a) = 3e-18 tol=1e-6 atol=1e-24
```

Names are free-form. Node `0` and node `00` are different nodes; `=`, commas and parentheses are separators.

```spice-test id=LEX-SEP-1 covers=device-name,name-char,node-name
V_in 1 0 1
V_two 00 0 2
Rload_1 1 0 1k
Rload_2 00 0 1k
* expect: v(1) = 1
* expect: i(v_two) = -2e-3
```

Separators: these two lines are equal. `DC=3` and `DC 3` are the same tokens.

```spice-test id=LEX-SEP-2
V1 a 0 DC=3
V2 b 0 DC 3
R1 a 0 1k
R2 b 0 1k
* expect: v(a) = 3
* expect: v(b) = 3
```

A parameter name and a braced expression.

```spice-test id=LEX-PARAM-1 covers=param-name,param-card,param-assign,braced dialect=ngspice
.param my_p1=3
V1 a 0 {my_p1*2}
R1 a 0 1k
* expect: v(a) = 6
```

A quoted expression is evaluated at expansion time. A bare expression in a behavioral source is evaluated during analysis.

```spice-test id=LEX-EXPR-1 covers=quoted,bare dialect=ngspice
.param q='2*3'
V1 a 0 'q'
B1 b 0 V=2*3
R1 a 0 1k
R2 b 0 1k
* expect: v(a) = 6
* expect: v(b) = 6
```
