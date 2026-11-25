# 03 Elements

Sources: `SP3-UG` Circuit Elements and Models page (the base forms);
`NGS-42` chapters 3 to 11 (the forms below); `XYC-REF` chapter 2 for
device syntax (not yet read). Registry:
[../sources/README.md](../sources/README.md).

**Reading the rules.** The ABNF below is the ngspice form. Parts that are
**not** in the SPICE3 form are ngspice additions (`dialect:ngspice`). The
SPICE3 base forms, from `SP3-UG`, are:

| Letter | SPICE3 form (`core`) |
|--------|----------------------|
| R | `R n1 n2 value` or `R n1 n2 [value] [model] [L=] [W=] [TEMP=]` |
| C | `C n+ n- value [IC=]` or `C n1 n2 [value] [model] [L=] [W=] [IC=]` |
| L | `L n+ n- value [IC=]` |
| K | `K L1 L2 value` |
| S, W | `S n+ n- nc+ nc- model [ON/OFF]`, `W n+ n- vname model [ON/OFF]` |
| V, I | `n+ n- [[DC] value] [AC [mag [phase]]] [DISTOF1 ..] [DISTOF2 ..] [function]` |
| E, G | `n+ n- nc+ nc- value` |
| F, H | `n+ n- vname value` |
| B | `B n+ n- [I=expr] [V=expr]` |
| T | `T n1 n2 n3 n4 Z0= [TD=] [F= [NL=]] [IC=v1,i1,v2,i2]` |
| O, U | `O n1 n2 n3 n4 model`; `U n1 n2 n3 model L= [N=]` |
| D | `D n+ n- model [area] [OFF] [IC=] [TEMP]` |
| Q | `Q nc nb ne [ns] model [area] [OFF] [IC=vbe,vce] [TEMP=]` |
| J | `J nd ng ns model [area] [OFF] [IC=vds,vgs] [TEMP]` |
| M | `M nd ng ns nb model [L=] [W=] [AD=] [AS=] [PD=] [PS=] [NRD=] [NRS=] [OFF] [IC=] [TEMP=]` |
| Z | `Z nd ng ns model [area] [OFF] [IC=vds,vgs]` |

Everything else in the rules below (for example `m=`, `scale=`, `tc1=`,
`dtemp=`, `noisy=`, `ac=` on R; thermal nodes on Q and D; `tj`; `vol=`/`cur=`
on E and G; `poly`; the fifth Q node) is `dialect:ngspice` per `NGS-42`
3.3.1 to 3.3.15, chapters 7 to 11. Entries in the **Base?** column below
were checked against `SP3-UG` and all exist there except Y, P, A and N, which
`SP3-UG` does not list.

Common definitions:

```abnf
node      = node-name
value     = number / braced / quoted          ; see 01-lexical, 05-expressions
model     = model-name
```

Fixed-position fields come first, then keyword parameters in any order.
Because `=` is a separator, a keyword parameter is recognized by a known
keyword followed by a value, not by the `=` itself (A-04).

| Letter | Element | Base? |
|--------|---------|-------|
| R C L K | passives, mutual inductor | yes (`SP3-UG`) |
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

`vname` names the voltage source that carries the controlling current.
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

## Examples (non-normative)

Examples illustrate the rules above and are **not normative**: where an
example and the rule text disagree, the rule text is the specification and
the example is a bug to investigate. Examples run as doctests on ngspice
(`tools/doctest.py`; see [doctests.md](doctests.md)). All are original.


Plain forms: value, and the `r=` keyword. Two 1k in parallel give 500 ohm.

```spice-test id=EL-R-1 covers=resistor,r-simple,node dialect=common
I1 0 a 1m
R1 a 0 1k
R2 a 0 r=1k
* expect: v(a) = 0.5
```

Resistor from a model: `rsh*l/w` = 100*10.

```spice-test id=EL-R-2 covers=r-semi,r-geom dialect=common
.model rm r(rsh=100)
I1 0 a 1m
R1 a 0 rm l=10u w=1u
* expect: v(a) = 1
```

`m=2` is a multiplier: two resistors in parallel.

```spice-test id=EL-R-3 covers=r-param dialect=common
I1 0 a 1m
R1 a 0 1k m=2
* expect: v(a) = 0.5
```

A resistor from an expression.

```spice-test id=EL-R-4 covers=r-behav dialect=common
I1 0 a 1m
R1 a 0 r='1k+1k'
* expect: v(a) = 2
```

A resistor line without a value is ignored with a warning, not an error. (Observed ngspice behavior.)

```spice-test id=EL-R-5 dialect=common expect=warn
V1 a 0 1
R1 a b
R2 b 0 1k
```

An unknown keyword parameter is an error. (Observed ngspice behavior.)

```spice-test id=EL-R-6 dialect=common expect=reject
V1 a 0 1
R1 a 0 1k foo=3
```

A capacitor charged by a current: v = i*t/C = 1 V at 1 ms (slightly less through the leak).

```spice-test id=EL-C-1 covers=capacitor dialect=common
I1 0 a 1m
C1 a 0 1u ic=0
R1 a 0 1meg
.tran 10u 1m uic
* expect: v(a) = 0.9995 tol=2e-3
```

An inductor is a short at DC.

```spice-test id=EL-L-1 covers=inductor dialect=common
V1 a 0 1
L1 a b 1m
R1 b 0 1k
* expect: v(b) = 1
```

Coupled inductors: with a light load, the voltage ratio is the coupling k. (A voltage source directly across an inductor would be a loop of source and inductor, which SPICE rejects, so the source has a series resistor.)

