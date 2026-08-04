"""Unit tests for claimgate.domain.duplicates."""

from datetime import date

import pytest

from claimgate.domain.duplicates import find_duplicates
from claimgate.domain.models import Candidate, ExistingClaim

EXISTING_CLAIM = ExistingClaim(
    claim_id="CLM-1001",
    policy_number="HO-1234567",
    loss_date=date(2026, 6, 1),
    loss_type="fire",
)


@pytest.mark.parametrize(
    ("policy_number", "loss_date", "loss_type", "expected_matches"),
    [
        ("HO-1234567", date(2026, 6, 1), "fire", ["CLM-1001"]),
        ("HO-1234567", date(2026, 6, 4), "fire", ["CLM-1001"]),
        ("HO-1234567", date(2026, 5, 29), "fire", ["CLM-1001"]),
        ("HO-1234567", date(2026, 6, 5), "fire", []),
        ("HO-1234567", date(2026, 5, 28), "fire", []),
        ("AU-7654321", date(2026, 6, 1), "fire", []),
        ("HO-1234567", date(2026, 6, 1), "water_damage", []),
    ],
)
def test_matching_against_a_single_existing_claim(
    policy_number: str, loss_date: date, loss_type: str, expected_matches: list[str]
) -> None:
    candidate = Candidate(policy_number=policy_number, loss_date=loss_date, loss_type=loss_type)

    matches = find_duplicates(candidate, [EXISTING_CLAIM])

    assert matches == expected_matches


def test_matches_are_returned_in_ascending_order_regardless_of_input_order() -> None:
    existing_claims = [
        ExistingClaim(
            claim_id="CLM-2002",
            policy_number="AU-7654321",
            loss_date=date(2026, 6, 11),
            loss_type="auto_collision",
        ),
        ExistingClaim(
            claim_id="CLM-2001",
            policy_number="AU-7654321",
            loss_date=date(2026, 6, 10),
            loss_type="auto_collision",
        ),
    ]
    candidate = Candidate(
        policy_number="AU-7654321", loss_date=date(2026, 6, 10), loss_type="auto_collision"
    )

    matches = find_duplicates(candidate, existing_claims)

    assert matches == ["CLM-2001", "CLM-2002"]
