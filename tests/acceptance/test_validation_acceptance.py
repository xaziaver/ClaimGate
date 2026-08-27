"""Acceptance tests binding features/validation.feature to the test API."""

from datetime import date
from typing import Any

from pytest_bdd import given, parsers, scenarios, then, when

from tests.api.validation import reason_codes, validate_record

scenarios("../../features/validation.feature")

# The configuration reaches the domain as a boolean (ASSUMPTIONS.md, "A
# carrier configuration crosses into the domain already resolved") - parsing
# the Gherkin text into that boolean is exactly the caller's job the entry
# describes, so it happens here, above the boundary. "required"/"not
# required" is the spec's complete, closed vocabulary for this step; any
# other value is a caller contract violation and raises KeyError.
_REQUIRED_BY_TEXT = {"required": True, "not required": False}


@given(parsers.re(r'the loss date is "(?P<value>.*)"'))
def set_loss_date(context: dict[str, Any], value: str) -> None:
    """The token "absent" is how the spec states that a notice carries no loss
    date, and this step is bound with parsers.re like every other field step in
    this file so a token that is not a date can reach it at all. It is not a
    date spelled "absent": every other value is still handed to
    date.fromisoformat, so an unrecognized token is a step-definition error and
    never resolves to a default."""
    context["fields"]["loss_date"] = None if value == "absent" else date.fromisoformat(value)


@given(parsers.re(r'the policy number is "(?P<value>.*)"'))
def set_policy_number(context: dict[str, Any], value: str) -> None:
    context["fields"]["policy_number"] = value


@given(parsers.re(r'the loss type is "(?P<value>.*)"'))
def set_loss_type(context: dict[str, Any], value: str) -> None:
    context["fields"]["loss_type"] = value


@given(parsers.re(r'the notice type is "(?P<value>.*)"'))
def set_notice_type(context: dict[str, Any], value: str) -> None:
    context["fields"]["notice_type"] = value


@given(parsers.re(r'the claimant name is "(?P<value>.*)"'))
def set_claimant_name(context: dict[str, Any], value: str) -> None:
    context["fields"]["claimant_name"] = value


@given(parsers.re(r'the claimant contact is "(?P<value>.*)"'))
def set_claimant_contact(context: dict[str, Any], value: str) -> None:
    context["fields"]["claimant_contact"] = value


@given(parsers.re(r'the incident description is "(?P<value>.*)"'))
def set_incident_description(context: dict[str, Any], value: str) -> None:
    context["fields"]["incident_description"] = value


@given("no claimant details are provided")
def clear_claimant_details(context: dict[str, Any]) -> None:
    context["fields"].update(
        claimant_name=None,
        claimant_contact=None,
        incident_description=None,
    )


@given(parsers.parse('claimant name is "{value}" by configuration'))
def set_claimant_name_required(context: dict[str, Any], value: str) -> None:
    context["claimant_name_required"] = _REQUIRED_BY_TEXT[value]


@given(parsers.parse('claimant contact is "{value}" by configuration'))
def set_claimant_contact_required(context: dict[str, Any], value: str) -> None:
    context["claimant_contact_required"] = _REQUIRED_BY_TEXT[value]


@given(parsers.parse('the recognized policy-number prefixes are "{value}" by configuration'))
def set_recognized_policy_number_prefixes(context: dict[str, Any], value: str) -> None:
    context["recognized_policy_number_prefixes"] = frozenset(value.split(";"))


@when("the candidate FNOL record is validated")
def run_validation(context: dict[str, Any]) -> None:
    today: date = context["today"]
    context["result"] = validate_record(
        now=today,
        claimant_name_required=context["claimant_name_required"],
        claimant_contact_required=context["claimant_contact_required"],
        recognized_policy_number_prefixes=context["recognized_policy_number_prefixes"],
        **context["fields"],
    )


@then("there are no blockers")
def check_no_blockers(context: dict[str, Any]) -> None:
    assert context["result"].blockers == ()


@then(parsers.parse("the blockers are:"))
def check_blockers_table(context: dict[str, Any], datatable: list[list[str]]) -> None:
    header, *rows = datatable
    expected = [dict(zip(header, row, strict=True)) for row in rows]
    actual = [{"code": b.code, "field": b.field} for b in context["result"].blockers]
    assert actual == expected


@then(parsers.re(r"^the blockers are (?P<value>.*)$"))
def check_blockers_compact(context: dict[str, Any], value: str) -> None:
    expected = _parse_compact_blockers(value)
    actual = [(b.code, b.field) for b in context["result"].blockers]
    assert actual == expected


@then(parsers.re(r"^the future-dated-loss determination is (?P<value>.*)$"))
def check_future_dated_loss_determination(context: dict[str, Any], value: str) -> None:
    """The value half is compared case-insensitively and the reason half
    exactly, the same reading test_jurisdiction_selection_acceptance.py makes of
    the same column and for the reason recorded there: the acceptance engine
    substitutes an upper-case TRUE with a lower-case `true` and returns before
    it tries a sibling swap (docs/harness-findings.md, "The boolean substitution
    is lowercase and preemptive"), so an exact comparison would kill this
    outline's four TRUE/FALSE mutants without asking which value was
    determined. Folding the case widens nothing: TRUE, FALSE and NOT_EVALUATED
    are the whole enumeration and no two of them differ only in case."""
    determination = context["result"].future_dated_loss
    expected, _, reason = value.partition(":")
    assert determination.value == expected.strip().upper()
    assert determination.reason == (reason.strip() or None)


@then(parsers.parse('the reason codes are "{value}"'))
def check_reason_codes(context: dict[str, Any], value: str) -> None:
    expected = value.split(";") if value else []
    assert reason_codes(context["result"]) == expected


def _parse_compact_blockers(value: str) -> list[tuple[str, str]]:
    value = value.strip()
    if not value:
        return []
    pairs: list[tuple[str, str]] = []
    for pair in value.split(";"):
        code, field = pair.split(":", 1)
        pairs.append((code, field))
    return pairs