```spice-test id=EL-K-1 covers=mutual dialect=common
Vin s 0 ac 1
Rs s a 1
L1 a 0 1m
L2 b 0 1m
R2 b 0 1meg
K1 L1 L2 0.9
.ac lin 1 1meg 1meg
* expect: mag(v(b)) = 0.9 tol=1e-3
```

DC value plus an AC magnitude.

```spice-test id=EL-V-1 covers=vsource,isource dialect=common
V1 a 0 dc 2 ac 1
I1 0 b 1m
R1 a 0 1k
R2 b 0 1k
* expect: v(a) = 2
* expect: v(b) = 1
```

Voltage-controlled voltage source, gain 2.

```spice-test id=EL-E-1 covers=vcvs dialect=common
V1 a 0 1
R1 a 0 1k
E1 b 0 a 0 2
R2 b 0 1k
* expect: v(b) = 2
```

Voltage-controlled current source, 1 mS.

```spice-test id=EL-G-1 covers=vccs dialect=common
V1 a 0 2
R1 a 0 1k
G1 0 b a 0 1m
R2 b 0 1k
* expect: v(b) = 2
```

Current-controlled current source. The control current is that flowing through V1 from its + node to its - node: -1 mA, so the output is -3 V.

```spice-test id=EL-F-1 covers=cccs dialect=common
V1 a 0 1
R1 a 0 1k
F1 0 b V1 3
R2 b 0 1k
* expect: v(b) = -3
```

Current-controlled voltage source, 1 kohm: 1k times -1 mA.

```spice-test id=EL-H-1 covers=ccvs dialect=common
V1 a 0 1
R1 a 0 1k
H1 b 0 V1 1k
R2 b 0 1k
* expect: v(b) = -1
```

E and G sources with expressions.

```spice-test id=EL-NL-1 covers=nl-e,nl-g dialect=common
V1 a 0 1
R1 a 0 1k
E1 b 0 vol='v(a)*2'
R2 b 0 1k
G1 0 c cur='v(a)*1m'
R3 c 0 1k
* expect: v(b) = 2
* expect: v(c) = 1
```

A polynomial source: 0 + 3*v(a). In ngspice this uses an XSPICE code model.

```spice-test id=EL-POLY-1 covers=poly dialect=ngspice needs=xspice
V1 a 0 1
R1 a 0 1k
E1 b 0 poly(1) a 0 0 3
R2 b 0 1k
* expect: v(b) = 3
```

A behavioral source.

```spice-test id=EL-B-1 covers=bsource dialect=common
V1 a 0 1
R1 a 0 1k
B1 b 0 v=v(a)+1
R2 b 0 1k
* expect: v(b) = 2
```

A diode with an area factor: area 2 acts like two in parallel.

```spice-test id=EL-D-1 covers=diode,model dialect=common
.model dmod d(is=1e-14)
I1 0 a 2m
D1 a 0 dmod area=2
* expect: v(a) = 0.6551 tol=2e-3
```

An NPN bias point: Ib about 10 uA, Ic about 1 mA, Vc about 5 V.

```spice-test id=EL-Q-1 covers=bjt dialect=common
.model qm npn(bf=100)
Vcc c1 0 10
Rb c1 b 930k
Rc c1 c 5k
Q1 c b 0 qm
* expect: v(c) = 4.975 tol=2e-2
```

An n-JFET with gate and source at ground: id = beta*vto^2 = 4 mA.

```spice-test id=EL-J-1 covers=jfet dialect=common
.model jm njf(vto=-2 beta=1m)
Vdd d1 0 10
Rd d1 d 1k
J1 d 0 0 jm
* expect: v(d) = 6 tol=1e-2
```

A MESFET line is accepted; no value is asserted.

```spice-test id=EL-Z-1 covers=mesfet dialect=common
.model zm nmf(vto=-2 beta=1m)
Vdd d1 0 10
Rd d1 d 1k
Z1 d 0 0 zm
```

A level-1 NMOS in saturation: id = kp/2 * w/l * (vgs-vto)^2 = 5 mA.

```spice-test id=EL-M-1 covers=mosfet dialect=common
.model nm nmos(vto=1 kp=1m)
Vdd d1 0 10
Vg g 0 2
Rd d1 d 1k
M1 d g 0 0 nm w=10u l=1u
* expect: v(d) = 5 tol=1e-3
```

A voltage-controlled switch, closed (control 1 V above threshold).

```spice-test id=EL-S-1 covers=vswitch dialect=ngspice
.model sw sw(vt=0.5 vh=0 ron=1 roff=1meg)
V1 a 0 1
Vc c 0 1
S1 a b c 0 sw
R1 b 0 1k
* expect: v(b) = 0.999 tol=1e-3
```

A current-controlled switch is accepted; no value is asserted.

```spice-test id=EL-W-1 covers=iswitch dialect=ngspice
.model cs csw(it=1m ih=0 ron=1 roff=1meg)
V1 a 0 1
Vc c 0 1
Rc c 0 1k
W1 a b Vc cs
R1 b 0 1k
```

A lossless line at DC passes the voltage through.

```spice-test id=EL-T-1 covers=tline dialect=common
V1 a 0 1
T1 a 0 b 0 z0=50 td=1n
R1 b 0 50
* expect: v(b) = 1
```

A lossy line (model type `ltra`) is accepted; no value is asserted.

```spice-test id=EL-O-1 covers=lossy dialect=common
.model lm ltra(r=1 l=1u c=1p len=0.1)
V1 a 0 1
O1 a 0 b 0 lm
R1 b 0 50
```

A distributed RC line is accepted; no value is asserted.

```spice-test id=EL-U-1 covers=urc dialect=ngspice
.model um urc(k=1.5 fmax=1g rperl=1 cperl=1p)
V1 a 0 1
U1 a b 0 um l=50u
R1 b 0 1k
```
