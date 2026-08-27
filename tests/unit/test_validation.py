"""Unit tests for claimgate.domain.validation."""

import dataclasses
from datetime import date

import pytest

from claimgate.domain.models import Candidate, FutureDatedLossResult, ValidationBlocker
from claimgate.domain.validation import (
    LOSS_DATE_IN_FUTURE,
    LOSS_TYPE_UNRECOGNIZED,
    MISSING_REQUIRED_FIELD,
    NO_JURISDICTION_DATE,
    NO_LOSS_DATE,
    NOTICE_TYPE_UNRECOGNIZED,
    POLICY_NUMBER_MALFORMED,
    RECOGNIZED_LOSS_TYPES,
    _SECTION_II_LOSS_TYPES,
    validate,
)

TODAY = date(2026, 8, 2)

BASE_CANDIDATE = Candidate(
    policy_number="HO-1234567",
    loss_date=date(2026, 7, 1),
    loss_type="wind_hail",
    notice_type="INITIAL",
)


def test_section_ii_loss_types_are_recognized() -> None:
    assert _SECTION_II_LOSS_TYPES <= RECOGNIZED_LOSS_TYPES


@pytest.mark.parametrize(
    ("loss_date", "expected_blockers", "expected_determination"),
    [
        (
            date(2027, 6, 1),
            (ValidationBlocker(LOSS_DATE_IN_FUTURE, "loss_date"),),
            FutureDatedLossResult("TRUE"),
        ),
        (
            date(2026, 8, 3),
            (ValidationBlocker(LOSS_DATE_IN_FUTURE, "loss_date"),),
            FutureDatedLossResult("TRUE"),
        ),
        (date(2026, 8, 2), (), FutureDatedLossResult("FALSE")),
        (date(2026, 8, 1), (), FutureDatedLossResult("FALSE")),
        (date(2022, 9, 28), (), FutureDatedLossResult("FALSE")),
    ],
)
def test_loss_date_must_not_be_in_the_future(
    loss_date: date,
    expected_blockers: tuple[ValidationBlocker, ...],
    expected_determination: FutureDatedLossResult,
) -> None:
    candidate = dataclasses.replace(BASE_CANDIDATE, loss_date=loss_date)

    result = validate(
        candidate,
        now=TODAY,
        claimant_name_required=True,
        claimant_contact_required=True,
        recognized_policy_number_prefixes={"HO"},
    )

    assert result.blockers == expected_blockers
    assert result.valid is (not expected_blockers)
    # The determination is asserted on every row beside the blocker it produces,
    # so a clean evaluation recording nothing would fail here rather than pass
    # for want of anything looking at it.
    assert result.future_dated_loss == expected_determination


def test_an_absent_loss_date_blocks_and_leaves_the_determination_unevaluated() -> None:
    # validation.feature's outline states this outcome; the unit assertion is
    # here because mutation runs over tests/unit alone, and without it every
    # mutant of the reason code and the NOT_EVALUATED value survives untested.
    # Two separate facts, deliberately asserted together: the blocker, which
    # does not come from the determination - a NOT_EVALUATED determination
    # raises none - and the determination, which names which absence stopped it.
    candidate = dataclasses.replace(BASE_CANDIDATE, loss_date=None)

    result = validate(
        candidate,
        now=TODAY,
        claimant_name_required=True,
        claimant_contact_required=True,
        recognized_policy_number_prefixes={"HO"},
    )

    assert result.blockers == (ValidationBlocker(MISSING_REQUIRED_FIELD, "loss_date"),)
    assert result.valid is False
    assert result.future_dated_loss == FutureDatedLossResult("NOT_EVALUATED", NO_LOSS_DATE)


