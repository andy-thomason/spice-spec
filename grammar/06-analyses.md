# 06 Analysis and control cards

Source: ngspice 42 manual chapter 15 (general forms only). Tag
`dialect:ngspice`; the first seven below are believed `core`.

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
