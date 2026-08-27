"""Unit tests for claimgate.domain.siu."""

import dataclasses
from datetime import date

import pytest

from claimgate.domain.models import Candidate
from claimgate.domain.siu import (
    NO_CONTINUOUS_COVERAGE_DATE,
    NO_JURISDICTION_DATE,
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
        BASE_CANDIDATE, loss_date=date(2026, 6, 15), continuous_coverage_date=inception_date
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
        BASE_CANDIDATE, loss_date=date(2026, 6, 15), continuous_coverage_date=None
    )

    indicators = compute_siu_indicators(
        candidate, TODAY, LATE_REPORTING_THRESHOLD_DAYS, RECENT_INCEPTION_THRESHOLD_DAYS
    )

    assert indicators.recent_policy_inception.value == "NOT_EVALUATED"
    assert indicators.recent_policy_inception.reason == NO_CONTINUOUS_COVERAGE_DATE


def test_recent_policy_inception_is_not_evaluated_when_no_threshold_configured() -> None:
    candidate = dataclasses.replace(
        BASE_CANDIDATE, loss_date=date(2026, 6, 15), continuous_coverage_date=date(2026, 6, 10)
    )

    indicators = compute_siu_indicators(candidate, TODAY, LATE_REPORTING_THRESHOLD_DAYS, None)

    assert indicators.recent_policy_inception.value == "NOT_EVALUATED"
    assert indicators.recent_policy_inception.reason == NO_THRESHOLD_CONFIGURED


def test_inception_date_after_loss_date_does_not_fire_indicator() -> None:
    candidate = dataclasses.replace(
        BASE_CANDIDATE, loss_date=date(2026, 6, 15), continuous_coverage_date=date(2026, 6, 20)
    )

    indicators = compute_siu_indicators(
        candidate, TODAY, LATE_REPORTING_THRESHOLD_DAYS, RECENT_INCEPTION_THRESHOLD_DAYS
    )

    assert indicators.recent_policy_inception.value == "FALSE"


def test_both_indicators_can_fire_together() -> None:
    candidate = Candidate(
        loss_date=date(2026, 6, 1),
        continuous_coverage_date=date(2026, 5, 20),
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


def test_no_jurisdiction_date_outranks_an_absent_threshold() -> None:
    # Precedence, ratified 2026-08-26: the reason names the gap that would still
    # block evaluation if the other were closed. A configured threshold cannot
    # help without a day to count to, so the two rows below name the missing
    # jurisdiction date whether or not a threshold exists - and the third row is
    # what keeps the first two from being a test of "whichever check ran first".
    with_threshold = compute_siu_indicators(
        BASE_CANDIDATE, None, LATE_REPORTING_THRESHOLD_DAYS, RECENT_INCEPTION_THRESHOLD_DAYS
    )
    without_threshold = compute_siu_indicators(
        BASE_CANDIDATE, None, None, RECENT_INCEPTION_THRESHOLD_DAYS
    )
    with_a_date = compute_siu_indicators(
        BASE_CANDIDATE, TODAY, None, RECENT_INCEPTION_THRESHOLD_DAYS
    )

    for indicators in (with_threshold, without_threshold):
        assert indicators.late_reporting.value == "NOT_EVALUATED"
        assert indicators.late_reporting.reason == NO_JURISDICTION_DATE
    assert with_a_date.late_reporting.reason == NO_THRESHOLD_CONFIGURED


def test_recent_policy_inception_needs_no_jurisdiction_date_at_all() -> None:
    # It measures loss date against coverage start, so the absent today that
    # stops late reporting has nothing to do with it. Without this the two
    # indicators could quietly become one rule with two names.
    candidate = dataclasses.replace(BASE_CANDIDATE, continuous_coverage_date=date(2026, 6, 1))

    indicators = compute_siu_indicators(
        candidate, None, LATE_REPORTING_THRESHOLD_DAYS, RECENT_INCEPTION_THRESHOLD_DAYS
    )

    assert indicators.recent_policy_inception.value == "TRUE"
    assert indicators.recent_policy_inception.reason is None


def test_an_indicator_evaluation_with_no_loss_date_raises() -> None:
    # Ratified 2026-08-27 (ASSUMPTIONS.md, "Item 5h, three decisions", decision
    # 3): no third NOT_EVALUATED reason, because the case is unreachable on the
    # designed path - evaluation runs only on a transition into TRIAGED and an
    # absent loss date pends the notice instead. Unreachable is exactly why it
    # is asserted here: nothing else in the suite can reach it, and a raise
    # nobody exercises is a raise nobody knows still fires.
    candidate = dataclasses.replace(BASE_CANDIDATE, loss_date=None)

    with pytest.raises(
        ValueError, match=r"^compute_siu_indicators: candidate states no loss date$"
    ):
        compute_siu_indicators(
            candidate, TODAY, LATE_REPORTING_THRESHOLD_DAYS, RECENT_INCEPTION_THRESHOLD_DAYS
        )
