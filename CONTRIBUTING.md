# Contributing

This project is clean room. Read [docs/clean-room.md](docs/clean-room.md)
first.

In short:

- Use documentation and black-box behavior only. Do not read, copy or
  paraphrase simulator source code.
- Write in your own words. Cite each rule with a source ID and section.
- Write tests from scratch. Do not copy netlists or expected outputs from
  any suite.
- Run `tools/audit-verbatim.py` on your changes against the reference
  documents (kept outside the repo).

## Declaration

Include this in your first pull request description:

> I have not read or copied the source code of any SPICE-family simulator
> for the areas this change covers, and I have not copied documentation
> text or test files. Exceptions (tools I have worked on the source of):
> none / <list>.

An AI assistant that helps write a change counts as a contributor: the
human submitting it makes the declaration after checking the output.
