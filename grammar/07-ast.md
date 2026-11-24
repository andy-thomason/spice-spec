# 07 AST

Status: draft v0.1. The tree a parser produces from the tokens of
[00-tokens.md](00-tokens.md) using the rules in files 02 to 06.

This is a design, not something derived from a source document: it is our
own specification of what a parser must record. The element argument
layouts come from [03-elements.md](03-elements.md) and its sources. There is
no reference parser yet, so nothing in this file is machine-checked; the
JSON in the last section is hand-written and illustrative.

## Principles

1. **Syntactic only.** The AST records what was written. It does not expand
   subcircuits, evaluate parameters or expressions, look up models, read
   `.include` or `.lib` files, apply defaults, or decide anything that
   needs a symbol table. Those belong to a later *elaboration* step (not yet
   specified).
2. **Faithful.** Names keep their case, numbers keep their text next to the
   value, expressions keep their raw text. Every node has a source span.
3. **Order preserved.** Items, parameters and arguments keep source order.
4. **Recoverable.** A line that cannot be parsed becomes an `Invalid` item
   with a diagnostic, and parsing continues. Whether that is fatal is a
   decision for the caller, because tools differ (observed: ngspice ignores
   a resistor line with no value with a warning, but stops on an unknown
   keyword parameter).
5. **Independent of the file system.** The same text always gives the same
   tree, whether or not the files it names exist.
6. **Dialect recorded, not hidden.** The deck records which dialect the
   parser used. A construct outside that dialect gets a diagnostic with code
   `dialect-extension` and is still parsed.
7. **Deferred decisions stay deferred.** Where the grammar cannot decide
   without a symbol table (open issues A-15, A-16, A-18), the AST keeps the
   undecided words in a list and the elaboration step decides.

## Notation

```text
Name = { field: Type, ... }     a node (record); every node also has span: Span
Type = Text | Bool | Int | Float | "literal" | Name | [Type] | Type? | Type | Type
```

`[T]` is a list, `T?` is optional (omitted when absent), `A | B` is a union
(in JSON, tagged by `kind`).

## Common nodes

```text
Span     = { file: Text, line: Int, col: Int, end_line: Int, end_col: Int,
             via: Span? }            via: the .include or .lib that brought it in
Ident    = { text: Text, lower: Text }          an unresolved name: node, model,
                                                parameter, subcircuit, source
NumberLit = { text: Text, mantissa: Text, exponent: Text?, scale: Text?,
              tail: Text, value: Float }        see 00-tokens.md, number()
Expr     = { form: "braced" | "quoted" | "bare", raw: Text, tree: ExprNode? }
Value    = NumberLit | Expr | Ident
Param    = { name: Ident, value: Value?, has_equals: Bool }
Diagnostic = { severity: "error" | "warning", code: Text, message: Text }
```

- `Ident.text` keeps the source case; `lower` is the folded form. Which of
  the two a name compares by is an elaboration matter (A-01).
- `Value` is what a `value` rule in the grammar produces. A word that
  starts with a number becomes `NumberLit`; `{...}` and `'...'` become
  `Expr`; any other word is an `Ident`. A word like `1k` in a *node* field
  is an `Ident` (positional decision, 00-tokens.md).
- `Param.value` is absent for flag-style parameters such as `off` or `uic`.
  `has_equals` records whether `=` was written (A-04).
- `Expr.tree` is present only if the parser was asked to parse expressions.
  Expression syntax differs between tools, so the raw text is always kept.

```text
ExprNode = Num   { lit: NumberLit }
         | Ref   { ident: Ident }
         | Unary { op: Text, operand: ExprNode }
         | Binary { op: Text, left: ExprNode, right: ExprNode }
         | Ternary { cond: ExprNode, then: ExprNode, else: ExprNode }
         | Call  { func: Ident, args: [ExprNode] }     includes v(a), i(v1)
```

## Deck and items

```text
Deck = { dialect: Text, title: Text, items: [Item], end: Span?,
         diagnostics: [Diagnostic], comments: [Comment]? }
Item = Element | DotCard | Invalid
Invalid = { raw: Text, reason: Text, severity: "error" | "warning" }
Comment = { text: Text }            kept only if the parser is asked to (A-31)
```

`end` is the span of `.end`, absent if the deck has none (that is a
diagnostic). `.title` replaces `title` (pass 1, P10).

## Elements

One record type covers all element letters, so that adding a dialect form
does not change the tree. The per-letter table says what is in each field.

```text
Element = { letter: Text, name: Ident, nodes: [Ident], rest: [Value],
            params: [Param], source: SourceSpec?, poly: Poly? }
```

