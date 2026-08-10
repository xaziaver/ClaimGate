"""Shared fixtures and step definitions for acceptance tests."""

from datetime import date
from typing import Any

import pytest
from pytest_bdd import given, parsers, then

DEFAULT_TODAY = date(2026, 8, 2)


@pytest.fixture
def context() -> dict[str, Any]:
    return {"today": DEFAULT_TODAY, "fields": {}}


@given(parsers.parse('today is "{value}"'))
def set_today(context: dict[str, Any], value: str) -> None:
    context["today"] = date.fromisoformat(value)


# Shared with siu_indicators.feature and triage.feature - both set thresholds
# with this exact step text (triage.feature's end-to-end scenario supplies the
# same thresholds it hands to compute_siu_indicators via the SIU test API).
@given(parsers.parse("the late reporting threshold is {value:d} days"))
def set_late_reporting_threshold(context: dict[str, Any], value: int) -> None:
    context["late_reporting_threshold_days"] = value


@given(parsers.parse("the recent policy inception threshold is {value:d} days"))
def set_recent_inception_threshold(context: dict[str, Any], value: int) -> None:
    context["recent_inception_threshold_days"] = value


# Bare form only (no reason code) - shared by triage.feature and the
# non-NOT_EVALUATED assertions in siu_indicators.feature. The "with reason"
# form stays local to the siu acceptance test file since only that spec
# asserts reason codes.
@then(parsers.parse("the late reporting indicator is {expected:w}"))
def check_late_reporting_indicator(context: dict[str, Any], expected: str) -> None:
    assert context["siu_indicators"].late_reporting.value == expected


@then(parsers.parse("the recent policy inception indicator is {expected:w}"))
def check_recent_inception_indicator(context: dict[str, Any], expected: str) -> None:
    assert context["siu_indicators"].recent_policy_inception.value == expected
