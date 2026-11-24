# 00 Tokens

Status: draft v0.1. Defines how a logical line becomes tokens. The parser
rules in files 02 to 06 and the tree in [07-ast.md](07-ast.md) are built on
this.

Sources: separators and numbers from `SP3-UG` (Circuit Description) and
`NGS-42` 2.1.4, as in [01-lexical.md](01-lexical.md). Everything marked
**observed** was measured on ngspice 42 (examples at the end, run by
`tools/doctest.py`) and is `dialect:ngspice`. Registry:
[../sources/README.md](../sources/README.md).

## Where tokenization sits

```text
file bytes
  -> pass 1 (01-lexical.md): logical lines, each with an origin map
  -> tokenizer (this file): tokens per logical line
  -> parser (02..06): Deck (07-ast.md)
  -> elaboration (not in this spec yet): expand, evaluate, resolve
```

Input to the tokenizer is a **logical line**: text, plus a map from each
character back to its file, line and column. The tokenizer never sees
comments or continuation markers. The first character of the logical line
selects the card kind (a letter for an element, `.` for a dot card);
that decision is the parser's, and the tokenizer is the same for both.

## Token kinds

| Kind | What it is | Notes |
|------|------------|-------|
| `Word` | A maximal run of characters that are not separators and do not start a group | Names, keywords, nodes, numbers, and the pieces of bare expressions. A word can be *numeric* (below). |
| `Equals` | `=` | Kept as a token, because the parser needs to know whether it was written (A-04). |
| `LParen`, `RParen` | `(` `)` | Kept for the same reason, and for function-call forms like `v(a)`. |
| `Comma` | `,` | |
| `Braced` | `{` ... `}` with nesting | One token holding the raw text. |
| `Quoted` | `'` ... `'` | One token holding the raw text. Used for expressions. |
| `DQuoted` | `"` ... `"` | One token holding the raw text. Used for file names (`.include "my inc.cir"`). |
| `Unterminated` | A group opener with no closer before end of line | An error token; carries which opener it was. |

End of line is not a token; each logical line is a separate token list.

**Separators** are blank, tab, `,`, `=`, `(` and `)`. Blanks and tabs
produce no token; instead each token records `space_before` (true when
white space came directly before it). Commas, equals signs and parentheses
produce their own tokens, and the parser treats them as optional where the
grammar says they are separators (for example `SIN(0 1 1k)` and `SIN 0 1 1k`
give the same words, with and without the punctuation tokens).

Each token carries: kind, raw text, start and end offsets in the logical
line, the origin span (file, line, column of start and end), and
`space_before`. Raw text keeps its original case. A lower-cased copy is
available for comparison.

**Groups** start at a token boundary. Inside a group everything is part of
the token, including blanks, separators and `;`. Nesting is counted for
`{}` only; `'` and `"` end at the next matching character. Whether a `{`
inside a word (as in `abc{1k}`) starts a group is **not specified (A-29)**.

## Context-free by design

The tokenizer has no modes. Constructs that need different splitting are
handled by the parser asking for **raw text between tokens**:

- A bare expression such as `v=v(a)+1` is made of the words and punctuation
  `v`, `=`, `v`, `(`, `a`, `)`, `+1`. The parser reads the raw text from the
  start of the first word of the expression to the end of the last, and
  stores it as an expression (07-ast.md). This works because every token
  keeps its offsets.
- `.title` text, `.include` and `.lib` file names, and `.control` bodies are
  taken as raw text (after the card word), so the tokenizer's splitting is
  not used for them. `.include` accepts a `DQuoted` token (observed: a file
  name with a blank works in double quotes and fails without them, A-11).

This keeps dialect differences out of the tokenizer except for the switches
below.

## Numeric words

A `Word` is **numeric** if it starts with a number. This is decided by one
function, `number(word)`, which returns the parts of the number or nothing.
The tokenizer attaches the result to the word. Whether a numeric word *is*
a number, a node name or a model name depends on its position (for example
`1k` is a name in a node field and a value in a value field); the parser
decides, not the tokenizer.

`number(word)`:

1. Optional sign `+` or `-`.
2. Mantissa: digits with an optional `.` and more digits, or `.` and digits.
   If there is no mantissa, the word is not numeric.
3. Optional exponent: `e` (or, observed in ngspice, `d`), optional sign, one
   or more digits. If no digits follow the marker, the exponent is absent
   and the marker becomes part of the ignored tail (`1e` is 1).
4. Optional scale factor, **longest match**: `meg`, `mil`, `t`, `g`, `k`,
   `m`, `u`, `n`, `p`, `f`, and `a` in dialects that read atto. Case is
   ignored.
5. Everything after that, up to the end of the word, is the **tail** and is
   ignored for the value (observed: digits and punctuation too).

The value is mantissa times 10^exponent times the scale factor as an IEEE
double. How the last digit rounds is not specified (A-30). The tokenizer
keeps the mantissa text, exponent, scale text and tail, so formatters can
reproduce the source.

## Dialect switches

| Switch | SPICE3 | ngspice | Xyce | Source |
|--------|--------|---------|------|--------|
| Line starting with white space | comment | ignored, line parsed | comment | pass 1, P3 |
| Scale factor `a` (atto) | no | yes | no (amperes unless `-hspice-ext units`) | 01-lexical |
| Exponent marker `d` | not documented | yes (observed) | not read | this file |
| `//` and `$` end-of-line comments | no | yes | `;` only documented | pass 1, P8 |
| Backslash continuation | no | yes | not read | pass 1, P7 |

