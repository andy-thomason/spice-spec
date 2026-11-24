"""Dialect switches, from grammar/00-tokens.md ("Dialect switches") and
grammar/01-lexical.md (pass 1). Each field names where it comes from.

Only ngspice and SPICE3 are filled in from documentation that was read;
the xyce preset is the documented subset and is otherwise a guess.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Dialect:
    name: str
    # Pass 1, step P3: a line starting with white space is a comment
    # (SPICE3, Xyce) unless its first non-blank character is '+'.
    leading_ws_comment: bool
    # Pass 1, step P4 (ngspice): a line starting with one of these is
    # replaced by a comment with a warning.
    special_leading: str
    # Pass 1, step P8: end-of-line comment starters.
    eol_chars: str
    eol_slashes: bool
    # Pass 1, step P7: a line ending in two backslashes continues.
    backslash_continuation: bool
    # Numbers: letter 'a' is atto; 'd' is an exponent marker.
    atto: bool
    d_exponent: bool


NGSPICE = Dialect(
    name="ngspice",
    leading_ws_comment=False,
    special_leading='=[]?()&%$§"!:',   # NGS-42 2.1.2.2
    eol_chars=";$",                            # NGS-42 2.3.4
    eol_slashes=True,
    backslash_continuation=True,
    atto=True,
    d_exponent=True,                           # observed, TOK-NUM-2
)

SPICE3 = Dialect(
    name="spice3",
    leading_ws_comment=True,                   # SP3-UG "Comments"
    special_leading="",
    eol_chars="",                              # none documented
    eol_slashes=False,
    backslash_continuation=False,
    atto=False,                                # SP3-UG scale list has no 'a'
    d_exponent=False,
)

XYCE = Dialect(
    name="xyce",
    leading_ws_comment=True,                   # XYC-REF 2.1.39.1
    special_leading="",
    eol_chars=";",                             # XYC-REF 2.1.39.2
    eol_slashes=False,
    backslash_continuation=False,
    atto=False,                                # XYC-REF 3.1, 6.2
    d_exponent=False,                          # not read
)

DIALECTS = {d.name: d for d in (NGSPICE, SPICE3, XYCE)}
