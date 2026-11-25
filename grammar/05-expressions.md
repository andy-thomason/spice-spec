# 05 Expressions

Sources: `NGS-42` 2.9.5 to 2.9.7 (everything below); `XYC-REF` 2.2 (the
expression chapter, partly read: contexts, braces, `log`), 6.1.14. Tag
`dialect:ngspice`; SPICE3 has no `.param` expressions, but `B` sources
(`SP3-UG` Elements) have expressions. The manual states that ngspice has
three expression parsers (front end, `.param`, control language), so this
file describes the netlist one.

**Tags after the Xyce 7.10 comparison**
([../spec/11-compat/xyce-vs-ngspice.md](../spec/11-compat/xyce-vs-ngspice.md)).
`common`: the four arithmetic operators, parentheses, unary minus on a
simple operand, comparison and `&&`/`||`, the ternary, and the usual functions
on in-range arguments (examples EXPR-1 to EXPR-6, EXPR-10). `dialect:ngspice`
(Xyce differs): `^` (Xyce: logical xor), `**` associativity and sign handling,
`!`, `\`, the `log` base (Xyce: base 10), `nint` ties, and division by zero or
`sqrt` of a negative (Xyce: 1e50 and 0, no error).

## Grammar

```abnf
expr      = ternary
ternary   = oror [ "?" expr ":" expr ]
oror      = andand *( "||" andand )
andand    = compare *( "&&" compare )
compare   = sum *( ( "==" / "!=" / "<>" / "<=" / ">=" / "<" / ">" ) sum )
sum       = signed *( ( "+" / "-" ) signed )
signed    = "-" signed / [ "+" ] term                ; see the rules below
term      = factor *( ( "*" / "/" / "%" / "\" ) factor )
factor    = "!" not-operand power-tail / power
power     = atom power-tail
power-tail = *( ( "**" / "^" ) pow-operand )         ; left-associative
pow-operand = [ "-" ] number / "!" not-operand / atom
not-operand = "!" not-operand / atom
atom      = number / ident / func "(" expr *( "," expr ) ")" / "(" expr ")"
```

All binary operators group left to right, including `**` and `^`.

**This is what ngspice 42 does, which differs from the manual's operator
table** (`NGS-42` 2.9.5, which puts unary minus above power). The facts below
were measured, 7,500 random expressions compared (see the doctests at the end
and the open issues):

1. **Precedence, tightest first:** `atom`; `!` (so `!1**0` is `(!1)**0`);
   `**` and `^`; `* / % \`; unary `-` and `+`; binary `+ -`; comparisons;
   `&&`; `||`; `?:`. A unary minus therefore covers a whole product:
   `-2**2` is -4, `-3*3\2` is -4, `-2+3` is 1.
2. **Power is left-associative:** `2^3^2` is 64.
3. **`**` and `^` compute `|x|` to the power `y`** (`(-2)**3` is 8, not -8);
   `pow(x,y)` is C `pow` (`pow(-2,3)` is -8) and `pwr(x,y)` is
   `pow(|x|,y)`.
4. **`\` is `trunc(|a| / |b|)`**: both signs are dropped (`(-7)\2` is 3,
   `-7\2` is -3 because of the unary minus). **`%` is the remainder with the
   sign of the dividend** (`-5.5%2` is -1.5, `5.5%-2` is 1.5), on real
   numbers, computed as `a - trunc(a/b)*b`.
5. **A minus after a binary operator belongs to the number that follows it**:
   `2*-2**2` is 8 (the number is `-2`, then `**`, then `*`). It is only
   accepted before a number literal: `2*-(3)` and `2+-sin(1)` are errors.
6. **A unary `+` is only accepted as the first token of an expression, a
   parenthesis or a function argument.** `!` cannot be followed by `-` or
   `+`.
7. **Arithmetic is IEEE**: `4/0` is infinity, `7==4/0` is 0, `ln(0)>1` is 0.
   An error is reported only if the **final** value is not a finite number
   (`7/0`, `ln(0)`, `sqrt(-4)`, `exp(1000)` as a whole expression).
8. **Not explained by any rule above, left unspecified (A-34):** `--2**2`
   (ngspice gives -4), `2*--2` (-4), and a minus after `?` or `:` before
   anything but a number (`1?-(2):3` gives 2, `1?-sin(1):3` gives +0.84).

Word forms of some operators (`not`, `and`, `or`, `div`, `mod`) are reserved
words (`NGS-42` 2.9.6) and map to the symbols.

## Truth values

Zero is false. Any other number is true. Logical and comparison operators
return exactly `1` or `0`.

## Power

`x**y`, `x^y` and `pwr(x,y)` are not identical. In compatibility mode `hs`
(HSPICE-like) a negative `x` uses `round(y)`. In mode `lt` a negative `x`
needs `y` close to an integer, otherwise the result is 0. These are
`dialect` differences and must appear in the compatibility tables.

## Built-in functions (manual 2.9.5)

Single argument: `sqrt sin cos tan sinh cosh tanh asin acos atan asinh acosh
atanh arctan exp ln log abs nint int floor ceil sgn`.
Two arguments: `pow pwr min max`.
Three: `ternary_fcn(x,y,z)`. Random: `gauss agauss unif aunif limit`.

Out-of-range arguments give NaN or infinity, which is an error only if it
reaches the final value (rule 7 above). **`log` is not the same everywhere**:
`XYC-REF` 6.1.14 says Xyce reads `log()` as base 10 and PSpice as natural log,
and 3.1 says `-hspice-ext math` makes Xyce's `log` natural, which implies
HSPICE is natural. **Observed on ngspice 42: `log(100)` is 4.605, the natural
logarithm, the same as `ln`;** `log10` is base 10. **A-22.**

## Contexts

| Form | Evaluated | Where |
|------|-----------|-------|
| `{expr}` or `'expr'` | at expansion, before analysis | `.param`, instance values |
| bare expr | during analysis | B, E, G sources and R, L, C `r=`, `l=`, `c=` |

In run-time contexts the expression can contain `v(node)`, `i(vname)`,
`time`, `temper` and `hertz`. In expansion contexts it cannot.

## Scale suffixes in expressions

The manual's list of suffixes in this section (`g meg k m u n p f`) is
shorter than the list in 2.1.4.2, which also has `t`, `mil` and `a`. Whether
`1a` or `1mil` work inside an expression is **open (A-23)** and needs a test.

## Examples (non-normative)

Examples illustrate the rules above and are **not normative**: where an
example and the rule text disagree, the rule text is the specification and
the example is a bug to investigate. Examples run as doctests on ngspice
(`tools/doctest.py`; see [doctests.md](doctests.md)). All are original.


Precedence: multiplication binds tighter than addition.

```spice-test id=EXPR-1 covers=expr,sum,term,factor,atom dialect=common
.param p={2+3*4}
V1 a 0 {p}
R1 a 0 1k
* expect: v(a) = 14
```

Power, written with `**`.

```spice-test id=EXPR-2 covers=power dialect=common
V1 a 0 {2**3}
R1 a 0 1k
* expect: v(a) = 8
```

Unary minus.

```spice-test id=EXPR-3 covers=signed dialect=common
V1 a 0 {-3+5}
R1 a 0 1k
* expect: v(a) = 2
```

The ternary operator.

```spice-test id=EXPR-4 covers=ternary dialect=common
V1 a 0 {1 > 0 ? 10 : 20}
R1 a 0 1k
* expect: v(a) = 10
```

Logical and comparison operators give exactly 1 or 0.

```spice-test id=EXPR-5 covers=oror,andand,compare dialect=common
V1 a 0 {(1 && 0) || 1}
V2 b 0 {3 <= 4}
R1 a 0 1k
R2 b 0 1k
* expect: v(a) = 1
* expect: v(b) = 1
```

A function call and a nested function.

```spice-test id=EXPR-6 dialect=common
V1 a 0 {sqrt(16) + abs(-1)}
R1 a 0 1k
* expect: v(a) = 5
```

Where a minus after an operator belongs to the following number, and a
leading minus covers a whole power or product (rules 1 and 5).

```spice-test id=EXPR-7 covers=pow-operand dialect=ngspice
V1 a 0 {2**-2}
V2 b 0 {-2**2}
V3 c 0 {2*-2**2}
V4 d 0 {-3*3\2}
R1 a 0 1k
R2 b 0 1k
R3 c 0 1k
R4 d 0 1k
* expect: v(a) = 0.25
* expect: v(b) = -4
* expect: v(c) = 8
* expect: v(d) = -4
```

Power is left-associative and drops the sign of its base (rules 2 and 3).

```spice-test id=EXPR-8 covers=power dialect=ngspice
V1 a 0 {2^3^2}
V2 b 0 {(-2)**3}
V3 c 0 {pow(-2,3)}
V4 d 0 {pwr(-2,3)}
R1 a 0 1k
R2 b 0 1k
R3 c 0 1k
R4 d 0 1k
* expect: v(a) = 64
* expect: v(b) = 8
* expect: v(c) = -8
* expect: v(d) = 8
```

`!` binds tighter than `**`; `\` and `%` on real numbers (rules 1 and 4).

```spice-test id=EXPR-9 covers=factor,not-operand,power-tail dialect=ngspice
V1 a 0 {!1**0 + !!2}
V2 b 0 {7.5\2.5}
V3 c 0 {(0-7)\2}
V4 d 0 {5.5%-2}
V5 e 0 {-5.5%2}
R1 a 0 1k
R2 b 0 1k
R3 c 0 1k
R4 d 0 1k
R5 e 0 1k
* expect: v(a) = 2
* expect: v(b) = 3
* expect: v(c) = 3
* expect: v(d) = 1.5
* expect: v(e) = -1.5
```

Arithmetic is IEEE and only the final value must be finite (rule 7): the
division by zero here is not an error, and the same expression as the whole
value is.

```spice-test id=EXPR-10 dialect=common
V1 a 0 {7 == 4/0}
V2 b 0 {ln(0) > 1}
R1 a 0 1k
R2 b 0 1k
* expect: v(a) = 0
* expect: v(b) = 0
```

```spice-test id=EXPR-11 dialect=ngspice expect=reject
V1 a 0 {7/0}
R1 a 0 1k
```

The natural logarithm is `log` as well as `ln` in ngspice.

```spice-test id=EXPR-12 dialect=ngspice
V1 a 0 {log(100)}
V2 b 0 {log10(100)}
R1 a 0 1k
R2 b 0 1k
* expect: v(a) = 4.605170186
* expect: v(b) = 2
```
