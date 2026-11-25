# Temperature scaling

Status: draft v0.1. How the circuit temperature changes resistors, diodes,
bipolar transistors and level 1 MOSFETs. Formulas the documents print are
stated in our own words and checked; two formulas the documents do **not**
print (the level 1 MOSFET threshold and mobility) were **fitted to
measurements** and are marked so. Examples were run on ngspice 42 and
Xyce 7.10 and are **non-normative**.

Sources: `SP3-UG` Elements ("Resistors", "Diode Model (D)", "BJT Models
(NPN/PNP)", "MOSFET Models (NMOS/PMOS)"); `NGS-42` 3.3.1 and 3.3.3
(resistor), 7.3 (diode temperature equations 7.6 to 7.17), 8.2 (BJT);
`XYC-REF` 2.3.7, 2.3.8, 2.3.17, 2.3.20.1.

## Temperatures

- **Kelvin from Celsius:** `T = temp + 273.15`.
- **Circuit temperature** `temp`: 27 degrees Celsius by default. Set it with
  `.options temp=VALUE` (`common`). The `.temp VALUE` card does the same in
  ngspice only (`dialect:ngspice`; Xyce ignores it with a warning, example
  EL-LIN-R-2 in [linear.md](linear.md)).
- **Nominal temperature** `tnom`: 27 degrees Celsius by default, the
  temperature at which the model parameters were measured. Set it with
  `.options tnom=VALUE`, or per model with the `tnom` parameter.
- **Per instance:** `temp=VALUE` sets the instance's temperature in degrees
  Celsius; `dtemp=VALUE` adds an offset to the circuit temperature. `common`
  for resistors and diodes (observed).
- **Thermal voltage** `vt = k T / q`. The constants differ in their last
  digits between tools, which is within the example tolerances.

## Resistor (`common`)

With temperature coefficients `tc1` and `tc2` (instance or model parameters):

```
R(T) = R * (1 + tc1 * (T - Tnom) + tc2 * (T - Tnom)^2)
```

Here `T` and `Tnom` are in the same unit as the coefficients' denominators:
Celsius degrees (`SP3-UG`, `NGS-42` 3.3.3).

```spice-test id=TMP-R-1 covers=resistor dialect=common
.options temp=127
I1 0 a 1m
R1 a 0 1k tc1=0.01
* expect: v(a) = 2
```

```spice-test id=TMP-R-2 dialect=common
I1 0 a 1m
R1 a 0 1k tc1=0.01 temp=127
* expect: v(a) = 2
```

```spice-test id=TMP-R-3 dialect=common
I1 0 a 1m
R1 a 0 1k tc1=0.01 dtemp=100
* expect: v(a) = 2
```

```spice-test id=TMP-R-4 dialect=common
I1 0 a 1m
R1 a 0 rm 1k temp=127
.model rm R(tc1=0.01 tc2=0.0001)
* expect: v(a) = 3
```

At 127 degrees the step from `Tnom` is 100: `1 + 0.01*100 + 1e-4*100^2 = 3`.

```spice-test id=TMP-R-5 dialect=common
.options tnom=127
I1 0 a 1m
R1 a 0 1k tc1=0.001
* expect: v(a) = 0.9
```

With `Tnom` 127 and the circuit at 27, `T - Tnom = -100`, so the resistance is
`1k * (1 - 0.1)`.

## Diode and BJT saturation current (`common`)

The saturation current scales with temperature as (`NGS-42` 7.3, 7.8 to 7.10)

```
IS(T) = IS * exp(logfactor / N)
logfactor = EG / vt(Tnom) - EG / vt(T) + XTI * ln(T / Tnom)
```

with the band-gap `EG` (default 1.11 eV) and the temperature exponent `XTI`
(diode default 3; BJT default 3) as model parameters, and `N` the emission
coefficient (BJT: 1). The checks below solve the junction equation with this
`IS(T)` and the thermal voltage at `T`.

```spice-test id=TMP-D-1 covers=diode dialect=common
.options temp=127
I1 0 a 1m
D1 a 0 dm
.model dm D(is=1e-14 n=1)
* expect: v(a) = 0.47382 tol=1e-3
```

At 27 degrees the same circuit gives 0.6551 V (example EL-SEMI-D-1). The
forward voltage falls by about 1.8 mV per kelvin.

```spice-test id=TMP-D-2 dialect=common
I1 0 a 1m
D1 a 0 dm temp=127
.model dm D(is=1e-14 n=1)
* expect: v(a) = 0.47382 tol=1e-3
```

```spice-test id=TMP-Q-1 covers=bjt dialect=common
.options temp=127
Vb b 0 0.65
Vc c 0 5
Q1 c b 0 qm
.model qm NPN(is=1e-15 bf=100)
* expect: i(vc) = -0.016555 tol=5e-3
* expect: i(vb) = -1.6555e-4 tol=5e-3
```

At a fixed `vbe` the collector current rises by 200 times from 27 to 127
degrees (82 uA to 16.6 mA at 0.65 V). The current gain `bf` does not change:
its temperature coefficient `xtb` defaults to 0.

## MOSFET level 1: mobility and threshold (**fitted**)

The documents print the diode temperature equations but not the level 1
MOSFET's. These were measured on both tools by running one device at 127,
27 and -23 degrees and two gate voltages, then solving for the transconductance
and threshold at each temperature. With `gamma = 0`:

```
kp(T)  = kp * (T / Tnom)^(-1.5)
vto(T) = vto - (Eg(T) - Eg(Tnom)) / 2 + (phi(T) - phi) / 2
phi(T) = phi * T / Tnom - vt(T) * (3 ln(T / Tnom) + Eg(Tnom)/vt(Tnom) - Eg(T)/vt(T))
Eg(T)  = 1.16 - 7.02e-4 * T^2 / (T + 1108)
```

(`Eg(T)` is the same silicon band-gap expression as the diode's equation 7.6
and 7.7 in `NGS-42`.) For `vto = 1`, `phi = 0.6`, `kp = 1e-4` this gives,
and both tools measured, `kp` ratios 0.6496 (127 degrees) and 1.3143
(-23 degrees), and thresholds 0.8993 V and 1.0488 V (about -1 mV/K). The
formulas matched ngspice to 5 digits; Xyce agreed to 3e-4 at 127 degrees.
The threshold with a non-zero `gamma` was not measured (A-49).

```spice-test id=TMP-M-1 covers=mosfet dialect=common
.options temp=127
Vg g 0 3
Vd d 0 5
M1 d g 0 0 nm w=10u l=1u
.model nm NMOS(level=1 vto=1 kp=1e-4 lambda=0 phi=0.6)
* expect: i(vd) = -1.4334e-3 tol=2e-3
```

```spice-test id=TMP-M-2 dialect=common
.options temp=-23
Vg g 0 3
Vd d 0 5
M1 d g 0 0 nm w=10u l=1u
.model nm NMOS(level=1 vto=1 kp=1e-4 lambda=0 phi=0.6)
* expect: i(vd) = -2.5020e-3 tol=2e-3
```

At 127 degrees the lower mobility wins over the lower threshold, so the
saturation current drops from 2.0 mA to 1.43 mA. At -23 degrees it rises to
2.50 mA.

## Not yet specified

Temperature dependence of capacitances and junction potentials (`NGS-42`
7.11 to 7.17 and similar), the BJT's `xtb`, `xti` and `eg` options, `tlev`
and the other temperature-model selectors, resistor `tce` and exponential
models, inductor and capacitor `tc1`/`tc2`, level 1 MOSFET body effect with
temperature (A-49), `.temp` with several values (a sweep), and
self-heating.
