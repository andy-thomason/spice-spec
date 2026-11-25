# Analyses: what `.op`, `.dc`, `.ac` and `.tran` compute

Status: draft v0.1. The syntax is in
[../../grammar/06-analyses.md](../../grammar/06-analyses.md); this page says
what each analysis does with the elaborated netlist
([../../grammar/08-elaboration.md](../../grammar/08-elaboration.md)) and what
it outputs.

Sources: `SP3-UG` "Analyses" and "Initial conditions"; `NGS-42` chapter 15
(analyses) and 15.2.x (`.ic`, `.nodeset`); `XYC-REF` chapter 6 (analysis
statements). Registry: [../../sources/README.md](../../sources/README.md).
Everything marked **observed** was measured on ngspice 42 and Xyce 7.10 with
the examples below (run with `tools/doctest.py`; see
[../11-compat/matrix.md](../11-compat/matrix.md)) and is not stated, or is
stated differently, in those documents. Examples are **non-normative**: the
text is the specification.

Each rule says where the tools agree (`common`) or differ
(`dialect:ngspice`, `dialect:xyce`). The numerical method, step control and
convergence aids (gmin stepping, source stepping, timestep rejection) are
**not specified**: a conforming tool may use any method whose results stay
within the tolerances the deck sets (`reltol`, `abstol`, `vntol`, documented
defaults 1e-3, 1 pA, 1 uV). Examples therefore compare with a tolerance.

## 1. Model

An analysis solves the circuit equations of the flat netlist. Every analysis
except `.tran ... uic` starts from a **DC operating point**; `.ac` linearizes
the circuit around it.

Element behavior at DC (`common`, `SP3-UG`, observed on both tools):

- a capacitor is an open circuit;
- an inductor is a short circuit (zero volts across it);
- an independent source supplies its DC value, except that a source with a
  time-varying waveform supplies a value that depends on the dialect: see
  [../06-sources/waveforms.md](../06-sources/waveforms.md).

One deck may hold several analysis cards. This page describes each one on its
own; running several in one deck and the order of their results are open
(A-44).

## 2. `.op`

The result is the operating point: every node voltage and every
voltage-source, inductor and other current-defined branch current.

```spice-test id=SEM-OP-1 covers=op-card dialect=common
V1 a 0 5
R1 a b 1k
C1 b 0 1u
R2 b c 1k
L1 c 0 1m
.op
* expect: v(a) = 5
* expect: v(b) = 2.5
* expect: v(c) = 0
* expect: i(l1) = 0.0025
* expect: i(v1) = -0.0025
```

The capacitor carries no current and the inductor has no voltage, so `R1`
and `R2` form a 2 kohm divider that carries 2.5 mA. `i(v1)` is negative
because SPICE defines a voltage source's current as flowing from its positive
node *through the source* to its negative node (`SP3-UG`).

**Floating nodes** (`dialect` agreed on the result, tools warn). A node whose
only connections are capacitors has no DC path to ground and the DC equations
are singular. Both tools warn, add a small conductance to ground and carry
on. The value is an artifact of that conductance, so it is
**implementation-defined**; both measured tools gave 0.5 here.

```spice-test id=SEM-OP-2 dialect=common expect=warn
V1 a 0 1
C1 a b 1u
C2 b 0 1u
.op
* expect: v(b) = 0.5 tol=1e-3
```

**`.ic` and `.op`** (`dialect:ngspice`, observed). ngspice's `.op` ignores
`.ic`. Xyce applies `.ic` to the operating point (v(a) = 2 below). The spec
treats `.ic` as a transient option (section 5); using it with `.op` is not
portable (A-42).

```spice-test id=SEM-OP-3 dialect=ngspice
V1 in 0 5
R1 in a 1k
C1 a 0 1u
.ic v(a)=2
.op
* expect: v(a) = 5
```

## 3. `.dc`

`.dc SRC START STOP STEP [SRC2 START2 STOP2 STEP2]` replaces the DC value of
the named independent source with each sweep value in turn and solves an
operating point at each (`common`).

- The first point is `START`. The next points are `START + k*STEP`, for
  `k = 1, 2, ...`, while the value has not passed `STOP`. `STOP` is included
  if it is reached, to within rounding. The point count is
  `floor((STOP - START)/STEP + e) + 1` for a small rounding allowance `e`.
  Observed: `0 1 0.1` gives exactly 11 points on both tools, and `0 1 0.3`
  stops at 0.9.
- The sweep may descend: give `START > STOP` and a negative `STEP`.
- `STEP` must have the sign of `STOP - START`. When it does not, ngspice
  produces no points and Xyce warns and produces the first point only. The
  spec treats this as an error (A-41).
- **Nesting.** With two sweeps, the **first** source is the inner loop, so it
  runs through its whole range for each value of the second (observed, both
  tools).

```spice-test id=SEM-DC-1 covers=dc-card dialect=common
V1 a 0 0
R1 a 0 1k
.dc V1 0 1 0.3
* expect: points(v(a)) = 4
* expect: v(a) = 0.9
```

