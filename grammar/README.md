# Grammar

Status: draft v0.1. Detailed first pass, to be reviewed before any parser is
written.

This directory specifies the syntax of a SPICE netlist. It is split so each
file can be reviewed and tested on its own.

| File | Content |
|------|---------|
| [01-lexical.md](01-lexical.md) | Pass 1 (physical to logical lines), separators, numbers, names |
| [02-netlist.md](02-netlist.md) | Deck structure, `.subckt`, `.model`, `.param`, `.include`, `.lib`, `.global`, `.if` |
| [03-elements.md](03-elements.md) | One rule per element letter |
| [04-sources.md](04-sources.md) | Independent source functions (PULSE, SIN, EXP, PWL, SFFM, AM) |
| [05-expressions.md](05-expressions.md) | Expression grammar, operators, functions |
| [06-analyses.md](06-analyses.md) | Analysis, initial-condition and output cards |
| [ambiguities.md](ambiguities.md) | Numbered open issues and decisions |

## Notation

Rules use ABNF (RFC 5234) with these conventions:

- Literals are case-insensitive, as in ABNF itself and as in SPICE.
- ABNF has no ordered choice. Where two alternatives can both match the same
  text (for example `meg` and `m`), the rule says **longest match wins** and
  the rule is marked `LM`.
- Rules are written over **tokens**. Tokens are separated by `SEP`
  (see 01-lexical.md), so `r = 5`, `r=5` and `r =5` are the same sentence.
  A space in a rule means "optional `SEP`" between tokens unless the rule
  says otherwise.
- Square brackets are optional parts. `*x` is zero or more, `1*x` one or more.

## Provenance tags

Every rule carries a tag from docs/design.md section 4:

- `core`: documented in the SPICE3 user guide (`SP3-UG`). Note this is the
  SPICE3 documentation, not the SPICE3f5 source; nothing has been run
  against SPICE3f5 itself.
- `common`: documented in both ngspice and Xyce. The documentation was
  compared, but meaning was not tested on Xyce. HSPICE documentation was not
  read, so no rule is marked as agreed by all three.
- `dialect:ngspice`, `dialect:xyce`, `dialect:hspice`: one tool only.

Where this draft says only "ngspice", the rule is `dialect:ngspice` until
other tools are compared.

## Sources used in this draft

Full registry with URLs: [../sources/README.md](../sources/README.md).
Source IDs used in the grammar files: `SP3-UG` (SPICE3 user guide),
`NGS-42` and `NGS-47` (ngspice manuals), `XYC-REF` (Xyce Reference Guide
7.10), `XYC-UG`, `HSP`.

- Read: `SP3-UG`, `NGS-42`, parts of `XYC-REF`. No text is copied; rules and
  prose are our own.
- Observed behavior of ngspice 42, recorded as conformance tests.
- Not read: HSPICE documentation, SPICE3f5 source, ngspice and Xyce source,
  `XYC-UG`.

## What is deliberately not in the grammar

These are checked after parsing and are specified as semantic rules in the
spec pages, not here: node counts per element, model type versus element
letter, parameter defaults, and that a referenced model or subcircuit exists.
