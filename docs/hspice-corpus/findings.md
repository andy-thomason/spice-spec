# Findings: syntax seen in open model libraries

Status: draft v0.1. Counts come from `tools/scan-syntax.py` run on the four
libraries listed in [../hspice-corpus.md](../hspice-corpus.md); the raw counts
are in the JSON files next to this page. Read the limits in that page first:
these libraries are mostly ngspice-oriented, so the counts describe what
HSPICE-style libraries *use*, not what HSPICE *accepts*. Evidence level is
**seen** unless stated.

## Corpus size

| | asap7 | ihp-sg13g2 | sky130 | gf180mcu |
|---|---|---|---|---|
| files scanned | 7 | 38 | 1232 | 115 |
| logical lines | 91 | 2685 | 20289 | 2929 |
| continuation lines | 1730 | 3161 | 1666236 | 45736 |
| files the reference parser rejects with an error | 0 | 0 | 0 | 0 |
| parser warnings (all `invalid-line`) | 4 | 0 | 2 | 31 |

## Cards

| card | asap7 | ihp-sg13g2 | sky130 | gf180mcu |
|---|---|---|---|---|
| `.model` | 48 | 55 | 6196 | 271 |
| `.param` | 0 | 1901 | 1563 | 287 |
| `.subckt` | 0 | 50 | 511 | 96 |
| `.lib` | 0 | 51 | 294 | 255 |
| `.endl` | 0 | 51 | 9 | 59 |
| `.include` | 0 | 109 | 1996 | 111 |
| `.option` | 0 | 0 | 165 | 0 |
| `.options` | 0 | 0 | 0 | 66 |
| `.temp` | 0 | 0 | 0 | 64 |
| `.if` | 0 | 59 | 0 | 0 |
| `.control` | 0 | 0 | 348 | 61 |
| `.csparam` | 0 | 0 | 72 | 0 |
| `.step` | 0 | 0 | 0 | 46 |
| `.meas` | 0 | 0 | 0 | 29 |
| `.print` | 0 | 0 | 0 | 54 |
| `.ic` | 0 | 0 | 0 | 3 |

Element letters seen: `a`, `c`, `d`, `e`, `f`, `i`, `l`, `m`, `n`, `o`, `p`, `q`, `r`, `s`, `t`, `v`, `w`, `x`.

## Model types and levels (`name:level` counts)

- `asap7`: `nmos:72` 24, `pmos:72` 24
- `ihp-sg13g2`: `d:3` 13, `d:1` 8, `npn:9` 6, `psp103va:103.60` 6, `pspnqs103va:103.60` 4, `mosvar:1000` 2, `pnp:1` 1
- `sky130`: `pmos:54.0` 3346, `nmos:54.0` 2737, `d:3.0` 22, `nmos:49.0` 12, `npn:1.0` 3, `pnp:1.0` 3, `pmos:49.0` 2, `pmos:5.400000` 2
- `gf180mcu`: `nmos:54` 101, `pmos:54` 99, `d:3` 29, `npn:1` 6, `pnp:1` 4

## Expressions

| | asap7 | ihp-sg13g2 | sky130 | gf180mcu |
|---|---|---|---|---|
| quoted or braced expressions | 0 | 1370 | 81637 | 1930 |
| `.param` values: bare / quoted / braced | 0 / 0 / 0 | 1848 / 260 / 20 | 154457 / 14067 / 443 | 953 / 333 / 0 |

Functions seen inside expressions (count): `sqrt` 23192, `max` 203, `agauss` 188, `abs` 163, `gauss` 129, `min` 36, `pow` 35, `tanh` 22, `pwr` 13, `n` 10, `log` 9, `cosh` 6, `ln` 1, `floor` 1.

Operators seen: `?` 227, `!=` 182, `!` 182, `**` 119, `==` 51, `||` 2, `<=` 2.

## Numbers

Tail letters after a number (count): `u` 2050, `v` 771, `meg` 333, `p` 217, `g` 17, `m` 11, `e3` 11, `e10` 8, `e4` 8, `e9` 7, `us` 6, `n` 5, `e5` 5, `e8` 5. Letters such as `u`, `p`, `meg`, `g` are scale factors; `v`, `us`, `ns` are scale plus unit or a unit word; `e3`-style tails are an exponent after a letter-led token (for example inside a parameter name).

## Comments, layout

