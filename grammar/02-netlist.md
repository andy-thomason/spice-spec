# 02 Netlist structure and dot cards

Sources and tags (registry in [../sources/README.md](../sources/README.md)):

| Production | Tag | Sources |
|------------|-----|---------|
| deck, title, `.end` | `core` | `SP3-UG` Description; `NGS-42` 2.1.1, 2.3; `XYC-REF` 2.1.6 |
| `.subckt`, `.ends`, `X` | `core` | `SP3-UG` Description "Subcircuits"; `NGS-42` 2.5; `XYC-REF` 2.1.37, 2.1.7 |
| `.model` | `core` | `SP3-UG` "Device Models" (15 types); `NGS-42` 2.4 (17 types); `XYC-REF` 2.1.21 |
| `.include` | `core` | `SP3-UG` "Combining files: .INCLUDE"; `NGS-42` 2.7; `XYC-REF` 2.1.15 (`.INC` or `.INCLUDE`) |
| `.lib` (call and definition) | `common` | `NGS-42` 2.8; `XYC-REF` 2.1.16 |
| `.param` | `common` | `NGS-42` 2.9; `XYC-REF` 2.1.26, 2.2.1 |
| `.func` | `common` | `NGS-42` 2.10; `XYC-REF` 2.1.10 |
| `.global` | `common` | `NGS-42` 2.6; `XYC-REF` 2.1.11 |
| `.global_param` | `dialect:xyce` | `XYC-REF` 2.1.12 |
| `.csparam`, `.if`, `.temp`, `.control` | `dialect:ngspice` | `NGS-42` 2.11, 2.13, 2.12, 16.4.3 |

"Common" means documented in both ngspice and Xyce; the meaning has not been
compared in detail, and HSPICE was not read. The prose below is from
`NGS-42`. SPICE3 lists 15 model types; ngspice adds `L` and `VDMOS`
(`SP3-UG` versus `NGS-42` Table 2.3).

## Deck

```abnf
deck        = title-line *card end-line
title-line  = *VCHAR                         ; always the first line (P2)
end-line    = ".end"
card        = element-card / dot-card
```

Order is free except that blocks must be complete: `.subckt` to `.ends`,
`.if` to `.endif`, `.control` to `.endc`, and `+` continuation lines must
follow their line (manual 2.1.1). `.control` blocks are specified separately
and are out of scope for this grammar (see ambiguities A-08).

## .subckt, .ends, X

```abnf
subckt-def  = ".subckt" subckt-name 1*node-name [ "params:" *param-assign ]
              *( element-card / model-card / subckt-def / param-card )
              ".ends" [ subckt-name ]
subckt-call = "X" name 1*node-name subckt-name [ "params:" ] *param-assign
param-assign = param-name "=" value
```

Rules from the manual (2.5):

- The port nodes in `.subckt` cannot be `0`.
- Control lines are not allowed inside a subcircuit. Models and subcircuit
  definitions inside are local to it.
- Nodes not in the port list are local. `0` is always global.
- `.ends` with a name closes that subcircuit; without a name it closes all
  open definitions. **This is surprising for nested definitions; confirm by
  test (A-09).**
- A call replaces the definition by text expansion. Hierarchy is not kept.
- The optional `params:` marker and its `name=value` parameters (manual 2.9.3
  describes the extended form). **Details to be read and recorded.**

## .model

```abnf
model-card  = ".model" model-name model-type [ "(" *param-assign ")" ]
model-type  = "R" / "C" / "L" / "SW" / "CSW" / "URC" / "LTRA" / "D"
            / "NPN" / "PNP" / "NJF" / "PJF" / "NMOS" / "PMOS"
            / "NMF" / "PMF" / "VDMOS" / other-model-type
```

Table 2.3 of the manual lists these types. Parentheses are separators, so
the form without them is also accepted. `other-model-type` covers the model
names of OSDI and other compact models, such as `bsimbulk` (manual 12.x).
Which parameters apply to which type is not grammar; it belongs in
`spec/04-models/`.

## .param, .func, .csparam, .temp, .global

```abnf
param-card   = ".param" 1*param-assign
param-assign = param-name "=" ( value / braced / quoted )
func-card    = ".func" func-name "(" [ param-name *( "," param-name ) ] ")" ( braced / quoted / expr )
global-card  = ".global" 1*node-name
temp-card    = ".temp" value
csparam-card = ".csparam" param-name "=" ( value / braced / quoted )
```

Manual 2.9 to 2.12. Rules:

- Assignments are executed in order through the expanded deck. A parameter
  must be assigned before its first use, and cannot refer to itself
  (`.param pip='pip+3'` fails).
- Several assignments on one line are allowed.
- An expression with spaces and no braces or quotes can be misparsed:
  an unbraced product followed by a second assignment on the same line can be misparsed (`NGS-42` 2.9.1 describes the failure; our own reproduction is a to-do under A-10).
  This is the weakest spot in the grammar. **A-10.**

