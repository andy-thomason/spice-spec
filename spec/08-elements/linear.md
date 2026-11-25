# Linear elements: R, C, L, K and controlled sources

Status: draft v0.1. What each element does in the equations. The card syntax
is in [../../grammar/03-elements.md](../../grammar/03-elements.md) and the
analyses that use them are in
[../07-analyses/analyses.md](../07-analyses/analyses.md).

Sources: `SP3-UG` Elements page ("Resistors", "Capacitors", "Inductors",
"Coupled (Mutual) Inductors", "Linear Dependent Sources", "Independent
Sources"); `NGS-42` 3.3.1 and 3.3.3 (resistor and model), 3.3.6 (capacitor),
3.3.10 (inductor), 3.3.12 (coupled inductors), 4.1 (sources), 4.2.1 to 4.2.4
(linear dependent sources); `XYC-REF` 2.3.4 to 2.3.7 and 2.3.12 to 2.3.15 (the
same devices). Registry: [../../sources/README.md](../../sources/README.md).
Rules marked **observed** were measured on ngspice 42 and Xyce 7.10 by the
examples below. Examples are **non-normative**; the text is the specification.

## Sign conventions (`common`)

- A node's voltage is relative to node 0 (ground).
- The current in a two-terminal element `X n1 n2` flows from `n1` through
  the element to `n2`. Voltage across it is `v(n1) - v(n2)`.
- The current of a **voltage source** (and of an inductor) is the current
  through it from its positive node to its negative node. A source that
  delivers power to a load therefore has a **negative** current. This is the
  value `i(V1)` returns and the value current-controlled elements read.
- A **current source** `I1 n1 n2 value` drives current from `n1` through the
  source to `n2`: it takes current out of `n1` and puts it into `n2`.

## Resistor `R`

`R name n1 n2 value`: `i = (v(n1) - v(n2)) / value` (`common`).
The temperature rule is `dialect:ngspice` here (Xyce ignores `.temp`, see
[../11-compat/xyce-vs-ngspice.md](../11-compat/xyce-vs-ngspice.md)): with
coefficients `tc1` and `tc2`, `R(T) = R0 (1 + tc1 (T - Tnom) + tc2 (T - Tnom)^2)`
where `Tnom` defaults to 27 degrees Celsius (`SP3-UG` Elements, "Resistors" and "Semiconductor Resistor Model"; `NGS-42`
3.3.1, 3.3.3).

```spice-test id=EL-LIN-R-1 covers=resistor dialect=common
I1 0 a 1m
R1 a 0 2k
* expect: v(a) = 2
```

The current source puts 1 mA into `a`, so `a` sits 2 V above ground.

```spice-test id=EL-LIN-R-2 dialect=ngspice
I1 0 a 1m
R1 a 0 1k tc1=0.01
.temp 127
* expect: v(a) = 2
```

At 127 degrees `dT = 100`, so the resistance doubles.

## Capacitor `C`

`C name n1 n2 value [ic=v0]`: `i = value * d(v(n1) - v(n2)) / dt`. It is open
at DC. A charge of `value * v` is stored (`common`).

```spice-test id=EL-LIN-C-1 covers=capacitor dialect=common
I1 0 a 1m
C1 a 0 1u
.tran 0.1m 1m uic
* expect: v(a) @ 1m = 1 tol=1e-3
```

A constant 1 mA into 1 uF raises the voltage by 1000 V/s, so 1 V in 1 ms.

## Inductor `L`

`L name n1 n2 value [ic=i0]`: `v(n1) - v(n2) = value * di/dt`. It is a short
at DC (`common`).

```spice-test id=EL-LIN-L-1 covers=inductor dialect=common
V1 a 0 1
L1 a 0 1m
.tran 0.1m 1m uic
* expect: i(l1) @ 1m = 1 tol=1e-3
```

## Mutual inductance `K`

`K name L1 L2 k` couples two inductors with coefficient `k`
(`0 < k <= 1`; mutual inductance `M = k sqrt(L1 L2)`). The dot of each
inductor is at its **first** node, so current entering both dotted nodes
produces aiding flux (`common`, `SP3-UG`). With a light load, the voltage
ratio is `k sqrt(L2/L1)` and the output is in phase with the input. (The
example adds a small series resistor: a voltage source directly across an
inductor makes the DC equations singular.)

```spice-test id=EL-LIN-K-1 covers=mutual dialect=common
V1 s 0 DC 0 AC 1
Rs s in 1m
L1 in 0 1m
L2 out 0 4m
K1 L1 L2 0.999
Rl out 0 1Meg
.ac lin 1 1k 1k
* expect: real(v(out)) = 1.998 tol=1e-3
* expect: imag(v(out)) = 0 atol=1e-3
```

## Controlled sources `E`, `F`, `G`, `H`

All four are linear in the controlling quantity (`common`; the nonlinear
`POLY` forms and `B` sources are in the expression pages).

| Card | Name | Output |
|------|------|--------|
| `E out+ out- c+ c- gain` | voltage-controlled voltage source | `v(out+) - v(out-) = gain * (v(c+) - v(c-))` |
| `G out+ out- c+ c- gm` | voltage-controlled current source | current `gm * (v(c+) - v(c-))` flows from `out+` through the source to `out-` |
| `F out+ out- Vname gain` | current-controlled current source | current `gain * i(Vname)` flows from `out+` through the source to `out-` |
| `H out+ out- Vname r` | current-controlled voltage source | `v(out+) - v(out-) = r * i(Vname)` |

`i(Vname)` is the current of the **named voltage source** with the sign rule
above, so the controlling element must be a voltage source (a zero-volt
source works as an ammeter).

```spice-test id=EL-LIN-E-1 covers=vcvs dialect=common
V1 in 0 1
E1 out 0 in 0 3
Rl out 0 1k
* expect: v(out) = 3
```

```spice-test id=EL-LIN-G-1 covers=vccs dialect=common
V1 in 0 2
G1 0 out in 0 1m
Rl out 0 1k
* expect: v(out) = 2
```

`G1 0 out ...` drives current from ground into `out`: 2 mA through 1 kohm.

```spice-test id=EL-LIN-F-1 covers=cccs dialect=common
V1 in 0 1
R1 in 0 1k
F1 0 out V1 2
Rl out 0 1k
* expect: v(out) = -2
```

`V1` delivers 1 mA, so `i(V1)` is -1 mA. `F1` drives `2 * (-1 mA)` from
ground into `out`, which gives -2 V.

```spice-test id=EL-LIN-H-1 covers=ccvs dialect=common
V1 in 0 1
R1 in 0 1k
H1 out 0 V1 1k
* expect: v(out) = -1
```
