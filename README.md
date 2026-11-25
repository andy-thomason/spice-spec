# spice-spec

An open, written specification of the SPICE circuit simulation language and
its semantics, built from SPICE3f5 and the documented behavior of ngspice,
Xyce and HSPICE.

Status: **design phase**. See [docs/design.md](docs/design.md).

`refimpl/` holds a small reference pass 1 and tokenizer used to check the spec.
It is not part of the spec and not for use by implementations.

The meaning of circuits (as opposed to their syntax) is being written in `spec/`;
the first page is [spec/06-sources/waveforms.md](spec/06-sources/waveforms.md).

This is a clean-room project: see [docs/clean-room.md](docs/clean-room.md) and
[CONTRIBUTING.md](CONTRIBUTING.md). No simulator source code is read or copied.

## Licence

Spec text, grammar and conformance tests: CC BY 4.0 ([LICENSE-text.txt](LICENSE-text.txt)). Tools and reference implementation: Apache-2.0 ([LICENSE-code.txt](LICENSE-code.txt)). See [LICENSE](LICENSE).
