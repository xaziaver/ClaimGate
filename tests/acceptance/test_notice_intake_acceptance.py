"""Acceptance tests binding features/notice_intake.feature to the test API."""

from datetime import datetime
from typing import Any

from pytest_bdd import given, parsers, scenarios, then, when

from tests.api.notice_intake import NoticeFields, NoticeStore, get_notice, submit_notice

scenarios("../../features/notice_intake.feature")


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


@given(parsers.parse('"{carrier}" has no late reporting threshold configured'))
def clear_late_reporting_threshold(context: dict[str, Any], carrier: str) -> None:
    _rules_entry(context, carrier).pop("late_reporting_threshold_days", None)


@given(parsers.parse('"{carrier}" configures a recent policy inception threshold of {value:d} days'))
def set_recent_inception_threshold(context: dict[str, Any], carrier: str, value: int) -> None:
    _rules_entry(context, carrier)["recent_inception_threshold_days"] = value


@given(parsers.parse('"{carrier}" configures a duplicate match window of {value:d} days'))
def set_duplicate_match_window(context: dict[str, Any], carrier: str, value: int) -> None:
    _rules_entry(context, carrier)["window_days"] = value


@given(parsers.parse('the notice is submitted by carrier "{carrier_code}"'))
def set_carrier_code(context: dict[str, Any], carrier_code: str) -> None:
    context["carrier_code"] = carrier_code


@given(parsers.parse('the jurisdiction observes "{timezone_name}"'))
def set_jurisdiction_timezone(context: dict[str, Any], timezone_name: str) -> None:
    context["jurisdiction_timezone"] = timezone_name


@given(parsers.parse('the notice is submitted at "{submitted_at}"'))
def set_submitted_at(context: dict[str, Any], submitted_at: str) -> None:
    context["submitted_at"] = submitted_at


@given(parsers.parse('the notice reports a policy number of "{value}"'))
def set_policy_number(context: dict[str, Any], value: str) -> None:
    context["fields"]["policy_number"] = "" if value == "absent" else value


@given(parsers.parse('the notice reports a loss date of "{value}"'))
def set_loss_date(context: dict[str, Any], value: str) -> None:
    context["fields"]["loss_date"] = value


@given(parsers.parse('the notice reports a loss type of "{value}"'))
def set_loss_type(context: dict[str, Any], value: str) -> None:
    context["fields"]["loss_type"] = value


@given(parsers.parse('the notice reports a notice type of "{value}"'))
def set_notice_type(context: dict[str, Any], value: str) -> None:
    context["fields"]["notice_type"] = value


@when("the notice is submitted for intake")
def submit(context: dict[str, Any]) -> None:
    store = context.setdefault("store", NoticeStore())
    context["response"] = submit_notice(
        store,
        carrier_code=context["carrier_code"],
        submitted_at=_parse_instant(context["submitted_at"]),
        jurisdiction_timezone=context["jurisdiction_timezone"],
        carrier_rules_source=context["carrier_rules_source"],
        fields=NoticeFields(**context["fields"]),
    )


@then(parsers.re(r"^the response is (?P<value>\d+)$"))
def check_response_status(context: dict[str, Any], value: str) -> None:
    assert context["response"].status == int(value)


@then(parsers.re(r"^the notice's state is (?P<value>.*)$"))
def check_state(context: dict[str, Any], value: str) -> None:
    assert context["response"].state == value


@then(parsers.re(r"^the notice's blockers are (?P<value>.*)$"))
def check_blockers(context: dict[str, Any], value: str) -> None:
    expected = _parse_compact_blockers(value)
    actual = [(b.code, b.field) for b in context["response"].blockers]
    assert actual == expected


@then(parsers.re(r"^the notice's severity and queue are (?P<value>.*)$"))
def check_severity_and_queue(context: dict[str, Any], value: str) -> None:
    if value == "not yet assigned":
        assert context["response"].severity is None
        assert context["response"].queue is None
        return
    severity, queue = (part.strip() for part in value.split(","))
    assert context["response"].severity == severity
    assert context["response"].queue == queue


@then(parsers.re(r"^the notice can be retrieved afterward, showing state (?P<value>.*)$"))
def check_retrieval(context: dict[str, Any], value: str) -> None:
    notice_id = context["response"].notice_id
    assert notice_id is not None
    view = get_notice(context["store"], notice_id)
    assert view is not None
    assert view.state == value


@then(parsers.re(r"^the audit trail's (?P<ordinal>\w+) entry moves it to (?P<state>.*)$"))
def check_audit_entry_state(context: dict[str, Any], ordinal: str, state: str) -> None:
    index = {"first": 0, "second": 1}[ordinal]
    trail = context["store"].get_audit_trail(context["response"].notice_id)
    entry = trail[index]
    context["current_entry"] = entry
    assert entry.to_state == state


@then(parsers.re(r"^that entry is entered by (?P<actor>.*)$"))
def check_entry_actor(context: dict[str, Any], actor: str) -> None:
    assert context["current_entry"].actor_type == actor


@then(parsers.re(r"^that entry carries (?P<identity>.*)$"))
def check_entry_identity(context: dict[str, Any], identity: str) -> None:
    assert context["current_entry"].actor_id == identity


@then(parsers.re(r"^that entry's blockers are (?P<phrase>.*)$"))
def check_entry_blockers(context: dict[str, Any], phrase: str) -> None:
    entry = context["current_entry"]
    if phrase == "none yet, since no rule has run":
        assert entry.blockers == ()
    elif phrase == "the same ones the notice itself carries":
        assert entry.blockers == context["response"].blockers
    else:
        raise ValueError(f"unrecognized blockers phrase: {phrase!r}")


@then("the audit trail holds no entry beyond those two")
def check_audit_trail_length(context: dict[str, Any]) -> None:
    trail = context["store"].get_audit_trail(context["response"].notice_id)
    assert len(trail) == 2


@then(parsers.re(r"^intake (?P<value>.*)$"))
def check_notice_outcome(context: dict[str, Any], value: str) -> None:
    if value == "creates the notice":
        assert context["response"].notice_id is not None
    elif value == "creates no notice":
        assert context["response"].notice_id is None
    else:
        raise ValueError(f"unrecognized notice outcome: {value!r}")


@then(parsers.re(r"^a record of the submission (?P<value>.*)$"))
def check_record_outcome(context: dict[str, Any], value: str) -> None:
    store = context["store"]
    response = context["response"]
    if value == "is kept, and reachable through the notice":
        assert response.notice_id is not None
        assert get_notice(store, response.notice_id) is not None
    elif value == "is kept anyway, with a reference of its own":
        assert response.notice_id is None
        assert response.reference is not None
        assert len(store.payloads) == 1
    elif value == "is not kept":
        assert response.notice_id is None
        assert response.reference is None
        assert len(store.notices) == 0
        assert len(store.payloads) == 0
    else:
        raise ValueError(f"unrecognized record outcome: {value!r}")


def _parse_instant(raw: str) -> datetime:
    return datetime.fromisoformat(raw.replace("Z", "+00:00"))


def _parse_compact_blockers(value: str) -> list[tuple[str, str]]:
    value = value.strip()
    if not value:
        return []
    pairs: list[tuple[str, str]] = []
    for pair in value.split(";"):
        code, field = pair.split(":", 1)
        pairs.append((code, field))
    return pairs
