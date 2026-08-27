"""Acceptance tests binding features/siu_separation.feature to the test API.

The Background is resolution.feature's, and every step in it is shared - the
carrier's configuration, the submission, and the reviewer's identity all live in
conftest.py. What lives here is the restricted read, the two ties between an
evaluation and the audit entry that moved the notice, and the leak negatives.

**The leak negatives read the whole serialized surface**, not a named field.
features/siu_separation.feature says so in as many words: what protects that rule
is that the steps run at all, since none of their assertions is an Examples cell
that mutation could reach. Reading the surface whole is what makes a field added
carelessly later fail here rather than pass because nobody thought to list it.
The names they look for come from the test API, which takes them from the code
that defines them - a step file holding its own copy of "late_reporting" would
keep passing after that name changed.

**One phrase deliberately overrides conftest.py's**, exactly as
test_resolution_acceptance.py does and for its reason: this spec uses "the
notice's state is" in Given position on a notice sitting PENDED, where the last
response is the submission's and the question is what the notice says now. The
reading is in support.py, shared with that module.

The steps below never assert an event's absence by reading a field that is null.
An evaluation that did not happen and one that happened and found nothing are
different facts, and the counts here are what tell them apart.
"""

import json
import re
from typing import Any

from pytest_bdd import given, parsers, scenarios, then

from tests.acceptance.support import (
    assert_notice_state,
    assert_recorded_indicator,
    parse_instant,
    recorded_indicator_event,
)
from tests.api.notice_intake import get_notice
from tests.api.siu import (
    LATE_REPORTING_INDICATOR,
    SIU_INDICATOR_NAMES,
    SIU_REASON_CODES,
    all_siu_indicator_events,
    serialized_audit_entry,
    serialized_notice_view,
    serialized_response,
    siu_indicator_events,
)

scenarios("../../features/siu_separation.feature")

_COUNTS = {"two": 2, "four": 4}
# Both spellings of each indicator, because a surface could name one in either.
_NEVER_ON_AN_ORDINARY_SURFACE = tuple(
    text.lower()
    for name in SIU_INDICATOR_NAMES
    for text in (name, name.replace("_", " "))
) + tuple(code.lower() for code in SIU_REASON_CODES)
_TWO_EVENTS = re.compile(
    r'^are two, both stamped "(?P<instant>[^"]+)" and both carrying the ruleset version'
    r" of the entry that released it$"
)


@given(parsers.re(r"^the notice's state is (?P<value>.*)$"))
@then(parsers.re(r"^the notice's state is (?P<value>.*)$"))
def check_state_against_the_stored_notice(context: dict[str, Any], value: str) -> None:
    assert_notice_state(context, value)


@then(
    parsers.re(
        r"^the (?P<indicator>late reporting|recent policy inception) indicator recorded for "
        r"the notice is (?P<phrase>.*)$"
    )
)
def check_recorded_indicator(context: dict[str, Any], indicator: str, phrase: str) -> None:
    """The reading is in support.py since item 5g, shared with
    features/jurisdiction_selection.feature, which states this phrase in the same
    words. The step definition stays here because pytest-bdd binds those per
    module and this file overrides conftest.py's "the notice's state is" - see
    the module docstring."""
    assert_recorded_indicator(context, indicator, phrase)


@then("exactly two SIU indicator events are recorded for the notice")
def check_exactly_two_events(context: dict[str, Any]) -> None:
    assert len(_events(context)) == 2


@given("no SIU indicator event is recorded for the notice")
def check_no_event_yet(context: dict[str, Any]) -> None:
    assert _events(context) == ()


@then(parsers.re(r"^the SIU indicator events recorded for the notice (?P<phrase>.*)$"))
def check_events_phrase(context: dict[str, Any], phrase: str) -> None:
    events = _events(context)
    if phrase == "are none":
        assert events == ()
        return
    match = _TWO_EVENTS.match(phrase)
    if match is None:
        raise ValueError(f"unrecognized SIU events phrase: {phrase!r}")
    assert len(events) == 2
    assert {event.evaluated_at for event in events} == {parse_instant(match.group("instant"))}
    _assert_version_matches_entry(context, events, context["notice_id"])


@then(parsers.re(r'^each of those events is stamped "(?P<instant>[^"]+)"$'))
def check_event_stamps(context: dict[str, Any], instant: str) -> None:
    events = _events(context)
    assert events != ()
    assert {event.evaluated_at for event in events} == {parse_instant(instant)}