@pytest.mark.parametrize(
    "loss_date",
    [date(2027, 6, 1), date(2026, 8, 2), date(2022, 9, 28)],
)
def test_no_jurisdiction_date_leaves_the_determination_unevaluated_and_raises_no_blocker(
    loss_date: date,
) -> None:
    # Three loss dates that reach three different answers when there is a
    # calendar to compare them against, and one answer when there is not: a
    # result that was not computed is never reported as a negative (CLAUDE.md),
    # and never blocks - an unsupported jurisdiction must not turn into a pend.
    candidate = dataclasses.replace(BASE_CANDIDATE, loss_date=loss_date)

    result = validate(
        candidate,
        now=None,
        claimant_name_required=True,
        claimant_contact_required=True,
        recognized_policy_number_prefixes={"HO"},
    )

    assert result.blockers == ()
    assert result.valid is True
    assert result.future_dated_loss == FutureDatedLossResult(
        "NOT_EVALUATED", NO_JURISDICTION_DATE
    )


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

    result = validate(
        candidate,
        now=TODAY,
        claimant_name_required=True,
        claimant_contact_required=True,
        recognized_policy_number_prefixes={"HO"},
    )

    assert result.blockers == expected_blockers


def test_absent_loss_type_is_a_missing_field() -> None:
    candidate = dataclasses.replace(BASE_CANDIDATE, loss_type="")

    result = validate(
        candidate,
        now=TODAY,
        claimant_name_required=True,
        claimant_contact_required=True,
        recognized_policy_number_prefixes={"HO"},
    )

    assert result.blockers == (ValidationBlocker(MISSING_REQUIRED_FIELD, "loss_type"),)


