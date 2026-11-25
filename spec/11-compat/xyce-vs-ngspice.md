# Xyce 7.10 and ngspice 42

Status: draft v0.1. What the doctest examples showed when run on both
simulators. Every statement is **measured** on the versions named, unless a
source ID is given (registry: [../../sources/README.md](../../sources/README.md)).
The per-example results are in [matrix.md](matrix.md); example IDs below refer
to it. HSPICE has not been read or run (`HSP`).

## How Xyce was run

- **Version:** Xyce 7.10.0, serial, built from the release tag
  `Release-7.10.0` of https://github.com/Xyce/Xyce with Trilinos 14.4.0 and
  SuiteSparse 7.8.3 (the versions its own `INSTALL.md` asks for), in a container
  from the official `ubuntu:24.04` image. The recipe is
  [../../tools/xyce/Dockerfile](../../tools/xyce/Dockerfile).
- **Source checksums** (tarballs from the tags): Xyce `b5a88319…4e2`,
  Trilinos `8e7d881c…4c6`, SuiteSparse `ce39b28d…259` (full values are printed
  in the build log by the Dockerfile).
- **Clean room:** the Xyce source was compiled, not read. Only the build
  guide, `INSTALL.md` and the Reference Guide (`XYC-REF`) were read.
- **Running:** each example is run in a throwaway container with no network
  and only its own directory mounted. `XYCE_NO_TRACKING` is set.

## Reproducing

```
# on a machine with Docker (about 30 to 60 minutes to build):
docker build -t xyce-local:7.10.0 tools/xyce
python3 tools/doctest.py --simulator xyce --json xyce.json \
  --xyce "docker run --rm --network none --user $(id -u):$(id -g) -v {dir}:/work -w /work xyce-local:7.10.0 Xyce" \
  grammar spec
python3 tools/doctest.py --ngspice $(which ngspice) --json ngspice.json grammar spec
python3 tools/matrix.py ngspice=ngspice.json xyce=xyce.json > spec/11-compat/matrix.md
```

For Xyce the runner prints values with `.print ... format=csv` instead of
ngspice's control language, appends `.op` when a deck has no analysis Xyce
knows, and adds a step ceiling to `.tran` so interpolated checks are
accurate. Of 127 examples, 21 do not apply to Xyce, 71 pass and 35 differ.

## Numbers (examples TOK-NUM-*, LEX-NUM-*, LEX-SEP-*)

| Word | ngspice 42 | Xyce 7.10 |
|------|-----------|-----------|
| `1k5`, `1_000`, `0x10`, `1.5.2`, `1m_eg` | read as `1k`, 1, 0, 1.5, 1e-3 (the rest ignored) | **error** ("Invalid DC value") |
| `1Mi`, `10Volts`, `1dk` | 1e-3, 10, 1000 | **error** |
| `1D3` | 1000 | **error** |
| `1e`, `1e+` | 1 | 1 |
| `5eu`, `5e-u`, `5e+meg` | 5e-6, 5e-6, 5e6 | 5e-6 (tested `5eu`) |
| `1A`, `3a` | 1e-18, 3e-18 (atto) | **1, 3** (amperes; the letter is ignored) |
| `1F`, `1G`, `1T`, `1Meg`, `1MEGOHM`, `1mil` | femto, giga, tera, mega, mega, mil | same |
| `10V`, `1Hz`, `2MA` | 10, 1, 2e-3 | same |
| `1e3x` | 1000 (`x` ignored) | **1e9** (`x` is a mega suffix, as in HSPICE) |

Xyce rejects a number word with unknown trailing characters, where ngspice
ignores everything up to the next separator. This confirms the `XYC-REF` 3.1
and 6.2 statements about atto (`a` is amperes unless `-hspice-ext units`).
The number rule in [../../grammar/00-tokens.md](../../grammar/00-tokens.md) is
therefore `dialect:ngspice`; a rule common to both tools is: digits, optional
fraction, optional `e` exponent, an optional scale factor from
`t g meg k mil m u n p f`, then at most unit letters.

## Separators and comments

- `DC=3` on a source is **accepted by ngspice and rejected by Xyce** (LEX-SEP-2).
  `=` is a separator in the SPICE3 manual and in ngspice, not in Xyce here.
- Parentheses around an element value, `R1 (a 0) (1k)`, are rejected by Xyce
  (TOK-PAR-1). They are accepted by ngspice.
- A line starting with white space is a comment in Xyce (`XYC-REF` 2.1.39.1),
  and the example TOK-WS-1 confirms it (the element on that line is missing).
  It is parsed as a card in ngspice. This is open issue A-25.
- End-of-line comments `;`, `$ ` and `//` all work in Xyce (TOK-COM-2 passes),
  although `XYC-REF` documents only `;`.
- `V1 a 0 5 * trailing` and `V1 a 0 1 mil` are errors in ngspice and are
  **accepted** by Xyce (TOK-COM-1, TOK-NUM-4): the extra fields are ignored.

## Cards and directives

| Feature | ngspice 42 | Xyce 7.10 |
|---------|-----------|-----------|
| `.if` / `.else` / `.endif` (NET-IF-1) | selects one branch | **not a feature**: both branches are read ("Duplicate device") |
| `.temp` (NET-TEMP-1) | sets the circuit temperature | **ignored with a warning** |
| `.csparam` (NET-CSPARAM-1) | parameter for the control language | warns |
| `.tf`, `.pz`, `.disto` (AN-TF-1, AN-PZ-1, AN-DISTO-1) | analyses | **warned and ignored** |
| `.sens v(out)` (AN-SENS-1) | analysis | different syntax: "No analysis specified" |
| bare `distof1` (AN-DISTO-2) | error (A-27) | accepted with a warning |
| `.options reltol=1e-4` (AN-OPTIONS-1) | option | warns: options need a package name (`.options timeint reltol=...`) |
| `.param`, `.func`, `.global`, `.include`, `.lib`, `.subckt`, `.model` | as specified | the examples pass |

