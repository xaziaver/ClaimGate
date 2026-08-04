"""Plain data types shared across the domain package."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict


@dataclass(frozen=True)
class Candidate:
    policy_number: str = ""
    loss_date: date = date.min
    loss_type: str = ""
    loss_amount: Decimal | None = None
    policy_inception_date: date | None = None
    injured_party_name: str | None = None
    injured_party_contact: str | None = None
    injury_description: str | None = None


@dataclass(frozen=True)
class ExistingClaim:
    claim_id: str
    policy_number: str
    loss_date: date
    loss_type: str


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    missing_field: str | None = None


@dataclass(frozen=True)
class SiuFlags:
    late_reporting: bool
    recent_policy_inception: bool


@dataclass(frozen=True)
class TriageOutcome:
    severity: str
    queue: str
