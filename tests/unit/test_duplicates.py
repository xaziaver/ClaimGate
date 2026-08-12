"""Unit tests for claimgate.domain.duplicates."""

from datetime import date

import pytest

from claimgate.domain.duplicates import (
    FOLLOW_ON_NOTICE_TYPE,
    NO_EXISTING_CLAIM_NOTICE_TYPE,
    find_duplicates,
)
from claimgate.domain.models import Candidate, ExistingClaim

WINDOW_DAYS = 60

EXISTING_CLAIM = ExistingClaim(
    claim_id="CLM-1001",
    policy_number="HO-1234567",
    loss_date=date(2026, 6, 1),
    loss_type="fire",
)


@pytest.mark.parametrize(
    ("policy_number", "loss_date", "loss_type", "expected_matches"),
    [
        ("HO-1234567", date(2026, 6, 1), "fire", ("CLM-1001",)),
        ("HO-1234567", date(2026, 7, 31), "fire", ("CLM-1001",)),
        ("HO-1234567", date(2026, 8, 1), "fire", ()),
        ("HO-1234567", date(2026, 4, 2), "fire", ("CLM-1001",)),
        ("HO-1234567", date(2026, 4, 1), "fire", ()),
        ("AU-7654321", date(2026, 6, 1), "fire", ()),
        ("HO-1234567", date(2026, 6, 1), "water_damage", ()),
    ],
)
def test_matching_against_a_single_existing_claim(
    policy_number: str, loss_date: date, loss_type: str, expected_matches: tuple[str, ...]
) -> None:
    candidate = Candidate(
        policy_number=policy_number,
        loss_date=loss_date,
        loss_type=loss_type,
        notice_type="INITIAL",
    )

    result = find_duplicates(candidate, [EXISTING_CLAIM], WINDOW_DAYS)

    assert result.value == "EVALUATED"
    assert result.matches == expected_matches
    assert result.reason is None


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
        policy_number="AU-7654321",
        loss_date=date(2026, 6, 10),
        loss_type="auto_collision",
        notice_type="INITIAL",
    )

    result = find_duplicates(candidate, existing_claims, WINDOW_DAYS)

    assert result.value == "EVALUATED"
    assert result.matches == ("CLM-2001", "CLM-2002")


@pytest.mark.parametrize("notice_type", ["SUPPLEMENTAL", "REOPENED"])
def test_a_follow_on_notice_type_is_not_evaluated(notice_type: str) -> None:
    candidate = Candidate(
        policy_number="HO-1234567",
        loss_date=date(2026, 6, 1),
        loss_type="fire",
        notice_type=notice_type,
    )

    result = find_duplicates(candidate, [EXISTING_CLAIM], WINDOW_DAYS)

    assert result.value == "NOT_EVALUATED"
    assert result.reason == FOLLOW_ON_NOTICE_TYPE
    assert result.matches == ()


def test_a_loss_assessment_notice_type_is_not_evaluated() -> None:
    candidate = Candidate(
        policy_number="HO-1234567",
        loss_date=date(2026, 6, 1),
        loss_type="fire",
        notice_type="LOSS_ASSESSMENT",
    )

    result = find_duplicates(candidate, [EXISTING_CLAIM], WINDOW_DAYS)

    assert result.value == "NOT_EVALUATED"
    assert result.reason == NO_EXISTING_CLAIM_NOTICE_TYPE
    assert result.matches == ()


def test_an_unrecognized_notice_type_raises() -> None:
    candidate = Candidate(
        policy_number="HO-1234567",
        loss_date=date(2026, 6, 1),
        loss_type="fire",
        notice_type="SUPPLEMENT",
    )

    with pytest.raises(
        ValueError, match=r"^find_duplicates: unrecognized notice_type 'SUPPLEMENT'$"
    ):
        find_duplicates(candidate, [EXISTING_CLAIM], WINDOW_DAYS)