- `name` is the full instance name including the letter (`R1`).
- `nodes` holds exactly the number of nodes fixed for that letter in the
  table below. Nothing more is taken as a node by the parser.
- `rest` holds the remaining positional words, in order, up to the first
  keyword parameter. What each one means is given in the table. Where
  the count is open, the table says so and elaboration decides.
- `params` holds keyword parameters (`name=value`) in order, including
  forms like `r='1k+1k'` and `v=expr` whose value is a bare `Expr`.

| Letter | `nodes` | `rest` (in order) | Notes |
|--------|---------|-------------------|-------|
| R | 2 | `[value] [model]` | `r=expr` form is a param. Value or model is told apart by `Value` kind (A-15). |
| C | 2 | `[value] [model]` | `ic`, `l`, `w`, ... are params. |
| L | 2 | `[value] [model]` | |
| K | 0 | `L1 L2 coupling` | `L1`, `L2` are idents. |
| V, I | 2 | none | `source` holds the value and waveform. |
| E, G | 2 | `nc+ nc- gain` | Or `vol=`/`cur=` params, or `poly`. |
| F, H | 2 | `vname gain` | Or `poly`. |
| B | 2 | none | `i=` / `v=` params. |
| D | 2 | `model [area]` | |
| Q | 3 | `[ns] [tj] model [area]` | Open count (A-16). |
| J | 3 | `model [area]` | |
| Z | 3 | `model [area]` | |
| M | 3 | `[bulk] model` | Bulk node present or not (A-16). |
| S | 4 | `model [on|off]` | |
| W | 2 | `vname model [on|off]` | |
| T | 4 | none | `z0`, `td`, `f`, `nl`, `ic` are params. |
| O | 4 | `model` | |
| U | 3 | `model` | URC; the XSPICE digital block sharing the letter is not specified (A-13). |
| X | 0 | all words | Last word is the subcircuit name (elaboration; A-18). |
| other letters | 0 | all words | Preserved as written. |

```text
SourceSpec = { dc: Value?, has_dc_keyword: Bool,
               ac: { mag: Value?, phase: Value? }?,
               distof1: { mag: Value?, phase: Value? }?,
               distof2: { mag: Value?, phase: Value? }?,
               function: SourceFunction? }
SourceFunction = { name: Ident, args: [Value], params: [Param], has_parens: Bool }
Poly = { dim: Value, items: [Value] }
```

- `SourceFunction.name` is the word as written (`SIN`, `pulse`). Which
  names are source functions and what each argument means is in
  [04-sources.md](04-sources.md); the parser does not check the count.
  `PWL`'s `r=` and `td=` are `params`. A word is a source function because
  of where it appears (after the node fields of a `V` or `I` card), never
  because of its spelling; the same spelling inside an expression is a math
  function (`Call`).
- `Poly.items` is the mixed list of controlling nodes (or source names) and
  coefficients; where one ends and the next begins is open (A-14).

## Dot cards

```text
DotCard = Model | Subckt | ParamCard | Func | Global | Temp | Csparam
        | Include | LibUse | LibDef | If | Analysis | OtherDot

Model    = { name: Ident, type: Ident, params: [Param] }
Subckt   = { name: Ident, ports: [Ident], params: [Param],
             items: [Item], ends_name: Ident? }
ParamCard = { assignments: [Param] }
Func     = { name: Ident, args: [Ident], body: Expr }
Global   = { nodes: [Ident] }
Temp     = { value: Value }
Csparam  = { assignments: [Param] }
Include  = { path: Text, form: "bare" | "double_quoted" | "quoted",
             expanded: [Item]? }
LibUse   = { path: Text, form: ..., section: Ident, expanded: [Item]? }
LibDef   = { name: Ident, items: [Item] }
If       = { branches: [{ cond: Expr?, items: [Item] }] }     cond absent for else
OtherDot = { name: Text, words: [Value], raw: Text }
```

- `Subckt.ports` stops at the `params:` marker if there is one (A-18);
  parameters after it are `params`. `ends_name` is the name after `.ends`,
  if any.
- `Include.expanded` and `LibUse.expanded` are absent after parsing. An
  expansion step may fill them in; the parser never reads files
  (principle 5). Pass 1 step P9 in 01-lexical.md says ngspice inserts the
  text before parsing; this spec keeps the node and lets a later step
  inline it. The difference is visible only in line numbers and in
  continuation lines that cross an include (A-28).
- `OtherDot` holds any card the spec does not define yet (`.print`,
  `.plot`, `.meas`, `.save`, `.four`, and so on), so that unknown cards
  survive. A `.control` block is one `OtherDot` whose `raw` is everything up
  to `.endc` (A-08).

### Analyses and initial conditions

