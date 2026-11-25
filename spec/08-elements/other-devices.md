# Other devices: JFET, switch, lossless transmission line

Status: draft v0.1. Basic behavior only, checked against closed-form values.
Card syntax is in [../../grammar/03-elements.md](../../grammar/03-elements.md).

Sources: `SP3-UG` Elements page ("Junction Field-Effect Transistors", "Switch
Model (SW/CSW)", "Lossless Transmission Lines"); `NGS-42` 9.1 and 9.2 (JFET),
3.3.15 and 3.3.16 (switches), 6.1 (lossless line); `XYC-REF` 2.3.18 (JFET),
2.3.22 and 2.3.23 (switches), 2.3.25 (lossless line). Registry:
[../../sources/README.md](../../sources/README.md). **Observed** means checked
by the examples on ngspice 42 and Xyce 7.10. Examples are **non-normative**.

## JFET `J`

Card `J name drain gate source model [area]`, model type `NJF` or `PJF`.
Parameters: threshold `vto` (default -2 V), `beta` (default 1e-4 A/V^2),
`lambda` (default 0). For an N-channel device with `vgs` and `vds`
(PJF: negate all voltages and currents) the standard square-law form is
(`common`, observed):

```
cutoff       vgs <= vto:                 id = 0
triode       vds <  vgs - vto:           id = beta * vds * (2 (vgs - vto) - vds) * (1 + lambda vds)
saturation   vds >= vgs - vto:           id = beta * (vgs - vto)^2 * (1 + lambda vds)
```

Note that the JFET's `beta` multiplies `(vgs - vto)^2` with no factor 1/2,
unlike the MOSFET's `kp * w/l / 2`. The documents print the parameters but
not these equations.

```spice-test id=EL-OTH-J-1 covers=jfet dialect=common
Vg g 0 -1
Vd d 0 5
J1 d g 0 jm
.model jm NJF(vto=-2 beta=1m lambda=0)
* expect: i(vd) = -1e-3 tol=1e-3
```

Saturation: `1e-3 * (-1 + 2)^2 = 1 mA`.

```spice-test id=EL-OTH-J-2 dialect=common
Vg g 0 -1
Vd d 0 0.5
J1 d g 0 jm
.model jm NJF(vto=-2 beta=1m lambda=0)
* expect: i(vd) = -7.5e-4 tol=1e-3
```

Triode: `1e-3 * 0.5 * (2 * 1 - 0.5) = 0.75 mA`.

## Voltage-controlled switch `S`

Card `S name n+ n- nc+ nc- model [on|off]`. The switch is a resistor between
`n+` and `n-` that is `ron` when the control voltage `v(nc+) - v(nc-)` is
above the threshold and `roff` when it is below. Defaults: `vt` 0 V, `vh`
0 V (hysteresis), `ron` 1 ohm, `roff` 1e12 ohm (`NGS-42` 3.3.16). The model
is never an ideal open or short.

The **model type name differs by tool** (`dialect:ngspice`): ngspice uses
`SW` with `vt`/`vh`; Xyce 7.10 does not accept `SW` ("No model found") and
uses `VSWITCH` with `von`/`voff`. With a clear margin from the threshold the
two give the same resistance, so the state at one control voltage is the same
on both (both measured 0.999001 V and 0.000999 V in the examples). The
behavior exactly at the threshold, and with `vh` not zero, is **not**
specified here.

```spice-test id=EL-OTH-S-1 covers=switch dialect=ngspice
Vc c 0 1
V1 a 0 1
S1 a b c 0 sm
R1 b 0 1k
.model sm SW(vt=0.5 vh=0 ron=1 roff=1Meg)
* expect: v(b) = 0.999001 tol=1e-4
```

On: `ron = 1` and `1 kohm` divide 1 V to `1000/1001`.

```spice-test id=EL-OTH-S-2 dialect=ngspice
Vc c 0 0
V1 a 0 1
S1 a b c 0 sm
R1 b 0 1k
.model sm SW(vt=0.5 vh=0 ron=1 roff=1Meg)
* expect: v(b) = 0.000999 tol=1e-3
```

Off: `1 kohm / (1 Mohm + 1 kohm)` gives about 1 mV.

## Lossless transmission line `T`

Card `T name n1 n2 n3 n4 z0=Z td=TD` (or `f=` and `nl=`). A two-port with
characteristic impedance `Z0` and one-way delay `TD`. A wave entering port 1
reaches port 2 after `TD`; a mismatch at either end reflects part of it with
coefficient `(ZL - Z0) / (ZL + Z0)`. Only one propagating mode is modeled.
Valid in transient analysis (`common`, observed on both tools).

```spice-test id=EL-OTH-T-1 covers=tline dialect=common
V1 s 0 PULSE(0 1 0 1p 1p 1 2)
Rs s in 50
T1 in 0 out 0 z0=50 td=1n
Rl out 0 50
.tran 0.1n 4n
* expect: v(out) @ 0.8n = 0 atol=1e-3
* expect: v(out) @ 1.5n = 0.5 tol=1e-3
* expect: v(out) @ 3.5n = 0.5 tol=1e-3
```

A matched line: the 1 V step is divided by the 50 ohm source and the line to
0.5 V, and arrives after 1 ns with no reflection.

```spice-test id=EL-OTH-T-2 dialect=common
V1 s 0 PULSE(0 1 0 1p 1p 1 2)
Rs s in 50
T1 in 0 out 0 z0=50 td=1n
.tran 0.1n 4n
* expect: v(out) @ 0.8n = 0 atol=1e-3
* expect: v(out) @ 1.5n = 1 tol=1e-3
```

An open far end reflects with coefficient +1, so the voltage there doubles
to 1 V after 1 ns.

## Not yet specified

Current-controlled switch `W`; switch hysteresis; lossy lines (`O`, `LTRA`),
distributed RC (`U`, `URC`) and the KSPICE lines (`TXL`, `CPL`); MESFET; the
`PJF` and PMOS polarity rules; JFET capacitances.
