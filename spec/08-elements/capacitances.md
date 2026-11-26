# Device capacitances

Status: draft v0.1. The charge-storage parts of the diode, BJT and MOSFET
level 1 models that can be checked from outside: diffusion capacitance and
BJT transit time, depletion (junction) capacitance, the MOS overlap and
junction capacitances, and the MOS gate (Meyer) capacitance. Formulas come from the documents, in our own words; every
number below was checked by an example on ngspice 42 and Xyce 7.10.
Examples are **non-normative**.

Sources: `NGS-42` 7.3 (diode capacitance, equations 7.4 and the diffusion
term), 8.2 (BJT charge storage), 11.2 (MOS charge storage, "Meyer");
`SP3-UG` Elements, "Diode Model (D)", "BJT Models (NPN/PNP)", "MOSFET Models
(NMOS/PMOS)"; `XYC-REF` 2.3.8, 2.3.17, 2.3.20.1.

## How the examples measure a capacitance

A capacitance is not an output of any analysis. Each example puts the
device behind a large resistor `R` and reads the voltage divider's response
at one frequency in an AC analysis, where the gain is
`1 / sqrt(1 + (2 pi f R C)^2)` for a capacitor to ground. The bias is set
by a DC source behind the resistor, so the device sits at a known junction
voltage. The resistor is large enough that the DC current (leakage, `gmin`)
does not change that voltage.

## Depletion capacitance (`common`)

A reverse-biased junction with zero-bias capacitance `C0`, built-in
potential `V0` and grading exponent `M` has, at junction voltage `v`
(negative in reverse):

```
C(v) = C0 * (1 - v / V0)^(-M)        for v < FC * V0
```

For `v >= FC * V0` (`FC` default 0.5) the formula is replaced by a straight
line that keeps the capacitance and its slope finite (`NGS-42` 7.3). The
examples stay in reverse bias. Names by device:

| Device | `C0` | `V0` | `M` |
|--------|------|------|-----|
| diode | `cj0` | `vj` (1) | `m` (0.5) |
| BJT base-emitter | `cje` | `vje` (0.75) | `mje` (0.33) |
| BJT base-collector | `cjc` | `vjc` (0.75) | `mjc` (0.33) |
| MOS drain-bulk, source-bulk | `cbd`, `cbs` | `pb` (0.8) | `mj` (0.5) |

The diode case is example EL-SEMI-D-3 in
[semiconductors.md](semiconductors.md).

```spice-test id=EL-CAP-Q-1 covers=bjt dialect=common
V1 s 0 DC 0 AC 1
R1 s b 2Meg
Vc c 0 1
Q1 c b b qm
.model qm NPN(is=1e-15 bf=100 cjc=1p vjc=0.75 mjc=0.33)
.ac lin 1 100k 100k
* expect: mag(v(b)) = 0.72496 tol=1e-3
```

The emitter is tied to the base, so only the base-collector junction at
`v = 0 - 1 = -1 V` matters: `C = 1p * (1 + 1/0.75)^(-0.33) = 0.7561 pF`.

```spice-test id=EL-CAP-M-1 covers=mosfet dialect=common
V1 s 0 DC 1 AC 1
R1 s d 2Meg
M1 d 0 0 0 nm w=10u l=1u
.model nm NMOS(level=1 vto=1 kp=1e-4 cbd=1p pb=0.8 mj=0.5)
.ac lin 1 100k 100k
* expect: mag(v(d)) = 0.76655 tol=1e-3
```

The drain-bulk junction is reverse biased by 1 V: `C = 1p * (1 + 1/0.8)^(-0.5)
= 0.6667 pF`.

## Diffusion capacitance (`common`)

A forward-biased junction stores charge of minority carriers. The diode's
diffusion capacitance is `tt` times the junction conductance, `C = tt * dId/dV`
(`NGS-42` 7.3). With `Id = is (exp(v / (n vt)) - 1)` at 1 mA, the conductance
is `gd = (Id + is) / (n vt) = 0.03866 S`. The BJT does the same with the
forward transit time `tf` and the transconductance (not tested here).

