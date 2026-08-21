"""Thin, stable test API over the validation domain area."""

from collections.abc import Collection
from datetime import date

from claimgate.domain.models import Candidate, ValidationResult
from claimgate.domain.validation import validate as _validate


def validate_record(
    *,
    now: date,
    claimant_name_required: bool,
    claimant_contact_required: bool,
    recognized_policy_number_prefixes: Collection[str],
    policy_number: str = "",
    loss_date: date = date.min,
    loss_type: str = "",
    notice_type: str = "",
    claimant_name: str | None = None,
    claimant_contact: str | None = None,
    incident_description: str | None = None,
) -> ValidationResult:
    candidate = Candidate(
        policy_number=policy_number,
        loss_date=loss_date,
        loss_type=loss_type,
        notice_type=notice_type,
        claimant_name=claimant_name,
        claimant_contact=claimant_contact,
        incident_description=incident_description,
    )
    return _validate(
        candidate,
        now=now,
        claimant_name_required=claimant_name_required,
        claimant_contact_required=claimant_contact_required,
        recognized_policy_number_prefixes=recognized_policy_number_prefixes,
    )


def reason_codes(result: ValidationResult) -> list[str]:
    # Derived, deduplicated view of blocker codes - API-response shaping,
    # not a domain concept, so it lives at the boundary.
    codes: list[str] = []
    for blocker in result.blockers:
        if blocker.code not in codes:
            codes.append(blocker.code)
    return codes
