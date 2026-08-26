"""Shared fixtures and step definitions for acceptance tests.

Steps live here when more than one feature file states them in the same words.
The notice-submission steps below arrived here with features/idempotency.feature
(item 5d), which restates features/notice_intake.feature's Background verbatim;
copying them into a second module would be a duplicate block the duplication
gate refuses, and rewording them is not available - both specs are locked.

A module's own step definition overrides one of the same text here (ordinary
pytest fixture precedence, confirmed by test_carrier_configuration_acceptance.py,
which keeps its own carrier-rules steps and its own rules-source vocabulary).
features/resolution.feature (item 5e) uses that override for one phrase and
shares the rest: the blockers assertion and the three idempotency phrases below
moved here when it became the second locked spec to state them word for word.

The reviewer's four phrases and the carrier's late reporting threshold moved here
in item 5f, by the same rule and for the same reason: features/siu_separation.
feature states all five in exactly the words another locked spec already used.
The threshold phrase came from test_carrier_configuration_acceptance.py, which
keeps its own definition of it - that module has its own rules-source vocabulary
and writes to its own context key, which neither submit_notice nor resolve_notice
reads. Written here on the _rules_entry pattern instead, it replaces the value in
place, which is what lets a scenario configure a threshold after the notice has
already arrived.
"""

from datetime import date, datetime
from typing import Any

import pytest
from pytest_bdd import given, parsers, then, when

from tests.acceptance.support import parse_compact_blockers, parse_instant
from tests.api.notice_intake import IN_MEMORY_DATABASE, NoticeFields, NoticeStore, submit_notice
from tests.api.resolution import resolve_notice

DEFAULT_TODAY = date(2026, 8, 2)
_SUPPLIED_FIELDS = {
    "policy number": "policy_number",
    "notice type": "notice_type",
    "loss type": "loss_type",
}


@pytest.fixture
def context() -> dict[str, Any]:
    return {"today": DEFAULT_TODAY, "fields": {}, "idempotency_key": None}


@given(parsers.parse('today is "{value}"'))
def set_today(context: dict[str, Any], value: str) -> None:
    context["today"] = date.fromisoformat(value)


# Shared with siu_indicators.feature and triage.feature - both set thresholds
# with this exact step text (triage.feature's end-to-end scenario supplies the
# same thresholds it hands to compute_siu_indicators via the SIU test API).
@given(parsers.parse("the late reporting threshold is {value:d} days"))
def set_late_reporting_threshold(context: dict[str, Any], value: int) -> None:
    context["late_reporting_threshold_days"] = value


@given(parsers.parse("the recent policy inception threshold is {value:d} days"))
def set_recent_inception_threshold(context: dict[str, Any], value: int) -> None:
    context["recent_inception_threshold_days"] = value


# Bare form only (no reason code) - shared by triage.feature and the
# non-NOT_EVALUATED assertions in siu_indicators.feature. The "with reason"
# form stays local to the siu acceptance test file since only that spec
# asserts reason codes.
@then(parsers.parse("the late reporting indicator is {expected:w}"))
def check_late_reporting_indicator(context: dict[str, Any], expected: str) -> None:
    assert context["siu_indicators"].late_reporting.value == expected


@then(parsers.parse("the recent policy inception indicator is {expected:w}"))
def check_recent_inception_indicator(context: dict[str, Any], expected: str) -> None:
    assert context["siu_indicators"].recent_policy_inception.value == expected


def _rules_entry(context: dict[str, Any], carrier: str) -> dict[str, Any]:
    return context.setdefault("carrier_rules_source", {}).setdefault(carrier, {})


@given(parsers.re(r'^(?:the carrier )?"(?P<carrier>[^"]+)" requires the claimant name$'))
def set_claimant_name_required(context: dict[str, Any], carrier: str) -> None:
    _rules_entry(context, carrier)["claimant_name_required"] = True


@given(parsers.parse('"{carrier}" does not require the claimant contact'))
def set_claimant_contact_not_required(context: dict[str, Any], carrier: str) -> None:
    _rules_entry(context, carrier)["claimant_contact_required"] = False


@given(parsers.parse('"{carrier}" recognizes the policy-number prefixes "{prefixes}"'))
def set_recognized_prefixes(context: dict[str, Any], carrier: str, prefixes: str) -> None:
    _rules_entry(context, carrier)["recognized_policy_number_prefixes"] = prefixes.split(";")


@given(parsers.parse('"{carrier}" configures a late reporting threshold of {value:d} days'))
def set_carrier_late_reporting_threshold(
    context: dict[str, Any], carrier: str, value: int
) -> None:
    _rules_entry(context, carrier)["late_reporting_threshold_days"] = value


@given(parsers.parse('"{carrier}" has no late reporting threshold configured'))
def clear_late_reporting_threshold(context: dict[str, Any], carrier: str) -> None:
    _rules_entry(context, carrier).pop("late_reporting_threshold_days", None)


@given(
    parsers.parse('"{carrier}" configures a recent policy inception threshold of {value:d} days')
)
def set_carrier_recent_inception_threshold(
    context: dict[str, Any], carrier: str, value: int
) -> None:
    _rules_entry(context, carrier)["recent_inception_threshold_days"] = value


