"""Unit tests for claimgate.domain.triage."""

from datetime import date
from decimal import Decimal

import pytest

from claimgate.domain.models import Candidate
from claimgate.domain.triage import assign_severity, route_queue, triage_and_route


@pytest.mark.parametrize(
    ("loss_type", "expected_severity"),
    [
        ("injury", "high"),
        ("fire", "high"),
        ("water_damage", "standard"),
        ("wind_hail", "standard"),
        ("vandalism", "standard"),
        ("liability", "standard"),
        ("auto_collision", "standard"),
        ("auto_comprehensive", "standard"),
    ],
)
def test_severity_by_loss_type(loss_type: str, expected_severity: str) -> None:
    assert assign_severity(loss_type, loss_amount=None) == expected_severity


@pytest.mark.parametrize(
    ("loss_amount", "expected_severity"),
    [
        (Decimal("499.99"), "low"),
        (Decimal("500.00"), "standard"),
        (Decimal("500.01"), "standard"),
    ],
)
def test_theft_severity_by_loss_amount(loss_amount: Decimal, expected_severity: str) -> None:
    assert assign_severity("theft", loss_amount) == expected_severity


def test_non_theft_loss_under_theft_threshold_is_not_low_severity() -> None:
    assert assign_severity("water_damage", Decimal("400.00")) == "standard"


@pytest.mark.parametrize(
    ("severity", "expected_queue"),
    [
        ("low", "fast_track"),
        ("standard", "standard"),
        ("high", "complex"),
    ],
)
def test_queue_routing(severity: str, expected_queue: str) -> None:
    assert route_queue(severity) == expected_queue


@pytest.mark.parametrize(
    (
        "loss_type",
        "loss_amount",
        "loss_date",
        "inception_date",
        "expected_severity",
        "expected_queue",
    ),
    [
        ("theft", Decimal("400.00"), date(2026, 8, 1), date(2024, 1, 1), "low", "fast_track"),
        ("theft", Decimal("400.00"), date(2026, 6, 15), date(2024, 1, 1), "low", "fast_track"),
        ("fire", Decimal("50000"), date(2026, 8, 1), date(2024, 1, 1), "high", "complex"),
        ("fire", Decimal("50000"), date(2026, 8, 1), date(2026, 7, 20), "high", "complex"),
        ("fire", Decimal("50000"), date(2026, 6, 1), date(2026, 5, 15), "high", "complex"),
        ("water_damage", Decimal("400.00"), date(2026, 8, 1), date(2024, 1, 1), "standard", "standard"),
        ("water_damage", Decimal("400.00"), date(2026, 6, 1), date(2026, 5, 15), "standard", "standard"),
    ],
)
def test_triage_and_route_end_to_end(
    loss_type: str,
    loss_amount: Decimal,
    loss_date: date,
    inception_date: date,
    expected_severity: str,
    expected_queue: str,
) -> None:
    candidate = Candidate(
        loss_type=loss_type,
        loss_amount=loss_amount,
        loss_date=loss_date,
        policy_inception_date=inception_date,
    )

    outcome = triage_and_route(candidate)

    assert outcome.severity == expected_severity
    assert outcome.queue == expected_queue
