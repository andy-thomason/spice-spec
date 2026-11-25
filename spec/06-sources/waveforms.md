# Independent source waveforms

Status: draft v0.1. What the source functions `PULSE`, `SIN`, `EXP`, `PWL`,
`SFFM` and `AM` produce. The syntax is in
[../../grammar/04-sources.md](../../grammar/04-sources.md); this page gives the
value of the source at every time.

Sources: `SP3-UG` Elements, "Independent Sources" (the first five functions);
`NGS-42` 4.1.1 to 4.1.6 (all six). Registry:
[../../sources/README.md](../../sources/README.md). Everything marked
**observed** was measured on ngspice 42 and is not stated, or is stated
differently, in those documents. The examples at the end of each section are
original and run with `tools/doctest.py`. They are **non-normative**: the text
is the specification, and an example that disagrees with it is a bug to
investigate.

**Tags after the Xyce 7.10 comparison**
([../11-compat/xyce-vs-ngspice.md](../11-compat/xyce-vs-ngspice.md)). The
formulas for `PULSE`, `SIN`, `EXP`, `PWL` (with `r=`) and `SFFM`, where all
their parameters are given, are `common`: both tools produce the same values.
These are `dialect:ngspice` (Xyce differs): the value used for DC and
operating-point analysis (time-zero value; Xyce uses the `DC` field, 0 if
none), a zero `tr`/`tf` (Xyce: instantaneous), the `PULSE` pulse count (Xyce:
ignored), `SIN` with no frequency (Xyce: error), `PWL td=` (Xyce: silent exit
1) and `AM` (not in Xyce).

## Conventions

- `t` is time in seconds. `tstep` and `tstop` are the first two fields of the
  `.tran` card of the same deck. Some defaults below depend on them.
- Angles (`phase`, `phasec`, `phases`) are in **degrees**.
- A parameter shown with a default can be omitted *from the end* of the list.
  How many parameters a function needs at least is given for each.
- **Time-zero value.** An analysis that has no time (`.op`, `.dc`, `.ac`
  bias point) and the starting point of `.tran` use the value of the source at
  `t = 0`. Each function states it.
- In a `.tran` analysis the printed value at an arbitrary time is a linear
  interpolation between the simulator's own time points, so a check on a
  curved waveform is only accurate to about the step size.

## PULSE

`PULSE(v1 v2 td tr tf pw per np)`. Needs at least `v1` and `v2`.

| Parameter | Meaning | Default |
|-----------|---------|---------|
| `v1` | initial value | none |
| `v2` | pulsed value | none |
| `td` | delay | 0 |
| `tr` | rise time | `tstep` |
| `tf` | fall time | `tstep` |
| `pw` | pulse width (time at `v2`) | `tstop` |
| `per` | period | `tstop` |
| `np` | number of pulses | unlimited |

Within one period, counting from `td`:

| Time | Value |
|------|-------|
| before `td` | `v1` |
| `td` to `td+tr` | rises linearly from `v1` to `v2` |
| `td+tr` to `td+tr+pw` | `v2` |
| `td+tr+pw` to `td+tr+pw+tf` | falls linearly from `v2` to `v1` |
| until `td+per` | `v1` |

The pattern repeats every `per`, starting again at `td+per`, `td+2·per`, and so
on, `np` times in all if `np` is given. The time-zero value is `v1`.

- A rise or fall time of **zero is replaced by `tstep`** (observed). A pulse
  with `tr = 0` therefore still rises over one step.
- `np` is accepted as the eighth parameter in the default mode (observed;
  `NGS-42` describes it as available only in an extended mode).
- A `per` shorter than `tr+pw+tf` is not specified here.

The pulse is high from 2 µs to 4 µs, low again from 5 µs, and the next pulse
starts at 11 µs:

