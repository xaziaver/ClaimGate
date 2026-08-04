"""Acceptance tests binding features/validation.feature to the test API."""

from datetime import date
from typing import Any

from pytest_bdd import given, parsers, scenarios, then, when

from tests.api.validation import validate_record

scenarios("../../features/validation.feature")


@given("the record is otherwise valid")
def set_baseline_fields(context: dict[str, Any]) -> None:
    context["fields"] = {
        "policy_number": "HO-1234567",
        "loss_date": date(2026, 7, 1),
        "loss_type": "fire",
    }


@given(parsers.parse('the loss date is "{value}"'))
def set_loss_date(context: dict[str, Any], value: str) -> None:
    context["fields"]["loss_date"] = date.fromisoformat(value)


@given(parsers.parse('the policy number is "{value}"'))
def set_policy_number(context: dict[str, Any], value: str) -> None:
    context["fields"]["policy_number"] = value


@given(parsers.parse('the loss type is "{value}"'))
def set_loss_type(context: dict[str, Any], value: str) -> None:
    context["fields"]["loss_type"] = value


@given(parsers.re(r'the injured party name is "(?P<value>.*)"'))
def set_injured_party_name(context: dict[str, Any], value: str) -> None:
    context["fields"]["injured_party_name"] = value


@given(parsers.re(r'the injured party contact is "(?P<value>.*)"'))
def set_injured_party_contact(context: dict[str, Any], value: str) -> None:
    context["fields"]["injured_party_contact"] = value


@given(parsers.re(r'the injury description is "(?P<value>.*)"'))
def set_injury_description(context: dict[str, Any], value: str) -> None:
    context["fields"]["injury_description"] = value


@given("no injured-party details are provided")
def clear_injured_party_details(context: dict[str, Any]) -> None:
    context["fields"].update(
        injured_party_name=None,
        injured_party_contact=None,
        injury_description=None,
    )


@when("the candidate FNOL record is validated")
def run_validation(context: dict[str, Any]) -> None:
    today: date = context["today"]
    context["result"] = validate_record(now=today, **context["fields"])


@then(parsers.parse('the validation result is "{expected}"'))
def check_validation_result(context: dict[str, Any], expected: str) -> None:
    result = context["result"]
    assert result.valid is (expected == "valid")


@then(parsers.parse('the missing field reported is "{expected}"'))
def check_missing_field(context: dict[str, Any], expected: str) -> None:
    result = context["result"]
    expected_field = None if expected == "none" else expected
    assert result.missing_field == expected_field
