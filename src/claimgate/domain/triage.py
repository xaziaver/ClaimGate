"""Pure severity assignment and queue routing for a candidate FNOL record."""

from decimal import Decimal

from claimgate.domain.models import Candidate, TriageOutcome

THEFT_LOW_SEVERITY_THRESHOLD = Decimal("500.00")

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


def route_queue(severity: str) -> str:
    return _SEVERITY_QUEUES[severity]


def triage_and_route(candidate: Candidate) -> TriageOutcome:
    severity = assign_severity(candidate.loss_type, candidate.loss_amount)
    queue = route_queue(severity)
    return TriageOutcome(severity=severity, queue=queue)