```spice-test id=WF-PULSE-1 dialect=common
V1 a 0 pulse(0 1 1u 1u 1u 2u 10u)
R1 a 0 1k
.tran 0.05u 15u
* expect: v(a) @ 0.5u = 0 atol=1e-9
* expect: v(a) @ 1.5u = 0.5 tol=1e-6
* expect: v(a) @ 3u = 1
* expect: v(a) @ 4.5u = 0.5 tol=1e-6
* expect: v(a) @ 6u = 0 atol=1e-9
* expect: v(a) @ 11.5u = 0.5 tol=1e-6
* expect: v(a) @ 14u = 1
```

Omitted parameters take their defaults from `.tran`: the rise is one `tstep`
and the pulse stays high to `tstop`.

```spice-test id=WF-PULSE-2 dialect=common
V1 a 0 pulse(0 1)
R1 a 0 1k
.tran 0.1u 10u
* expect: v(a) @ 0.05u = 0.5 tol=1e-6
* expect: v(a) @ 5u = 1
```

A zero rise time becomes one `tstep` (here 0.05 µs).

```spice-test id=WF-PULSE-3 dialect=ngspice
V1 a 0 pulse(0 1 1u 0 0 2u 10u)
R1 a 0 1k
.tran 0.05u 5u
* expect: v(a) @ 1.025u = 0.5 tol=1e-6
* expect: v(a) @ 2u = 1
```

`np` limits the number of pulses:

```spice-test id=WF-PULSE-4 dialect=ngspice
V1 a 0 pulse(0 1 1u 1u 1u 2u 10u 2)
R1 a 0 1k
.tran 0.05u 25u
* expect: v(a) @ 1.5u = 0.5 tol=1e-6
* expect: v(a) @ 11.5u = 0.5 tol=1e-6
* expect: v(a) @ 21.5u = 0 atol=1e-9
```

The time-zero value is `v1`, so the operating point sees 3 V:

```spice-test id=WF-PULSE-5 dialect=ngspice
V1 a 0 pulse(3 5 1u 1u 1u 2u 10u)
R1 a 0 1k
.op
* expect: v(a) = 3
```

## SIN

`SIN(vo va freq td theta phase)`. Needs at least `vo` and `va`.

| Parameter | Meaning | Default |
|-----------|---------|---------|
| `vo` | offset | none |
| `va` | amplitude | none |
| `freq` | frequency, Hz | `1/tstop` |
| `td` | delay | 0 |
| `theta` | damping factor, 1/s | 0 |
| `phase` | phase, degrees | 0 |

For `t >= td`:

    v(t) = vo + va · exp(-(t - td)·theta) · sin(2π·freq·(t - td) + phase)

For `t < td` the source holds the value the formula has at `t = td`:

    v(t) = vo + va · sin(phase)                      (observed)

The documents say `vo` here; the two differ whenever `phase` is not a multiple
of 180°. The time-zero value is therefore `vo + va·sin(phase)` (when `td` is
zero or the delay is positive, the same expression).

```spice-test id=WF-SIN-1 dialect=common
V1 a 0 sin(1 2 1k)
R1 a 0 1k
.tran 2u 1m
* expect: v(a) @ 0.25m = 3 tol=1e-4
* expect: v(a) @ 0.5m = 1 atol=1e-4
* expect: v(a) @ 0.75m = -1 tol=1e-4
```

With a delay, damping and a phase. Before the delay the value is
`1 + 2·sin(30°) = 2`, not `vo = 1`:

```spice-test id=WF-SIN-2 dialect=common
V1 a 0 sin(1 2 1k 0.2m 2k 30)
R1 a 0 1k
.tran 2u 1.2m
* expect: v(a) @ 0.1m = 2 tol=1e-6
* expect: v(a) @ 0.3m = 2.495896 tol=1e-3
```

The operating point uses the time-zero value, which includes the phase:

```spice-test id=WF-SIN-3 dialect=ngspice
V1 a 0 sin(1 2 1k 0 0 90)
R1 a 0 1k
.op
* expect: v(a) = 3
```

`freq` defaults to the reciprocal of `tstop`, here 1 kHz:

```spice-test id=WF-SIN-4 dialect=ngspice
V1 a 0 sin(0 1)
R1 a 0 1k
.tran 2u 1m
* expect: v(a) @ 0.25m = 1 tol=1e-3
```

