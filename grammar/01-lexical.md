# 01 Lexical structure

Source: ngspice manual 2.1, 2.3, 2.9.5. Tag `dialect:ngspice` unless stated.

## Pass 1: physical lines to logical lines

Pass 1 is a procedure, not a grammar. Apply these steps in order.

| Step | Rule | Notes |
|------|------|-------|
| P1 | Read the file as UTF-8. Stop with an error on invalid UTF-8. | ngspice 2.1.2.1. |
| P2 | The **first physical line is the title**, whatever it contains. | A leading `*` still works because the title is free text. |
| P3 | Strip leading white space from every line. Drop empty lines. | |
| P4 | If a line's first character is one of `=[]?()&%$\"!:` (and `§`), replace it by `*` and warn. | ngspice 2.1.2.2. Treated as a comment. |
| P5 | A line starting with `*` is a comment. Drop it. | |
| P6 | A line starting with `+` continues the previous logical line. Remove the `+` and join with a blank. | The continuation must directly follow. Comment lines between a line and its `+` line: **open, see A-03**. |
| P7 | A line ending in two backslashes (`\\`) is joined with the next line. | ngspice 2.1.4.1. Not allowed for `.title`, `.lib`, `.include` (2.3.5). |
| P8 | Remove an end-of-line comment: from `$ ` (dollar and a space) or `//` or `;` to the end of the line. A bare `$` is also accepted. | `$` is an ordinary character in PSPICE compatibility mode. |
| P9 | Expand `.include` in place (before pass 2 sees the next line). | `.lib file name` selects a section. See 02-netlist.md. |
| P10 | A `.title text` line anywhere replaces the title. | ngspice 2.3.1. |
| P11 | The last logical line must be `.end`. | ngspice 2.1.1. |

Case folding: node and device names are case-insensitive in batch mode. In
interactive or control mode, they follow the front end's rules (2.1.4.4).
**Open: A-01** on what is case-folded where, since file names and some
strings must keep their case.

Order of P6 and P8 matters: comments are removed from each physical line
before joining, so a `;` comment on a line does not swallow a following `+`
line. This follows the manual text for continuation lines (2.3.5), which
says end-of-line comments are ignored. **To confirm by test, A-03.**

## Separators

A field is separated by any run of the following, as stated in the manual
(2.1.4.1):

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

```abnf
number     = [ sign ] mantissa [ exponent ] [ scale ] *letter    ; LM
sign       = "+" / "-"
mantissa   = 1*DIGIT [ "." *DIGIT ] / "." 1*DIGIT
exponent   = "e" [ sign ] 1*DIGIT
scale      = "t" / "g" / "meg" / "k" / "mil" / "m" / "u" / "n" / "p" / "f" / "a"
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

Rules 3 and 4 were checked on ngspice 42 (conformance test LEX-001).

| Text | Value |
|------|-------|
| `1k`, `1kHz`, `1000`, `1e3`, `1.0e3` | 1000 |
| `10Volts`, `10V`, `10` | 10 |
| `1Meg`, `1MEGOHM` | 1e6 |
| `1m`, `1Mi`, `2MA` | 1e-3, 1e-3, 2e-3 |
| `1mil` | 25.4e-6 |
| `1A` | 1e-18 |
| `1F` | 1e-15 |

Dialect notes (not yet checked): LT compatibility mode accepts RKM notation
such as `2K7` and `100R` (manual 2.1.4.3). HSPICE is believed to use the
same suffixes but treats some unit words differently. Compare when HSPICE
documentation is read.

## Names

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

```abnf
param-name = ALPHA *( ALPHA / DIGIT / "!" / "#" / "$" / "%" / "[" / "]" / "_" )
```

Manual 2.9.1. Some of these characters are also separators or comment
markers elsewhere (`$`, `%`, `[`, `]`), so the lexer needs the context
"inside `.param`" to read them. **Open: A-06.** Reserved names: `time`,
`temper`, `hertz`, `or`, `and`, `not`, `div`, `mod`, `defined`, and the
function names (manual 2.9.6).

## Expression tokens

An expression is written in one of three forms:

```abnf
braced     = "{" expr "}"        ; evaluated at netlist-expansion time
quoted     = "'" expr "'"        ; same time as braced
bare       = expr                ; run-time in B, E, G, R, L, C sources
```

Braced and quoted expressions are evaluated when the deck is expanded.
Bare expressions in behavioral elements are evaluated during analysis. See
05-expressions.md and **A-07**.