```spice-test id=EL-CAP-D-1 covers=diode dialect=common
I1 0 a DC 1m AC 1
D1 a 0 dm
.model dm D(is=1e-14 n=1 tt=1u cj0=1f)
.ac lin 1 159154.943 159154.943
* expect: real(v(a)) = 12.9325 tol=1e-3
* expect: imag(v(a)) = -12.9325 tol=1e-3
```

`C = 1u * 0.03866 = 38.66 nF`. At 159.155 kHz, `2 pi f C` equals `gd`, so
the diode's admittance is `gd (1 + j)` and its impedance has equal real and
negative imaginary parts. The 1 fF zero-bias capacitance `cj0` is there for
Xyce, and adds about 1.6 fF at this bias, negligible against 38.66 nF.

**Xyce difference** (`dialect:xyce`, measured). With `tt` set and **no**
junction capacitance (`cj0` absent or 0), Xyce 7.10 gives no diffusion
capacitance in an AC analysis: the impedance is purely real, 25.864 ohm
(`1/gd`). Any non-zero `cj0`, even 1 fF, switches it on. ngspice includes the
`tt` term either way (A-48).

```spice-test id=EL-CAP-D-2 dialect=ngspice
I1 0 a DC 1m AC 1
D1 a 0 dm
.model dm D(is=1e-14 n=1 tt=1u)
.ac lin 1 159154.943 159154.943
* expect: real(v(a)) = 12.9325 tol=1e-3
* expect: imag(v(a)) = -12.9325 tol=1e-3
```

## MOS overlap capacitance (`common`)

`cgso`, `cgdo` and `cgbo` are capacitances **per meter of channel width**
(F/m) between the gate and the source, drain and bulk. They are constant,
independent of bias, and the device multiplies them by its width `w`
(here with no lateral diffusion, `ld = 0`).

```spice-test id=EL-CAP-M-2 covers=mosfet dialect=common
V1 s 0 DC 0 AC 1
R1 s g 1Meg
M1 0 g 0 0 nm w=10u l=1u
.model nm NMOS(level=1 vto=1 kp=1e-4 cgso=1e-7 cgdo=1e-7)
.ac lin 1 100k 100k
* expect: mag(v(g)) = 0.62268 tol=1e-3
```

The gate is the only node, with source, drain and bulk grounded, so
`C = (cgso + cgdo) * w = 2e-7 * 10e-6 = 2 pF`.

## MOS gate capacitance, level 1 (Meyer) (`common`)

The level 1 MOSFET has a voltage-dependent gate capacitance only if the model
gives `tox` (`NGS-42` 11.2). It is the piecewise model of Meyer: the total
oxide capacitance

```
Cox = eps_ox * w * l / tox          eps_ox = 3.9 * 8.854214871e-12 F/m
```

is shared between the gate and the source, drain and bulk, depending on the
region. With `vgst = vgs - vt`, and `vt` the threshold:

| Region | Cgs | Cgd | Cgb |
|--------|-----|-----|-----|
| accumulation (`vgs` well below `vt - phi`) | 0 | 0 | `Cox` |
| saturation (`vds >= vgst`) | `2/3 Cox` | 0 | 0 |
| triode (`vds < vgst`) | `2/3 Cox (1 - ((vgst - vds)/(2 vgst - vds))^2)` | `2/3 Cox (1 - (vgst/(2 vgst - vds))^2)` | 0 |

The overlap capacitances of the previous section are added. The partial
region between accumulation and threshold (`vt - phi < vgs < vt`) is not
specified here (A-50). Each example measures the **total** gate capacitance
(`Cgs + Cgd + Cgb`), because the gate is the node where the AC divider can be
attached. The device is `w=100u`, `l=10u`, `tox=10 nm`, so `Cox = 3.453 pF`;
the check value is the divider gain at 100 kHz with 1 Mohm.