## EXP

`EXP(v1 v2 td1 tau1 td2 tau2)`. Needs at least `v1` and `v2`; a single
parameter makes the deck fail (observed).

| Parameter | Meaning | Default |
|-----------|---------|---------|
| `v1` | initial value | none |
| `v2` | final value of the rise | none |
| `td1` | rise delay | 0 |
| `tau1` | rise time constant | `tstep` |
| `td2` | fall delay | `td1 + tstep` |
| `tau2` | fall time constant | `tstep` |

    v(t) = v1                                                      for t < td1
    v(t) = v1 + (v2 - v1)·(1 - exp(-(t - td1)/tau1))               for td1 <= t < td2
    v(t) = v1 + (v2 - v1)·(1 - exp(-(t - td1)/tau1))
              + (v1 - v2)·(1 - exp(-(t - td2)/tau2))               for t >= td2

The time-zero value is `v1` when `td1 > 0`. With the default `td2`, the fall
begins one step after the rise, so a source with only `v1` and `v2` ends near
`v1` again.

```spice-test id=WF-EXP-1 dialect=common
V1 a 0 exp(0 1 0.1m 0.2m 0.5m 0.1m)
R1 a 0 1k
.tran 2u 1.2m
* expect: v(a) @ 0.3m = 0.632121 tol=1e-3
* expect: v(a) @ 0.6m = 0.285794 tol=3e-3
```

## PWL

`PWL(t1 v1 t2 v2 ...) r=<time> td=<time>`. Needs at least one pair. The times
must not decrease. An odd number of values is not specified (ngspice 42
accepts it and the result is not meaningful).

- Between two points the value is linear in time.
- **Before the first time the value is the first value, and after the last time
  it is the last value** (observed for the first; documented for the last).
  The time-zero value is the first value, even if the first time is later
  than zero.
- `td` delays the whole sequence by that time; before `td` the value is the
  first value.
- `r` sets a **repeat time**, which must be one of the times of the sequence.
  When the last point is reached, the sequence continues again from the point
  at time `r`, over and over, with the period `tlast - r`. `r=0` repeats the
  whole sequence. Without `r`, or with `r=-1`, the sequence runs once.
- `r` and `td` are accepted on voltage sources; for current sources the
  documents say they are not available (open, A-19).

```spice-test id=WF-PWL-1 dialect=common
V1 a 0 pwl(1u 1 2u 3 4u 3 5u 0)
R1 a 0 1k
.tran 0.05u 8u
* expect: v(a) @ 0.5u = 1
* expect: v(a) @ 1.5u = 2 tol=1e-6
* expect: v(a) @ 3u = 3
* expect: v(a) @ 4.5u = 1.5 tol=1e-6
* expect: v(a) @ 7u = 0 atol=1e-9
```

Repeat from the point at 1 µs; the repeating part is 2 µs long:

```spice-test id=WF-PWL-2 dialect=common
V1 a 0 pwl(0 0 1u 1 2u 0 3u 2) r=1u
R1 a 0 1k
.tran 0.05u 8u
* expect: v(a) @ 3u = 2
* expect: v(a) @ 3.5u = 0.5 tol=1e-6
* expect: v(a) @ 4.5u = 1 tol=1e-6
* expect: v(a) @ 5.5u = 0.5 tol=1e-6
```

A delay holds the first value until it is over:

```spice-test id=WF-PWL-3 dialect=ngspice
V1 a 0 pwl(0 1 1u 2) td=2u
R1 a 0 1k
.tran 0.05u 5u
* expect: v(a) @ 1u = 1
* expect: v(a) @ 2.5u = 1.5 tol=1e-6
* expect: v(a) @ 4u = 2
```

The operating point uses the first value, even before the first time:

```spice-test id=WF-PWL-4 dialect=ngspice
V1 a 0 pwl(1u 5 2u 6)
R1 a 0 1k
.op
* expect: v(a) = 5
```

## SFFM

