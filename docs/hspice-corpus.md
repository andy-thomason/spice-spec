# Inferring HSPICE syntax from open model libraries

Status: draft v0.1. This page records **how** we collect evidence about
HSPICE syntax from public model libraries, what we did, and what the evidence
can and cannot show. The findings are in
[hspice-corpus/findings.md](hspice-corpus/findings.md).

## Why

We have no HSPICE documentation or binary (the HSPICE manual is not public and
its licence limits publishing benchmark results). Model libraries written for
HSPICE are public data, and a library shows which syntax real users write.
Counting that syntax tells us **what the HSPICE layer has to accept**. It does
not tell us what the syntax **means**.

## Rules for this work (see also [clean-room.md](clean-room.md))

1. **Open licences only.** A library goes into the corpus only if its
   repository carries an open licence (Apache-2.0, BSD-3-Clause here). Each
   one is listed below with the licence and the commit that was scanned.
   Foundry PDKs under NDA, and any file that came with a commercial tool, are
   out of bounds.
2. **The libraries stay outside the repository.** We keep them in a separate
   directory (`~/pdk-corpus` on the author's machine). Nothing from them is
   copied into the spec, the examples or the tests.
3. **Only counts are committed.** `tools/scan-syntax.py` writes card names,
   element letters, number suffixes, function names, option names and
   parser error codes with their counts. It writes no library text, model
   parameter names or cell names. The output is in `docs/hspice-corpus/*.json`.
4. **No tool source.** The scanner reads library files only. It uses the
   reference parser from `refimpl/` (spec-validation tooling) to count parse
   errors.
5. **Examples are our own.** Where a finding needs a runnable example, we write
   one from scratch for the spec's doctests. We do not shorten or adapt a
   library's text.
6. **Evidence has a level.** Each `dialect:hspice` item in the spec says how we
   know it: `seen` (used in a library, source of the meaning unknown),
   `documented` (in a manual we read), or `measured` (run on a tool).
   Libraries give only `seen`.

## Corpus

The libraries were cloned shallowly (`git clone --depth 1`), each into its own
directory, and scanned at the commit shown. The scan is a snapshot.

| Name | Repository | Licence | Commit | Files scanned | Note |
|------|------------|---------|--------|---------------|------|
| `asap7` | The-OpenROAD-Project/asap7_pdk_r1p7 | BSD-3-Clause | 58d72c9 | 7 | ASAP7 7 nm predictive models, directory named `hspice`, BSIM-CMG |
| `ihp-sg13g2` | IHP-GmbH/IHP-Open-PDK (sparse: `ihp-sg13g2/libs.tech/ngspice`) | Apache-2.0 | e73adb4 | 38 | SG13G2 130 nm BiCMOS; targets ngspice, not HSPICE |
| `sky130` | google/skywater-pdk-libs-sky130_fd_pr | Apache-2.0 | f62031a | 1232 | SkyWater 130 nm; targets ngspice, Xyce and others |
| `gf180mcu` | google/globalfoundries-pdk-libs-gf180mcu_fd_pr | Apache-2.0 | 9f992d5 | 115 | GlobalFoundries 180 nm; targets ngspice |

`google/gf180mcu-pdk` (the documentation repository) holds no model files and
was dropped.

## Method

1. **Collect.** Clone, record the commit, check the licence file.
2. **Scan.** `python3 -I tools/scan-syntax.py --name NAME --root DIR --parse
   --out docs/hspice-corpus/NAME.json`. Files above 2 MB are skipped and
   counted. The scanner runs pass 1 of the reference implementation (ngspice
   preset, no title line, since library files start with comments or `.lib`),
   then counts per logical line:
   - card names, element first letters, first characters that are neither;
   - `.model` types and `level=` values, and models with `lmin`/`lmax`
     (binning);
   - `.lib` argument forms, `.param` value styles (bare, quoted, braced),
     `.subckt` defaults and `params:`, `.option` names, `.include` forms;
   - number suffix tails, function names and operators inside quoted or
     braced expressions;
   - comment styles, continuation lines, tabs, carriage returns.
   With `--parse` it also runs the reference parser and counts diagnostics by
   code.
3. **Read the counts, then look at lines.** A count that is surprising is
   investigated by looking at the library file locally (reading public data).
   What we learn goes into the findings as a description in our own words.
4. **Cross-check on running tools.** Where a finding suggests an HSPICE
   construct, we write a small original deck and run it on ngspice 42 and Xyce
   7.10 (Xyce documents some HSPICE compatibility). That gives `measured`
   evidence for those two tools only.
5. **Record.** Findings and open questions go to the findings page and, as
   `dialect:hspice` rows, to `grammar/ambiguities.md`.

Scanner limitation found in the first run: the extension `.lib` also matches
Cadence's `cds.lib` configuration file (asap7), which is not SPICE. It adds 4
parser warnings and no counts that matter. Exclude it in the next run.

## Results

Four libraries, 1,392 files, about 26 thousand logical lines (millions of
physical lines, because model cards are very long). Summary in
[hspice-corpus/findings.md](hspice-corpus/findings.md). Cross-checks on
ngspice 42 and Xyce 7.10: three constructs (`DC` before a waveform, `.option
scale`, unit words) are `common`; model binning differs. They are examples
LIB-* in
[../spec/09-dialects/library-conventions.md](../spec/09-dialects/library-conventions.md).

## What the evidence can and cannot show

- It shows what syntax is **used**. It does not show semantics: a library that
  uses model binning does not tell us which bin wins at a boundary.
- A construct that does not appear is **not** evidence that HSPICE lacks it.
- Open libraries are mostly written or converted for ngspice (and sometimes
  Xyce). Only part of the corpus is real HSPICE style (`asap7`'s `hspice`
  directory). The scan therefore describes the common subset of HSPICE-style
  and ngspice-style libraries, not HSPICE.
- Four libraries is a small sample. Counts are descriptive, not statistics.
- The reference parser is our own and follows the ngspice dialect, so its parse
  errors mean "outside our current spec", not "invalid HSPICE".

## Reproducing

```
mkdir ~/pdk-corpus && cd ~/pdk-corpus
git clone --depth 1 https://github.com/The-OpenROAD-Project/asap7_pdk_r1p7.git
git clone --depth 1 https://github.com/google/skywater-pdk-libs-sky130_fd_pr.git
git clone --depth 1 https://github.com/google/globalfoundries-pdk-libs-gf180mcu_fd_pr.git gf180
git clone --depth 1 --filter=blob:none --sparse https://github.com/IHP-GmbH/IHP-Open-PDK.git ihp
(cd ihp && git sparse-checkout set ihp-sg13g2/libs.tech/ngspice)
# check out the commits listed above to reproduce the counts exactly, then
cd ~/spice-spec
for p in asap7:asap7_pdk_r1p7 ihp-sg13g2:ihp sky130:skywater-pdk-libs-sky130_fd_pr gf180mcu:gf180; do
  python3 -I tools/scan-syntax.py --name ${p%%:*} --root ~/pdk-corpus/${p##*:} --parse \
    --out docs/hspice-corpus/${p%%:*}.json
done
```
