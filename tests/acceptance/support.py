"""Values and helpers the acceptance step definitions share.

A plain module rather than conftest.py, for the reason tests/shell/support.py
records: pytest imports a conftest.py in a directory with no __init__.py under
its own module name, so importing the same file again by path produces a second
module object. Constants and functions survive that; anything identity-sensitive
does not. Step definitions still belong in conftest.py - that is where pytest-bdd
finds them - and only what they share comes here.
"""

from datetime import datetime
from typing import Any

from tests.api.resolution import notice_record


def parse_instant(value: str) -> datetime:
    """The "...Z" spelling every spec writes an instant in, as a UTC datetime."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def assert_notice_state(context: dict[str, Any], expected: str) -> None:
    """features/resolution.feature's reading of "the notice's state is", shared
    with features/siu_separation.feature. The stored notice first, because
    resolution.feature's 400 row asserts a state on a response that carries none
    - the reviewer's identity is checked before the notice is read - and the
    response as well whenever it does report one, because idempotency.feature's
    replay rule is exactly that a replay reports the state the notice is in now.

    The two files keep their own step definition rather than this reading moving
    to conftest.py: three other specs assert the phrase on responses to
    submissions that created no notice, and a shared definition would have no
    stored notice to read."""
    record = notice_record(context["store"], context["notice_id"])
    assert record is not None
    assert record.state == expected
    reported = context["response"].state
    if reported is not None:
        assert reported == expected


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
