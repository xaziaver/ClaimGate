"""Acceptance tests binding features/coverage_verification.feature to the test API.

The term-history Givens this spec shares word for word with
features/continuous_coverage.feature moved to conftest.py at item 7b; the When
and the Thens here are this spec's own. Every quoted date goes through
date.fromisoformat and nothing else. The acceptance engine's marker mutation
appends "_gauntlet" to a literal, and a step that tolerated one - by
defaulting, skipping, or parsing leniently - would let that mutant survive. An
unparseable date is a step error on purpose, and the determination and reason
strings are compared exactly for the same reason.
"""

from datetime import date
from typing import Any

from pytest_bdd import parsers, scenarios, then, when

from tests.acceptance.support import policy_terms
from tests.api.coverage import determine_term_in_force, term_history

scenarios("../../features/coverage_verification.feature")


@when(parsers.parse('the in-force determination runs for a loss dated "{loss_date}"'))
def run_determination(context: dict[str, Any], loss_date: str) -> None:
    if "term_history" not in context:
        context["term_history"] = term_history(policy_terms(context))
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
