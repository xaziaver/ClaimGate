"""Acceptance tests binding features/triage.feature to the test API."""

from datetime import date
from decimal import Decimal
from typing import Any

from pytest_bdd import given, parsers, scenarios, then, when

from tests.api.siu import siu_indicators
from tests.api.triage import assign_severity, route_queue, triage_and_route

scenarios("../../features/triage.feature")


@given(parsers.parse('the loss type is "{value}"'))
def set_loss_type(context: dict[str, Any], value: str) -> None:
    context["loss_type"] = value


@when("the candidate FNOL record is triaged")
def run_triage(context: dict[str, Any]) -> None:
    context["severity"] = assign_severity(context["loss_type"])


@then(parsers.parse('the assigned severity is "{expected}"'))
def check_severity(context: dict[str, Any], expected: str) -> None:
    assert context["severity"] == expected


@given(parsers.parse('the assigned severity is "{value}"'))
def set_assigned_severity(context: dict[str, Any], value: str) -> None:
    context["severity"] = value


@when("the candidate FNOL record is routed to a queue")
def run_route_queue(context: dict[str, Any]) -> None:
    context["queue"] = route_queue(context["severity"])


@then(parsers.parse('the routed queue is "{expected}"'))
def check_queue(context: dict[str, Any], expected: str) -> None:
    assert context["queue"] == expected


@given(
    parsers.re(
        r'a candidate with loss type "(?P<loss_type>[^"]*)", loss amount (?P<loss_amount>\S+), '
        r'loss date "(?P<loss_date>[^"]*)", and continuous coverage date "(?P<coverage_start>[^"]*)"'
    )
)
def set_end_to_end_candidate(
    context: dict[str, Any],
    loss_type: str,
    loss_amount: str,
    loss_date: str,
    coverage_start: str,
) -> None:
    context["candidate_fields"] = {
        "loss_type": loss_type,
        "loss_amount": Decimal(loss_amount),
        "loss_date": date.fromisoformat(loss_date),
        "continuous_coverage_date": date.fromisoformat(coverage_start) if coverage_start else None,
    }


@when("the candidate FNOL record is triaged and routed")
def run_triage_and_route(context: dict[str, Any]) -> None:
    fields = context["candidate_fields"]
    outcome = triage_and_route(**fields)
    context["severity"] = outcome.severity
    context["queue"] = outcome.queue

    context["siu_indicators"] = siu_indicators(
        now=context["today"],
        loss_date=fields["loss_date"],
        late_reporting_threshold_days=context.get("late_reporting_threshold_days"),
        recent_inception_threshold_days=context.get("recent_inception_threshold_days"),
        continuous_coverage_date=fields["continuous_coverage_date"],
    )
