"""Acceptance tests binding features/idempotency.feature to the test API.

Only the steps this spec alone states live here. Its Background is
features/notice_intake.feature's Background word for word, and the submission
and response-status steps are shared too - all of those are in conftest.py.

"the original" is the whole response of the submission the spec names as such,
not just its identifier: Rule 6's first submission is a schema refusal that
carries no notice_id at all, and the replay is still judged against it. The
three steps that name it moved to conftest.py when item 5e's
features/resolution.feature became the second locked spec to state them.
"""

from typing import Any

from pytest_bdd import parsers, scenarios, then

from tests.api.notice_intake import get_notice

scenarios("../../features/idempotency.feature")


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
