# Semiconductor devices: diode, BJT, MOSFET level 1

Status: draft v0.1. The **basic** large-signal equations of the three oldest
SPICE devices, enough to check an implementation against closed-form values.
Capacitances, noise, breakdown, high-injection effects, temperature scaling
and the many later MOSFET levels (BSIM and others) are **not** specified here.
Card syntax is in [../../grammar/03-elements.md](../../grammar/03-elements.md).

Sources: `SP3-UG` Elements page ("Junction Diodes", "Diode Model (D)",
"Bipolar Junction Transistors", "BJT Models (NPN/PNP)", "MOSFETs", "MOSFET
Models (NMOS/PMOS)"); `NGS-42` 7.1 to 7.3 (diode, model, equations), 8.1 and
8.2 (BJT), 11.1 and 11.2.1 (MOSFET, MOS level 1); `XYC-REF` 2.3.8 (diode),
2.3.17 (BJT), 2.3.20.1 (level 1 MOSFET). Registry: [../../sources/README.md](../../sources/README.md).
The equations below are standard textbook device physics as the documents
describe them, written in our own words. **Observed** means checked by the
examples on ngspice 42 and Xyce 7.10. Examples are **non-normative**.

## Thermal voltage

`vt = k T / q`, with `T = 300.15 K` (27 degrees Celsius, the default `Tnom`
and circuit temperature), giving `vt = 25.865 mV`. The physical constants
differ in their last digits between tools, which changes `vt` by about 1e-5
relative. Examples therefore use a tolerance of 1e-2 or wider on quantities
that depend on `exp(v/vt)`.

## Diode `D`

Card `D name anode cathode model [area]`. With junction voltage `vd` across
the junction (after the series resistance `rs`):

```
id = is * (exp(vd / (n vt)) - 1)        forward and weak reverse
```

`is` defaults to 1e-14 A, `n` (emission coefficient) to 1, `rs` to 0
(`common`; defaults from `SP3-UG` "Diode Model (D)" and `NGS-42` 7.2). The terminal voltage is `vd + id * rs`. A small
conductance `gmin` (default 1e-12 S) is added across the junction by both
tools to help convergence; it changes results by less than the examples'
tolerance.

```spice-test id=EL-SEMI-D-1 covers=diode dialect=common
I1 0 a 1m
D1 a 0 dm
.model dm D(is=1e-14 n=1)
* expect: v(a) = 0.65512 tol=2e-3
```

`vd = n vt ln(id/is + 1)` with `id = 1 mA` gives 0.6551 V.

```spice-test id=EL-SEMI-D-2 dialect=common
I1 0 a 1m
D1 a 0 dm
.model dm D(is=1e-14 n=1 rs=10)
* expect: v(a) = 0.66512 tol=2e-3
```

A 10 ohm series resistance adds 10 mV at 1 mA.

### Diode depletion capacitance

With zero-bias capacitance `cj0`, built-in potential `vj` (default 1 V) and
grading coefficient `m` (default 0.5), the junction capacitance at reverse
voltage `V` (negative for reverse, `v = vanode - vcathode`) is
`C = cj0 * (1 - v / vj)^(-m)` while `v < fc * vj` (`fc` default 0.5). For
larger `v` the formula is replaced by a straight-line extension, so that the
capacitance stays finite (`common`; `NGS-42` 7.3, `XYC-REF` 2.3.8).
Examples check the capacitance through its effect on an AC divider.

```spice-test id=EL-SEMI-D-3 dialect=common
V1 s 0 DC 1 AC 1
R1 s a 2Meg
D1 0 a dm
.model dm D(is=1e-14 cj0=1p vj=1 m=0.5)
.ac lin 1 100k 100k
* expect: mag(v(a)) = 0.74752 tol=1e-3
```

The diode is reverse biased by 1 V, so `C = 1p / sqrt(2) = 0.7071 pF`. The
`2 Mohm` resistor and this capacitance form a low-pass filter with
`|H| = 1 / sqrt(1 + (2 pi f R C)^2) = 0.7475` at 100 kHz.

### Diode breakdown

Breakdown applies only if `bv` is given. In breakdown (reverse voltage beyond
`bv`) the reverse current rises exponentially with the same `n vt` slope as
the forward current. The model parameter `ibv` (default 1 mA) is the current
at which the diode reaches `bv`. Observed on both tools, with `ibv` well above
the reverse leakage `is`: the voltage across the diode at reverse current `i`
is `bv + n vt ln(i / ibv)` (`common` for these values; the documents say only
that `bv` and `ibv` fix the breakdown region, `NGS-42` 7.3).

```spice-test id=EL-SEMI-D-4 dialect=common
I1 0 a 10m
D1 0 a dm
.model dm D(is=1e-14 bv=5 ibv=1m)
* expect: v(a) = 5.05957 tol=5e-4
```

Reverse current of 10 mA: `5 + 0.025865 * ln(10) = 5.0596 V`.

## Bipolar transistor `Q` (Gummel-Poon, simple case)

Card `Q name collector base emitter model`. With the base-emitter and
base-collector junctions in forward active mode (`vbc` strongly negative) and
no Early effect (`vaf` infinite, the default), the model reduces to:

```
ic = is * (exp(vbe / vt) - 1)
ib = ic / bf
```

for an NPN transistor, with `is` default 1e-16 A and `bf` default 100
(`common`). PNP is the same with all voltages and currents reversed. Because
`i(V)` is a source's current, a source holding the collector at a positive
voltage reports `-ic`.

```spice-test id=EL-SEMI-Q-1 covers=bjt dialect=common
Vb b 0 0.65
Vc c 0 5
Q1 c b 0 qm
.model qm NPN(is=1e-15 bf=100)
* expect: i(vc) = -8.2047e-5 tol=1e-2
* expect: i(vb) = -8.2047e-7 tol=1e-2
```

With a forward Early voltage `vaf` (default infinite), the collector current
in forward active mode is multiplied by `1 - vbc / vaf`, which is
`1 + (vce - vbe) / vaf`; the base current is unchanged (`common`, observed).

```spice-test id=EL-SEMI-Q-2 dialect=common
Vb b 0 0.65
Vc c 0 10
Q1 c b 0 qm
.model qm NPN(is=1e-15 bf=100 vaf=100)
* expect: i(vc) = -8.9718e-5 tol=3e-3
* expect: i(vb) = -8.2047e-7 tol=1e-2
```

## MOSFET level 1 `M`

Card `M name drain gate source bulk model [w= l=]`, model type `NMOS` or
`PMOS` with `level=1`. With `vgs`, `vds` in the transistor's own polarity
(for PMOS, negate all voltages and currents), `vt` the threshold `vto` (here
without body effect, `gamma = 0`), `beta = kp * w / l`, and `lambda` the
channel-length modulation:

```
cutoff       vgs <= vt:             id = 0
triode       vds <  vgs - vt:       id = beta * ((vgs - vt) * vds - vds^2 / 2) * (1 + lambda * vds)
saturation   vds >= vgs - vt:       id = (beta / 2) * (vgs - vt)^2 * (1 + lambda * vds)
```

`kp` defaults to 2e-5 A/V^2, `vto` to 0, `lambda` to 0 (`common`). The
documents name the model (Shichman-Hodges) and its parameters (`NGS-42`
11.2.1; `SP3-UG` "MOSFET Models") but do not print the drain-current
equations, so the formulas above are the standard textbook form and are
**checked only where the examples test them**. Both tools apply the
`(1 + lambda*vds)` factor in the triode region too (examples below).

**Body effect.** With `gamma` (default 0) and surface potential `phi`
(default 0.6 V), the threshold depends on the bulk-source voltage `vbs`:
`vt = vto + gamma * (sqrt(phi - vbs) - sqrt(phi))` (NMOS; observed on both
tools).

```spice-test id=EL-SEMI-M-1 covers=mosfet dialect=common
Vg g 0 3
Vd d 0 5
M1 d g 0 0 nm w=10u l=1u
.model nm NMOS(level=1 vto=1 kp=1e-4 lambda=0)
* expect: i(vd) = -2e-3 tol=1e-3
```

Saturation: `(1e-4 * 10 / 2) * (3 - 1)^2 = 2 mA`.

```spice-test id=EL-SEMI-M-2 dialect=common
Vg g 0 3
Vd d 0 0.5
M1 d g 0 0 nm w=10u l=1u
.model nm NMOS(level=1 vto=1 kp=1e-4 lambda=0)
* expect: i(vd) = -8.75e-4 tol=1e-3
```

Triode: `1e-3 * (2 * 0.5 - 0.125) = 0.875 mA`.

```spice-test id=EL-SEMI-M-3 dialect=common
Vg g 0 0.5
Vd d 0 5
M1 d g 0 0 nm w=10u l=1u
.model nm NMOS(level=1 vto=1 kp=1e-4 lambda=0)
* expect: i(vd) = 0 atol=1e-9
```

Cutoff: the drain current is 0 within the solver's leakage allowance (1e-12
S `gmin` times 5 V is 5 pA).