```spice-test id=EL-CAP-M-3 covers=mosfet dialect=common
V1 s 0 DC 3 AC 1
R1 s g 1Meg
Vd d 0 5
M1 d g 0 0 nm w=100u l=10u
.model nm NMOS(level=1 vto=1 kp=1e-4 lambda=0 phi=0.6 tox=1e-8)
.ac lin 1 100k 100k
* expect: mag(v(g)) = 0.56868 tol=1e-3
```

Saturation: the gate sees `Cgs = 2/3 Cox = 2.302 pF`.

```spice-test id=EL-CAP-M-4 dialect=common
V1 s 0 DC 3 AC 1
R1 s g 1Meg
M1 0 g 0 0 nm w=100u l=10u
.model nm NMOS(level=1 vto=1 kp=1e-4 lambda=0 phi=0.6 tox=1e-8)
.ac lin 1 100k 100k
* expect: mag(v(g)) = 0.41858 tol=1e-3
```

Triode with `vds = 0`: `Cgs = Cgd = Cox / 2`, total `Cox`.

```spice-test id=EL-CAP-M-5 dialect=common
V1 s 0 DC 3 AC 1
R1 s g 1Meg
Vd d 0 0.5
M1 d g 0 0 nm w=100u l=10u
.model nm NMOS(level=1 vto=1 kp=1e-4 lambda=0 phi=0.6 tox=1e-8)
.ac lin 1 100k 100k
* expect: mag(v(g)) = 0.42094 tol=1e-3
```

Triode with `vds = 0.5`, `vgst = 2`: `Cgs = 0.5442 Cox`, `Cgd = 0.4490 Cox`,
total `0.9932 Cox`.

```spice-test id=EL-CAP-M-6 dialect=common
V1 s 0 DC -2 AC 1
R1 s g 1Meg
Vd d 0 0
M1 d g 0 0 nm w=100u l=10u
.model nm NMOS(level=1 vto=1 kp=1e-4 lambda=0 phi=0.6 tox=1e-8)
.ac lin 1 100k 100k
* expect: mag(v(g)) = 0.41858 tol=1e-3
```

Accumulation (`vgs = -2`): the whole `Cox` is gate-to-bulk.

Both tools matched these formulas to better than 1e-6 (the table is the
standard Meyer model; the documents name it but print no equations, so the
region values here are `measured`).

## BJT forward transit time (`common`)

In forward active operation the base-emitter junction also stores diffusion
charge `tf * ic`, which is a capacitance `Cpi = tf * gm` in parallel with
`gpi = gm / bf`, where `gm = ic / vt` (`NGS-42` 8.2; bias-dependent `tf`, via
`xtf`, `vtf`, `itf`, is not tested). The example drives the base with a
10 uA current (so `ic = bf * 10 uA = 1 mA`, `gm = 0.03866 S`) and reads the
base voltage at the frequency where `2 pi f Cpi = gpi`.

```spice-test id=EL-CAP-Q-2 covers=bjt dialect=common
I1 0 b DC 10u AC 1
Vc c 0 5
Q1 c b 0 qm
.model qm NPN(is=1e-15 bf=100 tf=1n)
.ac lin 1 1.5915494e6 1.5915494e6
* expect: real(v(b)) = 1293.25 tol=1e-3
* expect: imag(v(b)) = -1293.25 tol=1e-3
```

`Cpi = 1n * 0.03866 = 38.66 pF` and `gpi = 0.3866 mS`, so the input impedance
is `(1 - j) / (2 gpi)` at 1.5915 MHz.

## Not yet specified

- **Meyer gate capacitance** in the depletion region
  (`vt - phi < vgs < vt`), the split of the total between `Cgs`, `Cgd`
  and `Cgb`, and `tox` handling of other MOS levels (A-50).
- **BJT** bias dependence of `tf` (`xtf`, `vtf`, `itf`), reverse transit time
  `tr`, `xcjc`, substrate capacitance, and the forward-bias linear extension
  (`fc`).
- **Diode and MOS** forward-bias extension, sidewall (`cjsw`, `pj`, `cjp`)
  and area scaling, and the temperature dependence of capacitances.
- **JFET** `cgs` and `cgd`.