| | asap7 | ihp-sg13g2 | sky130 | gf180mcu |
|---|---|---|---|---|
| `*` comment lines | 1428 | 1566 | 146746 | 2652 |
| `$` end-of-line comments | 4 | 0 | 37 | 22 |
| `;` end-of-line comments | 1 | 9 | 0 | 0 |
| `//` end-of-line comments | 0 | 0 | 0 | 0 |
| lines starting with white space | 0 | 1918 | 7 | 733 |
| lines with a tab | 0 | 0 | 62 | 97 |
| lines with a carriage return | 0 | 0 | 0 | 0 |
| files without a final newline | 0 | 0 | 0 | 32 |
| files that are not UTF-8 | 0 | 1 | 0 | 0 |

## Reading the counts

What the HSPICE layer has to accept, in order of how much of the corpus uses it:

1. **Long logical lines.** The BSIM model cards run to thousands of `+`
   continuation lines (sky130: 1.67 million continuation lines for 20 thousand
   logical lines). Pass 1 must join them without a line-length limit.
2. **Quoted expressions, everywhere.** Parameter values and model parameters
   are written as `'expression'` (sky130: about 82 thousand quoted or braced
   expressions, 14 thousand of them in `.param` values). Braces are rare.
   The functions used are few: `sqrt` dominates, then `abs`, `min`, `max`,
   `pow`, `pwr`, `tanh`, `cosh`, `log`, `ln`, `floor`. The statistical
   functions `agauss` and `gauss` appear in one library (ihp-sg13g2) for
   Monte Carlo parameters. The operators seen are `**`, `?:`, `!=`, `==`, `||`,
   `<=` and `!`.
3. **`.lib` with a section.** `.lib file section` (call) and `.lib section`
   ... `.endl` (definition) are the main structure of every PDK except asap7.
4. **Model binning.** About 6 thousand sky130 models, 200 gf180mcu models and
   2 in ihp-sg13g2 carry `lmin`/`lmax`/`wmin`/`wmax`. The semantics need the
   boundary rule (see [spec/09-dialects/library-conventions.md](../../spec/09-dialects/library-conventions.md), A-47).
5. **`.option scale`** and `tnom` as options (A-46), and `.temp`.
6. **Subcircuits with parameter defaults** (`.subckt name a b w=1 l=1`). The
   `params:` keyword was not seen at all in this corpus.
7. **Unit words** after numbers (`1.8v`, `10pf`, `1ns`, `10us`).
8. **`DC` followed directly by a waveform** (A-45).

Seen and **specific to ngspice or other tools**, so not evidence for HSPICE:
`.control`/`.endc` blocks and `#` comment lines inside them, `.csparam`,
`.if`/`.else`/`.endif` (ihp-sg13g2; ngspice's conditional blocks), OSDI
(`N` elements, `psp103va` models), XSPICE (`A` elements) and template
placeholders such as `{{name}}` in gf180mcu test decks (not SPICE at all).
These account for nearly all the reference parser's warnings.

## What this changed

- Open questions A-45 to A-47 in
  [../../grammar/ambiguities.md](../../grammar/ambiguities.md).
- Three measured examples (LIB-DC-1, LIB-SCALE-1, LIB-UNIT-1) in
  [../../spec/09-dialects/library-conventions.md](../../spec/09-dialects/library-conventions.md).
- The reference parser reported no errors on any file. Its 37 warnings are
  these, found by looking at the flagged lines locally:
  - 26 in gf180mcu: `DC` before a waveform (A-45);
  - 5 in gf180mcu: template placeholders such as `{{sign}}` and a line that is
    only a placeholder (not SPICE);
  - 4 in asap7: the file `cds.lib` is a Cadence configuration file, not
    SPICE (the scan matched it by extension; a scanner limitation);
  - 2 in sky130: a card line `include "file"` written **without the leading
    dot**, and a resistor-like line with a stray `=`, both in test files.
  So the grammar already covers the structure of these libraries. The count
  was not rechecked after the scanner's `.lib` extension handling; `cds.lib`
  files should be excluded in a later run.

## Not found

None of the cards `.alter`, `.data`, `.protect`, `.unprotect`, `.hdl`,
`.macro` or `.eom` appeared in any of the four libraries (checked in the card
counts). That tells us nothing about HSPICE (see the limits in
[../hspice-corpus.md](../hspice-corpus.md)); these libraries just do not use
them.

## Next

Libraries written for commercial HSPICE (vendor PDKs, device vendors'
models) would show more, but are not open. Public device-vendor models
(for example power MOSFETs and op-amps distributed as `.lib` files) are a
possible next corpus once their licences are checked file by file.
