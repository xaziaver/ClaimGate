"""Unit tests for claimgate.domain.siu."""

import dataclasses
from datetime import date

import pytest

from claimgate.domain.models import Candidate
from claimgate.domain.siu import compute_siu_flags

TODAY = date(2026, 8, 2)

BASE_CANDIDATE = Candidate(loss_date=date(2026, 6, 15))


@pytest.mark.parametrize(
    ("loss_date", "expected_late_reporting"),
    [
        (date(2026, 7, 3), False),
        (date(2026, 7, 2), True),
        (date(2026, 7, 28), False),
        (date(2026, 5, 4), True),
        (date(2025, 6, 28), True),
    ],
)
def test_late_reporting_threshold(loss_date: date, expected_late_reporting: bool) -> None:
    candidate = dataclasses.replace(BASE_CANDIDATE, loss_date=loss_date)

    flags = compute_siu_flags(candidate, now=TODAY)

    assert flags.late_reporting is expected_late_reporting


@pytest.mark.parametrize(
    ("inception_date", "expected_recent_inception"),
    [
        (date(2026, 6, 15), True),
        (date(2026, 5, 16), True),
        (date(2026, 5, 15), False),
        (date(2026, 6, 10), True),
        (date(2026, 3, 17), False),
    ],
)
def test_recent_policy_inception_threshold(
    inception_date: date, expected_recent_inception: bool
) -> None:
    candidate = dataclasses.replace(
        BASE_CANDIDATE, loss_date=date(2026, 6, 15), policy_inception_date=inception_date
    )

    flags = compute_siu_flags(candidate, now=TODAY)

    assert flags.recent_policy_inception is expected_recent_inception


def test_recent_policy_inception_is_false_when_no_inception_date_known() -> None:
    candidate = dataclasses.replace(
        BASE_CANDIDATE, loss_date=date(2026, 6, 15), policy_inception_date=None
    )

    flags = compute_siu_flags(candidate, now=TODAY)

    assert flags.recent_policy_inception is False


def test_both_indicators_can_fire_together() -> None:
    candidate = Candidate(
        loss_date=date(2026, 7, 1),
        policy_inception_date=date(2026, 6, 20),
    )

    flags = compute_siu_flags(candidate, now=TODAY)

    assert flags.late_reporting is True
    assert flags.recent_policy_inception is True
    assert {f.name for f in dataclasses.fields(flags)} == {
        "late_reporting",
        "recent_policy_inception",
    }
