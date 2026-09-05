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

from tests.api.coverage import PolicyTerm
from tests.api.resolution import notice_record
from tests.api.siu import (
    LATE_REPORTING_INDICATOR,
    RECENT_POLICY_INCEPTION_INDICATOR,
    siu_indicator_events,
)

INDICATORS = {
    "late reporting": LATE_REPORTING_INDICATOR,
    "recent policy inception": RECENT_POLICY_INCEPTION_INDICATOR,
}


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


def assert_recorded_indicator(context: dict[str, Any], indicator: str, phrase: str) -> None:
    """The stored event, not a computed value: conftest.py's "the late reporting
    indicator is ..." reads what the domain returned and this reads what the
    trail kept. Two subjects, two phrases, on purpose.

    Shared by features/siu_separation.feature and features/jurisdiction_selection.
    feature, which state the phrase in the same words. It is here rather than in
    conftest.py because both files must keep their own step definitions - see
    assert_notice_state above - and pytest-bdd binds those per module.

    The expected value is compared case-insensitively, and only the value: the
    acceptance engine substitutes an upper-case TRUE with a lower-case `true`
    before it ever tries a sibling swap (docs/harness-findings.md, "The boolean
    substitution is lowercase and preemptive"), so an exact comparison kills
    every such mutant without testing anything. Folding the case is what makes
    the mutant a real question about which value was recorded. The reason code is
    compared exactly - no mutation ever changes its case, and folding it would
    only widen what an assertion accepts.
    """
    event = recorded_indicator_event(context, INDICATORS[indicator])
    value, _, reason = phrase.partition(" with reason ")
    assert event.value == value.strip().upper()
    assert event.reason_code == (reason.strip() or None)


def recorded_indicator_event(context: dict[str, Any], indicator: str) -> Any:
    matching = [
        event
        for event in siu_indicator_events(context["store"], context["notice_id"])
        if event.indicator == indicator
    ]
    assert len(matching) == 1
    return matching[0]


def policy_terms(context: dict[str, Any]) -> list[PolicyTerm]:
    """The policy terms a scenario has stated so far, in order: written by the
    term-history steps in conftest.py, read by the two coverage rules' When
    steps, each in its own module."""
    terms: list[PolicyTerm] = context.setdefault("terms", [])
    return terms