```spice-test id=SEM-DC-2 dialect=common
V1 a 0 0
R1 a 0 1k
.dc V1 1 0 -0.25
* expect: points(v(a)) = 5
* expect: v(a) = 0
```

```spice-test id=SEM-DC-3 dialect=common
V1 a 0 0
V2 b 0 0
R1 a 0 1k
R2 b 0 1k
.dc V1 0 1 1 V2 0 20 10
* expect: points(v(a)) = 6
* expect: v(a) = 1
* expect: v(b) = 20
```

```spice-test id=SEM-DC-4 dialect=common
V1 a 0 0
R1 a 0 1k
.dc V1 0 1 0.1
* expect: points(v(a)) = 11
* expect: v(a) = 1
```

## 4. `.ac`

`.ac dec|oct|lin N FSTART FSTOP` finds the operating point, replaces every
element by its small-signal linear model at that point, and solves the
complex linear system at each frequency (`common`, `SP3-UG`).

- **Sources.** Only independent sources with an `AC` field are excited: the
  field gives magnitude and phase in **degrees** (default 0). All other
  sources, including their DC values, are zero in the AC system. With no `AC`
  source every result is 0 (observed, both tools).
- **Frequencies.**
  - `lin N`: N points in total from `FSTART` to `FSTOP` inclusive, evenly
    spaced. `N` counts points, not intervals.
  - `dec N`: N points per decade, `f = FSTART * 10^(k/N)`. `oct N`: N points
    per octave, `f = FSTART * 2^(k/N)`. When `FSTOP/FSTART` is a whole number
    of decades (octaves) the count is `N * decades + 1` and the last point is
    `FSTOP`.
  - Otherwise the tools differ (`dialect`): ngspice uses
    `floor(N*log10(FSTOP/FSTART)) + 1` points for `dec` and rescales the
    spacing so that the last point is exactly `FSTOP`. For `oct` it keeps the
    nominal ratio (last point of `oct 1 1 6` was 4). Xyce keeps the nominal
    ratio for `dec` and stops at the last point not above `FSTOP`. Treat the
    point set for such ranges as implementation-defined (A-43).
- **Output.** Each point holds complex node voltages and branch currents.
  Phase is a complex-number property: the unit is chosen by the output
  function. Observed: ngspice `ph()` returns radians by default, and Xyce
  `VP()` returns degrees. Examples below check magnitude, real and imaginary
  parts, which do not depend on the unit.

The RC low-pass in these examples has its corner at exactly 1 Hz
(`1k * 159.15494309u = 1/(2*pi) s`), so at 1 Hz the gain is `1/sqrt(2)` and the
phase is -45 degrees.

```spice-test id=SEM-AC-1 covers=ac-card dialect=common
V1 in 0 DC 0 AC 1
R1 in out 1k
C1 out 0 159.15494309u
.ac dec 2 1 100
* expect: points(mag(v(out))) = 5
* expect: mag(v(out)) @ 1 = 0.70710678 tol=1e-6
* expect: db(v(out)) @ 1 = -3.0103 tol=1e-4
* expect: mag(v(out)) @ 10 = 0.099503719 tol=1e-6
```

```spice-test id=SEM-AC-2 dialect=common
V1 in 0 DC 0 AC 2 90
R1 in out 1k
C1 out 0 159.15494309u
.ac oct 1 1 8
* expect: points(mag(v(out))) = 4
* expect: real(v(out)) @ 1 = 1 tol=1e-6
* expect: imag(v(out)) @ 1 = 1 tol=1e-6
* expect: mag(v(out)) @ 8 = 0.24806947 tol=1e-6
```

The source above has magnitude 2 and phase 90 degrees, so it equals `2j`.
Multiplying by the filter's `(1 - j)/2` at 1 Hz gives `1 + j`.

```spice-test id=SEM-AC-3 dialect=common
V1 in 0 DC 0 AC 1
R1 in out 1k
C1 out 0 159.15494309u
.ac lin 4 1 10
* expect: points(mag(v(out))) = 4
* expect: mag(v(out)) @ 4 = 0.24253563 tol=1e-6
```

```spice-test id=SEM-AC-4 dialect=common
V1 in 0 DC 1
R1 in out 1k
C1 out 0 1u
.ac dec 1 1 10
* expect: points(mag(v(out))) = 2
* expect: mag(v(out)) = 0
```

```spice-test id=SEM-AC-5 dialect=ngspice
V1 in 0 DC 0 AC 1
R1 in out 1k
C1 out 0 159.15494309u
.ac dec 1 1 50
* expect: points(mag(v(out))) = 2
* expect: mag(v(out)) @ 50 = 0.019996 tol=1e-4
```

## 5. `.tran`

`.tran TSTEP TSTOP [TSTART [TMAX]] [uic]` computes the response from time 0
to `TSTOP`.

