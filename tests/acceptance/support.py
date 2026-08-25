"""Values and helpers the acceptance step definitions share.

A plain module rather than conftest.py, for the reason tests/shell/support.py
records: pytest imports a conftest.py in a directory with no __init__.py under
its own module name, so importing the same file again by path produces a second
module object. Constants and functions survive that; anything identity-sensitive
does not. Step definitions still belong in conftest.py - that is where pytest-bdd
finds them - and only what they share comes here.
"""


def parse_compact_blockers(value: str) -> list[tuple[str, str]]:
    """The CODE:field;CODE:field spelling three specs use for a blocker list, as
    ordered pairs. An empty cell is an empty list, not "any blockers": every
    caller compares with == so that a mutated row producing two blockers where
    one is asserted is caught."""
    value = value.strip()
    if not value:
        return []
    pairs: list[tuple[str, str]] = []
    for pair in value.split(";"):
        code, field = pair.split(":", 1)
        pairs.append((code, field))
    return pairs
