"""Thin, stable test API over the validation domain area."""

from datetime import date

from claimgate.domain.models import Candidate, ValidationResult
from claimgate.domain.validation import validate as _validate


def validate_record(
    *,
    now: date,
    policy_number: str = "",
    loss_date: date = date.min,
    loss_type: str = "",
    injured_party_name: str | None = None,
    injured_party_contact: str | None = None,
    injury_description: str | None = None,
) -> ValidationResult:
    candidate = Candidate(
        policy_number=policy_number,
        loss_date=loss_date,
        loss_type=loss_type,
        injured_party_name=injured_party_name,
        injured_party_contact=injured_party_contact,
        injury_description=injury_description,
    )
    return _validate(candidate, now=now)
