# 05 Expressions

Source: ngspice 42 manual 2.9.5 to 2.9.7. Tag `dialect:ngspice`. The manual
itself states that ngspice has three expression parsers with different
syntax (front end, `.param`, and the control language), so this file
describes the netlist one.

## Grammar

```abnf
expr      = ternary
ternary   = oror [ "?" expr ":" expr ]
oror      = andand *( "||" andand )
andand    = compare *( "&&" compare )
compare   = sum *( ( "==" / "!=" / "<>" / "<=" / ">=" / "<" / ">" ) sum )
sum       = term *( ( "+" / "-" ) term )
term      = power *( ( "*" / "/" / "%" / "\" ) power )
power     = unary *( ( "**" / "^" ) unary )
unary     = [ "-" / "!" ] atom
atom      = number / ident / func "(" expr *( "," expr ) ")" / "(" expr ")"
```

The ordering above follows the precedence table in the manual (unary 1,
power 2, multiply 3, add 4, comparison 5, and 6, or 7, ternary 8). The
manual lists unary minus and `!` at the **same level as the tightest binding**,
and power at level 2, which means `-2^2` and `2^-2` need testing before
this grammar is accepted (A-21). Equal precedence binary operators group
left to right. The verbose operators `not and or div mod` are reserved words
(manual 2.9.6) and map to the symbols.

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

Details to specify per function: domain, treatment of out-of-range
arguments, and whether `log` is natural (the manual lists `ln, log` together).
**A-22.**

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
