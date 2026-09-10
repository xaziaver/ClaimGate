"""Acceptance tests binding features/duplicate_evaluation.feature to the test API.

The Background is policy_match.feature's, word for word, so every step in it is
conftest.py's, as are the submission, the resolution, the state as a Given and
a Then, the response status, the policy match and the identified-on reader.
What lives here is the claims side of the carrier's one core-system stand-in -
the claims it holds on a policy, and the claims-only fault - and the evaluation
the notice shows afterward on GET /notices/{id}, read from the notice and never
from a response, one structure: status, candidates, reason.

The value steps are anchored regular expressions, as policy_match.feature's are,
so a NOT_EVALUATED cell cannot match an OBTAINED parser by prefix, and every
cell is compared whole: the acceptance engine's marker mutation appends
"_gauntlet" to a literal, and a step that tolerated one would let that mutant
survive. The candidates cell is `none` or a comma-separated list of claim ids,
compared in order - the same tuple of ids tests/api/duplicates.py returns.
"""

from datetime import date
from typing import Any

from pytest_bdd import given, parsers, scenarios, then

from tests.api.policy_match import DuplicateEvaluationView, duplicate_evaluation

scenarios("../../features/duplicate_evaluation.feature")


@given(
    parsers.re(
        r'^"(?P<carrier>[^"]+)"\'s claims source holds claim "(?P<claim_id>[^"]+)"'
        r' on policy "(?P<reference>[^"]+)" with loss date "(?P<loss_date>[^"]+)"'
        r' and loss type "(?P<loss_type>[^"]+)"$'
    )
)
def hold_claim(
    context: dict[str, Any], carrier: str, claim_id: str, reference: str, loss_date: str,
    loss_type: str,
) -> None:
    context["policy_sources"].hold_claim(
        carrier, reference, claim_id, date.fromisoformat(loss_date), loss_type
    )


@given(parsers.parse('"{carrier}"\'s claims source is unavailable'))
def set_claims_unavailable(context: dict[str, Any], carrier: str) -> None:
    context["policy_sources"].claims_unavailable(carrier)


@then(parsers.re(r"^the duplicate evaluation is (?P<value>.*)$"))
def check_status(context: dict[str, Any], value: str) -> None:
    assert _evaluation(context).status == value


@then(parsers.re(r"^the duplicate candidates are (?P<value>.*)$"))
def check_candidates(context: dict[str, Any], value: str) -> None:
    expected = () if value == "none" else tuple(part.strip() for part in value.split(","))
    assert _evaluation(context).candidates == expected


@then(parsers.re(r"^the duplicate evaluation's reason is (?P<value>.*)$"))
def check_reason(context: dict[str, Any], value: str) -> None:
    assert _evaluation(context).reason == (None if value == "none" else value)


@given("the notice has no duplicate evaluation")
@then("the notice has no duplicate evaluation")
def check_no_evaluation(context: dict[str, Any]) -> None:
    # The reader raises for a notice nobody has, so None here is a notice
    # that exists and has not been triaged - not an absent notice.
    assert duplicate_evaluation(context["store"], context["notice_id"]) is None


def _evaluation(context: dict[str, Any]) -> DuplicateEvaluationView:
    shown = duplicate_evaluation(context["store"], context["notice_id"])
    assert shown is not None
    return shown
