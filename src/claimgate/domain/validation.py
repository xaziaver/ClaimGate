"""Pure validation rules for a candidate FNOL record."""

import re
from datetime import date

from claimgate.domain.models import Candidate, ValidationResult

REPORTING_WINDOW_DAYS = 365
POLICY_NUMBER_PATTERN = re.compile(r"^(?:HO|AU|CP|CA|GL)-\d{7}$")


def validate(candidate: Candidate, now: date) -> ValidationResult:
    if not _loss_date_in_window(candidate.loss_date, now):
        return ValidationResult(valid=False)
    if not POLICY_NUMBER_PATTERN.match(candidate.policy_number):
        return ValidationResult(valid=False)
    if candidate.loss_type == "injury":
        missing_field = _first_missing_injury_field(candidate)
        if missing_field is not None:
            return ValidationResult(valid=False, missing_field=missing_field)
    return ValidationResult(valid=True)


def _loss_date_in_window(loss_date: date, now: date) -> bool:
    if loss_date > now:
        return False
    return (now - loss_date).days <= REPORTING_WINDOW_DAYS


def _first_missing_injury_field(candidate: Candidate) -> str | None:
    fields = (
        ("injured_party_name", candidate.injured_party_name),
        ("injured_party_contact", candidate.injured_party_contact),
        ("injury_description", candidate.injury_description),
    )
    for field_name, value in fields:
        if not value:
            return field_name
    return None
