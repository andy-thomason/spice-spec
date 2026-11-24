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
