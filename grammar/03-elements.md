# 03 Elements

Source: ngspice 42 manual chapters 3 to 11 (instance lines only). Tag
`dialect:ngspice` until compared with SPICE3f5 and other tools; entries in
the **Base?** column say whether the letter is believed to exist in
SPICE3f5 (hypothesis, not yet checked against its manual).

Common definitions:

```abnf
node      = node-name
value     = number / braced / quoted          ; see 01-lexical, 05-expressions
model     = model-name
pa        = param-name "=" value              ; instance parameter
```

Fixed-position fields come first, then keyword parameters in any order.
Because `=` is a separator, a keyword parameter is recognized by a known
keyword followed by a value, not by the `=` itself (A-04).

| Letter | Element | Base? |
|--------|---------|-------|
| R C L K | passives, mutual inductor | yes |
| V I | independent sources | yes |
| E F G H | dependent sources | yes |
| B | behavioral source | yes |
| D Q J M Z | semiconductors | yes (Z believed yes) |
| S W | switches | yes |
| T O U | transmission lines | yes |
| X | subcircuit call | yes |
| Y P | extra lossy lines | no (ngspice) |
| A N | XSPICE code model, numerical device | no (ngspice) |

## R resistor (manual 3.3.1 to 3.3.4)

```abnf
resistor     = "R" name node node ( r-simple / r-semi / r-behav )
r-simple     = [ "r" "=" ] value *r-param           ; plain value
r-semi       = [ value ] model *( r-geom / r-param ) ; value or model, with l, w
r-behav      = [ "r" "=" ] quoted-or-braced-expr *r-param
r-param      = ( "ac" / "m" / "scale" / "temp" / "dtemp" / "tc1" / "tc2"
               / "tce" / "noisy" ) "=" value
r-geom       = ( "l" / "w" ) "=" value
```

Notes: the value may be negative but not zero. If both a value and a model
are given, the value wins. If the value is absent, the model and a length
must be given. Distinguishing `R1 1 2 RMOD` (model) from `R1 1 2 1k` (value)
depends on whether the token parses as a number (A-15).

## C capacitor (3.3.6 to 3.3.8)

```abnf
capacitor = "C" name node node [ value ] [ model ]
            *( "l" / "w" / "m" / "scale" / "temp" / "dtemp" / "tc1" / "tc2" / "ic" ) "=" value )
          / "C" name node node ( "c" / "q" ) "=" expr *( "tc1" / "tc2" ) "=" value )
```

`ic` is the initial voltage, used only when `uic` is on `.tran`.

## L inductor, K mutual (3.3.10 to 3.3.12)

```abnf
inductor  = "L" name node node [ value ] [ model ]
            *( ( "nt" / "m" / "scale" / "temp" / "dtemp" / "tc1" / "tc2" / "ic" ) "=" value )
mutual    = "K" name inductor-name inductor-name value
```

## V, I independent sources (4.1)

```abnf
vsource  = "V" name node node [ [ "dc" ] value ] [ "ac" [ value [ value ] ] ]
           [ "distof1" [ value [ value ] ] ] [ "distof2" [ value [ value ] ] ]
           [ source-function ]
isource  = "I" name node node  ; same tail as vsource
```

Order matters in the manual's general form: DC value, then AC, then
DISTOF, then a time function. A bare number is the DC value. Source
functions are in 04-sources.md. Whether the order is mandatory, or the
parts may appear in any order, is **open (A-17)** and is a good test.

## E, F, G, H dependent sources (4.2)

```abnf
vcvs  = "E" name node node node node value
vccs  = "G" name node node node node value [ "m" "=" value ]
cccs  = "F" name node node vname value [ "m" "=" value ]
ccvs  = "H" name node node vname value
nl-e  = "E" name node node "vol" "=" quoted-or-braced-expr
nl-g  = "G" name node node "cur" "=" quoted-or-braced-expr [ "m" "=" value ]
poly  = ( "E" / "G" / "F" / "H" ) name node node "poly" "(" int ")" 1*ref 1*value
```

`vname` is the name of a voltage source whose current controls the element.
`poly` has `ref` as controlling node pairs (E, G) or source names (F, H).
Its semantics (coefficient ordering) belong in the spec pages (A-14).

## B behavioral source (5.1)

```abnf
bsource = "B" name node node ( "i" / "v" ) "=" expr
          *( ( "tc1" / "tc2" / "temp" / "dtemp" ) "=" value )
```

Expressions here are run-time (unbraced) and may use `time`, `temper`,
`hertz`, node voltages `v(n)` and branch currents `i(vname)`.

## Semiconductors (chapters 7 to 11)

```abnf
diode = "D" name node node model *( ( "area" / "m" / "pj" / "ic" / "temp" / "dtemp"
        / "lm" / "wm" / "lp" / "wp" ) "=" value / "off" )
bjt   = "Q" name node node node [ node ] [ node ] model
        *( ( "area" / "areac" / "areab" / "m" / "temp" / "dtemp" ) "=" value
         / "ic" "=" value value / "off" )
jfet  = "J" name node node node model [ [ "area" "=" ] value ] [ "off" ]
        [ "ic" "=" value value ] [ "temp" "=" value ]
mesfet = "Z" name node node node model [ value ] [ "off" ] [ "ic" "=" value value ]
mosfet = "M" name node node node node model
         *( ( "m" / "l" / "w" / "ad" / "as" / "pd" / "ps" / "nrd" / "nrs" / "temp" ) "=" value
          / "off" / "ic" "=" value value [ value ] )
```

BJT has three, four or five node fields before the model name (`ns` and the
thermal node `tj`). The count is decided by whether the next token is a
known model name, which needs a symbol table (A-16). The manual also lists
thermal forms with `thermal` and extra nodes for VDMOS and diodes; these are
`dialect:ngspice`.

## S, W switches (3.3.15)

```abnf
vswitch = "S" name node node node node model [ "on" / "off" ]
iswitch = "W" name node node vname model [ "on" / "off" ]
```

## Transmission lines (chapter 6)

```abnf
tline  = "T" name node node node node "z0" "=" value
         [ "td" "=" value ] [ "f" "=" value [ "nl" "=" value ] ]
         [ "ic" "=" value value value value ]
lossy  = "O" name node node node node model
urc    = "U" name node node node model "l" "=" value [ "n" "=" value ]
```

`U` is also the prefix for XSPICE digital blocks (manual 14.1.3); the two
forms are told apart by context. **A-13.**

## X subcircuit call

See 02-netlist.md. The last node-like field before the first keyword is the
subcircuit name; an implementation must know where nodes stop (A-18).
