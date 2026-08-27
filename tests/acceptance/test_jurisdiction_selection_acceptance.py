"""Acceptance tests binding features/jurisdiction_selection.feature to the test API.

Almost every step this spec states is one another locked spec already stated in
the same words, so almost all of them are conftest.py's: the carrier's
configuration, the property state, the submission, the reviewer's vocabulary and
the response status. What is here is the two readings this spec alone makes and
one phrase it has to take back from conftest.py.

**"the notice's state is" is defined here rather than inherited**, for the reason
test_resolution_acceptance.py and test_siu_separation_acceptance.py define it:
this spec uses the phrase in Given position, on a notice sitting PENDED whose
last response was the submission's. conftest.py's definition is @then-only and
reads the response alone. The reading is support.assert_notice_state, the same
one both those modules use - deliberately not a looser local copy, because four
of this file's mutants are `TRIAGED -> TRIAGED_gauntlet` and they are real tests
only while the comparison refuses a token it does not recognize.

**The two readings this spec alone makes are both off the stored notice**, not
off a response. The marking and the determination are what the notice says now,
and both scenarios in the last rule assert them after a resolution has replaced
what the submission concluded - a response-shaped reading would have nothing to
compare on the Given rows at all.
"""

from typing import Any

from pytest_bdd import given, parsers, scenarios, then

from tests.acceptance.support import assert_notice_state, assert_recorded_indicator
from tests.api.jurisdiction import JURISDICTION_UNSUPPORTED
from tests.api.resolution import notice_record

scenarios("../../features/jurisdiction_selection.feature")

# "none" is the absence of a marking and is not a marking spelled "none"; the
# other spelling comes from the code that defines it rather than from a literal
# here. Anything else is a step-definition error and not a failed assertion -
# an unrecognized token must never resolve to one of these two by default.
_MARKINGS: dict[str, str | None] = {
    "none": None,
    JURISDICTION_UNSUPPORTED: JURISDICTION_UNSUPPORTED,
}


@given(parsers.re(r"^the notice's state is (?P<value>.*)$"))
@then(parsers.re(r"^the notice's state is (?P<value>.*)$"))
def check_state_against_the_stored_notice(context: dict[str, Any], value: str) -> None:
    assert_notice_state(context, value)


@given(parsers.re(r"^the notice's jurisdiction marking is (?P<value>.*)$"))
@then(parsers.re(r"^the notice's jurisdiction marking is (?P<value>.*)$"))
def check_jurisdiction_marking(context: dict[str, Any], value: str) -> None:
    if value not in _MARKINGS:
        raise ValueError(f"unrecognized jurisdiction marking: {value!r}")
    assert _stored(context).jurisdiction_marking == _MARKINGS[value]


@then(parsers.re(r"^the future-dated-loss determination recorded for the notice is (?P<value>.*)$"))
def check_future_dated_loss(context: dict[str, Any], value: str) -> None:
    """The compact VALUE:REASON spelling this spec uses for the determination,
    which is deliberately not the "NOT_EVALUATED with reason ..." spelling it
    uses for a recorded indicator - two subjects, two spellings.

    The value half is compared case-insensitively and the reason half exactly.
    The acceptance engine substitutes an upper-case TRUE with a lower-case
    `true` and returns before it tries a sibling swap (docs/harness-findings.md,
    "The boolean substitution is lowercase and preemptive"), so an exact
    comparison would kill all six of this file's TRUE/FALSE mutants without
    asking which value was determined. Folding the case is what makes each one a
    real question. It widens nothing: `TRUE`, `FALSE` and `NOT_EVALUATED` are
    the whole enumeration and no two of them differ only in case."""
    determination = _stored(context).future_dated_loss
    assert determination is not None
    expected, _, reason = value.partition(":")
    assert determination.value == expected.strip().upper()
    assert determination.reason == (reason.strip() or None)


@then(parsers.re(r"^the late reporting indicator recorded for the notice is (?P<phrase>.*)$"))
def check_recorded_late_reporting(context: dict[str, Any], phrase: str) -> None:
    """The same reading test_siu_separation_acceptance.py uses, in support.py
    since both specs state the phrase in the same words. Narrowed to the one
    indicator this spec asserts."""
    assert_recorded_indicator(context, "late reporting", phrase)


def _stored(context: dict[str, Any]) -> Any:
    record = notice_record(context["store"], context["notice_id"])
    assert record is not None
    return record