- **Starting state.** Without `uic`, the analysis starts from the operating
  point at time 0 (every source at its time-0 value). With `uic` ("use
  initial conditions") it skips the operating point and starts from the
  initial conditions of section 6 (`common`).
- **Output points.** `TSTEP` is the suggested print step and the first guess
  for the internal step; `TMAX` caps the internal step (default
  `min(TSTEP, (TSTOP-TSTART)/50)`). The times at which a tool reports values
  are **implementation-defined**: both tools report their own internal time
  points, not a uniform grid. Compare by interpolating (examples use
  `v(a) @ T`). The first reported time is 0 unless `TSTART > 0`, in which
  case nothing before `TSTART` is reported (observed: ngspice's first point
  was slightly after `TSTART`; Xyce's was exactly at it).
- **Last point.** The last reported time is `TSTOP`.

```spice-test id=SEM-TRAN-1 covers=tran-card dialect=common
V1 in 0 5
R1 in a 1k
C1 a 0 1u
.tran 0.5m 2m
* expect: v(a) @ 1m = 5
* expect: v(a) = 5
```

An RC circuit that starts from its operating point is already settled, so
`v(a)` stays at 5 V.

```spice-test id=SEM-TRAN-2 dialect=common
V1 in 0 5
R1 in a 1k
C1 a 0 1u
.tran 0.5m 2m uic
* expect: v(a) @ 1m = 3.1606028 tol=2e-3
```

With `uic` and no initial conditions, the node starts at 0 and charges with
time constant 1 ms: `5 * (1 - e^-1)` at 1 ms.

## 6. Initial conditions: `.ic`, `ic=` and `.nodeset`

Three mechanisms set the state at the start of a transient run:

1. **`.ic v(node)=value`** forces the node to the value.
   - Without `uic`, the operating point is solved with the node held at the
     value, and the transient run starts from that (`common`, observed). The
     node then evolves freely.
   - With `uic`, the value is the node's initial voltage; all other nodes
     start at 0 (`common`, observed).
2. **Element `ic=` parameters** (capacitor voltage, inductor current).
   - With `uic`: they set the initial state (`common`, observed).
   - Without `uic`: **ngspice ignores them, Xyce applies them** (observed).
     The spec treats `ic=` without `uic` as having no defined effect (A-42).
3. **`.nodeset v(node)=value`** is only a hint for the DC operating-point
   solver: it picks the starting guess, so it selects among several valid
   solutions of a circuit with more than one (a latch, say) and changes
   nothing for a circuit with one solution (`common`, observed on both).

```spice-test id=SEM-IC-1 covers=ic-card dialect=common
V1 in 0 5
R1 in a 1k
C1 a 0 1u
.ic v(a)=2
.tran 0.5m 2m
* expect: v(a) @ 0 = 2
* expect: v(a) @ 1m = 3.8964 tol=2e-3
```

Without `uic` the run starts at 2 V (not the operating point 5 V) and charges
toward 5 V: `5 - 3 e^-1` at 1 ms.

```spice-test id=SEM-IC-2 dialect=common
R1 a 0 1k
C1 a 0 1u ic=2
.tran 0.5m 2m uic
* expect: v(a) @ 1m = 0.7357589 tol=2e-3
```

```spice-test id=SEM-IC-3 dialect=common
R1 a 0 1k
C1 a 0 1u
.ic v(a)=2
.tran 0.5m 2m uic
* expect: v(a) @ 1m = 0.7357589 tol=2e-3
```

```spice-test id=SEM-IC-4 dialect=ngspice
V1 in 0 5
R1 in a 1k
C1 a 0 1u ic=2
.tran 0.5m 2m
* expect: v(a) @ 1m = 5
```

The last example shows ngspice ignoring `ic=` without `uic`.

A circuit with two stable states shows `.nodeset`: two inverting `B`
sources feed each other, and the hint picks which state the operating point
reaches.

```spice-test id=SEM-NS-1 covers=nodeset-card dialect=common
B1 a 0 V=tanh(10*v(b))
B2 b 0 V=tanh(10*v(a))
.nodeset v(a)=1 v(b)=1
.op
* expect: v(a) = 1 tol=1e-6
* expect: v(b) = 1 tol=1e-6
```

```spice-test id=SEM-NS-2 dialect=common
B1 a 0 V=tanh(10*v(b))
B2 b 0 V=tanh(10*v(a))
.nodeset v(a)=-1 v(b)=-1
.op
* expect: v(a) = -1 tol=1e-6
* expect: v(b) = -1 tol=1e-6
```

## Open questions

A-41 to A-44 in [../../grammar/ambiguities.md](../../grammar/ambiguities.md):
wrong-sign sweep steps, `.ic`/`ic=` outside the cases above, point sets for
non-whole-decade `.ac` ranges, and several analysis cards in one deck.
Not yet covered: `.noise`, `.tf`, `.pz`, `.sens`, `.disto`, temperature
sweeps, `.step`, `.measure`, and the printed form of `.print`.
