# spice-spec design document

Status: draft v0.1

## 1. Problem

SPICE has no open, normative specification. SPICE2G.6 and SPICE3f5 are
reference implementations, HSPICE is a proprietary de facto dialect, and
ngspice, Xyce, LTspice, PSpice and Spectre each implement overlapping but
different supersets. Only the compact model equations (CMC: BSIM etc.) and
Verilog-A are formally standardized.

Consequences: netlists are not reliably portable, parsers and translators
are written by trial and error, and "correct" is defined by whichever tool
you happen to run.

## 2. Goals

1. A readable, versioned, normative specification of netlist syntax and
   simulation semantics, starting with SPICE3f5 as the baseline.
2. Explicit, per-feature documentation of where ngspice, Xyce and HSPICE
   agree, differ, or extend the baseline.
3. A machine-checkable form: a formal grammar plus a conformance test
   suite that ties each normative statement to runnable netlists.
4. Usable by implementers of parsers, simulators, translators and linters.

## 3. Non-goals

- Not a new simulator, and not a new language. We describe existing
  behavior; we do not invent syntax.
- Not a replacement for compact model specs (BSIM, HICUM, ...) or
  Verilog-A. We reference them and specify only how SPICE invokes them.
- No reproduction of proprietary documentation (see section 8).

## 4. Scope and layering

The spec is organized in layers so each feature has a clear provenance.

| Layer | Content | Source of truth |
|-------|---------|-----------------|
| L0 Core | SPICE3f5 netlist language, elements, analyses, built-in models | SPICE3f5 source and manual |
| L1 Common | Features present in at least two of ngspice, Xyce, HSPICE with compatible meaning | Cross-implementation comparison |
| L2 Dialect | Per-tool extensions (`.measure` variants, expression syntax, option names) | Tool docs and observed behavior |
| L3 Models | How `.model` and `.subckt` bind to device equations; model parameter tables | CMC specs, tool docs |

Each normative requirement carries a tag: `core`, `common`, or
`dialect:<tool>`.

## 5. Document structure

```
docs/            design and process
spec/
  01-lexical/        line continuation, comments, case, numbers, suffixes
  02-netlist/        title line, cards, .include/.lib, hierarchy, scoping
  03-elements/       R L C K V I E F G H D Q J M B S W T X, per element
  04-models/         .model syntax, parameter binding, level selection
  05-analyses/       .op .dc .ac .tran .noise .tf .sens .pz .disto
  06-sources/        PULSE SIN EXP PWL SFFM AM, behavioral sources
  07-parameters/     .param, expressions, functions, .func
  08-control/        .options, .ic, .nodeset, .temp, .measure, .print
  09-numerics/       MNA formulation, integration, Newton, convergence, gmin
  10-output/         rawfile format, print/plot semantics
  11-compat/         cross-tool difference tables and translation notes
grammar/             formal grammar (see section 6)
conformance/         test netlists and expected results (see section 7)
sources/             provenance notes and citations (no copied text)
```

Each spec page uses a fixed template: syntax, parameters and defaults,
semantics, edge cases, per-tool notes, conformance test IDs.

## 6. Formal grammar

- A line-oriented grammar must be handled in two passes: (1) physical
  lines to logical lines (continuation `+`, comments `*`, `;`, `$`,
  case folding); (2) card parsing.
- Express pass 2 in a standard notation (ABNF or EBNF) in `grammar/`, with
  a reference parser used only to validate the grammar against real decks.
- Dialect differences are expressed as grammar variants or flags, not
  separate grammars, so differences stay visible in one place.
- Open question: ambiguities that SPICE3f5 resolves procedurally (for
  example positional parameter parsing) may not fit a context-free
  grammar. Decide whether to specify those procedurally.

## 7. Conformance suite

- Each normative statement has an ID (for example `R-004`) and one or more
  test netlists in `conformance/`.
- Tests fall into three kinds:
  - **Syntax:** accepted or rejected, with expected diagnostics class.
  - **Analytic:** circuits with closed-form answers (RC step, RLC ring,
    divider, diode at known bias), checked within stated tolerance.
  - **Cross-tool:** no analytic answer; record results from each tool and
    report agreement within tolerance.
- A runner script drives ngspice and Xyce in batch mode (both open
  source) and records results per tool and version. HSPICE results can
  only be recorded by users with a licence and are optional.
- Tolerances are explicit per test. Results are stored with tool name,
  version and options so claims are reproducible.
- Seed from existing open suites (ngspice `tests/`, Xyce regression
  suite), subject to licence compatibility (section 8).

## 8. Sources, provenance and licensing

This is the main legal and practical risk.

- **SPICE3f5:** Berkeley-licensed (BSD-style). Source and original
  manuals may be read and cited; check licence text before copying.
- **ngspice:** open source (mixed BSD-style and other licences per
  component). Manual and source readable; verify licence before reusing
  text or tests.
- **Xyce:** open source (GPL). Treat its source and regression tests as
  read-only references; do not copy code or tests into a differently
  licensed repo without checking.
- **HSPICE:** proprietary documentation. Do not copy or closely
  paraphrase it. Record only facts about behavior, with a citation to the
  document and section, written in our own words, and confirmed by
  observation where possible. Contributors must not use confidential
  material (NDA, foundry PDKs).
- Every spec page lists its sources in `sources/` notes.
- Choose a licence for the spec text and a separate one for the
  conformance suite before accepting outside contributions. (Open: CC-BY
  for text, permissive for tests.)

## 9. Method

1. **Baseline:** read SPICE3f5 source and manual; write L0 pages with
   citations to the source files and functions that define behavior.
2. **Compare:** for each feature, check ngspice and Xyce docs and source,
   then run conformance netlists to confirm real behavior.
3. **Add HSPICE:** from public documentation, marked `dialect:hspice`
   and flagged "documented, not independently verified" unless a licensed
   contributor confirms.
4. **Review:** each page needs a second reviewer and passing tests.

Where docs and observed behavior disagree, observed behavior is recorded
and the discrepancy noted.

## 10. Milestones

- **M0:** repo scaffold, licences, page template, test runner skeleton.
- **M1:** lexical layer and netlist structure (L0), with grammar and
  syntax tests.
- **M2:** passive elements, independent sources, `.op/.dc/.ac/.tran`
  (L0) with analytic tests.
- **M3:** semiconductor elements and built-in model levels (L0).
- **M4:** parameters, expressions, `.measure`, `.options` (L1/L2), the
  area with the most divergence.
- **M5:** compatibility tables and translation notes across tools.

## 11. Risks

- HSPICE content cannot be verified without a licence, and copying
  documentation is not allowed.
- Numerical behavior (convergence, timestep control) is
  implementation-defined and hard to specify; we may need to specify
  only observable contracts and tolerances.
- Scope growth: the number of dialect features is large. Mitigate by
  milestone order and the layer model.
- Test licensing from GPL sources.

## 12. Open questions

1. Licences for text and tests.
2. Spec format: Markdown with a static site, or another toolchain?
3. How far into numerics (integration method, timestep) is normative?
4. Which tool versions are the reference points (SPICE3f5, current
   ngspice, current Xyce, which HSPICE release)?
5. Should L3 include model parameter tables, or only link to CMC specs?
