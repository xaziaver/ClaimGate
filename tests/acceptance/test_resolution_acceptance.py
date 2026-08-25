"""Acceptance tests binding features/resolution.feature to the test API.

The Background is notice_intake.feature's plus one line, and the submission,
response-status, blockers and idempotency steps are shared - all of those are in
conftest.py. What lives here is the reviewer's vocabulary, the record sequence,
and the audit assertions this spec alone makes.

**One phrase deliberately overrides conftest.py's rather than reusing it.**
"the notice's state is" there asserts the state the last response reports, which
is what idempotency.feature needs. This spec's 400 row asserts the notice's state
on a response that carries none - the reviewer's identity is checked before the
notice is read, so a caller who has not said who they are learns nothing about
it - so here the phrase reads the stored notice, and additionally checks the
response whenever the response does report a state. That second half is what
keeps the replay rule a proof about the replay: its whole point is that the
replay reports the state the notice is in now.

**Which arrival a record came from is checked against what arrived**, not
against the position the step just used to select the record. A step that read
the origin off arrival_index would be asserting the index it indexed by. Each
named arrival is rebuilt from what the scenario supplied and hashed with the
design's own payload_reference recipe, so "the second record is the reviewer's
first resolution" is a claim about content that can fail.
"""

from dataclasses import asdict
from datetime import datetime
from typing import Any

from pytest_bdd import given, parsers, scenarios, then, when

from tests.acceptance.support import parse_compact_blockers
from tests.api.notice_intake import NoticeFields
from tests.api.resolution import (
    merged_view,
    notice_record,
    notice_records,
    payload_reference,
    resolve_notice,
)

scenarios("../../features/resolution.feature")

_SUPPLIED_FIELDS = {
    "policy number": "policy_number",
    "notice type": "notice_type",
    "loss type": "loss_type",
}
_ORDINALS = {"first": 1, "second": 2, "third": 3, "fourth": 4}
_TRAIL_LENGTHS = {
    "gains a third entry, for the resolution": 3,
    "still holds only its two intake entries": 2,
    "holds four entries": 4,
}
_SUBMISSION = "the submission the notice was created from"
_RECORD_SETS = {
    "are two, the submission and the resolution": (_SUBMISSION, "the reviewer's resolution"),
    "are one, the submission it was created from": (_SUBMISSION,),
}


@given(parsers.parse('the reviewer is identified as "{value}"'))
def set_reviewer(context: dict[str, Any], value: str) -> None:
    # "absent" here means no identity in the body at all, which is what makes
    # the body schema-invalid. It is a different absence from a field the
    # reviewer simply did not supply.
    context["reviewer"] = None if value == "absent" else value


@when(parsers.re(r'^the reviewer supplies a (?P<name>[a-z ]+) of "(?P<value>[^"]*)"$'))
@given(parsers.re(r'^the reviewer supplies a (?P<name>[a-z ]+) of "(?P<value>[^"]*)"$'))
def supply_field(context: dict[str, Any], name: str, value: str) -> None:
    # "absent" means the field is not in the resolution payload. There is no way
    # to blank a field in phase 2, only to replace one, so it never means
    # cleared - it means this reviewer said nothing about it.
    if name not in _SUPPLIED_FIELDS:
        raise ValueError(f"unrecognized supplied field: {name!r}")
    if value != "absent":
        context.setdefault("supplied", {})[_SUPPLIED_FIELDS[name]] = value


@when("the reviewer supplies no field values")
def supply_nothing(context: dict[str, Any]) -> None:
    context["supplied"] = {}


@given(parsers.parse('the reviewer\'s resolution is submitted at "{instant}"'))
@when(parsers.parse('the reviewer\'s resolution is submitted at "{instant}"'))
def submit_resolution(context: dict[str, Any], instant: str) -> None:
    supplied = context.pop("supplied", {})
    context.setdefault("resolutions", []).append(supplied)
    context["response"] = resolve_notice(
        context["store"],
        context["notice_id"],
        actor_id=context["reviewer"],
        resolved_at=_instant(instant),
        jurisdiction_timezone=context["jurisdiction_timezone"],
        carrier_rules_source=context["carrier_rules_source"],
        supplied=supplied,
    )


@given(parsers.re(r"^the notice's state is (?P<value>.*)$"))
@then(parsers.re(r"^the notice's state is (?P<value>.*)$"))
def check_notice_state(context: dict[str, Any], value: str) -> None:
    assert _record(context).state == value
    reported = context["response"].state
    if reported is not None:
        assert reported == value


@then(parsers.re(r"^the notice's severity is (?P<value>.*)$"))
def check_severity(context: dict[str, Any], value: str) -> None:
    assert _assigned(context["response"].severity) == value


