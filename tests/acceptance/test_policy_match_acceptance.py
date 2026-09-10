"""Acceptance tests binding features/policy_match.feature to the test API.

The Background is the intake Background five locked specs share, plus the two
steps that give the carrier's policy source a policy to find - conftest.py's
since item 7h, when features/duplicate_evaluation.feature restated them, with
the match and identified-on readers the two specs also share; the submission,
the response status, the state and the blockers are conftest.py's too. What
lives here is the rest of the source's shapes and the verification's other
attributes, read from GET /notices/{id} through support.py and never from the
response: the search's answer is an attribute of the notice for whoever opens
it, which is the spec's own claim.

Every quoted date goes through date.fromisoformat and every reference is
compared whole, for the reason conftest.py's term-history steps give: the
acceptance engine's marker mutation appends "_gauntlet" to a literal, and a step
that tolerated one would let that mutant survive. The recent policy inception
indicator step is conftest.py's, shared with features/siu_separation.feature,
which states it in the same words.
"""

from datetime import date
from typing import Any

from pytest_bdd import given, parsers, scenarios, then

from tests.acceptance.support import parse_instant, verification

scenarios("../../features/policy_match.feature")


@given(
    parsers.parse(
        'that policy\'s only term is effective "{effective}" and expiring "{expiration}"'
    )
)
def set_only_term(context: dict[str, Any], effective: str, expiration: str) -> None:
    context["policy_sources"].set_only_term(
        date.fromisoformat(effective), date.fromisoformat(expiration)
    )


@given(parsers.parse('"{carrier}"\'s policy source searches by policy number only'))
def search_by_number_only(context: dict[str, Any], carrier: str) -> None:
    context["policy_sources"].search_by_number_only(carrier)


@given(parsers.parse('"{carrier}"\'s policy source answers as before'))
def source_answers_as_before(context: dict[str, Any], carrier: str) -> None:
    """The row that leaves the source as the Background stood it up. Its
    sibling row faults the source; this one says, in the spec's words, that
    nothing changed between the intake search and the re-search."""


@then(parsers.re(r"^the matched policy is (?P<value>.*)$"))
def check_matched_policy(context: dict[str, Any], value: str) -> None:
    # The cell quotes a reference or says none; anything else is a spelling this
    # step does not know, not a reference to compare.
    if value == "none":
        assert verification(context).matched_policy is None
    elif len(value) > 2 and value[0] == value[-1] == '"':
        assert verification(context).matched_policy == value[1:-1]
    else:
        raise ValueError(f"unrecognized matched policy: {value!r}")


@then(parsers.re(r"^the verification's reason is (?P<value>.*)$"))
def check_reason(context: dict[str, Any], value: str) -> None:
    assert verification(context).reason == value


@then(parsers.re(r"^the term in force at the loss date is (?P<value>.*)$"))
def check_term_in_force(context: dict[str, Any], value: str) -> None:
    assert verification(context).term_in_force == value


@then(parsers.parse('the deciding term is effective "{effective}" and expiring "{expiration}"'))
def check_deciding_term(context: dict[str, Any], effective: str, expiration: str) -> None:
    shown = verification(context)
    assert shown.deciding_term_effective == date.fromisoformat(effective)
    assert shown.deciding_term_expiration == date.fromisoformat(expiration)


@then(parsers.parse('the coverage verification is as of "{instant}"'))
def check_as_of(context: dict[str, Any], instant: str) -> None:
    assert verification(context).as_of == parse_instant(instant)


@then(parsers.parse('the notice\'s continuous coverage date is "{value}"'))
def check_continuous_coverage_date(context: dict[str, Any], value: str) -> None:
    assert verification(context).continuous_coverage_date == date.fromisoformat(value)


@then("the notice has no continuous coverage date")
def check_no_continuous_coverage_date(context: dict[str, Any]) -> None:
    shown = verification(context)
    # Absent with a reason, never absent alone: a date that was not derived is
    # a not-evaluated result, and the view says why.
    assert shown.continuous_coverage_date is None
    assert shown.continuous_coverage_reason is not None


@then(parsers.re(r"^the continuous coverage reason is (?P<value>.*)$"))
def check_continuous_coverage_reason(context: dict[str, Any], value: str) -> None:
    # The derivation's own reason, from continuous_coverage.feature's closed
    # enumeration; compared exactly, as every reason code in these files is.
    assert verification(context).continuous_coverage_reason == value
