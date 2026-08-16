"""Unit tests for claimgate.domain.validation."""

import dataclasses
from datetime import date

import pytest

from claimgate.domain.models import Candidate, ValidationBlocker
from claimgate.domain.validation import (
    LOSS_DATE_IN_FUTURE,
    LOSS_TYPE_UNRECOGNIZED,
    MISSING_REQUIRED_FIELD,
    NOTICE_TYPE_UNRECOGNIZED,
    POLICY_NUMBER_MALFORMED,
    validate,
)

TODAY = date(2026, 8, 2)

BASE_CANDIDATE = Candidate(
    policy_number="HO-1234567",
    loss_date=date(2026, 7, 1),
    loss_type="wind_hail",
    notice_type="INITIAL",
)


@pytest.mark.parametrize(
    ("loss_date", "expected_blockers"),
    [
        (date(2027, 6, 1), (ValidationBlocker(LOSS_DATE_IN_FUTURE, "loss_date"),)),
        (date(2026, 8, 3), (ValidationBlocker(LOSS_DATE_IN_FUTURE, "loss_date"),)),
        (date(2026, 8, 2), ()),
        (date(2026, 8, 1), ()),
        (date(2022, 9, 28), ()),
    ],
)
def test_loss_date_must_not_be_in_the_future(
    loss_date: date, expected_blockers: tuple[ValidationBlocker, ...]
) -> None:
    candidate = dataclasses.replace(BASE_CANDIDATE, loss_date=loss_date)

    result = validate(candidate, now=TODAY)

    assert result.blockers == expected_blockers
    assert result.valid is (not expected_blockers)


@pytest.mark.parametrize(
    ("policy_number", "expected_blockers"),
    [
        ("HO-1234567", ()),
        ("AU-1234567", (ValidationBlocker(POLICY_NUMBER_MALFORMED, "policy_number"),)),
        ("CP-1234567", (ValidationBlocker(POLICY_NUMBER_MALFORMED, "policy_number"),)),
        ("CA-1234567", (ValidationBlocker(POLICY_NUMBER_MALFORMED, "policy_number"),)),
        ("GL-1234567", (ValidationBlocker(POLICY_NUMBER_MALFORMED, "policy_number"),)),
        ("XX-1234567", (ValidationBlocker(POLICY_NUMBER_MALFORMED, "policy_number"),)),
        ("HO-123456", (ValidationBlocker(POLICY_NUMBER_MALFORMED, "policy_number"),)),
        ("HO-12345678", (ValidationBlocker(POLICY_NUMBER_MALFORMED, "policy_number"),)),
        ("ho-1234567", (ValidationBlocker(POLICY_NUMBER_MALFORMED, "policy_number"),)),
        ("HO1234567", (ValidationBlocker(POLICY_NUMBER_MALFORMED, "policy_number"),)),
        ("HO-ABCDEFG", (ValidationBlocker(POLICY_NUMBER_MALFORMED, "policy_number"),)),
        ("", (ValidationBlocker(MISSING_REQUIRED_FIELD, "policy_number"),)),
        ("   ", (ValidationBlocker(MISSING_REQUIRED_FIELD, "policy_number"),)),
    ],
)
def test_policy_number_format(
    policy_number: str, expected_blockers: tuple[ValidationBlocker, ...]
) -> None:
    candidate = dataclasses.replace(BASE_CANDIDATE, policy_number=policy_number)

    result = validate(candidate, now=TODAY)

    assert result.blockers == expected_blockers


def test_absent_loss_type_is_a_missing_field() -> None:
    candidate = dataclasses.replace(BASE_CANDIDATE, loss_type="")

    result = validate(candidate, now=TODAY)

    assert result.blockers == (ValidationBlocker(MISSING_REQUIRED_FIELD, "loss_type"),)


@pytest.mark.parametrize(
    ("loss_type", "expected_blockers"),
    [
        ("fire", ()),
        ("flood", ()),
        ("hurricane", ()),
        ("liability", ()),
        ("lightning", ()),
        ("mold", ()),
        ("roof_leak", ()),
        ("sinkhole", ()),
        ("smoke", ()),
        ("theft", ()),
        ("vandalism", ()),
        ("water_damage", ()),
        ("wind_hail", ()),
        ("watr_damage", (ValidationBlocker(LOSS_TYPE_UNRECOGNIZED, "loss_type"),)),
        ("WIND_HAIL", (ValidationBlocker(LOSS_TYPE_UNRECOGNIZED, "loss_type"),)),
    ],
)
def test_loss_type(
    loss_type: str, expected_blockers: tuple[ValidationBlocker, ...]
) -> None:
    candidate = dataclasses.replace(BASE_CANDIDATE, loss_type=loss_type)

    result = validate(candidate, now=TODAY)

    assert result.blockers == expected_blockers


