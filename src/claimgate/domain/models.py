"""Plain data types shared across the domain package."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal


@dataclass(frozen=True)
class Candidate:
    policy_number: str = ""
    loss_date: date = date.min
    loss_type: str = ""
    notice_type: str = ""
    loss_amount: Decimal | None = None
    continuous_coverage_date: date | None = None
    claimant_name: str | None = None
    claimant_contact: str | None = None
    incident_description: str | None = None


@dataclass(frozen=True)
class ExistingClaim:
    claim_id: str
    policy_number: str
    loss_date: date
    loss_type: str


DuplicateMatchValue = Literal["EVALUATED", "NOT_EVALUATED"]


@dataclass(frozen=True)
class DuplicateMatchResult:
    # Same convention as SiuIndicatorResult: reason is set only when value is
    # NOT_EVALUATED, and matches is only ever populated when value is
    # EVALUATED - "unevaluated is not negative" (ASSUMPTIONS.md) applies here
    # as "unevaluated carries no matches", not an empty result read as none found.
    value: DuplicateMatchValue
    matches: tuple[str, ...] = ()
    reason: str | None = None


@dataclass(frozen=True)
class ValidationBlocker:
    code: str
    field: str


@dataclass(frozen=True)
class ValidationResult:
    blockers: tuple[ValidationBlocker, ...] = ()

    @property
    def valid(self) -> bool:
        return not self.blockers


SiuIndicatorValue = Literal["TRUE", "FALSE", "NOT_EVALUATED"]


@dataclass(frozen=True)
class SiuIndicatorResult:
    # "Unevaluated is not negative" (ASSUMPTIONS.md): reason is set only when
    # value is NOT_EVALUATED - a required input was missing, not found false.
    value: SiuIndicatorValue
    reason: str | None = None


@dataclass(frozen=True)
class SiuIndicators:
    late_reporting: SiuIndicatorResult
    recent_policy_inception: SiuIndicatorResult


@dataclass(frozen=True)
class TriageOutcome:
    severity: str
    queue: str


JurisdictionDateValue = Literal["RESOLVED", "REFUSED"]


@dataclass(frozen=True)
class JurisdictionDateResult:
    # Same convention as DuplicateMatchResult: reason is set only when value
    # is REFUSED, and resolved_date is only ever populated when value is
    # RESOLVED - a refusal, not a missing input, but "unevaluated is not
    # negative" (ASSUMPTIONS.md) applies the same way: a result that was not
    # computed is never reported as a date.
    value: JurisdictionDateValue
    resolved_date: date | None = None
    reason: str | None = None
