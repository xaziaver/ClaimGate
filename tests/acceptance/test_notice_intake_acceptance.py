"""Acceptance tests binding features/notice_intake.feature to the test API.

The Background steps, the submission step, and the response-status and state
assertions this file used to own now live in conftest.py: item 5d's
features/idempotency.feature restates them verbatim and both specs are locked,
so sharing was the only way to keep the duplication gate green. The blockers
assertion joined them with item 5e's features/resolution.feature, the second
locked spec to state that phrase word for word. What stays here is what only
this spec asserts - severity and queue, retrieval, and the audit trail.
"""

from typing import Any

from pytest_bdd import parsers, scenarios, then

from tests.api.notice_intake import get_notice

scenarios("../../features/notice_intake.feature")


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
        assert len(store.list_payloads()) == 1
    elif value == "is not kept":
        assert response.notice_id is None
        assert response.reference is None
        assert store.count_notices() == 0
        assert len(store.list_payloads()) == 0
    else:
        raise ValueError(f"unrecognized record outcome: {value!r}")
