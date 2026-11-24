# Conformance tests

Each test is a directory holding one or more netlists and a `test.yaml`.

```
conformance/<group>/<id>-<name>/
  netlist.cir            portable netlist (no tool-specific cards)
  netlist.<tool>.cir     variant for a tool where syntax must differ
  test.yaml              id, tags, analysis, checks, tolerances, status
```

## test.yaml fields

| Field | Meaning |
|-------|---------|
| `id` | Stable ID, e.g. `RAD-001` |
| `tags` | `core`, `common` or `dialect:<tool>` (see docs/design.md) |
| `kind` | `syntax`, `analytic` or `cross-tool` |
| `netlists` | Netlist per tool, `default` for the portable one |
| `checks` | What to measure, expected value, tolerance |
| `status` | `unverified` until run and recorded (see below) |
| `refs` | Where the expected value comes from |

## Rules

- Portable netlists must not use `.control` blocks. Output is requested with
  `.print` and read from batch-mode output or the rawfile.
- Comments go on their own `*` lines, not inline, since inline comment
  characters differ between tools.
- Expected values for `analytic` tests come from hand calculation, shown in
  `test.yaml`. Tolerances are stated explicitly.

## Status

`unverified`: written from calculation, never run on any simulator. A test
only moves to `verified` once results are recorded for at least ngspice
and Xyce, with tool name and version. No runner exists yet (milestone M0).