@then(parsers.re(r"^the notice's queue is (?P<value>.*)$"))
def check_queue(context: dict[str, Any], value: str) -> None:
    assert _assigned(context["response"].queue) == value


@then(parsers.re(r"^the notice's audit trail (?P<phrase>.*)$"))
def check_trail_length(context: dict[str, Any], phrase: str) -> None:
    if phrase not in _TRAIL_LENGTHS:
        raise ValueError(f"unrecognized audit trail phrase: {phrase!r}")
    assert len(_trail(context)) == _TRAIL_LENGTHS[phrase]


@then(parsers.re(r"^the audit trail's last entry records the outcome (?P<outcome>.*)$"))
def check_last_entry_outcome(context: dict[str, Any], outcome: str) -> None:
    entry = _trail(context)[-1]
    context["current_entry"] = entry
    assert entry.outcome == outcome


@then(parsers.re(r"^that entry is entered by (?P<actor>.*)$"))
def check_entry_actor(context: dict[str, Any], actor: str) -> None:
    assert context["current_entry"].actor_type == actor


@then(parsers.re(r"^that entry's blockers are (?P<value>.*)$"))
def check_entry_blockers(context: dict[str, Any], value: str) -> None:
    entry = context["current_entry"]
    actual = [(b.code, b.field) for b in entry.blockers]
    assert actual == parse_compact_blockers(value)


@then("that entry records the reviewer's own asserted identity, unverified")
def check_entry_identity(context: dict[str, Any]) -> None:
    entry = context["current_entry"]
    assert entry.actor_id == context["reviewer"]
    assert entry.actor_authenticated is False


@then(parsers.re(r"^the audit trail's last entry is stamped (?P<instant>.*)$"))
def check_last_entry_instant(context: dict[str, Any], instant: str) -> None:
    assert _trail(context)[-1].occurred_at == _instant(instant)


@then(parsers.re(r"^the notice's pend is still stamped (?P<instant>.*)$"))
def check_pend_instant(context: dict[str, Any], instant: str) -> None:
    assert _record(context).pended_at == _instant(instant)


@then(parsers.re(r"^the notice's records (?P<phrase>.*)$"))
def check_record_set(context: dict[str, Any], phrase: str) -> None:
    if phrase not in _RECORD_SETS:
        raise ValueError(f"unrecognized records phrase: {phrase!r}")
    expected = _RECORD_SETS[phrase]
    records = notice_records(context["store"], context["notice_id"])
    assert len(records) == len(expected)
    for record, origin in zip(records, expected, strict=True):
        assert record.reference == payload_reference(_arrival(context, origin))


@then(
    parsers.re(
        r"^the (?P<ordinal>\w+) record kept for the notice reports a policy number of "
        r"(?P<value>.*)$"
    )
)
def check_record_policy_number(context: dict[str, Any], ordinal: str, value: str) -> None:
    record = notice_records(context["store"], context["notice_id"])[_ORDINALS[ordinal] - 1]
    context["current_record"] = record
    assert record.content.get("policy_number", "") == ("" if value == "absent" else value)


@then(parsers.re(r"^that record (?P<origin>.*)$"))
def check_record_origin(context: dict[str, Any], origin: str) -> None:
    expected = _arrival(context, origin.removeprefix("is "))
    assert context["current_record"].reference == payload_reference(expected)


@then(parsers.re(r"^no (?P<ordinal>\w+) record is kept for the notice$"))
def check_no_further_record(context: dict[str, Any], ordinal: str) -> None:
    records = notice_records(context["store"], context["notice_id"])
    assert len(records) == _ORDINALS[ordinal] - 1


@given(parsers.parse('the notice\'s current view reports a policy number of "{value}"'))
@then(parsers.parse('the notice\'s current view reports a policy number of "{value}"'))
def check_current_view(context: dict[str, Any], value: str) -> None:
    assert merged_view(context["store"], context["notice_id"]).policy_number == value


def _instant(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _assigned(value: str | None) -> str:
    return "not yet assigned" if value is None else value


def _record(context: dict[str, Any]) -> Any:
    record = notice_record(context["store"], context["notice_id"])
    assert record is not None
    return record


def _trail(context: dict[str, Any]) -> Any:
    return context["store"].get_audit_trail(context["notice_id"])


def _arrival(context: dict[str, Any], origin: str) -> dict[str, Any]:
    """What the named arrival carried, rebuilt from the scenario's own steps.
    The submission is every field it reported; a resolution is only what its
    reviewer supplied."""
    if origin == _SUBMISSION:
        return asdict(NoticeFields(**context["fields"]))
    index = {
        "the reviewer's resolution": 0,
        "the reviewer's first resolution": 0,
        "the reviewer's second resolution": 1,
    }
    if origin not in index:
        raise ValueError(f"unrecognized record origin: {origin!r}")
    return dict(context["resolutions"][index[origin]])
