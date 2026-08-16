"""Pure validation rules for a candidate FNOL record."""

import re
from datetime import date

from claimgate.domain.models import Candidate, ValidationBlocker, ValidationResult

POLICY_NUMBER_PATTERN = re.compile(r"^HO-\d{7}$")
RECOGNIZED_NOTICE_TYPES = frozenset({"INITIAL", "REOPENED", "SUPPLEMENTAL", "LOSS_ASSESSMENT"})
RECOGNIZED_LOSS_TYPES = frozenset(
    {
        "fire",
        "flood",
        "hurricane",
        "injury",
        "liability",
        "lightning",
        "mold",
        "roof_leak",
        "sinkhole",
        "smoke",
        "theft",
        "vandalism",
        "water_damage",
        "wind_hail",
    }
)

POLICY_NUMBER_MALFORMED = "POLICY_NUMBER_MALFORMED"
NOTICE_TYPE_UNRECOGNIZED = "NOTICE_TYPE_UNRECOGNIZED"
LOSS_TYPE_UNRECOGNIZED = "LOSS_TYPE_UNRECOGNIZED"
LOSS_DATE_IN_FUTURE = "LOSS_DATE_IN_FUTURE"
MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"

# Canonical order is a declared property of the code enumeration, not the
# order checks happen to run in below. The check order is deliberately
# different from this so that a mutant deleting the sort in _canonical_order
# is caught by a scenario expecting canonical order rather than passing by
# coincidence. Do not reorder the checks below to match this tuple.
_CANONICAL_CODE_ORDER = (
    POLICY_NUMBER_MALFORMED,
    NOTICE_TYPE_UNRECOGNIZED,
    LOSS_TYPE_UNRECOGNIZED,
    LOSS_DATE_IN_FUTURE,
    MISSING_REQUIRED_FIELD,
)


def validate(candidate: Candidate, now: date) -> ValidationResult:
    blockers = (
        _check_loss_date(candidate, now)
        + _check_injury_fields(candidate)
        + _check_notice_type(candidate)
        + _check_loss_type(candidate)
        + _check_policy_number(candidate)
    )
    return ValidationResult(blockers=tuple(_canonical_order(blockers)))


def _canonical_order(blockers: list[ValidationBlocker]) -> list[ValidationBlocker]:
    return sorted(blockers, key=lambda b: (_CANONICAL_CODE_ORDER.index(b.code), b.field))


def _check_loss_date(candidate: Candidate, now: date) -> list[ValidationBlocker]:
    if candidate.loss_date > now:
        return [ValidationBlocker(LOSS_DATE_IN_FUTURE, "loss_date")]
    return []


def _check_policy_number(candidate: Candidate) -> list[ValidationBlocker]:
    if not candidate.policy_number.strip():
        return [ValidationBlocker(MISSING_REQUIRED_FIELD, "policy_number")]
    if not POLICY_NUMBER_PATTERN.match(candidate.policy_number):
        return [ValidationBlocker(POLICY_NUMBER_MALFORMED, "policy_number")]
    return []


def _check_loss_type(candidate: Candidate) -> list[ValidationBlocker]:
    if not candidate.loss_type.strip():
        return [ValidationBlocker(MISSING_REQUIRED_FIELD, "loss_type")]
    if candidate.loss_type not in RECOGNIZED_LOSS_TYPES:
        return [ValidationBlocker(LOSS_TYPE_UNRECOGNIZED, "loss_type")]
    return []


def _check_notice_type(candidate: Candidate) -> list[ValidationBlocker]:
    if not candidate.notice_type.strip():
        return [ValidationBlocker(MISSING_REQUIRED_FIELD, "notice_type")]
    if candidate.notice_type not in RECOGNIZED_NOTICE_TYPES:
        return [ValidationBlocker(NOTICE_TYPE_UNRECOGNIZED, "notice_type")]
    return []


def _check_injury_fields(candidate: Candidate) -> list[ValidationBlocker]:
    if candidate.loss_type != "injury":
        return []
    fields = (
        ("injured_party_name", candidate.injured_party_name),
        ("injured_party_contact", candidate.injured_party_contact),
        ("injury_description", candidate.injury_description),
    )
    return [
        ValidationBlocker(MISSING_REQUIRED_FIELD, field_name)
        for field_name, value in fields
        if not value
    ]
