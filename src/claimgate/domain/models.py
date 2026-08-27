"""Plain data types shared across the domain package."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal


@dataclass(frozen=True)
class Candidate:
    # None is "no loss date was stated", a fact the reporter may genuinely not
    # have (ASSUMPTIONS.md, "An absent loss date is a domain blocker, not a
    # schema refusal"). It replaced a date.min default, which was a sentinel
    # wearing a date's type: every consumer read it as a real 0001-01-01 and
    # none of them could tell it from one.
    policy_number: str = ""
    loss_date: date | None = None
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


FutureDatedLossValue = Literal["TRUE", "FALSE", "NOT_EVALUATED"]


@dataclass(frozen=True)
class FutureDatedLossResult:
    # Same convention as SiuIndicatorResult, and its own closed reason
    # enumeration rather than a share of that one (CLAUDE.md): reason is set
    # only when value is NOT_EVALUATED. A loss date that could not be compared
    # to a jurisdiction's today is not a loss date found not to be ahead of it.
    value: FutureDatedLossValue
    reason: str | None = None


@dataclass(frozen=True)
class ValidationResult:
    # No default on either: the determination is what the loss-date check
    # concluded and the blocker follows from it, so a result carrying blockers
    # and no determination is not a state validate() can produce.
    blockers: tuple[ValidationBlocker, ...]
    future_dated_loss: FutureDatedLossResult

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


@dataclass(frozen=True)
class Jurisdiction:
    # One value in phase 2 (PHASE2_DESIGN.md, "Jurisdiction axis"): every
    # statutory value in STATUTORY_REGISTER.md is non-gating at intake and
    # window selection is not built, so the timezone is what a jurisdiction
    # currently supplies. A dataclass and not a bare string so a second value
    # lands here rather than widening every signature that carries one.
    timezone: str


JurisdictionSelectionValue = Literal["SELECTED", "UNSUPPORTED", "MALFORMED"]


@dataclass(frozen=True)
class JurisdictionSelectionResult:
    # Same convention as CarrierIdentityResult: jurisdiction is set only when
    # value is SELECTED. The other two are different facts and never collapse.
    # UNSUPPORTED is the absence of an entry - not a refusal, since the notice
    # is still received and still triaged, and something about this
    # deployment's configuration rather than about the notice. MALFORMED is an
    # entry that exists and cannot be read, which is our own defect and is
    # escalated rather than marked (shell/rules.py); defaulting it to a
    # timezone, or to UNSUPPORTED, would answer a misconfiguration by telling
    # a reporter their state is not supported.
    value: JurisdictionSelectionValue
    jurisdiction: Jurisdiction | None = None


@dataclass(frozen=True)
class CarrierRules:
    claimant_name_required: bool
    claimant_contact_required: bool
    recognized_policy_number_prefixes: frozenset[str]
    late_reporting_threshold_days: int | None
    recent_inception_threshold_days: int | None
    window_days: int


@dataclass(frozen=True)
class ConfigurationRejection:
    code: str
    # "" for CARRIER_NOT_CONFIGURED, which names no single value - every other
    # code names the business-language field it was raised against.
    field: str = ""


CarrierConfigurationValue = Literal["RESOLVED", "REFUSED"]


@dataclass(frozen=True)
class CarrierConfigurationResult:
    # Same convention as JurisdictionDateResult: rules is set only when value
    # is RESOLVED, rejections only when REFUSED - "unevaluated is not
    # negative" (ASSUMPTIONS.md) applies here as "a refusal carries no rules."
    value: CarrierConfigurationValue
    rules: CarrierRules | None = None
    rejections: tuple[ConfigurationRejection, ...] = ()


@dataclass(frozen=True)
class CarrierIdentity:
    name: str
    naic: int
    naic_group: int | None


CarrierIdentityValue = Literal["RESOLVED", "REFUSED"]


@dataclass(frozen=True)
class CarrierIdentityResult:
    # Same convention as CarrierConfigurationResult: identity is set only
    # when value is RESOLVED - "unevaluated is not negative" applies here as
    # "a refusal carries no identity."
    value: CarrierIdentityValue
    identity: CarrierIdentity | None = None
