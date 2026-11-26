# Conventions seen in model libraries

Status: draft v0.1. Three syntax habits that appear in the open model
libraries scanned for the HSPICE layer
([../../docs/hspice-corpus.md](../../docs/hspice-corpus.md)), each checked with
an original example on ngspice 42 and Xyce 7.10. The libraries show that
the syntax is **used** (evidence level `seen`); the examples are the
`measured` evidence. Examples are **non-normative**.

## `DC` keyword directly before a waveform

Libraries write source cards such as `V1 n 0 DC PULSE(...)`: the `DC` keyword
is followed by the waveform name and not by a number. Both tools accept this.
The DC value is then 0 (the source takes its waveform value in transient
analysis). The grammar's source rule requires a number after `DC`; this form
is an addition (A-45, `common`).

```spice-test id=LIB-DC-1 dialect=common
V1 a 0 dc pulse(0 5 1n 1p 1p 100n 200n)
R1 a 0 1k
.tran 1n 150n
* expect: v(a) @ 50n = 5 tol=1e-3
* expect: v(a) @ 150n = 0 atol=1e-3
```

## `.option scale`

`.option scale=S` multiplies the MOS geometry parameters (`w`, `l`, and the
other lengths) written on the device card by `S`. Libraries write device sizes
in micrometers and set `scale=1u`. Both tools apply it to the length and width
of a MOSFET (`common`, observed on a level 1 device; which other parameters
are scaled is not specified here, A-46).

```spice-test id=LIB-SCALE-1 dialect=common
.option scale=1u
Vg g 0 3
Vd d 0 5
M1 d g 0 0 nm w=10 l=1
.model nm NMOS(level=1 vto=1 kp=1e-4 lambda=0)
* expect: i(vd) = -2e-3 tol=1e-3
```

This is the same device as example EL-SEMI-M-1 (`w=10u l=1u`): 2 mA.

## Unit words after numbers

Libraries write `1.8v`, `10pf` and `1ns`. A scale letter followed by a unit
letter works on both tools (`common`, observed for these three). Xyce rejects
longer trailing words such as `10Volts` (example LEX-NUM-2), so a portable
library keeps to one or two unit letters.

```spice-test id=LIB-UNIT-1 dialect=common
V1 a 0 1.8v
R1 a b 1k
C1 b 0 10pf
V2 c 0 PULSE(0 1 0 1ns 1ns 10ns 20ns)
R2 c 0 1k
* expect: v(a) = 1.8
```

## Model binning (not run)

Libraries name geometry-range variants `name.1`, `name.2`, ... with
`lmin`, `lmax`, `wmin`, `wmax`, and the instance names just `name`. The
documents say the simulator picks the variant by the instance's `w` and `l`
(`NGS-42` 3.2.3). Measured with level 1 devices (A-47):

| Behavior | ngspice 42 | Xyce 7.10 |
|----------|-----------|-----------|
| Level 1 device with binned models | **error**: "could not find a valid modelname" (the manual says binning is implemented for BSIM3 and BSIM4 only) | selects a bin; warns that `lmin`, `lmax`, `wmin`, `wmax` are not model parameters of the level |
| Choice at the boundary `l = lmax(bin 1) = lmin(bin 2)` | not measured | the **upper** bin (`lmin <= l < lmax`) |

A level 1 example cannot be run on both, so there is no doctest for it. The
BSIM4 case, where both tools agree, is specified with doctests in
[../08-elements/binning.md](../08-elements/binning.md).
