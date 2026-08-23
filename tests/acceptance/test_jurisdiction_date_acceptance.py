"""Acceptance tests binding features/jurisdiction_date.feature to the test API."""

from datetime import datetime
from typing import Any

from pytest_bdd import given, parsers, scenarios, then, when

from tests.api.jurisdiction import resolve_jurisdiction_date

scenarios("../../features/jurisdiction_date.feature")


@given(parsers.parse('the jurisdiction timezone is "{timezone}"'))
def set_jurisdiction_timezone(context: dict[str, Any], timezone: str) -> None:
    context["timezone"] = timezone


@when(parsers.parse("the instant {instant} is resolved to a calendar date"))
def run_resolve_with_context_timezone(context: dict[str, Any], instant: str) -> None:
    context["jurisdiction_date_result"] = resolve_jurisdiction_date(
        instant=datetime.fromisoformat(instant), timezone_name=context["timezone"]
    )


@when(
    parsers.re(
        r'the instant "(?P<instant>[^"]*)" is resolved to a calendar date in the jurisdiction '
        r"timezone (?P<timezone>\S+)"
    )
)
def run_resolve_with_given_timezone(context: dict[str, Any], instant: str, timezone: str) -> None:
    context["jurisdiction_date_result"] = resolve_jurisdiction_date(
        instant=datetime.fromisoformat(instant), timezone_name=timezone
    )


@then(parsers.parse("the resolved date is {resolved_date}"))
def check_resolved_date(context: dict[str, Any], resolved_date: str) -> None:
    result = context["jurisdiction_date_result"]
    assert result.value == "RESOLVED"
    assert str(result.resolved_date) == resolved_date


@then(parsers.parse("the result is {outcome}"))
def check_result(context: dict[str, Any], outcome: str) -> None:
    result = context["jurisdiction_date_result"]
    if result.value == "RESOLVED":
        assert str(result.resolved_date) == outcome
    else:
        assert result.reason == outcome