## .include, .lib

```abnf
include-card = ".include" filename
lib-use      = ".lib" filename libname
lib-def      = ".lib" libname *card ".endl" [ libname ]
```

Manual 2.7 and 2.8. A relative file name not found directly is searched in
the `sourcepath` variable. In PSPICE compatibility mode `.lib filename`
(without a library name) is a plain include. File name quoting and spaces:
**A-11.**

## .if / .elseif / .else / .endif

```abnf
if-block = ".if" "(" bool-expr ")" *card
           *( ".elseif" "(" bool-expr ")" *card )
           [ ".else" *card ]
           ".endif"
```

Manual 2.13. Which cards may appear inside is **open, A-12.**

## Cards starting with an element letter

An element card begins with a letter that selects its form, see
03-elements.md. A card beginning with `.` is a dot card. Any other first
character is an error, except the characters rewritten to `*` by pass 1
step P4.

## Examples (non-normative)

Examples illustrate the rules above and are **not normative**: where an
example and the rule text disagree, the rule text is the specification and
the example is a bug to investigate. Examples run as doctests on ngspice
(`tools/doctest.py`; see [doctests.md](doctests.md)). All are original.



```spice-file name=inc.cir
R1 a 0 1k
```

```spice-file name=lib.lib
* library file with one section
.lib mylib
R1 a 0 2k
.endl mylib
```

A complete deck: title line, cards, and `.end`.

```spice-test id=NET-DECK-1 covers=deck,title-line,end-line,card deck=full
This line is the title and may say anything
* a comment line
V1 a 0 1
R1 a 0 1k
.end
```

A divider as a subcircuit. `0` is global, so the subcircuit has two ports.

```spice-test id=NET-SUB-1 covers=subckt-def,subckt-call
.subckt half in out
R1 in out 1k
R2 out 0 1k
.ends half
V1 a 0 4
X1 a b half
* expect: v(b) = 2
```

A diode model; `.model name type (params)`.

```spice-test id=NET-MODEL-1 covers=model-card,model-type
.model dmod d(is=1e-14)
I1 0 a 1m
D1 a 0 dmod
* expect: v(a) = 0.6551 tol=2e-3
```

`.csparam` makes a parameter available to the control language.

```spice-test id=NET-CSPARAM-1 covers=csparam-card dialect=ngspice
.csparam x=5
V1 a 0 1
R1 a 0 1k
* expect: x = 5
```

A user function.

```spice-test id=NET-FUNC-1 covers=func-card dialect=ngspice
.func double(x) {2*x}
V1 a 0 {double(3)}
R1 a 0 1k
* expect: v(a) = 6
```

A global node is visible inside subcircuits without being a port.

```spice-test id=NET-GLOBAL-1 covers=global-card dialect=ngspice
.global vdd
.subckt load out
R1 vdd out 1k
R2 out 0 1k
.ends load
V1 vdd 0 5
X1 o load
* expect: v(o) = 2.5
```

Circuit temperature; the resistor has a first-order coefficient.

```spice-test id=NET-TEMP-1 covers=temp-card dialect=ngspice
.temp 50
I1 0 a 1m
R1 a 0 1k tc1=0.001
* expect: v(a) = 1.023 tol=1e-3
```

`.include` inserts the file at that point.

```spice-test id=NET-INC-1 covers=include-card dialect=ngspice uses=inc.cir
.include inc.cir
I1 0 a 1m
* expect: v(a) = 1
```

`.lib file name` selects one library section from a file.

```spice-test id=NET-LIB-1 covers=lib-use,lib-def dialect=ngspice uses=lib.lib
.lib lib.lib mylib
I1 0 a 1m
* expect: v(a) = 2
```

Conditional netlist; only one branch is read.

```spice-test id=NET-IF-1 covers=if-block dialect=ngspice
.if (1 > 2)
R1 a 0 1k
.else
R1 a 0 2k
.endif
I1 0 a 1m
* expect: v(a) = 2
```

### Expansion, observed with `listing expand`

These examples show what ngspice 42 produces after it expands subcircuits
and evaluates parameters, using `listing expand` (documented; `NGS-42`
17.5). As in the pass 1 examples, the expected output is **observed**, is
not stated in the manuals, and shows ngspice naming conventions that this
spec does not require of other tools. They are the oracle for the future
elaboration step. In expanded output, control sections and `.param`,
`.subckt` and `.func` definitions are gone, and numbers that came from
parameters are printed as 16-digit floats.

A subcircuit instance is replaced by its elements, named
`<letter>.<instance>.<element>`. Node `0` stays global.