@then("those two events record the same ruleset version as each other")
def check_events_agree_on_the_version(context: dict[str, Any]) -> None:
    versions = {event.ruleset_version for event in _events(context)}
    # Two events carrying nothing would agree here too, so the populated check
    # is what stops this passing over a pair of empty labels.
    assert len(versions) == 1
    assert None not in versions


@then(
    parsers.re(
        r"^those two events record the same ruleset version as the audit entry that "
        r"(?:triaged|released) the notice$"
    )
)
def check_events_agree_with_the_entry(context: dict[str, Any]) -> None:
    _assert_version_matches_entry(context, _events(context), context["notice_id"])


@then("every recorded event carries the ruleset version of the audit entry that triaged its own notice")
def check_every_event_agrees_with_its_own_entry(context: dict[str, Any]) -> None:
    events = all_siu_indicator_events(context["store"])
    assert events != ()
    for notice_id in {event.notice_id for event in events}:
        _assert_version_matches_entry(
            context, tuple(e for e in events if e.notice_id == notice_id), notice_id
        )


@then(parsers.re(r"^the late reporting event records a threshold of (?P<days>\d+) days$"))
def check_recorded_threshold(context: dict[str, Any], days: str) -> None:
    assert recorded_indicator_event(context, LATE_REPORTING_INDICATOR).threshold_days == int(days)


@then("the late reporting event records no threshold")
def check_no_recorded_threshold(context: dict[str, Any]) -> None:
    # Absent, and never a zero: a configured zero is a real carrier choice that
    # makes every notice late, so it has to stay distinguishable from this.
    assert recorded_indicator_event(context, LATE_REPORTING_INDICATOR).threshold_days is None


@then("the original notice still has exactly two SIU indicator events")
def check_original_events(context: dict[str, Any]) -> None:
    assert len(_events_for(context, context["original"].notice_id)) == 2


@then(parsers.re(r"^(?P<count>\w+) SIU indicator events have been recorded in all$"))
def check_total_events(context: dict[str, Any], count: str) -> None:
    assert len(all_siu_indicator_events(context["store"])) == _COUNTS[count]


@then("the response names no SIU indicator and no SIU reason code")
def check_response_is_clean(context: dict[str, Any]) -> None:
    _assert_nothing_siu_on(serialized_response(context["response"]))


@then("the notice's own view names no SIU indicator and no SIU reason code")
def check_view_is_clean(context: dict[str, Any]) -> None:
    view = get_notice(context["store"], context["notice_id"])
    assert view is not None
    _assert_nothing_siu_on(serialized_notice_view(view))


@then("every entry in the audit trail names no SIU indicator and no SIU reason code")
def check_audit_trail_is_clean(context: dict[str, Any]) -> None:
    trail = context["store"].get_audit_trail(context["notice_id"])
    assert trail != ()
    for entry in trail:
        _assert_nothing_siu_on(serialized_audit_entry(entry))


@given("the blockers in that response name no SIU reason code")
def check_blockers_are_clean(context: dict[str, Any]) -> None:
    blockers = context["response"].blockers
    # On a pended response there is a real blocker list here; the assertion
    # would prove nothing over an empty one.
    assert blockers != ()
    _assert_nothing_siu_on([{"code": b.code, "field": b.field} for b in blockers])


def _events(context: dict[str, Any]) -> tuple[Any, ...]:
    return _events_for(context, context["notice_id"])


def _events_for(context: dict[str, Any], notice_id: str) -> tuple[Any, ...]:
    return siu_indicator_events(context["store"], notice_id)


def _assert_version_matches_entry(
    context: dict[str, Any], events: tuple[Any, ...], notice_id: str
) -> None:
    """The events of one evaluation against the entry that moved that notice
    into TRIAGED. Named by outcome rather than by position, so an implementation
    writing an extra entry cannot make this pass by accident."""
    entered = [
        entry
        for entry in context["store"].get_audit_trail(notice_id)
        if entry.to_state == "TRIAGED" and entry.outcome == "APPLIED"
    ]
    assert len(entered) == 1
    assert entered[0].ruleset_version is not None
    assert {event.ruleset_version for event in events} == {entered[0].ruleset_version}


def _assert_nothing_siu_on(surface: Any) -> None:
    """The whole surface as text, so a field nobody listed here is still read."""
    rendered = json.dumps(surface, sort_keys=True).lower()
    for name in _NEVER_ON_AN_ORDINARY_SURFACE:
        assert name not in rendered, f"{name!r} reached {rendered}"
