"""Unit tests for claimgate.domain.validation."""

import dataclasses
from datetime import date

import pytest

from claimgate.domain.models import Candidate
from claimgate.domain.validation import validate

TODAY = date(2026, 8, 2)

BASE_CANDIDATE = Candidate(
    policy_number="HO-1234567",
    loss_date=date(2026, 7, 1),
    loss_type="fire",
)


@pytest.mark.parametrize(
    ("loss_date", "expected_valid"),
    [
        (date(2026, 8, 3), False),
        (date(2026, 8, 2), True),
        (date(2026, 8, 1), True),
        (date(2025, 8, 2), True),
        (date(2025, 8, 1), False),
    ],
)
def test_loss_date_window(loss_date: date, expected_valid: bool) -> None:
    candidate = dataclasses.replace(BASE_CANDIDATE, loss_date=loss_date)

    result = validate(candidate, now=TODAY)

    assert result.valid is expected_valid


@pytest.mark.parametrize(
    ("policy_number", "expected_valid"),
    [
        ("HO-1234567", True),
        ("AU-1234567", True),
        ("CP-1234567", True),
        ("CA-1234567", True),
        ("GL-1234567", True),
        ("XX-1234567", False),
        ("HO-123456", False),
        ("HO-12345678", False),
        ("ho-1234567", False),
        ("HO1234567", False),
        ("HO-ABCDEFG", False),
    ],
)
def test_policy_number_format(policy_number: str, expected_valid: bool) -> None:
    candidate = dataclasses.replace(BASE_CANDIDATE, policy_number=policy_number)

    result = validate(candidate, now=TODAY)

    assert result.valid is expected_valid


@pytest.mark.parametrize(
    ("name", "contact", "description", "expected_valid", "expected_missing_field"),
    [
        ("Jane Doe", "555-0100", "Twisted ankle, wet floor", True, None),
        ("", "555-0100", "Twisted ankle, wet floor", False, "injured_party_name"),
        ("Jane Doe", "", "Twisted ankle, wet floor", False, "injured_party_contact"),
        ("Jane Doe", "555-0100", "", False, "injury_description"),
    ],
)
def test_injury_required_fields(
    name: str,
    contact: str,
    description: str,
    expected_valid: bool,
    expected_missing_field: str | None,
) -> None:
    candidate = dataclasses.replace(
        BASE_CANDIDATE,
        loss_type="injury",
        injured_party_name=name,
        injured_party_contact=contact,
        injury_description=description,
    )

    result = validate(candidate, now=TODAY)

    assert result.valid is expected_valid
    assert result.missing_field == expected_missing_field


def test_non_injury_loss_does_not_require_injured_party_details() -> None:
    candidate = dataclasses.replace(BASE_CANDIDATE, loss_type="fire")

    result = validate(candidate, now=TODAY)

    assert result.valid is True
