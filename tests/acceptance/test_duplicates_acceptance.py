"""Acceptance tests binding features/duplicates.feature to the test API."""

from datetime import date
from typing import Any

from pytest_bdd import given, parsers, scenarios, then, when

from tests.api.duplicates import ExistingClaimRecord, find_duplicates

scenarios("../../features/duplicates.feature")

# features/duplicates.feature's locked 60-day window - a fixed value for this
# scenario suite, not parameterized via Gherkin text (see the spec comment
# under "A candidate match has the same policy, a loss date within 60 days,
# and the same loss type"). find_duplicates itself takes window_days with no
# default; this is the caller supplying it, same as any other test caller.
DUPLICATE_MATCH_WINDOW_DAYS = 60


@given(
    parsers.parse(
        'an existing claim "{claim_id}" with policy number "{policy_number}", '
        'loss date "{loss_date}", and loss type "{loss_type}"'
    )
)
def add_existing_claim(
    context: dict[str, Any],
    claim_id: str,
    policy_number: str,
    loss_date: str,
    loss_type: str,
) -> None:
    existing_claims: list[ExistingClaimRecord] = context.setdefault("existing_claims", [])
    existing_claims.append(
        ExistingClaimRecord(
            claim_id=claim_id,
            policy_number=policy_number,
            loss_date=date.fromisoformat(loss_date),
            loss_type=loss_type,
        )
    )


@given(
    parsers.parse(
        'a candidate with policy number "{policy_number}", loss date "{loss_date}", '
        'loss type "{loss_type}", and notice type "{notice_type}"'
    )
)
def set_candidate(
    context: dict[str, Any],
    policy_number: str,
    loss_date: str,
    loss_type: str,
    notice_type: str,
) -> None:
    context["candidate_fields"] = {
        "policy_number": policy_number,
        "loss_date": date.fromisoformat(loss_date),
        "loss_type": loss_type,
        "notice_type": notice_type,
    }


@when("duplicate detection runs against the existing claims")
def run_find_duplicates(context: dict[str, Any]) -> None:
    existing_claims: list[ExistingClaimRecord] = context.get("existing_claims", [])
    context["result"] = find_duplicates(
        existing_claims=existing_claims,
        window_days=DUPLICATE_MATCH_WINDOW_DAYS,
        **context["candidate_fields"],
    )


@then(parsers.re(r'^the candidate match is "(?P<expected>.*)"$'))
def check_single_candidate_match(context: dict[str, Any], expected: str) -> None:
    result = context["result"]
    assert result.value == "EVALUATED"
    assert result.matches == ((expected,) if expected else ())


@then(parsers.parse("the candidate matches are:"))
def check_candidate_matches_table(context: dict[str, Any], datatable: list[list[str]]) -> None:
    header, *rows = datatable
    assert header == ["claim_id"]
    expected = tuple(row[0] for row in rows)
    result = context["result"]
    assert result.value == "EVALUATED"
    assert result.matches == expected


@then(parsers.parse("duplicate matching is NOT_EVALUATED with reason {reason:w}"))
def check_not_evaluated_with_reason(context: dict[str, Any], reason: str) -> None:
    result = context["result"]
    assert result.value == "NOT_EVALUATED"
    assert result.reason == reason


@then("there are no candidate matches")
def check_no_candidate_matches(context: dict[str, Any]) -> None:
    assert context["result"].matches == ()