A tokenizer takes a dialect option; the rest of this file is dialect
independent.

## Token errors

| Error | Meaning |
|-------|---------|
| `Unterminated` | A group was opened and not closed on the logical line. Observed: ngspice exits with an error for `{2 * 3`. |
| Unexpected character | None defined: every other printable character is part of a word. |

Everything else (wrong field count, unknown keyword, a word where a number is
required) is a parser error, not a token error. The parser decides whether
it is fatal in a given dialect: observed, ngspice treats a malformed resistor
line as a warning and ignores it, but an unknown keyword parameter as an
error.

## Tokenization, shown

These are illustrations, not machine-checked yet (there is no reference
tokenizer). `W(x)` is a Word, `N(x)` a numeric Word.

```text
R1 a 0 r={1k}
  W(R1) W(a) N(0) W(r) Equals Braced({1k})

V1 a 0 SIN(0 1 1k)
  W(V1) W(a) N(0) W(SIN) LParen N(0) N(1) N(1k) RParen

B1 b 0 v=v(a)+1
  W(B1) W(b) N(0) W(v) Equals W(v) LParen W(a) RParen N(+1)
  (the parser takes raw text "v(a)+1" from the second v to the last token)

.include "my inc.cir"
  W(.include) DQuoted("my inc.cir")

V1 a 0 {2 * 3
  W(V1) W(a) N(0) Unterminated({)
```

## Examples (non-normative)

The first group below checks the number rules on ngspice. All examples are
original and run with `tools/doctest.py` (see [doctests.md](doctests.md)).
They are non-normative: if one disagrees with the rules above, the rules
are the specification.

Digits and punctuation after a number are ignored, not only letters.

```spice-test id=TOK-NUM-1 covers=trailing dialect=ngspice
V1 a 0 1k5
V2 b 0 1_000
V3 c 0 0x10
V4 d 0 1.5.2
R1 a 0 1k
R2 b 0 1k
R3 c 0 1k
R4 d 0 1k
* expect: v(a) = 1000
* expect: v(b) = 1
* expect: v(c) = 0
* expect: v(d) = 1.5
```

An exponent marker with no digits is part of the ignored tail, and `d` is an
exponent marker.

```spice-test id=TOK-NUM-2 covers=exponent dialect=ngspice
V1 a 0 1e
V2 b 0 1e+
V3 c 0 1D3
V4 d 0 1e-3k
R1 a 0 1k
R2 b 0 1k
R3 c 0 1k
R4 d 0 1k
* expect: v(a) = 1
* expect: v(b) = 1
* expect: v(c) = 1000
* expect: v(d) = 1
```

Longest match on scale factors: `m` followed by letters is milli, `mil` is
the mil, `meg` is mega.

```spice-test id=TOK-NUM-3 covers=scale dialect=ngspice
V1 a 0 1m_eg
V2 b 0 1mm
V3 c 0 1MIL
V4 d 0 1MEG
R1 a 0 1k
R2 b 0 1k
R3 c 0 1k
R4 d 0 1k
* expect: v(a) = 1e-3
* expect: v(b) = 1e-3
* expect: v(c) = 2.54e-5
* expect: v(d) = 1e6
```

A number followed by a separate word is two fields, not one: `1 mil` is a
field error.

```spice-test id=TOK-NUM-4 dialect=ngspice expect=reject
V1 a 0 1 mil
R1 a 0 1k
```

A star inside a line is not a comment, but `;`, `$` and `//` start end-of-line comments.

```spice-test id=TOK-COM-1 dialect=ngspice expect=reject
V1 a 0 5 * trailing
R1 a 0 1k
```

```spice-test id=TOK-COM-2 dialect=ngspice
V1 a 0 5 ; semicolon
V2 b 0 6 $ dollar
V3 c 0 7 // slashes
R1 a 0 1k
R2 b 0 1k
R3 c 0 1k
* expect: v(a) = 5
* expect: v(b) = 6
* expect: v(c) = 7
```

Leading blanks and tabs are ignored in ngspice, and names are case
insensitive. (In SPICE3 and Xyce a line starting with white space is a
comment, A-25.)

```spice-test id=TOK-WS-1 dialect=ngspice
   V1 A 0 5
	R1	a	0	1k
* expect: v(a) = 5
```

A braced group may hold blanks. An unterminated one is an error.

```spice-test id=TOK-GRP-1 dialect=ngspice
V1 a 0 {2 * 3}
R1 a 0 1k
* expect: v(a) = 6
```

```spice-test id=TOK-GRP-2 dialect=ngspice expect=reject
V1 a 0 {2 * 3
R1 a 0 1k
```

File names: a double-quoted name may hold a blank; an unquoted one ends at
the first blank.

```spice-file name="my inc.cir"
R1 a 0 1k
```

```spice-test id=TOK-INC-1 dialect=ngspice uses="my inc.cir"
.include "my inc.cir"
I1 0 a 1m
* expect: v(a) = 1
```

Parentheses around a value are separators, so they do no harm.

```spice-test id=TOK-PAR-1 dialect=ngspice
V1 a 0 5
R1 (a 0) (1k)
* expect: v(a) = 5
```