```text
Analysis = Op | Dc | Ac | Tran | Noise | Tf | Pz | Sens | Disto | Ic | Nodeset | Options

OutputRef = { kind: "v" | "i", args: [Ident] }                  v(5,3), i(v1)
Sweep     = { variation: "dec" | "oct" | "lin", points: Value, fstart: Value, fstop: Value }

Op      = { }
Dc      = { sweeps: [{ source: Ident, start: Value, stop: Value, step: Value }] }
Ac      = { sweep: Sweep }
Tran    = { tstep: Value, tstop: Value, tstart: Value?, tmax: Value?, uic: Bool }
Noise   = { output: OutputRef, reference: Ident?, source: Ident, sweep: Sweep,
            points_per_summary: Value? }
Tf      = { output: OutputRef, source: Ident }
Pz      = { nodes: [Ident], kind: "cur" | "vol", mode: "pol" | "zer" | "pz" }
Sens    = { output: OutputRef, ac: Sweep? }
Disto   = { sweep: Sweep, f2overf1: Value? }
Ic      = { items: [{ target: OutputRef, value: Value }] }
Nodeset = { all: Value?, items: [{ target: OutputRef, value: Value }] }
Options = { items: [Param] }
```

`Dc.sweeps` has one or two entries. `Pz.nodes` has four.

## Invariants

A conforming parser's tree satisfies:

1. Every `Item` has a span inside the file or include it came from.
2. Items appear in source order. Nested items (`Subckt`, `LibDef`, `If`) keep
   theirs.
3. `Element.nodes` has the fixed length from the table, unless the line was
   too short, in which case the item is `Invalid`.
4. No node refers to another by anything but `Ident` text. There are no
   pointers to definitions.
5. Re-reading the spans (and, if kept, comments) reproduces the source up to
   white space.

## What the AST does not do (elaboration)

Subcircuit expansion; parameter and expression evaluation; `.if` branch
selection (it needs parameter values); file reading for `.include` and
`.lib`; model, source and subcircuit lookup; deciding the `Q`, `M` and `X`
field splits; ground aliasing (`gnd` to `0`); case folding; dialect
defaults; checking argument counts of source functions. These need a symbol
table or a dialect table and are specified separately.

## Machine form

Tools exchange the AST as JSON:

- Every node is an object with a `kind` field naming its type. Union
  members are distinguished by `kind`.
- Field names are as written above. Absent optional fields are omitted.
- `span` is the string `"file:line:col-line:col"`; with `via`, the include
  chain is joined by ` <- `.
- Numbers keep their text: `{"kind":"NumberLit","text":"1k","value":1000.0,...}`.

Illustrative only; no tool produced this.

```text
R1 a 0 1k
```

```json
{
  "kind": "Element", "letter": "R",
  "name": {"kind": "Ident", "text": "R1", "lower": "r1"},
  "nodes": [
    {"kind": "Ident", "text": "a", "lower": "a"},
    {"kind": "Ident", "text": "0", "lower": "0"}
  ],
  "rest": [
    {"kind": "NumberLit", "text": "1k", "mantissa": "1", "scale": "k", "tail": "", "value": 1000.0}
  ],
  "params": [],
  "span": "deck.cir:2:1-2:10"
}
```

A source card:

```text
V1 a 0 dc 0 sin(0 1 1k)
```

```json
{
  "kind": "Element", "letter": "V",
  "name": {"kind": "Ident", "text": "V1", "lower": "v1"},
  "nodes": [{"kind": "Ident", "text": "a"}, {"kind": "Ident", "text": "0"}],
  "rest": [], "params": [],
  "source": {
    "has_dc_keyword": true,
    "dc": {"kind": "NumberLit", "text": "0", "value": 0.0},
    "function": {
      "name": {"kind": "Ident", "text": "sin"}, "has_parens": true,
      "args": [
        {"kind": "NumberLit", "text": "0", "value": 0.0},
        {"kind": "NumberLit", "text": "1", "value": 1.0},
        {"kind": "NumberLit", "text": "1k", "mantissa": "1", "scale": "k", "value": 1000.0}
      ]
    }
  },
  "span": "deck.cir:3:1-3:24"
}
```

A card whose line the tool ignores:

```text
R1 a b
```

```json
{"kind": "Invalid", "raw": "R1 a b", "reason": "resistor needs a value or model",
 "severity": "warning", "span": "deck.cir:4:1-4:7"}
```

## Open decisions

| ID | Question |
|----|----------|
| A-28 | Where `.include` and `.lib` are expanded: before parsing (as ngspice does) or after, as here. |
| A-29 | Whether `{` inside a word starts a group. |
| A-30 | Rounding of `NumberLit.value` (decimal-to-double). |
| A-31 | Whether comments are part of the tree. |
