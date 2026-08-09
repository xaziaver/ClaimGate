"""Acceptance tests binding features/triage.feature to the test API."""

from datetime import date
from decimal import Decimal
from typing import Any

from pytest_bdd import given, parsers, scenarios, then, when

from tests.api.siu import siu_flags
from tests.api.triage import assign_severity, route_queue, triage_and_route

scenarios("../../features/triage.feature")


@given(parsers.parse('the loss type is "{value}"'))
def set_loss_type(context: dict[str, Any], value: str) -> None:
    context["loss_type"] = value


@given(parsers.parse("the loss amount is {value}"))
def set_loss_amount(context: dict[str, Any], value: str) -> None:
    context["loss_amount"] = Decimal(value)


@when("the candidate FNOL record is triaged")
def run_triage(context: dict[str, Any]) -> None:
    context["severity"] = assign_severity(context["loss_type"], context.get("loss_amount"))


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
    parsers.parse(
        'a candidate with loss type "{loss_type}", loss amount {loss_amount}, '
        'loss date "{loss_date}", and policy inception date "{inception_date}"'
    )
)
def set_end_to_end_candidate(
    context: dict[str, Any],
    loss_type: str,
    loss_amount: str,
    loss_date: str,
    inception_date: str,
) -> None:
    context["candidate_fields"] = {
        "loss_type": loss_type,
        "loss_amount": Decimal(loss_amount),
        "loss_date": date.fromisoformat(loss_date),
        "policy_inception_date": date.fromisoformat(inception_date),
    }


@when("the candidate FNOL record is triaged and routed")
def run_triage_and_route(context: dict[str, Any]) -> None:
    fields = context["candidate_fields"]
    outcome = triage_and_route(**fields)
    context["severity"] = outcome.severity
    context["queue"] = outcome.queue

    flags = siu_flags(
        now=context["today"],
        loss_date=fields["loss_date"],
        policy_inception_date=fields["policy_inception_date"],
    )
    context["late_reporting"] = flags.late_reporting
    context["recent_inception"] = flags.recent_policy_inception


@then(parsers.parse("the late reporting SIU flag is {expected}"))
def check_late_reporting_flag(context: dict[str, Any], expected: str) -> None:
    assert context["late_reporting"] is (expected == "true")


@then(parsers.parse("the recent policy inception SIU flag is {expected}"))
def check_recent_inception_flag(context: dict[str, Any], expected: str) -> None:
    assert context["recent_inception"] is (expected == "true")
