# Semiconductor devices: diode, BJT, MOSFET level 1

Status: draft v0.1. The **basic** large-signal equations of the three oldest
SPICE devices, enough to check an implementation against closed-form values.
Capacitances, noise, breakdown, high-injection effects, temperature scaling
and the many later MOSFET levels (BSIM and others) are **not** specified here.
Card syntax is in [../../grammar/03-elements.md](../../grammar/03-elements.md).

Sources: `SP3-UG` "Semiconductor devices" and the model parameter tables;
`NGS-42` chapters on the diode, BJT and MOSFET models (chapter numbers not yet checked); `XYC-REF` chapter 2 (device cards) and the device
model reference. Registry: [../../sources/README.md](../../sources/README.md).
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
(`common`, `SP3-UG`). The terminal voltage is `vd + id * rs`. A small
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
triode region's `(1 + lambda*vds)` factor is applied in SPICE for
continuity of the current at the boundary (`SP3-UG`, `NGS-42` 11.2.1); the
examples use `lambda = 0` and do not test it.

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

## Not yet specified

Junction and diffusion capacitances, transit time, breakdown, Early and knee
currents, `gamma`/`phi` body effect, `tox`-derived `kp`, overlap
capacitances, noise and temperature scaling. Each needs its own page with
measured examples; the tools may differ in defaults (`XYC-REF` lists
Xyce-specific parameters).
