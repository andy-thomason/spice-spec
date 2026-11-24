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
