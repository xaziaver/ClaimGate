"""Acceptance tests binding features/idempotency.feature to the test API.

Only the steps this spec alone states live here. Its Background is
features/notice_intake.feature's Background word for word, and the submission
and response-status steps are shared too - all of those are in conftest.py.

"the original" is the whole response of the submission the spec names as such,
not just its identifier: Rule 6's first submission is a schema refusal that
carries no notice_id at all, and the replay is still judged against it.
"""

from typing import Any

from pytest_bdd import given, parsers, scenarios, then, when

from tests.api.notice_intake import get_notice

scenarios("../../features/idempotency.feature")


@given(parsers.parse('the notice is submitted with the idempotency key "{value}"'))
@when(parsers.parse('the notice is submitted with the idempotency key "{value}"'))
def set_idempotency_key(context: dict[str, Any], value: str) -> None:
    # "absent" is the same cell convention notice_intake.feature already uses
    # for a policy number that was never supplied.
    context["idempotency_key"] = None if value == "absent" else value


@given("that submission is remembered as the original")
def remember_the_original(context: dict[str, Any]) -> None:
    context["original"] = context["response"]


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


@then(parsers.re(r"^the response reports (?P<phrase>.*)$"))
def check_timestamp_relation(context: dict[str, Any], phrase: str) -> None:
    reported = context["response"].received_at
    original = context["original"].received_at
    if phrase == "the original receipt timestamp":
        assert reported == original
    elif phrase == "its own new receipt timestamp":
        assert reported == context["submitted_at"]
        assert reported != original
    else:
        raise ValueError(f"unrecognized timestamp relation: {phrase!r}")


@then("the original notice's audit trail still holds exactly its two entries")
def check_original_trail_unchanged(context: dict[str, Any]) -> None:
    trail = context["store"].get_audit_trail(context["original"].notice_id)
    assert len(trail) == 2


@then(parsers.re(r"^the original notice can still be retrieved, showing state (?P<value>.*)$"))
def check_original_still_retrievable(context: dict[str, Any], value: str) -> None:
    view = get_notice(context["store"], context["original"].notice_id)
    assert view is not None
    assert view.state == value