```spice-test id=EX-FLAT-1 deck=full listing=expand dialect=ngspice
t
.subckt half in out
R1 in out 1k
R2 out 0 1k
.ends half
V1 a 0 4
X1 a b half
.end
```

```spice-listing for=EX-FLAT-1
t
v1 a 0 4
r.x1.r1 a b 1k
r.x1.r2 b 0 1k
.end
```

Internal nodes are prefixed with the instance name and a dot, so two
instances do not share them.

```spice-test id=EX-NODE-1 deck=full listing=expand dialect=ngspice
t
.subckt s in out
R1 in m 1k
R2 m out 1k
.ends s
X1 a b s
X2 b c s
.end
```

```spice-listing for=EX-NODE-1
t
r.x1.r1 a x1.m 1k
r.x1.r2 x1.m b 1k
r.x2.r1 b x2.m 1k
r.x2.r2 x2.m c 1k
.end
```

Nested instances nest the names.

```spice-test id=EX-NEST-1 deck=full listing=expand dialect=ngspice
t
.subckt inner p q
R1 p q 1k
.ends inner
.subckt outer p q
X2 p q inner
R9 p q 2k
.ends outer
X1 a b outer
.end
```

```spice-listing for=EX-NEST-1
t
r.x1.x2.r1 a b 1k
r.x1.r9 a b 2k
.end
```

A subcircuit defined inside another one, closed with an unnamed `.ends`, is
usable inside it. Note the doubled prefix in the result.

```spice-test id=EX-ENDS-1 deck=full listing=expand dialect=ngspice
t
.subckt outer p q
.subckt inner a b
R1 a b 1k
.ends
X1 p q inner
.ends outer
X9 u v outer
.end
```

```spice-listing for=EX-ENDS-1
t
r.x9.r.x1.r1 u v 1k
.end
```

Parameters: braced expressions are evaluated. A bare parameter name used as
a value is also replaced by its value in ngspice, so a name in a value
position can be a parameter and not only a model name (A-15).

```spice-test id=EX-PARAM-1 deck=full listing=expand dialect=ngspice
t
.param rv=2k
R1 a 0 {rv}
R2 a 0 {rv*2}
R3 a 0 rv
.end
```

```spice-listing for=EX-PARAM-1
t
r1 a 0 2.000000000000000e+03
r2 a 0 4.000000000000000e+03
r3 a 0 2.000000000000000e+03
.end
```

Subcircuit parameters have defaults and can be overridden at the call.

```spice-test id=EX-PARAMS-1 deck=full listing=expand dialect=ngspice
t
.subckt s in out params: r=1k
R1 in out {r}
.ends s
X1 a b s
X2 b c s r=2k
.end
```

```spice-listing for=EX-PARAMS-1
t
r.x1.r1 a b 1.000000000000000e+03
r.x2.r1 b c 2.000000000000000e+03
.end
```

A model defined inside a subcircuit is renamed per instance, with a colon
(not a dot) in the new name.

```spice-test id=EX-MODEL-1 deck=full listing=expand dialect=ngspice
t
.subckt s in out
.model dm d(is=1e-14)
D1 in out dm
.ends s
X1 a b s
.end
```

```spice-listing for=EX-MODEL-1
t
.model x1:dm d(is=1e-14)
d.x1.d1 a b x1:dm
.end
```

A global node is not renamed.

```spice-test id=EX-GLOBAL-1 deck=full listing=expand dialect=ngspice
t
.global vdd
.subckt s out
R1 vdd out 1k
.ends s
X1 o s
.end
```

```spice-listing for=EX-GLOBAL-1
t
r.x1.r1 vdd o 1k
.end
```

`.if` keeps only the branch whose condition holds.

```spice-test id=EX-IF-1 deck=full listing=expand dialect=ngspice
t
.if (1 > 2)
R1 a 0 1k
.else
R1 a 0 2k
.endif
.end
```

```spice-listing for=EX-IF-1
t
r1 a 0 2k
.end
```

`.func` calls are evaluated in braces.

```spice-test id=EX-FUNC-1 deck=full listing=expand dialect=ngspice
t
.func double(x) {2*x}
R1 a 0 {double(3)}
.end
```

```spice-listing for=EX-FUNC-1
t
r1 a 0 6.000000000000000e+00
.end
```

Subcircuit names are looked up without regard to case.

```spice-test id=EX-CASE-1 deck=full listing=expand dialect=ngspice
t
.subckt s in out
R1 in out 1k
.ends
X1 a b S
.end
```

```spice-listing for=EX-CASE-1
t
r.x1.r1 a b 1k
.end
```

Instance names are case-insensitive too, so two instances that differ only
in case collide and ngspice reports an error.

```spice-test id=EX-DUP-1 dialect=ngspice expect=reject
.subckt s in out
R1 in out 1k
.ends
V1 a 0 1
x1 a b s
X1 b c s
```
