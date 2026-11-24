# 04 Independent source functions

Source: ngspice 42 manual 4.1.1 to 4.1.6. Tag `dialect:ngspice`; PULSE, SIN,
EXP, PWL and SFFM are believed `core` (hypothesis).

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
  modulation phase is counted from `td`. With `phases=90` the envelope did
  not shift; the effect on carrier phase was not examined. Used in
  RAD-002. Remaining part of A-20: the exact role of `phases`.
- `trnoise`, `trrandom`, `external` and the RF port form are
  `dialect:ngspice` extensions and are not yet specified.
- For analyses before `.tran`, the source value is the time-zero value.
