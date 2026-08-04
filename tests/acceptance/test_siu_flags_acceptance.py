"""Acceptance tests binding features/siu_flags.feature to the test API."""

from datetime import date
from typing import Any

from pytest_bdd import given, parsers, scenarios, then, when

from tests.api.siu import siu_flags

scenarios("../../features/siu_flags.feature")


@given(parsers.parse('the loss date is "{value}"'))
def set_loss_date(context: dict[str, Any], value: str) -> None:
    context["loss_date"] = date.fromisoformat(value)


@given(parsers.parse('the policy inception date is "{value}"'))
def set_policy_inception_date(context: dict[str, Any], value: str) -> None:
    context["policy_inception_date"] = date.fromisoformat(value)


@when("SIU flags are computed for the candidate FNOL record")
def run_compute_siu_flags(context: dict[str, Any]) -> None:
    today: date = context["today"]
    context["siu_flags"] = siu_flags(
        now=today,
        loss_date=context["loss_date"],
        policy_inception_date=context.get("policy_inception_date"),
    )


@then(parsers.parse("the late reporting flag is {expected}"))
def check_late_reporting_flag(context: dict[str, Any], expected: str) -> None:
    flags = context["siu_flags"]
    assert flags.late_reporting is (expected == "true")


@then(parsers.parse("the recent policy inception flag is {expected}"))
def check_recent_inception_flag(context: dict[str, Any], expected: str) -> None:
    flags = context["siu_flags"]
    assert flags.recent_policy_inception is (expected == "true")


@then("no other SIU flag is present")
def check_no_other_flag(context: dict[str, Any]) -> None:
    flags = context["siu_flags"]
    assert set(vars(flags)) == {"late_reporting", "recent_policy_inception"}
