# 02 Netlist structure and dot cards

Source: ngspice manual 2.1 to 2.13. Tag `dialect:ngspice` unless stated.

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
  `.param a = 123 * 3 b = sqrt(9)` does not work as intended (manual 2.9.1).
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
