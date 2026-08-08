"""Acceptance tests binding features/validation.feature to the test API."""

from datetime import date
from typing import Any

from pytest_bdd import given, parsers, scenarios, then, when

from tests.api.validation import reason_codes, validate_record

scenarios("../../features/validation.feature")


@given(parsers.parse('the loss date is "{value}"'))
def set_loss_date(context: dict[str, Any], value: str) -> None:
    context["fields"]["loss_date"] = date.fromisoformat(value)


@given(parsers.re(r'the policy number is "(?P<value>.*)"'))
def set_policy_number(context: dict[str, Any], value: str) -> None:
    context["fields"]["policy_number"] = value


@given(parsers.re(r'the loss type is "(?P<value>.*)"'))
def set_loss_type(context: dict[str, Any], value: str) -> None:
    context["fields"]["loss_type"] = value


@given(parsers.re(r'the notice type is "(?P<value>.*)"'))
def set_notice_type(context: dict[str, Any], value: str) -> None:
    context["fields"]["notice_type"] = value


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


@then(parsers.parse('the reason codes are "{value}"'))
def check_reason_codes(context: dict[str, Any], value: str) -> None:
    assert reason_codes(context["result"]) == value.split(";")


def _parse_compact_blockers(value: str) -> list[tuple[str, str]]:
    value = value.strip()
    if not value:
        return []
    pairs: list[tuple[str, str]] = []
    for pair in value.split(";"):
        code, field = pair.split(":", 1)
        pairs.append((code, field))
    return pairs
