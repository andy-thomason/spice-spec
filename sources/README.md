# Sources

Registry of the documents this spec draws on. Every grammar production and
conformance test cites these IDs. URLs were checked on 2026-11-24 (HTTP 200
unless noted). No text is copied from any of them.

## Registry

| ID | Document | Version | URL | Read |
|----|----------|---------|-----|------|
| `SP3-UG` | SPICE3 User Guide, University of California, Berkeley (web pages: Overview, Circuit Description, Circuit Elements and Models, Analyses) | SPICE3, as archived 2022 to 2023 | https://web.archive.org/web/2022/http://bwrcs.eecs.berkeley.edu/Classes/IcBook/SPICE/UserGuide/description.html , `.../elements.html`, `.../analyses.html` , index at http://bwrcs.eecs.berkeley.edu/Classes/IcBook/SPICE/ | Description, elements, analyses pages read. Transient analysis and options pages not read. |
| `NGS-42` | Ngspice User's Manual | 42 (Debian package `ngspice-doc` 42+ds-3build1, file `manual.pdf`) | https://ngspice.sourceforge.io/docs.html (older manuals listed there) | Chapters 2, 3, 4, 5.1 and the analysis chapter read |
| `NGS-47` | Ngspice User's Manual | 47+ (development), dated 2026-11-15 | https://ngspice.sourceforge.io/docs/ngspice-manual.pdf | Used only to map section numbers (see below) |
| `XYC-REF` | Xyce Parallel Electronic Simulator Reference Guide, SAND2025-05993 | 7.10 | https://xyce.sandia.gov/download/2068/ (link from https://xyce.sandia.gov/documentation-tutorials/ ) | Searched, selected sections read |
| `XYC-BLD` | Xyce build documentation: building guide https://xyce.sandia.gov/documentation-tutorials/building-guide/ and `INSTALL.md` of the release tag https://github.com/Xyce/Xyce/blob/Release-7.10.0/INSTALL.md | 7.10 | as listed | Read, to build Xyce (`tools/xyce/Dockerfile`) |
| `XYC-UG` | Xyce Users' Guide, SAND2025-05995 | 7.10 | https://xyce.sandia.gov/download/1756/ | Downloaded, not yet read |
| `HSP` | Synopsys HSPICE documentation | not accessed | https://www.synopsys.com (login required) | **Not read.** HSPICE statements in this repo come only from `XYC-REF` or are marked "from memory". |

Source code of any simulator is **out of bounds** for this project and is
not listed here as a source. See [../docs/clean-room.md](../docs/clean-room.md).

## Citing

- `SP3-UG`: cite the page and heading, since the pages have no section numbers.
  The pages were archived by the Internet Archive; the capture date used is in
  the registry. The original bwrcs.eecs.berkeley.edu pages are not reliably
  live.
- `NGS-42` and `NGS-47`: cite section number **and** title, because numbers
  moved between versions (table below).
- `XYC-REF`: cite section number (for example `2.1.39.3`).
- Where a statement was checked by running a tool, cite the conformance test
  ID and the tool version instead.

## Section number map, ngspice 42 to 47+

Headings I checked in both manuals. Chapter 2 sections moved, and the
analysis chapter moved from 15 to 11.

| Topic | NGS-42 | NGS-47 |
|-------|--------|--------|
| Input file structure | 2.1.1 | 2.1.1 |
| Letters following a number | 2.1.4.3 | 2.1.3.3 |
| Ground node | 2.1.4.5 | 2.1.3.5 |
| End-of-line comments | 2.3.4 | 2.4.4 |
| Continuation lines | 2.3.5 | 2.4.5 |
| `.ENDS` line | 2.5.2 | 2.6.2 |
| Syntax of expressions | 2.9.5 | 2.11.5 |
| Resistors | 3.3.1 | 3.3.1 |
| Coupled inductors | 3.3.12 | 3.3.12 |
| Switches | 3.3.15 | 3.3.15 |
| AM source | 4.1.6 | 4.1.6 |
| Behavioral source | 5.1 | 5.1 |
| `.AC` / `.DC` / `.TRAN` | 15.3.1 / 15.3.2 / 15.3.10 | 11.3.1 / 11.3.2 / 11.3.10 |

Other sections cited as `NGS-42` were not checked against `NGS-47` and may have
moved.

## Findings that came from comparing sources

| Finding | Sources |
|---------|---------|
| SPICE3 has no atto (`a`) scale factor; ngspice has. So `1A` is 1 in SPICE3 (letters ignored), 1e-18 in ngspice. | `SP3-UG` Circuit Description, "Numbers"; `NGS-42` 2.1.4.2; test LEX-001 |
| Xyce reads `a` as amperes by default and as atto only with `-hspice-ext units`. It says HSPICE accepts atto. | `XYC-REF` 3.1 and 6.2 |
| A line starting with white space is a comment in SPICE3 and in Xyce (unless the next character is `+`). In ngspice it is not a comment: leading white space is ignored. | `SP3-UG` Circuit Description, "Comments"; `XYC-REF` 2.1.39.1; `NGS-42` 2.1.1 |
| `log()` is base 10 in Xyce by default and natural in PSpice and in Xyce with `-hspice-ext math`. | `XYC-REF` 3.1, 6.1.14 |
| `AM(...)` is documented in ngspice only. It was not found in `XYC-REF`. | `NGS-42` 4.1.6; text search of `XYC-REF` |
| SPICE3 source functions have fewer parameters: PULSE 7 (no pulse count), SIN 5 (no phase), SFFM 5 (no phases), PWL without `r` or `td`. | `SP3-UG` Elements, "Independent Sources" |
| SPICE3 `R`, `C`, `L` take just a value (plus `IC` for C and L) or a model with `L=`, `W=`. `m`, `tc1`, `scale`, `temp`, `dtemp`, `noisy` are ngspice additions. | `SP3-UG` Elements; `NGS-42` 3.3.1 to 3.3.10 |
| Xyce says its switch differs from SPICE3F5 (SPICE3F5 has a single threshold). | `XYC-REF` 6.2 |
