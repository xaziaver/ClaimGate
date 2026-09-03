"""Acceptance tests binding features/coverage_verification.feature to the test API.

Every quoted date here goes through date.fromisoformat and nothing else. The
acceptance engine's marker mutation appends "_gauntlet" to a literal, and a step
that tolerated one - by defaulting, skipping, or parsing leniently - would let
that mutant survive. An unparseable date is a step error on purpose, and the
determination and reason strings are compared exactly for the same reason.
"""

from datetime import date
from typing import Any

from pytest_bdd import given, parsers, scenarios, then, when

from tests.api.coverage import (
    PolicyTerm,
    cancelled,
    determine_term_in_force,
    policy_term,
    reinstated,
    reinstated_retroactively,
    term_history,
    unobtained_term_history,
)

scenarios("../../features/coverage_verification.feature")


def _terms(context: dict[str, Any]) -> list[PolicyTerm]:
    terms: list[PolicyTerm] = context.setdefault("terms", [])
    return terms


@given(parsers.parse('a policy term effective "{effective}" and expiring "{expiration}"'))
def add_term(context: dict[str, Any], effective: str, expiration: str) -> None:
    _terms(context).append(
        policy_term(date.fromisoformat(effective), date.fromisoformat(expiration))
    )


# "the term" in the three status steps is the term most recently stated.
@given(parsers.parse('the term was cancelled effective "{effective}"'))
def cancel_term(context: dict[str, Any], effective: str) -> None:
    terms = _terms(context)
    terms[-1] = cancelled(terms[-1], date.fromisoformat(effective))


@given(parsers.parse('the term was reinstated effective "{effective}"'))
def reinstate_term(context: dict[str, Any], effective: str) -> None:
    terms = _terms(context)
    terms[-1] = reinstated(terms[-1], date.fromisoformat(effective))


@given(parsers.parse('the term was reinstated retroactively as of "{as_of}"'))
def reinstate_term_retroactively(context: dict[str, Any], as_of: str) -> None:
    terms = _terms(context)
    terms[-1] = reinstated_retroactively(terms[-1], date.fromisoformat(as_of))


@given(parsers.parse('the policy\'s term history could not be obtained, with reason "{reason}"'))
def set_history_unobtained(context: dict[str, Any], reason: str) -> None:
    context["term_history"] = unobtained_term_history(reason)


@when(parsers.parse('the in-force determination runs for a loss dated "{loss_date}"'))
def run_determination(context: dict[str, Any], loss_date: str) -> None:
    if "term_history" not in context:
        context["term_history"] = term_history(_terms(context))
    context["determination"] = determine_term_in_force(
        context["term_history"], date.fromisoformat(loss_date)
    )


@then(parsers.parse('the determination is "{value}"'))
def check_determination(context: dict[str, Any], value: str) -> None:
    assert context["determination"].value == value


@then(
    parsers.parse(
        'the determination cites the term effective "{effective}" and expiring "{expiration}"'
    )
)
def check_cited_term(context: dict[str, Any], effective: str, expiration: str) -> None:
    term = context["determination"].term
    assert term is not None
    assert (term.effective, term.expiration) == (
        date.fromisoformat(effective),
        date.fromisoformat(expiration),
    )


@then(parsers.parse('the determination cites the cancellation effective "{effective}"'))
def check_cited_cancellation(context: dict[str, Any], effective: str) -> None:
    assert context["determination"].cancellation_effective == date.fromisoformat(effective)


@then(parsers.parse('the determination reason is "{reason}"'))
def check_reason(context: dict[str, Any], reason: str) -> None:
    assert context["determination"].reason == reason
