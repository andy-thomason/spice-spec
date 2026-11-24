# 08 Elaboration

Status: draft v0.1. Turns the AST of [07-ast.md](07-ast.md) into a flat
netlist: subcircuits expanded, parameters and expressions evaluated,
conditional blocks resolved, files read.

Sources: `NGS-42` 2.4 to 2.14 (subcircuits, `.param`, `.func`, `.if`, `.lib`,
`.include`) for what is documented; everything marked **observed** was
measured on ngspice 42 with `listing expand` and a randomized comparison of
expressions (the `EX-*` examples in [02-netlist.md](02-netlist.md) and the
`EXPR-*` examples in [05-expressions.md](05-expressions.md)). Registry:
[../sources/README.md](../sources/README.md).

## Input and output

**Input:** a `Deck` (07-ast.md), the dialect, and optionally a way to read
files by name.

**Output:** a `Netlist`:

```text
Netlist = { title: Text, items: [Item], diagnostics: [Diagnostic],
            params: { Text: Float } }
Item    = Device | ModelDef | Directive
Device  = { letter: Text, name: Text, nodes: [Text], rest: [Value],
            params: [Param], source: Source?, poly: Poly?, origin: Text }
ModelDef = { name: Text, type: Text, params: [Param], origin: Text }
Directive = an analysis, option or other top-level card, unchanged
Value   = Number { text: Text?, value: Float, computed: Bool }
        | Name   { text: Text }
        | Expr   { text: Text }               left for the analysis (below)
```

All names are folded to lower case (A-01). `Number.computed` is true when the
number came from evaluating a parameter or expression and false when it is
a number as written. `origin` is the instance path the item came from, empty
at the top level. Items keep the order in which they appear after expansion:
a subcircuit's items replace the call.

## Steps

The walk is sequential, in source order, over the items of a block (the
deck, a subcircuit body, an `.if` branch, an included file). Elaboration of
one item can use only what was defined earlier **except** for subcircuit
definitions, which are collected from the whole block first, so a call may
come before its definition (observed).

**E1. Definitions.** Before the walk of a block, register its `.subckt`
definitions, `.lib` sections and `.global` nodes. A `.subckt` defined inside
another is visible only inside it; lookup goes from the innermost enclosing
subcircuit outward to the top. Names are compared without regard to case.

**E2. Parameters.** `.param` (and `.csparam`) assignments are evaluated in
order, in the current scope, and each stores a number. A later assignment of
the same name replaces the earlier one. An expression may use only names
assigned before it; otherwise it is an error. A scope has a parent: inside a
subcircuit instance the parent is the caller's scope, so parameters of the
caller are visible, and a `.param` inside a subcircuit is local to that
instance (observed).

**E3. Values.** In an element, model or option:
- a number as written stays as written (`1k` keeps its text);
- a braced or quoted expression is evaluated now and becomes a computed
  number;
- a bare expression is left as text for the analysis (it may use `v()`,
  `i()`, `time`), except in `.param` and `.csparam`, where it is
  evaluated now;
- a bare name that is a parameter in scope is replaced by its value;
  observed in value positions such as `R1 a 0 rv`. This means a word in the
  value slot can be a value, a model name or a parameter, decided here by
  the symbol table (A-15). A name that is none of them stays a name.

Expression syntax and meaning are in [05-expressions.md](05-expressions.md).
An error in an expression is a diagnostic; the item is dropped.

**E4. Functions.** `.func name(args) body` defines a function visible
everywhere after its definition, replacing a built-in of the same name. The
body is evaluated with its arguments bound and sees the parameters of the
scope where it was defined.

**E5. Conditionals.** `.if` and `.elseif` conditions are evaluated in order
with the parameters defined so far; the items of the first true branch (or the
`.else` branch) are elaborated in the current scope and the others are
discarded.

**E6. Files.** `.include file` and `.lib file section` are read here, not
by the parser. The text of an included file has no title line (observed:
its first line is an ordinary card). `.lib file section` elaborates the
items of the `.lib section ... .endl` block of that file. A file that cannot
be read, or a missing section, is an error.

**E7. Subcircuit calls.** For `X name nodes... subckt [params]`:
1. Find the definition (E1). Error if there is none, or if the number of
   nodes differs from the number of ports.
2. Error if the same subcircuit is already being expanded (recursion), or if
   the nesting is deeper than 64.
3. Error if an instance with the same name, compared without regard to case,
   already exists at this level (observed: `x1` and `X1` collide).
4. Build a new scope whose parent is the caller's scope. Evaluate the call's
   `name=value` parameters in the **caller's** scope. For each default in the
   definition's `params:` list, in order: use the call's value if given,
   else evaluate the default in the **new** scope. A call parameter with no
   default is set anyway.
5. Bind each port to the node used in the call, itself already mapped in the
   caller.
6. Elaborate the definition's items in the new scope.

**E8. Names inside an instance.**
- A node that is a port becomes the node it was bound to.
- `0`, `gnd` and nodes named by `.global` stay as they are (observed).
- Any other node is local: it gets the instance path as a prefix.
- A device, source or inductor referred to by another element (`F`, `H`, `W`
  first value, `K` first two values) is renamed the same way as devices.
- A `.model` inside a subcircuit is local to the instance: it is renamed, and
  references in the same instance are rewritten.

**E9. Top-level cards.** Analyses, `.options`, `.ic`, `.nodeset`, `.temp` and
other cards are kept as directives, in order. A `.control` block is dropped
(observed: `listing expand` removes control sections). Cards inside a
subcircuit that are not elements, models, parameters, functions or
subcircuits are ignored.

## Names of flattened items

The way flattened items are named is **not normative**: tools differ, and
only that distinct items get distinct names matters. The spec requires only
that the mapping is a function of the instance path. As observed on
ngspice 42, and used by the examples:

| Item | Name | Example |
|------|------|---------|
| Device `R1` in instance `X1` | `<letter>.<path>.<name>` | `r.x1.r1` |
| Device in nested instances | the path has every instance | `r.x1.x2.r1` |
| Local node `m` in `X1` | `<path>.<node>` | `x1.m` |
| Local model `dm` in `X1` | `<path>:<model>` | `x1:dm` |

Not reproduced: for a subcircuit defined **inside** another subcircuit and
called from it, ngspice prefixes the device name twice (`r.x9.r.x1.r1`,
example EX-ENDS-1). The reference elaboration yields `r.x9.x1.r1`.

## Diagnostics

Elaboration reports these codes, each with a span: `expression` (an
expression or parameter could not be evaluated), `unknown-subckt`,
`port-count`, `recursion`, `depth`, `duplicate-name` (two devices or two
instances with the same flattened name), `subckt-call` (a call with no
subcircuit name), `include` (file or section not available).

## Not specified here

Evaluation of expressions that need the analysis (`v()`, `time`); model
parameter checks; whether a node name that looks like a number is the same
node as another spelling of that number (`0` and `00` are different nodes,
`LEX-SEP-1`); `.lib` blocks that are defined but never used (they produce no
items); the order of items when directives and elements are mixed in a
subcircuit.

## Open issues

| ID | Question |
|----|----------|
| A-35 | Which of the observed naming forms (E8 table) a conforming tool must produce, if any. |
| A-36 | Whether a bare name in a value slot may be both a model and a parameter, and which wins (the reference lets a local model win). |
| A-37 | Call parameters with no default: set (as here) or error. |
| A-38 | `.lib` sections that call each other, and `.include` inside a subcircuit. |
