# Model binning (BSIM4 example)

Status: draft v0.1. How a MOSFET instance picks one of several model cards
that cover different geometry ranges. Binning is used by almost every
foundry library (see [../../docs/hspice-corpus/findings.md](../../docs/hspice-corpus/findings.md)).
Sources: `NGS-42` 3.2.3 (model binning); `XYC-REF` 2.3.20.7 (BSIM4 model
versions). The documents say binning picks a card "by the requested W and L"
and do not print the selection rule, the boundary rule or the error case.
Everything below was **measured** on ngspice 42 and Xyce 7.10 with the
examples. (Xyce prints warnings about parameters it adjusts in the default
BSIM4 card, such as `pbswgs`; they do not affect the result.) They are **non-normative**.

## Rule (`common`, measured on BSIM4)

1. **Names.** A binned model is a set of `.model` cards named `base.1`,
   `base.2`, ... (any positive integers). The instance refers to the model by
   the plain name `base`, not by a numbered name.
2. **Bin limits.** Each card gives `lmin`, `lmax`, `wmin`, `wmax`, in meters.
3. **Selection.** The instance uses the card whose limits satisfy
   `lmin <= L < lmax` and `wmin <= W < wmax`, with `L` and `W` the instance
   geometry. The lower limit is inclusive and the upper limit is exclusive:
   an instance exactly on the shared edge of two bins uses the bin that
   starts there.
4. **No match.** If no card contains the instance's `L` and `W`, the deck
   is rejected (an error on both tools).
5. **Which models.** ngspice documents binning for BSIM3 and BSIM4 only, and
   rejects binned level 1 models (example in
   [../09-dialects/library-conventions.md](../09-dialects/library-conventions.md)).
   Xyce also bins level 1 models, with warnings; the two tools agree on BSIM4,
   which is the case specified here (A-47).

The examples use three BSIM4 cards (`level=54`, `version=4.8.2`, which both
tools accept without a version warning) that differ only in `vth0`, so the
chosen card shows in the current at `vgs = 0.6 V`, `vds = 1 V`: threshold 0.2 V
conducts about 0.56 mA, threshold 0.8 V gives a sub-threshold leakage of
about 1e-10 A. The numbers below are the measured values; both tools agreed
to better than 1e-5 relative.

| Card | `L` range | `W` range | `vth0` |
|------|-----------|-----------|--------|
| `nm.1` | 0.1u to 0.2u | 1u to 10u | 0.2 |
| `nm.2` | 0.2u to 0.4u | 1u to 10u | 0.8 |
| `nm.3` | 0.1u to 0.2u | 10u to 20u | 0.8 |

```spice-test id=BIN-1 covers=mosfet dialect=common
Vg g 0 0.6
Vd d 0 1
M1 d g 0 0 nm w=5u l=0.15u
.model nm.1 NMOS(level=54 version=4.8.2 lmin=0.1u lmax=0.2u wmin=1u wmax=10u vth0=0.2)
.model nm.2 NMOS(level=54 version=4.8.2 lmin=0.2u lmax=0.4u wmin=1u wmax=10u vth0=0.8)
.model nm.3 NMOS(level=54 version=4.8.2 lmin=0.1u lmax=0.2u wmin=10u wmax=20u vth0=0.8)
* expect: i(vd) = -5.55979e-4 tol=1e-3
```

`L = 0.15u` and `W = 5u` fall in `nm.1`, the low-threshold card: 0.556 mA.

```spice-test id=BIN-2 dialect=common
Vg g 0 0.6
Vd d 0 1
M1 d g 0 0 nm w=5u l=0.3u
.model nm.1 NMOS(level=54 version=4.8.2 lmin=0.1u lmax=0.2u wmin=1u wmax=10u vth0=0.2)
.model nm.2 NMOS(level=54 version=4.8.2 lmin=0.2u lmax=0.4u wmin=1u wmax=10u vth0=0.8)
.model nm.3 NMOS(level=54 version=4.8.2 lmin=0.1u lmax=0.2u wmin=10u wmax=20u vth0=0.8)
* expect: i(vd) = -2.53592e-10 tol=1e-2
```

