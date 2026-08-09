"""Acceptance tests binding features/siu_indicators.feature to the test API."""

import dataclasses
from datetime import date
from typing import Any

from pytest_bdd import given, parsers, scenarios, then, when

from tests.api.siu import siu_indicators

scenarios("../../features/siu_indicators.feature")


@given(parsers.parse('the loss date is "{value}"'))
def set_loss_date(context: dict[str, Any], value: str) -> None:
    context["loss_date"] = date.fromisoformat(value)


@given(parsers.parse('the policy inception date is "{value}"'))
def set_policy_inception_date(context: dict[str, Any], value: str) -> None:
    context["policy_inception_date"] = date.fromisoformat(value)


@given("no policy inception date is known")
def clear_policy_inception_date(context: dict[str, Any]) -> None:
    context["policy_inception_date"] = None


@given("no late reporting threshold is configured")
def clear_late_reporting_threshold(context: dict[str, Any]) -> None:
    context["late_reporting_threshold_days"] = None


@when("SIU indicators are computed for the candidate FNOL record")
def run_compute_siu_indicators(context: dict[str, Any]) -> None:
    context["siu_indicators"] = siu_indicators(
        now=context["today"],
        loss_date=context["loss_date"],
        late_reporting_threshold_days=context.get("late_reporting_threshold_days"),
        recent_inception_threshold_days=context.get("recent_inception_threshold_days"),
        policy_inception_date=context.get("policy_inception_date"),
    )


@then(parsers.parse("the late reporting indicator is {expected:w} with reason {reason:w}"))
def check_late_reporting_indicator_with_reason(
    context: dict[str, Any], expected: str, reason: str
) -> None:
    result = context["siu_indicators"].late_reporting
    assert result.value == expected
    assert result.reason == reason


@then(
    parsers.parse("the recent policy inception indicator is {expected:w} with reason {reason:w}")
)
def check_recent_inception_indicator_with_reason(
    context: dict[str, Any], expected: str, reason: str
) -> None:
    result = context["siu_indicators"].recent_policy_inception
    assert result.value == expected
    assert result.reason == reason


@then("no other SIU indicator is present")
def check_no_other_indicator(context: dict[str, Any]) -> None:
    indicators = context["siu_indicators"]
    assert {f.name for f in dataclasses.fields(indicators)} == {
        "late_reporting",
        "recent_policy_inception",
    }
