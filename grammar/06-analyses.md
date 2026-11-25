# 06 Analysis and control cards

Sources: `SP3-UG` Analyses page (`.OP`, `.DC`, `.AC`, `.NOISE`, `.DISTO`,
`.PZ`, `.SENS`, `.TF`, `.IC`, `.NODESET`, `.OPTIONS`; the `.TRAN` page was not
read); `NGS-42` 15.1 to 15.3 (in `NGS-47` the analyses are 11.3.x);
`XYC-REF` 2.1.1 `.AC`, 2.1.3 `.DC`, 2.1.14 `.IC`, 2.1.22 `.NODESET`, 2.1.23
`.NOISE`, 2.1.24 `.OP`, 2.1.25 `.OPTIONS`, 2.1.35 `.SENS`, 2.1.38 `.TRAN`
(documented; forms not yet compared). Registry:
[../sources/README.md](../sources/README.md).

`.op .dc .ac .noise .disto .pz .sens .tf .ic .nodeset .options` are `core`
by `SP3-UG`. `.tran` is `core` by name (SPICE2 and SPICE3 have it) but its
SPICE3 page was not read. `.pss`, `.sp`, `.optran` are `dialect:ngspice`.

```abnf
op-card     = ".op"
dc-card     = ".dc" src value value value [ src value value value ]
ac-card     = ".ac" ( "dec" / "oct" / "lin" ) int value value
tran-card   = ".tran" value value [ value [ value ] ] [ "uic" ]
noise-card  = ".noise" "v" "(" node [ node ] ")" src ( "dec" / "lin" / "oct" ) int value value [ int ]
tf-card     = ".tf" outvar src
pz-card     = ".pz" node node node node ( "cur" / "vol" ) ( "pol" / "zer" / "pz" )
sens-card   = ".sens" outvar [ "ac" ( "dec" / "oct" / "lin" ) int value value ]
disto-card  = ".disto" ( "dec" / "oct" / "lin" ) int value value [ value ]
ic-card     = ".ic" 1*( "v" "(" node ")" "=" value )
nodeset-card = ".nodeset" ( 1*( "v" "(" node ")" "=" value ) / "all" "=" value )
options-card = ".options" 1*( opt-name [ "=" value ] )
```

Not yet written up: `.four`, `.meas`/`.measure` (many forms), `.print`,
`.plot`, `.probe`, `.save`, `.width`, `.pss`, `.sp`, `.optran`.

Notes:

- `.tran tstep tstop [tstart [tmax]] [uic]`. `tstep` is the printing step.
  `tmax` limits the internal step. Rules for `tmax` default belong in the
  spec text (09-numerics), not here.
- `.dc` may sweep a second source (the inner loop is the first). A
  sweep of a temperature, parameter or model parameter uses other forms
  (A-24).
- `.ac` points: `dec` points per decade, `oct` per octave, `lin` total.
- `.options` names and defaults are a large table, specified in
  `spec/08-control/`. The grammar only fixes that an option is a name or a
  `name=value` pair.
- `.measure` is where dialects diverge the most. It should be specified
  after the core forms.

## Examples (non-normative)

Examples illustrate the rules above and are **not normative**: where an
example and the rule text disagree, the rule text is the specification and
the example is a bug to investigate. Examples run as doctests on ngspice
(`tools/doctest.py`; see [doctests.md](doctests.md)). All are original.


Operating point.

```spice-test id=AN-OP-1 covers=op-card dialect=common
V1 a 0 1
R1 a 0 1k
.op
* expect: v(a) = 1
```

DC sweep; the last point is checked.

```spice-test id=AN-DC-1 covers=dc-card dialect=common
V1 a 0 0
R1 a 0 1k
.dc V1 1 2 1
* expect: v(a) = 2
```

AC analysis at one frequency: RC low-pass at its corner is -3 dB (magnitude 0.7071).

```spice-test id=AN-AC-1 covers=ac-card dialect=common
Vin a 0 ac 1
R1 a b 1k
C1 b 0 159.155n
.ac lin 1 1k 1k
* expect: mag(v(b)) = 0.70711 tol=1e-3
```

Transient with `uic`: the capacitor starts at its `ic` value.

```spice-test id=AN-TRAN-1 covers=tran-card dialect=common
V1 a 0 0
R1 a b 1k
C1 b 0 1u ic=2
.tran 10u 1m uic
* expect: v(b) = 0.7358 tol=2e-2
```

A noise analysis runs; no value is asserted.

```spice-test id=AN-NOISE-1 covers=noise-card dialect=common
Vin a 0 dc 0 ac 1
R1 a b 1k
R2 b 0 1k
.noise v(b) Vin dec 5 10 1k
```

Transfer function runs; no value is asserted.

```spice-test id=AN-TF-1 covers=tf-card dialect=ngspice
V1 a 0 1
R1 a b 1k
R2 b 0 1k
.tf v(b) V1
```

Pole-zero analysis of an RC low-pass; accepted. The input node must not be driven by an ideal voltage source, which would short the input.

```spice-test id=AN-PZ-1 covers=pz-card dialect=ngspice
R0 a 0 1k
R1 a b 1k
C1 b 0 1u
R2 b 0 1k
.pz a 0 b 0 vol pol
```

Sensitivity analysis; accepted.

```spice-test id=AN-SENS-1 covers=sens-card dialect=ngspice
V1 a 0 1
R1 a b 1k
R2 b 0 1k
.sens v(b)
```

Distortion analysis of a diode; accepted.

```spice-test id=AN-DISTO-1 covers=disto-card dialect=ngspice
.model dm d(is=1e-14)
V1 a 0 dc 0.5 ac 1 distof1 1
R1 a b 100
D1 b 0 dm
.disto dec 2 100 1k
```

Discrepancy: the manual says the `distof1` magnitude is optional, but ngspice 42 rejects a bare `distof1`. (Open issue A-27.)

```spice-test id=AN-DISTO-2 dialect=ngspice expect=reject
.model dm d(is=1e-14)
V1 a 0 dc 0.5 ac 1 distof1
R1 a b 100
D1 b 0 dm
.disto dec 2 100 1k
```

`.ic` sets the starting node voltage for a transient started with `uic`: 2*exp(-1) after one time constant.

```spice-test id=AN-IC-1 covers=ic-card dialect=common
R1 a 0 1k
C1 a 0 1u
.ic v(a)=2
.tran 10u 1m uic
* expect: v(a) = 0.7358 tol=2e-2
```

`.nodeset` is only a starting guess; the answer is unchanged.

```spice-test id=AN-NODESET-1 covers=nodeset-card dialect=common
V1 a 0 1
R1 a 0 1k
.nodeset v(a)=5
* expect: v(a) = 1
```

An option, with `name=value` form.

```spice-test id=AN-OPTIONS-1 covers=options-card dialect=ngspice
V1 a 0 1
R1 a 0 1k
.options reltol=1e-4
* expect: v(a) = 1
```
