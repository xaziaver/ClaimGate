"""Acceptance tests binding features/continuous_coverage.feature to the test API.

The term-history Givens this spec shares word for word with
features/coverage_verification.feature live in conftest.py; the horizon and
prior-carrier Givens, the When and the two Thens are this spec's own. Every
quoted date goes through date.fromisoformat and nothing else, and the value and
reason strings are compared exactly: the acceptance engine's marker mutation
appends "_gauntlet" to a literal, and a step that tolerated one - by defaulting,
skipping, or parsing leniently - would let that mutant survive.
"""

from datetime import date
from typing import Any

from pytest_bdd import given, parsers, scenarios, then, when

from tests.acceptance.support import policy_terms
from tests.api.coverage import derive_continuous_coverage, prior_coverage, term_history

scenarios("../../features/continuous_coverage.feature")


@given(parsers.parse('the source supplies history from "{value}" onward'))
def set_history_from(context: dict[str, Any], value: str) -> None:
    context["history_from"] = date.fromisoformat(value)


@given(
    parsers.parse(
        "the source records coverage on the risk by a prior carrier"
        ' effective "{effective}" and ending "{ending}"'
    )
)
def set_prior_coverage(context: dict[str, Any], effective: str, ending: str) -> None:
    context["prior_coverage"] = prior_coverage(
        date.fromisoformat(effective), date.fromisoformat(ending)
    )


@when(parsers.parse('the continuous-coverage derivation runs for a loss dated "{loss_date}"'))
def run_derivation(context: dict[str, Any], loss_date: str) -> None:
    if "term_history" not in context:
        context["term_history"] = term_history(
            policy_terms(context),
            history_from=context.get("history_from"),
            prior=context.get("prior_coverage"),
        )
    context["derivation"] = derive_continuous_coverage(
        context["term_history"], date.fromisoformat(loss_date)
    )


@then(parsers.parse('the continuous-coverage date is "{value}"'))
def check_date(context: dict[str, Any], value: str) -> None:
    derivation = context["derivation"]
    assert derivation.value == "DERIVED"
    assert derivation.reason is None
    assert derivation.continuous_since == date.fromisoformat(value)


@then(parsers.parse('the continuous-coverage derivation is "{value}" with reason "{reason}"'))
def check_not_evaluated(context: dict[str, Any], value: str, reason: str) -> None:
    derivation = context["derivation"]
    assert derivation.value == value
    assert derivation.reason == reason
    assert derivation.continuous_since is None
