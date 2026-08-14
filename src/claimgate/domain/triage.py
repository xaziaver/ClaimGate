"""Pure severity assignment and queue routing for a candidate FNOL record."""

from claimgate.domain.models import Candidate, TriageOutcome

_HIGH_SEVERITY_LOSS_TYPES = frozenset({"injury", "fire", "sinkhole"})
_SEVERITY_QUEUES = {"standard": "standard", "high": "complex"}


def assign_severity(loss_type: str) -> str:
    if loss_type in _HIGH_SEVERITY_LOSS_TYPES:
        return "high"
    return "standard"


def route_queue(severity: str) -> str:
    return _SEVERITY_QUEUES[severity]


def triage_and_route(candidate: Candidate) -> TriageOutcome:
    severity = assign_severity(candidate.loss_type)
    queue = route_queue(severity)
    return TriageOutcome(severity=severity, queue=queue)