@pytest.mark.parametrize(
    ("notice_type", "expected_blockers"),
    [
        ("INITIAL", ()),
        ("REOPENED", ()),
        ("SUPPLEMENTAL", ()),
        ("LOSS_ASSESSMENT", ()),
        ("", (ValidationBlocker(MISSING_REQUIRED_FIELD, "notice_type"),)),
        ("SUPPLEMENT", (ValidationBlocker(NOTICE_TYPE_UNRECOGNIZED, "notice_type"),)),
    ],
)
def test_notice_type(
    notice_type: str, expected_blockers: tuple[ValidationBlocker, ...]
) -> None:
    candidate = dataclasses.replace(BASE_CANDIDATE, notice_type=notice_type)

    result = validate(candidate, now=TODAY)

    assert result.blockers == expected_blockers


@pytest.mark.parametrize(
    ("name", "contact", "description", "expected_blockers"),
    [
        ("Pat Rivera", "555-0101", "Guest slipped on the pool deck and fractured a wrist", ()),
        (
            "",
            "555-0101",
            "Guest slipped on the pool deck and fractured a wrist",
            (ValidationBlocker(MISSING_REQUIRED_FIELD, "injured_party_name"),),
        ),
        (
            "Pat Rivera",
            "",
            "Guest slipped on the pool deck and fractured a wrist",
            (ValidationBlocker(MISSING_REQUIRED_FIELD, "injured_party_contact"),),
        ),
        (
            "Pat Rivera",
            "555-0101",
            "",
            (ValidationBlocker(MISSING_REQUIRED_FIELD, "injury_description"),),
        ),
    ],
)
def test_injury_required_fields(
    name: str,
    contact: str,
    description: str,
    expected_blockers: tuple[ValidationBlocker, ...],
) -> None:
    candidate = dataclasses.replace(
        BASE_CANDIDATE,
        loss_type="injury",
        injured_party_name=name,
        injured_party_contact=contact,
        injury_description=description,
    )

    result = validate(candidate, now=TODAY)

    assert result.blockers == expected_blockers


def test_non_injury_loss_does_not_require_injured_party_details() -> None:
    candidate = dataclasses.replace(BASE_CANDIDATE, loss_type="wind_hail")

    result = validate(candidate, now=TODAY)

    assert result.blockers == ()


def test_multiple_missing_injury_fields_survive_ordered_by_field_name() -> None:
    candidate = dataclasses.replace(
        BASE_CANDIDATE,
        loss_type="injury",
        injured_party_name="",
        injured_party_contact="",
        injury_description="Dog bit a visitor on the front porch",
    )

    result = validate(candidate, now=TODAY)

    assert result.blockers == (
        ValidationBlocker(MISSING_REQUIRED_FIELD, "injured_party_contact"),
        ValidationBlocker(MISSING_REQUIRED_FIELD, "injured_party_name"),
    )


def test_all_four_canonical_codes_fire_in_canonical_order() -> None:
    candidate = dataclasses.replace(
        BASE_CANDIDATE,
        policy_number="XX-1234567",
        notice_type="SUPPLEMENT",
        loss_date=date(2026, 8, 3),
        loss_type="injury",
        injured_party_name="",
        injured_party_contact="555-0101",
        injury_description="Guest slipped on the pool deck and fractured a wrist",
    )

    result = validate(candidate, now=TODAY)

    assert result.blockers == (
        ValidationBlocker(POLICY_NUMBER_MALFORMED, "policy_number"),
        ValidationBlocker(NOTICE_TYPE_UNRECOGNIZED, "notice_type"),
        ValidationBlocker(LOSS_DATE_IN_FUTURE, "loss_date"),
        ValidationBlocker(MISSING_REQUIRED_FIELD, "injured_party_name"),
    )


def test_non_contiguous_canonical_subset_still_sorts_correctly() -> None:
    candidate = dataclasses.replace(
        BASE_CANDIDATE,
        policy_number="XX-1234567",
        loss_type="injury",
        injured_party_name="Pat Rivera",
        injured_party_contact="555-0101",
        injury_description="",
    )

    result = validate(candidate, now=TODAY)

    assert result.blockers == (
        ValidationBlocker(POLICY_NUMBER_MALFORMED, "policy_number"),
        ValidationBlocker(MISSING_REQUIRED_FIELD, "injury_description"),
    )