```spice-test id=EL-SEMI-M-4 dialect=common
Vg g 0 3
Vd d 0 5
M1 d g 0 0 nm w=10u l=1u
.model nm NMOS(level=1 vto=1 kp=1e-4 lambda=0.1)
* expect: i(vd) = -3e-3 tol=1e-3
```

Saturation with `lambda = 0.1`: `2 mA * (1 + 0.1 * 5) = 3 mA`.

```spice-test id=EL-SEMI-M-5 dialect=common
Vg g 0 3
Vd d 0 0.5
M1 d g 0 0 nm w=10u l=1u
.model nm NMOS(level=1 vto=1 kp=1e-4 lambda=0.1)
* expect: i(vd) = -9.1875e-4 tol=1e-3
```

Triode with `lambda = 0.1`: `0.875 mA * (1 + 0.1 * 0.5) = 0.91875 mA`.

```spice-test id=EL-SEMI-M-6 dialect=common
Vg g 0 3
Vd d 0 5
Vb b 0 -2
M1 d g 0 b nm w=10u l=1u
.model nm NMOS(level=1 vto=1 kp=1e-4 lambda=0 gamma=0.5 phi=0.6)
* expect: i(vd) = -1.2499e-3 tol=1e-3
```

With `vbs = -2`, `vt = 1 + 0.5 (sqrt(2.6) - sqrt(0.6)) = 1.4189`, and the
saturation current is `0.5 mA * (3 - 1.4189)^2 * 2 = 1.25 mA`.

## Not yet specified

High-injection (`ik`) effects, the BJT's knee currents, `tox`-derived `kp`,
noise and temperature scaling. Capacitances are in [capacitances.md](capacitances.md). Each needs its own page with
measured examples; the tools may differ in defaults (`XYC-REF` lists
Xyce-specific parameters).
