# 04 Independent source functions

Sources: `SP3-UG` Elements page, "Independent Sources" (PULSE, SIN, EXP,
PWL, SFFM); `NGS-42` 4.1.1 to 4.1.6 (all functions; section 4.1.6 is AM);
`XYC-REF` 2.3.x (not yet read). Registry:
[../sources/README.md](../sources/README.md).

The five functions exist in SPICE3 and are `core`, but with fewer
parameters: PULSE has seven (V1 V2 TD TR TF PW PER, no pulse count), SIN has
five (VO VA FREQ TD THETA, no phase), SFFM has five (VO VA FC MDI FS, no
phases), and PWL has no `r` or `td`. The extra parameters are
`dialect:ngspice`. `AM` is `dialect:ngspice`: it is not on the SPICE3 page,
and a text search of `XYC-REF` found no `AM(` source function.

Parentheses and commas are separators, so the following are equivalent:
`PULSE(0 1 0 1n 1n 5n 10n)` and `PULSE 0 1 0 1n 1n 5n 10n`.

```abnf
source-function = pulse / sin / exp / pwl / sffm / am / trnoise / trrandom
pulse   = "pulse" "(" v1 v2 [ td [ tr [ tf [ pw [ per [ np ] ] ] ] ] ] ")"
sin     = "sin"   "(" vo va [ freq [ td [ theta [ phase ] ] ] ] ")"
exp     = "exp"   "(" v1 v2 [ td1 [ tau1 [ td2 [ tau2 ] ] ] ] ")"
pwl     = "pwl"   "(" time value *( time value ) ")" [ "r" "=" value ] [ "td" "=" value ]
sffm    = "sffm"  "(" vo va [ fc [ mdi [ fs [ phasec [ phases ] ] ] ] ] ")"
am      = "am"    "(" va vo mf [ fc [ td [ phases ] ] ] ")"
```

Each parameter is a `value`. Omitted trailing parameters take defaults, some
of which depend on the `.tran` card (`tstep`, `tstop`). Defaults from the
manual:

| Function | Default |
|----------|---------|
| PULSE | td 0; tr, tf = tstep; pw, per = tstop; np unlimited |
| SIN | freq 1/tstop; td 0; theta 0; phase 0 (degrees) |
| EXP | td1 0; tau1 = tstep; td2 = td1 + tstep; tau2 = tstep |
| SFFM | fc, fs = 1/tstop; phasec, phases 0 |
| AM | fc 1/tstop; phases 0 |

Notes and open points:

- `r` and `td` on PWL are available for voltage sources only, per the
  manual. Whether the grammar should reject them on `I` sources, or
  accept and ignore, is open (A-19).
- An optional eighth PULSE parameter (phase) exists with
  `behavior=xs` (manual 4.1.1). `dialect:ngspice`.
- The AM formula printed in the manual is garbled (it uses `phases` twice
  and puts `vo` inside a sum). Observed on ngspice 42 with
  `AM(0.05 2 1k 1meg 0 0)`: the waveform is
  `va*(vo + sin(2*pi*mf*t))*sin(2*pi*fc*t)`, with envelope peaks at the
  predicted values. With `td=0.5m` the output is zero until `td` and the
  modulation phase is counted from `td`. `phases` is accepted and ignored
  (measured with several values), and fewer than four parameters give a zero
  source. The waveforms, with tests, are in
  [../spec/06-sources/waveforms.md](../spec/06-sources/waveforms.md). Used in
  RAD-002.
- `trnoise`, `trrandom`, `external` and the RF port form are
  `dialect:ngspice` extensions and are not yet specified.
- For analyses before `.tran`, the source value is the time-zero value.

## Examples (non-normative)

Examples illustrate the rules above and are **not normative**: where an
example and the rule text disagree, the rule text is the specification and
the example is a bug to investigate. Examples run as doctests on ngspice
(`tools/doctest.py`; see [doctests.md](doctests.md)). All are original.


PULSE(v1 v2 td tr tf pw per): at 3 us the pulse is high.

```spice-test id=SRC-PULSE-1 covers=pulse,source-function
V1 a 0 pulse(0 1 0 1n 1n 5u 10u)
R1 a 0 1k
.tran 100n 3u
* expect: v(a) = 1
```

SIN(vo va freq): at a quarter period the value is the amplitude.

```spice-test id=SRC-SIN-1 covers=sin
V1 a 0 sin(0 1 1k)
R1 a 0 1k
.tran 1u 250u
* expect: v(a) = 1 tol=1e-3
```

EXP(v1 v2 td1 tau1 td2 tau2): rising for 5 time constants, 1-exp(-5).

```spice-test id=SRC-EXP-1 covers=exp
V1 a 0 exp(0 1 0 1m 10 1m)
R1 a 0 1k
.tran 10u 5m
* expect: v(a) = 0.993262 tol=1e-3
```

Piece-wise linear: rises 0 to 2 V in 1 ms.

```spice-test id=SRC-PWL-1 covers=pwl
V1 a 0 pwl(0 0 1m 2)
R1 a 0 1k
.tran 10u 1m
* expect: v(a) = 2 tol=1e-3
```

SFFM with modulation index 0 is a plain sine at the carrier frequency.

```spice-test id=SRC-SFFM-1 covers=sffm dialect=ngspice
V1 a 0 sffm(0 1 1k 0 100)
R1 a 0 1k
.tran 1u 250u
* expect: v(a) = 1 tol=1e-3
```

AM(va vo mf fc td phases): at 0.25 us the carrier is at its peak and the envelope is 0.05*(2+sin(2*pi*1k*0.25u)).

```spice-test id=SRC-AM-1 covers=am dialect=ngspice
V1 a 0 am(0.05 2 1k 1meg 0 0)
R1 a 0 1k
.tran 5n 250n
* expect: v(a) = 0.1000079 tol=1e-3
```
