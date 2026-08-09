"""Unit tests for claimgate.domain.siu."""

import dataclasses
from datetime import date

import pytest

from claimgate.domain.models import Candidate
from claimgate.domain.siu import (
    NO_POLICY_INCEPTION_DATE,
    NO_THRESHOLD_CONFIGURED,
    compute_siu_indicators,
)

TODAY = date(2026, 8, 2)
LATE_REPORTING_THRESHOLD_DAYS = 45
RECENT_INCEPTION_THRESHOLD_DAYS = 30

BASE_CANDIDATE = Candidate(loss_date=date(2026, 6, 15))


@pytest.mark.parametrize(
    ("loss_date", "expected_value"),
    [
        (date(2026, 7, 28), "FALSE"),
        (date(2026, 6, 18), "FALSE"),
        (date(2026, 6, 17), "TRUE"),
        (date(2026, 5, 4), "TRUE"),
        (date(2025, 6, 28), "TRUE"),
    ],
)
def test_late_reporting_threshold(loss_date: date, expected_value: str) -> None:
    candidate = dataclasses.replace(BASE_CANDIDATE, loss_date=loss_date)

    indicators = compute_siu_indicators(
        candidate, TODAY, LATE_REPORTING_THRESHOLD_DAYS, RECENT_INCEPTION_THRESHOLD_DAYS
    )

    assert indicators.late_reporting.value == expected_value
    assert indicators.late_reporting.reason is None


def test_late_reporting_is_not_evaluated_when_no_threshold_configured() -> None:
    candidate = dataclasses.replace(BASE_CANDIDATE, loss_date=date(2025, 1, 1))

    indicators = compute_siu_indicators(candidate, TODAY, None, RECENT_INCEPTION_THRESHOLD_DAYS)

    assert indicators.late_reporting.value == "NOT_EVALUATED"
    assert indicators.late_reporting.reason == NO_THRESHOLD_CONFIGURED


@pytest.mark.parametrize(
    ("inception_date", "expected_value"),
    [
        (date(2026, 6, 15), "TRUE"),
        (date(2026, 5, 16), "TRUE"),
        (date(2026, 5, 15), "FALSE"),
        (date(2026, 6, 10), "TRUE"),
        (date(2026, 3, 17), "FALSE"),
    ],
)
def test_recent_policy_inception_threshold(inception_date: date, expected_value: str) -> None:
    candidate = dataclasses.replace(
        BASE_CANDIDATE, loss_date=date(2026, 6, 15), policy_inception_date=inception_date
    )

    indicators = compute_siu_indicators(
        candidate, TODAY, LATE_REPORTING_THRESHOLD_DAYS, RECENT_INCEPTION_THRESHOLD_DAYS
    )

    assert indicators.recent_policy_inception.value == expected_value
    assert indicators.recent_policy_inception.reason is None


# Reverses the old test_recent_policy_inception_is_false_when_no_inception_date_known
# (previously lines 56-63 of this file), which asserted an absent inception date
# resolved to False. That was the exact behavior "unevaluated is not negative"
# (ASSUMPTIONS.md) forbids: absence of the required input must read as
# NOT_EVALUATED with a reason, never as a determination that happens to be False.
def test_recent_policy_inception_is_not_evaluated_when_no_inception_date_known() -> None:
    candidate = dataclasses.replace(
        BASE_CANDIDATE, loss_date=date(2026, 6, 15), policy_inception_date=None
    )

    indicators = compute_siu_indicators(
        candidate, TODAY, LATE_REPORTING_THRESHOLD_DAYS, RECENT_INCEPTION_THRESHOLD_DAYS
    )

    assert indicators.recent_policy_inception.value == "NOT_EVALUATED"
    assert indicators.recent_policy_inception.reason == NO_POLICY_INCEPTION_DATE


def test_recent_policy_inception_is_not_evaluated_when_no_threshold_configured() -> None:
    candidate = dataclasses.replace(
        BASE_CANDIDATE, loss_date=date(2026, 6, 15), policy_inception_date=date(2026, 6, 10)
    )

    indicators = compute_siu_indicators(candidate, TODAY, LATE_REPORTING_THRESHOLD_DAYS, None)

    assert indicators.recent_policy_inception.value == "NOT_EVALUATED"
    assert indicators.recent_policy_inception.reason == NO_THRESHOLD_CONFIGURED


def test_inception_date_after_loss_date_does_not_fire_indicator() -> None:
    candidate = dataclasses.replace(
        BASE_CANDIDATE, loss_date=date(2026, 6, 15), policy_inception_date=date(2026, 6, 20)
    )

    indicators = compute_siu_indicators(
        candidate, TODAY, LATE_REPORTING_THRESHOLD_DAYS, RECENT_INCEPTION_THRESHOLD_DAYS
    )

    assert indicators.recent_policy_inception.value == "FALSE"


def test_both_indicators_can_fire_together() -> None:
    candidate = Candidate(
        loss_date=date(2026, 6, 1),
        policy_inception_date=date(2026, 5, 20),
    )

    indicators = compute_siu_indicators(
        candidate, TODAY, LATE_REPORTING_THRESHOLD_DAYS, RECENT_INCEPTION_THRESHOLD_DAYS
    )

    assert indicators.late_reporting.value == "TRUE"
    assert indicators.recent_policy_inception.value == "TRUE"
    assert {f.name for f in dataclasses.fields(indicators)} == {
        "late_reporting",
        "recent_policy_inception",
    }
