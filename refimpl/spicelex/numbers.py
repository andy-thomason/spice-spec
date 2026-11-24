"""number(word): the numeric-word classification of grammar/00-tokens.md."""
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

# Longest match first: meg and mil before m (00-tokens.md, step 4).
_SCALES = [
    ("meg", Decimal("1e6")), ("mil", Decimal("25.4e-6")),
    ("t", Decimal("1e12")), ("g", Decimal("1e9")), ("k", Decimal("1e3")),
    ("m", Decimal("1e-3")), ("u", Decimal("1e-6")), ("n", Decimal("1e-9")),
    ("p", Decimal("1e-12")), ("f", Decimal("1e-15")),
]
_ATTO = ("a", Decimal("1e-18"))
_MANTISSA = re.compile(r"([+-]?)(\d+(?:\.\d*)?|\.\d+)")


@dataclass(frozen=True)
class NumberInfo:
    text: str
    mantissa: str            # with sign
    exponent: Optional[str]  # as written, e.g. "e-3"; None if there were no digits
    skipped: str             # exponent marker (and sign) consumed without digits, e.g. "e-"
    scale: Optional[str]     # as written, e.g. "Meg"
    tail: str                # ignored characters
    value: float
    error: Optional[str] = None   # the dialect's tool rejects this word


def number(word, dialect):
    """Return NumberInfo if `word` starts with a number, else None."""
    m = _MANTISSA.match(word)
    if not m:
        return None
    sign, digits = m.group(1), m.group(2)
    pos = m.end()
    exponent, skipped, error = None, "", None
    exp_value = 0
    marker = "ed" if dialect.d_exponent else "e"
    if pos < len(word) and word[pos].lower() in marker:
        is_d = word[pos].lower() == "d"
        e = re.match(r"\d+" if is_d else r"[+-]?\d+", word[pos + 1:])   # d: unsigned only
        if e:
            exponent = word[pos:pos + 1 + e.end()]
            exp_value = int(e.group(0))
            pos += 1 + e.end()
        else:
            # A marker without digits is consumed, with its sign; a scale factor may follow.
            skip = 1 + (1 if word[pos + 1:pos + 2] in ("+", "-") else 0)
            skipped = word[pos:pos + skip]
            pos += skip
    scale_text, factor = None, Decimal(1)
    low = word[pos:].lower()
    scales = _SCALES + ([_ATTO] if dialect.atto else [])
    for name, f in scales:
        if low.startswith(name):
            scale_text, factor = word[pos:pos + len(name)], f
            pos += len(name)
            break
    if dialect.d_exponent and re.search(r"d[+-]", word.lower()):
        # Observed: ngspice stops with an error on a numeric word that has a
        # 'd' followed by a sign anywhere, even in the ignored tail.
        error = "signed-d-exponent"
    value = Decimal(sign + digits) * (Decimal(10) ** exp_value) * factor
    return NumberInfo(word, sign + digits, exponent, skipped, scale_text, word[pos:],
                      float(value), error)