`L = 0.3u` selects `nm.2`, the high-threshold card.

```spice-test id=BIN-3 dialect=common
Vg g 0 0.6
Vd d 0 1
M1 d g 0 0 nm w=5u l=0.2u
.model nm.1 NMOS(level=54 version=4.8.2 lmin=0.1u lmax=0.2u wmin=1u wmax=10u vth0=0.2)
.model nm.2 NMOS(level=54 version=4.8.2 lmin=0.2u lmax=0.4u wmin=1u wmax=10u vth0=0.8)
.model nm.3 NMOS(level=54 version=4.8.2 lmin=0.1u lmax=0.2u wmin=10u wmax=20u vth0=0.8)
* expect: i(vd) = -1.66362e-10 tol=1e-2
```

`L = 0.2u` is the upper limit of `nm.1` and the lower limit of `nm.2`: the
instance uses `nm.2` (the current is the leakage current, not 0.5 mA).

```spice-test id=BIN-4 dialect=common
Vg g 0 0.6
Vd d 0 1
M1 d g 0 0 nm w=15u l=0.15u
.model nm.1 NMOS(level=54 version=4.8.2 lmin=0.1u lmax=0.2u wmin=1u wmax=10u vth0=0.2)
.model nm.2 NMOS(level=54 version=4.8.2 lmin=0.2u lmax=0.4u wmin=1u wmax=10u vth0=0.8)
.model nm.3 NMOS(level=54 version=4.8.2 lmin=0.1u lmax=0.2u wmin=10u wmax=20u vth0=0.8)
* expect: i(vd) = -8.40192e-10 tol=1e-2
```

`W = 15u` selects `nm.3`. The same rule applies to the width limits.

```spice-test id=BIN-6 dialect=common
Vg g 0 0.6
Vd d 0 1
M1 d g 0 0 nm w=10u l=0.15u
.model nm.1 NMOS(level=54 version=4.8.2 lmin=0.1u lmax=0.2u wmin=1u wmax=10u vth0=0.2)
.model nm.2 NMOS(level=54 version=4.8.2 lmin=0.2u lmax=0.4u wmin=1u wmax=10u vth0=0.8)
.model nm.3 NMOS(level=54 version=4.8.2 lmin=0.1u lmax=0.2u wmin=10u wmax=20u vth0=0.8)
* expect: i(vd) = -4.78678e-10 tol=1e-2
```

`W = 10u` exactly (the shared edge of `nm.1` and `nm.3`) selects `nm.3`.

```spice-test id=BIN-5 dialect=common expect=reject
Vg g 0 0.6
Vd d 0 1
M1 d g 0 0 nm w=5u l=0.5u
.model nm.1 NMOS(level=54 version=4.8.2 lmin=0.1u lmax=0.2u wmin=1u wmax=10u vth0=0.2)
.model nm.2 NMOS(level=54 version=4.8.2 lmin=0.2u lmax=0.4u wmin=1u wmax=10u vth0=0.8)
.model nm.3 NMOS(level=54 version=4.8.2 lmin=0.1u lmax=0.2u wmin=10u wmax=20u vth0=0.8)
```

`L = 0.5u` is outside every bin: both tools stop with an error.

## Not specified here

- The role of `binunit` and of the per-bin geometry parameters (`lvth0`,
  `wvth0`, `pvth0`, ...), which the BSIM4 equations use to scale a parameter
  with the instance geometry.
- Binning with the instance parameters `nf` (fingers) and `m` (multiplier):
  whether `W` is the total width or the width per finger when comparing with
  `wmin` and `wmax`.
- Models other than BSIM4, a bin with only some limits given, overlapping
  bins, and what happens when two bins both contain the instance.
