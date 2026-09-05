"""Acceptance tests binding features/policy_identification.feature to the test API.

Every quoted value is bound with parsers.re and a `.*` capture, validation's
convention, because the spec states absence as "" and whitespace as "   " and a
parsers.parse field needs at least one character. pytest-bdd fullmatches every
pattern, so a literal the acceptance engine marks with "_gauntlet" outside its
quotes matches no step and that mutant dies at resolution - which is the only
place it can die, since a marked value never reaches an assertion. Arms, carried
identifiers and the blocker are compared exactly, never leniently, for the
Examples mutants that do reach one.
"""

from typing import Any

from pytest_bdd import given, parsers, scenarios, then, when

from tests.api.policy_identification import evaluate_identifier_sufficiency

scenarios("../../features/policy_identification.feature")


@given(parsers.re(r'the policy number is "(?P<value>.*)"'))
def set_policy_number(context: dict[str, Any], value: str) -> None:
    context["policy_number"] = value


@given(parsers.re(r'the insured name is "(?P<value>.*)"'))
def set_insured_name(context: dict[str, Any], value: str) -> None:
    context["insured_name"] = value


@given(parsers.re(r'the risk postal code is "(?P<value>.*)"'))
def set_risk_postal_code(context: dict[str, Any], value: str) -> None:
    context["risk_postal_code"] = value


@when("identifier sufficiency is evaluated")
def evaluate(context: dict[str, Any]) -> None:
    context["sufficiency"] = evaluate_identifier_sufficiency(
        context["policy_number"], context["insured_name"], context["risk_postal_code"]
    )


@then(parsers.re(r'the notice is searchable on "(?P<arms>.*)"'))
def check_searchable(context: dict[str, Any], arms: str) -> None:
    sufficiency = context["sufficiency"]
    assert sufficiency.value == "SEARCHABLE"
    assert sufficiency.blocker is None
    assert ";".join(sufficiency.arms) == arms


@then(parsers.re(r'the search carries policy number "(?P<value>.*)"'))
def check_policy_number_carried(context: dict[str, Any], value: str) -> None:
    assert context["sufficiency"].search.policy_number == value


@then(
    parsers.re(
        r'the search carries insured name "(?P<name>.*)" and risk postal code "(?P<postal>.*)"'
    )
)
def check_name_and_postal_code_carried(context: dict[str, Any], name: str, postal: str) -> None:
    search = context["sufficiency"].search
    assert search.insured_name == name
    assert search.risk_postal_code == postal


@then("the search carries no insured name and no risk postal code")
def check_no_name_or_postal_code(context: dict[str, Any]) -> None:
    search = context["sufficiency"].search
    assert search.insured_name is None
    assert search.risk_postal_code is None


@then("the search carries no policy number")
def check_no_policy_number(context: dict[str, Any]) -> None:
    assert context["sufficiency"].search.policy_number is None


@then(parsers.re(r'the identification blocker is "(?P<value>.*)"'))
def check_blocker(context: dict[str, Any], value: str) -> None:
    """The spec spells the blocker CODE:field;field - one code naming every
    absent field, which is not the CODE:field;CODE:field list three other specs
    spell with the same characters. How the blocker serializes onto a notice is
    item 7g's; this reads the domain's code and field tuple and nothing else."""
    sufficiency = context["sufficiency"]
    assert sufficiency.value == "INSUFFICIENT"
    assert sufficiency.arms == ()
    assert sufficiency.search is None
    blocker = sufficiency.blocker
    assert blocker is not None
    assert f"{blocker.code}:{';'.join(blocker.fields)}" == value