`SFFM(vo va fc mdi fs phasec phases)`. Needs at least `vo` and `va`.

| Parameter | Meaning | Default |
|-----------|---------|---------|
| `vo` | offset | none |
| `va` | amplitude | none |
| `fc` | carrier frequency, Hz | `1/tstop` |
| `mdi` | modulation index | 0 |
| `fs` | signal frequency, Hz | `1/tstop` |
| `phasec` | carrier phase, degrees | 0 |
| `phases` | signal phase, degrees | 0 |

    v(t) = vo + va · sin(2π·fc·t + phasec + mdi · sin(2π·fs·t + phases))

There is no delay. The time-zero value is
`vo + va·sin(phasec + mdi·sin(phases))`. The SPICE3 form has five parameters
(no phases); the two phases are an ngspice addition.

```spice-test id=WF-SFFM-1 dialect=common
V1 a 0 sffm(1 2 10k 3 1k)
R1 a 0 1k
.tran 1u 1m
* expect: v(a) @ 0.25m = 0.71776 tol=2e-3
* expect: v(a) @ 0.6m = -0.963035 tol=2e-3
```

The phases act on the time-zero value:

```spice-test id=WF-SFFM-2 dialect=ngspice
V1 a 0 sffm(1 2 10k 3 1k 20 40)
R1 a 0 1k
.op
* expect: v(a) = 2.521105 tol=1e-5
```

## AM

`AM(va vo mf fc td phases)`. Needs at least `va`, `vo`, `mf` and `fc`; with
fewer than four parameters the source is **zero at all times** and no error is
reported (observed, although the documents give `fc` a default).

| Parameter | Meaning | Default |
|-----------|---------|---------|
| `va` | amplitude | none |
| `vo` | offset (of the modulating term) | none |
| `mf` | modulating frequency, Hz | none |
| `fc` | carrier frequency, Hz | none (see above) |
| `td` | delay | 0 |
| `phases` | phase | accepted and **ignored** (observed) |

    v(t) = 0                                              for t < td
    v(t) = va · (vo + sin(2π·mf·(t - td))) · sin(2π·fc·(t - td))     for t >= td

(This is the measured behavior. The formula printed in `NGS-42` 4.1.6 uses
`phases` twice and does not match it.) The time-zero value is 0. To get a
carrier of peak 0.1 V modulated 50% at `mf`, use `va = 0.05` and `vo = 2`,
since the envelope is `va·vo` with a swing of `±va`.

```spice-test id=WF-AM-1 dialect=ngspice
V1 a 0 am(1 2 1k 10k 0 0)
V2 b 0 am(1 2 1k 10k 0 90)
R1 a 0 1k
R2 b 0 1k
.tran 1u 1m
* expect: v(a) @ 25u = 2.156434 tol=1e-3
* expect: v(b) @ 25u = 2.156434 tol=1e-3
```

The delay shifts both the modulation and the carrier:

```spice-test id=WF-AM-2 dialect=ngspice
V1 a 0 am(1 2 1k 10k 0.1m 0)
R1 a 0 1k
.tran 1u 1m
* expect: v(a) @ 0.05m = 0 atol=1e-9
* expect: v(a) @ 0.125m = 2.156434 tol=1e-3
```

With only three parameters the source is zero:

```spice-test id=WF-AM-3 dialect=ngspice
V1 a 0 am(1 2 1k)
R1 a 0 1k
.tran 1u 1m
* expect: v(a) @ 0.25m = 0 atol=1e-9
```

## Open points

| ID | Question |
|----|----------|
| A-20 | `AM` is resolved for ngspice 42 above (`phases` ignored, four parameters needed). Other tools not checked. |
| A-39 | The documents' statements that differ from the measured behavior: `SIN` before the delay (`vo` versus `vo + va·sin(phase)`), the `AM` formula, the default `fc` of `AM`, `np` as the eighth `PULSE` parameter. |
| A-40 | Zero `tr`/`tf` replaced by `tstep`: whether that is the print step or the internal step limit (the examples cannot tell them apart). |
