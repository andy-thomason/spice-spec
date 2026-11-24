# spice-spec

An open, written specification of the SPICE circuit simulation language and
its semantics, built from SPICE3f5 and the documented behavior of ngspice,
Xyce and HSPICE.

Status: **design phase**. See [docs/design.md](docs/design.md).

`refimpl/` holds a small reference pass 1 and tokenizer used to check the spec.
It is not part of the spec and not for use by implementations.

This is a clean-room project: see [docs/clean-room.md](docs/clean-room.md) and
[CONTRIBUTING.md](CONTRIBUTING.md). No simulator source code is read or copied.
