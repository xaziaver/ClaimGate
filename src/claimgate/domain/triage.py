"""Pure severity assignment and queue routing for a candidate FNOL record."""

from datetime import date
from decimal import Decimal

from claimgate.domain.models import Candidate, SiuFlags, TriageOutcome
from claimgate.domain.siu import compute_siu_flags

THEFT_LOW_SEVERITY_THRESHOLD = Decimal("500.00")
SIU_QUEUE = "siu_review"

_HIGH_SEVERITY_LOSS_TYPES = frozenset({"injury", "fire"})
_SEVERITY_QUEUES = {"low": "fast_track", "standard": "standard", "high": "complex"}


def assign_severity(loss_type: str, loss_amount: Decimal | None) -> str:
    if loss_type in _HIGH_SEVERITY_LOSS_TYPES:
        return "high"
    if _is_low_severity_theft(loss_type, loss_amount):
        return "low"
    return "standard"


def _is_low_severity_theft(loss_type: str, loss_amount: Decimal | None) -> bool:
    if loss_type != "theft" or loss_amount is None:
        return False
    return loss_amount < THEFT_LOW_SEVERITY_THRESHOLD


def route_queue(severity: str, siu_flags: SiuFlags) -> str:
    if siu_flags.late_reporting or siu_flags.recent_policy_inception:
        return SIU_QUEUE
    return _SEVERITY_QUEUES[severity]


def triage_and_route(candidate: Candidate, now: date) -> TriageOutcome:
    severity = assign_severity(candidate.loss_type, candidate.loss_amount)
    siu_flags = compute_siu_flags(candidate, now)
    queue = route_queue(severity, siu_flags)
    return TriageOutcome(severity=severity, queue=queue)