@given(parsers.parse('"{carrier}" configures a duplicate match window of {value:d} days'))
def set_duplicate_match_window(context: dict[str, Any], carrier: str, value: int) -> None:
    _rules_entry(context, carrier)["window_days"] = value


@given(parsers.parse('the notice is submitted by carrier "{carrier_code}"'))
@when(parsers.parse('the notice is submitted by carrier "{carrier_code}"'))
def set_carrier_code(context: dict[str, Any], carrier_code: str) -> None:
    context["carrier_code"] = carrier_code


@given(parsers.parse('the jurisdiction observes "{timezone_name}"'))
def set_jurisdiction_timezone(context: dict[str, Any], timezone_name: str) -> None:
    context["jurisdiction_timezone"] = timezone_name


@given(parsers.parse('the notice is submitted at "{submitted_at}"'))
@when(parsers.parse('the notice is submitted at "{submitted_at}"'))
def set_submitted_at(context: dict[str, Any], submitted_at: str) -> None:
    # Parsed here rather than at submission time so idempotency.feature's
    # "reports its own new receipt timestamp" has an instant to compare
    # against without re-parsing the cell.
    context["submitted_at"] = datetime.fromisoformat(submitted_at.replace("Z", "+00:00"))


@given(parsers.parse('the notice reports a policy number of "{value}"'))
def set_policy_number(context: dict[str, Any], value: str) -> None:
    context["fields"]["policy_number"] = "" if value == "absent" else value


@given(parsers.parse('the notice reports a loss date of "{value}"'))
@when(parsers.parse('the notice reports a loss date of "{value}"'))
def set_loss_date(context: dict[str, Any], value: str) -> None:
    context["fields"]["loss_date"] = value


@given(parsers.parse('the notice reports a loss type of "{value}"'))
@when(parsers.parse('the notice reports a loss type of "{value}"'))
def set_loss_type(context: dict[str, Any], value: str) -> None:
    context["fields"]["loss_type"] = value


@given(parsers.parse('the notice reports a notice type of "{value}"'))
def set_notice_type(context: dict[str, Any], value: str) -> None:
    context["fields"]["notice_type"] = value


@given(parsers.parse('the notice is submitted with the idempotency key "{value}"'))
@when(parsers.parse('the notice is submitted with the idempotency key "{value}"'))
def set_idempotency_key(context: dict[str, Any], value: str) -> None:
    # "absent" is the same cell convention notice_intake.feature already uses
    # for a policy number that was never supplied.
    context["idempotency_key"] = None if value == "absent" else value


@given("the notice is submitted for intake")
@when("the notice is submitted for intake")
def submit(context: dict[str, Any]) -> None:
    store = context.setdefault("store", NoticeStore(IN_MEMORY_DATABASE))
    context["response"] = submit_notice(
        store,
        carrier_code=context["carrier_code"],
        submitted_at=context["submitted_at"],
        jurisdiction_timezone=context["jurisdiction_timezone"],
        carrier_rules_source=context["carrier_rules_source"],
        fields=NoticeFields(**context["fields"]),
        idempotency_key=context["idempotency_key"],
    )
    # The notice a later step addresses, kept here because a resolution is a
    # second call against the same notice and the response it leaves behind is
    # its own, not the submission's. A refusal that created nothing leaves None,
    # which no spec that refuses then addresses the notice exists to read.
    context["notice_id"] = context["response"].notice_id


@given("that submission is remembered as the original")
def remember_the_original(context: dict[str, Any]) -> None:
    context["original"] = context["response"]


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


@given(parsers.parse('the reviewer\'s resolution is submitted at "{instant}"'))
@when(parsers.parse('the reviewer\'s resolution is submitted at "{instant}"'))
def submit_resolution(context: dict[str, Any], instant: str) -> None:
    supplied = context.pop("supplied", {})
    context.setdefault("resolutions", []).append(supplied)
    context["response"] = resolve_notice(
        context["store"],
        context["notice_id"],
        actor_id=context["reviewer"],
        resolved_at=parse_instant(instant),
        jurisdiction_timezone=context["jurisdiction_timezone"],
        carrier_rules_source=context["carrier_rules_source"],
        supplied=supplied,
    )


@given(parsers.re(r"^the response is (?P<value>\d+)$"))
@then(parsers.re(r"^the response is (?P<value>\d+)$"))
def check_response_status(context: dict[str, Any], value: str) -> None:
    assert context["response"].status == int(value)


@then(parsers.re(r"^the response identifies (?P<phrase>.*)$"))
def check_notice_relation(context: dict[str, Any], phrase: str) -> None:
    identified = context["response"].notice_id
    original = context["original"].notice_id
    if phrase == "the original notice":
        assert identified is not None
        assert identified == original
    elif phrase == "a new notice, not the original":
        assert identified is not None
        assert identified != original
    elif phrase == "no notice at all":
        assert identified is None
    else:
        raise ValueError(f"unrecognized notice relation: {phrase!r}")


@then(parsers.re(r"^the notice's state is (?P<value>.*)$"))
def check_state(context: dict[str, Any], value: str) -> None:
    assert context["response"].state == value


@then(parsers.re(r"^the notice's blockers are (?P<value>.*)$"))
def check_blockers(context: dict[str, Any], value: str) -> None:
    actual = [(b.code, b.field) for b in context["response"].blockers]
    assert actual == parse_compact_blockers(value)
