# Clean-room policy

Status: draft v0.1. Applies to every file in this repo and to every
contributor, human or AI.

## Aim

Write a specification of SPICE that does not derive from any simulator's
source code. Specification text, grammar, and tests must come from
published documentation and from observed behavior of running programs.

## What is allowed

| Input | Allowed use |
|-------|-------------|
| Published documentation (manuals, guides, papers, standards) | Read, cite, and restate in our own words. |
| Observed behavior of a program run as a black box | Run unmodified binaries, record inputs and outputs, and state what was observed, with tool and version. |
| Public standards (CMC compact-model specs, Verilog-A, IEEE, IBIS) | Read and cite under their terms. |
| Our own experiments and test netlists | Yes, written from scratch. |

## What is not allowed

1. **Reading simulator source code**, for any tool (SPICE3f5, ngspice,
   Xyce, HSPICE, LTspice, PSpice, others), including "just to check a
   detail", reading it on a code-hosting site, in a debugger, in a
   decompiler, or in a patch or issue.
2. **Copying source code**, comments, identifiers or file names from any
   simulator into this repo.
3. **Copying documentation prose**, tables of text, or figures. Short
   syntax forms and parameter lists are interface facts and may match the
   manuals; the explanatory text may not.
4. **Copying test netlists, regression tests, expected outputs, model
   files or PDK content** from any tool or foundry. Tests here are written
   from scratch.
5. **Using confidential material** (NDA documentation, internal manuals,
   foundry PDKs).
6. **Instrumenting or modifying a simulator** to expose internals.
   Observation is limited to documented inputs, outputs and options.

If a question cannot be answered from documentation or by running an
experiment, the answer is "open". It goes in `grammar/ambiguities.md`; it
does not get answered from the source.

## Process

1. **Draft** from documentation. Cite each production and rule with a
   source ID (`sources/README.md`) and a section number.
2. **Restate** in our own words. Do not paste then edit.
3. **Test** the claim by running tools. Record tool name, version and
   outcome in a conformance test (`conformance/`).
4. **Disagreement** between documentation and behavior: record both and
   the discrepancy. Do not resolve by reading source.
5. **Review**: a second person checks the page against the rules here
   before merge.

## Controls

- **Declaration.** Each contributor states, in their first pull request,
  that they have not read or copied the source of any SPICE-family
  simulator for the areas they write (see CONTRIBUTING.md). A contributor
  who has worked on a simulator's source declares which one. Such a
  contributor does not write or review the specification of the areas
  they worked on; others cover those.
- **Overlap audit.** `tools/audit-verbatim.py` reports runs of shared
  words between our text and the reference documents. Run it with the
  reference texts kept outside the repo. A hit of prose must be reworded.
  A hit that is only a syntax signature (parameter list, keyword order)
  is an interface fact and is accepted after review.
- **Provenance.** Every page cites its sources. A page without a source
  or test is not accepted.
- **No source in the working tree.** Do not keep a clone of any simulator's
  source in the project or in a folder this project's tools search.
- **Reference material stays out of the repo.** Manuals are cited by URL,
  not stored.

## AI assistants

An AI assistant may have seen simulator source code in training, and that
cannot be checked. Mitigations: assistants are given only documentation
and observed output; they are told not to recall or reproduce source code;
all assistant output goes through the overlap audit and human review; and
tests are original circuits with hand-calculated expected values where
possible. The residual risk is stated here and not hidden.

## Separate implementation projects

An implementation of the spec is written as a **separate project**, under
the same rules, so that the spec is the only thing connecting the two.

- The implementers' inputs are the spec (`grammar/`, `spec/`), the
  conformance tests, and published documentation. They do not read simulator
  source code and make the same declaration as other contributors.
- They do **not** read or reuse `refimpl/` (or any code the spec authors
  wrote). It is spec-validation tooling, and copying it would hide spec gaps
  that an independent implementation should expose. `tools/doctest.py` and the
  tests themselves may be used.
- The spec authors do not read the implementation's code to settle a spec
  question. The decision goes into the spec text.
- Questions and bug reports go to the spec repo as issues or pull requests,
  with an original test case. The answer is a change to the spec.

## Status of the existing repo

An audit on 2026-11-24 compared all text, YAML and netlists in the repo
against the ngspice 42 and 47+ manuals, the SPICE3 user guide pages and the
Xyce 7.10 Reference Guide (seven-word runs). No simulator source code had
been read or used. Findings: two sentences from the SPICE3 guide and one
phrase from the ngspice manual had been quoted closely; they have been
reworded. The remaining matches are parameter lists and keyword sequences
(for example `PULSE(V1 V2 TD TR TF PW PER)`), which are interface facts.