## Elements

- **Switches** (EL-S-1, EL-W-1): ngspice's `.model sw sw(...)` and `csw` are not
  found by Xyce ("No model found for switch device"); its model type names
  differ. `XYC-REF` 6.2 also says its switch behaves differently from SPICE3's.
- **URC line** (EL-U-1): `U1 a b 0 um l=50u` is not accepted by Xyce.
- Mesfet and lossy-line examples (EL-Z-1, EL-O-1) run on Xyce with a warning.
- The rest of the element examples (R, C, L, K, V, I, E, F, G, H, B, D, Q, J, M,
  T) give the same values on both.

## Expressions (EXPR-*)

Measured with a list of expressions evaluated by both. This is the largest
disagreement in the arithmetic.

| Expression | ngspice 42 | Xyce 7.10 |
|------------|-----------|-----------|
| `2^3^2` | 64 (left-associative power) | **1** (`^` is logical xor in Xyce) |
| `2^0.5` | 1.414 | **0** (same reason) |
| `2**3**2` | 64 | **512** (right-associative) |
| `(-2)**3` | 8 (sign of the base dropped) | **-8** |
| `pwr(-2,3)` | 8 | **-8** |
| `-2**2`, `2**-2`, `-2+3`, `2*-3` | -4, 0.25, 1, -6 | same |
| `5%3`, `5.5%2` | 2, 1.5 | same |
| `1<2<3`, `3>2>1`, `1?2:3`, `1+1?3:4`, `1&&0||1` | 1, 0, 2, 3, 1 | same |
| `nint(2.5)` | 2 (half to even) | **3** (half away from zero) |
| `int(-2.7)`, `floor(-2.7)`, `ceil(-2.2)`, `sgn`, `min`, `max`, `abs` | same | same |
| `log(100)` | 4.605 (natural) | **2** (base 10, as `XYC-REF` 6.1.14 says) |
| `ln(100)`, `log10(100)` | 4.605, 2 | same |
| `7/0` | **error** (non-finite result) | **1e50**, no error |
| `7==4/0` | 0 | 0 |
| `sqrt(-4)` | error | **0** |
| `!2`, `5\3` | 0, 1 | **syntax error** (no `!` or `\` operators) |

The precedence rules measured on ngspice in
[../../grammar/05-expressions.md](../../grammar/05-expressions.md) are therefore
**not common**. Where they agree (unary minus below power, comparisons left to
right, `%`), the rule may be called common; for `^`, `**` associativity,
rounding, and domain errors they must be written per tool. Open issues A-21,
A-22 and A-34.

## Source waveforms (WF-*)

| Behavior | ngspice 42 | Xyce 7.10 |
|----------|-----------|-----------|
| `AM(...)` source (SRC-AM-1, WF-AM-*) | works | **not supported** (`XYC-REF` has no such function) |
| DC and operating-point value of a source (WF-PULSE-5, WF-SIN-3, WF-PWL-4, WF-SFFM-2) | its value at `t = 0` (`v1`, `vo+va·sin(phase)`, first PWL value, ...) | **its `DC` value, 0 if none** |
| `PULSE` with `tr = 0` (WF-PULSE-3) | rises over `tstep` | **instantaneous** |
| `PULSE` 8th parameter, pulse count (WF-PULSE-4) | limits the number of pulses | **ignored** (pulses continue) |
| `SIN(vo va)` with no frequency (WF-SIN-4) | uses `1/tstop` | **error**: "V0, VA and FREQ are required" |
| `PWL(...) td=` (WF-PWL-3) | delays the sequence | exits with status 1 and **no message** |
| `PULSE`, `SIN`, `EXP`, `PWL` (with `r=`), `SFFM` waveforms (WF-PULSE-1,2, WF-SIN-1,2, WF-EXP-1, WF-PWL-1,2, WF-SFFM-1) | as in [../06-sources/waveforms.md](../06-sources/waveforms.md) | the same values |

So the waveform formulas in the spec are common to both tools, but the
**time-zero value** and the **defaults for missing parameters** are not. The
spec page marks them as ngspice behavior.

## Consequences for the spec

1. Rules proved on both tools may be tagged `common`: the element examples
   above, comments with `;`, the waveform formulas, `.param`, `.func`,
   `.global`, `.subckt`, `.include`, `.lib`.
2. Rules found only on ngspice stay `dialect:ngspice` and get a Xyce note:
   number tail, `=` as separator, `.if`, `.temp`, `.tf`/`.pz`/`.disto`, `AM`,
   expression operators `\` and `!`, time-zero source values.
3. A netlist that must run on both tools has to avoid: `1D3`-style exponents,
   unit words after numbers, `DC=value`, parentheses around element values,
   `.if`, `.temp`, `^` as power, `!`, `\`, and `AM`.
4. The doctests are now tagged from the matrix: `dialect=common` (68) passes
   on both tools, `dialect=ngspice` (56) does not. An example Xyce accepts
   only by ignoring a card with a warning counts as `ngspice`. Retag after
   each matrix run.
