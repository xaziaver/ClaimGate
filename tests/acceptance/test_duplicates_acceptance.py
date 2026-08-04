"""Acceptance tests binding features/duplicates.feature to the test API."""

import ast
from datetime import date
from typing import Any

from pytest_bdd import given, parsers, scenarios, then, when

from tests.api.duplicates import ExistingClaimRecord, find_duplicates

scenarios("../../features/duplicates.feature")


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
        'and loss type "{loss_type}"'
    )
)
def set_candidate(
    context: dict[str, Any], policy_number: str, loss_date: str, loss_type: str
) -> None:
    context["candidate_fields"] = {
        "policy_number": policy_number,
        "loss_date": date.fromisoformat(loss_date),
        "loss_type": loss_type,
    }


@when("duplicate detection runs against the existing claims")
def run_find_duplicates(context: dict[str, Any]) -> None:
    existing_claims: list[ExistingClaimRecord] = context.get("existing_claims", [])
    context["matches"] = find_duplicates(
        existing_claims=existing_claims, **context["candidate_fields"]
    )


@then(parsers.parse("the probable duplicate claim ids in ascending order are {expected}"))
def check_matches(context: dict[str, Any], expected: str) -> None:
    assert context["matches"] == ast.literal_eval(expected)