@pytest.mark.parametrize(
    ("loss_type", "expected_blockers"),
    [
        ("fire", ()),
        ("flood", ()),
        ("hurricane", ()),
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
    # injury and liability are excluded here - both are Section II and
    # require claimant details, so a bare row for either could not assert
    # an empty blockers cell. See test_section_ii_required_fields below.
    candidate = dataclasses.replace(BASE_CANDIDATE, loss_type=loss_type)

    result = validate(
        candidate,
        now=TODAY,
        claimant_name_required=True,
        claimant_contact_required=True,
        recognized_policy_number_prefixes={"HO"},
    )

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

    result = validate(
        candidate,
        now=TODAY,
        claimant_name_required=True,
        claimant_contact_required=True,
        recognized_policy_number_prefixes={"HO"},
    )

    assert result.blockers == expected_blockers


_INJURY_DESCRIPTION = "Guest slipped on the pool deck and fractured a wrist"
_LIABILITY_DESCRIPTION = "Delivery driver slipped on the wet lobby floor and left before being identified"


@pytest.mark.parametrize(
    (
        "loss_type",
        "description",
        "claimant_name_required",
        "claimant_contact_required",
        "name",
        "contact",
        "expected_blockers",
    ),
    [
        # All fields present, both required: no blockers.
        ("injury", _INJURY_DESCRIPTION, True, True, "Pat Rivera", "555-0101", ()),
        ("liability", _LIABILITY_DESCRIPTION, True, True, "Pat Rivera", "555-0101", ()),
        # name required and absent: blocks. name not required and absent:
        # does not block. Contact held constant (required, present).
        (
            "injury",
            _INJURY_DESCRIPTION,
            True,
            True,
            "",
            "555-0101",
            (ValidationBlocker(MISSING_REQUIRED_FIELD, "claimant_name"),),
        ),
        ("injury", _INJURY_DESCRIPTION, False, True, "", "555-0101", ()),
        (
            "liability",
            _LIABILITY_DESCRIPTION,
            True,
            True,
            "",
            "555-0101",
            (ValidationBlocker(MISSING_REQUIRED_FIELD, "claimant_name"),),
        ),
        ("liability", _LIABILITY_DESCRIPTION, False, True, "", "555-0101", ()),
        # contact required and absent: blocks. contact not required and
        # absent: does not block. Name held constant (required, present).
        (
            "injury",
            _INJURY_DESCRIPTION,
            True,
            True,
            "Pat Rivera",
            "",
            (ValidationBlocker(MISSING_REQUIRED_FIELD, "claimant_contact"),),
        ),
        ("injury", _INJURY_DESCRIPTION, True, False, "Pat Rivera", "", ()),
        (
            "liability",
            _LIABILITY_DESCRIPTION,
            True,
            True,
            "Pat Rivera",
            "",
            (ValidationBlocker(MISSING_REQUIRED_FIELD, "claimant_contact"),),
        ),
        ("liability", _LIABILITY_DESCRIPTION, True, False, "Pat Rivera", "", ()),
    ],
)
def test_section_ii_required_fields(
    loss_type: str,
    description: str,
    claimant_name_required: bool,
    claimant_contact_required: bool,
    name: str,
    contact: str,
    expected_blockers: tuple[ValidationBlocker, ...],
) -> None:
    candidate = dataclasses.replace(
        BASE_CANDIDATE,
        loss_type=loss_type,
        claimant_name=name,
        claimant_contact=contact,
        incident_description=description,
    )

    result = validate(
        candidate,
        now=TODAY,
        claimant_name_required=claimant_name_required,
        claimant_contact_required=claimant_contact_required,
        recognized_policy_number_prefixes={"HO"},
    )

    assert result.blockers == expected_blockers


@pytest.mark.parametrize("loss_type", ["injury", "liability"])
def test_incident_description_is_required_unconditionally(loss_type: str) -> None:
    candidate = dataclasses.replace(
        BASE_CANDIDATE,
        loss_type=loss_type,
        claimant_name="Pat Rivera",
        claimant_contact="555-0101",
        incident_description="",
    )

    result = validate(
        candidate,
        now=TODAY,
        claimant_name_required=False,
        claimant_contact_required=False,
        recognized_policy_number_prefixes={"HO"},
    )

    assert result.blockers == (ValidationBlocker(MISSING_REQUIRED_FIELD, "incident_description"),)


def test_section_i_loss_does_not_require_claimant_details() -> None:
    candidate = dataclasses.replace(BASE_CANDIDATE, loss_type="wind_hail")

    result = validate(
        candidate,
        now=TODAY,
        claimant_name_required=True,
        claimant_contact_required=True,
        recognized_policy_number_prefixes={"HO"},
    )

    assert result.blockers == ()


def test_multiple_missing_claimant_fields_survive_ordered_by_field_name() -> None:
    candidate = dataclasses.replace(
        BASE_CANDIDATE,
        loss_type="injury",
        claimant_name="",
        claimant_contact="",
        incident_description="Dog bit a visitor on the front porch",
    )

    result = validate(
        candidate,
        now=TODAY,
        claimant_name_required=True,
        claimant_contact_required=True,
        recognized_policy_number_prefixes={"HO"},
    )

    assert result.blockers == (
        ValidationBlocker(MISSING_REQUIRED_FIELD, "claimant_contact"),
        ValidationBlocker(MISSING_REQUIRED_FIELD, "claimant_name"),
    )


def test_all_four_canonical_codes_fire_in_canonical_order() -> None:
    candidate = dataclasses.replace(
        BASE_CANDIDATE,
        policy_number="XX-1234567",
        notice_type="SUPPLEMENT",
        loss_date=date(2026, 8, 3),
        loss_type="injury",
        claimant_name="",
        claimant_contact="555-0101",
        incident_description="Guest slipped on the pool deck and fractured a wrist",
    )

    result = validate(
        candidate,
        now=TODAY,
        claimant_name_required=True,
        claimant_contact_required=True,
        recognized_policy_number_prefixes={"HO"},
    )

    assert result.blockers == (
        ValidationBlocker(POLICY_NUMBER_MALFORMED, "policy_number"),
        ValidationBlocker(NOTICE_TYPE_UNRECOGNIZED, "notice_type"),
        ValidationBlocker(LOSS_DATE_IN_FUTURE, "loss_date"),
        ValidationBlocker(MISSING_REQUIRED_FIELD, "claimant_name"),
    )


def test_non_contiguous_canonical_subset_still_sorts_correctly() -> None:
    candidate = dataclasses.replace(
        BASE_CANDIDATE,
        policy_number="XX-1234567",
        loss_type="injury",
        claimant_name="Pat Rivera",
        claimant_contact="555-0101",
        incident_description="",
    )

    result = validate(
        candidate,
        now=TODAY,
        claimant_name_required=True,
        claimant_contact_required=True,
        recognized_policy_number_prefixes={"HO"},
    )

    assert result.blockers == (
        ValidationBlocker(POLICY_NUMBER_MALFORMED, "policy_number"),
        ValidationBlocker(MISSING_REQUIRED_FIELD, "incident_description"),
    )
