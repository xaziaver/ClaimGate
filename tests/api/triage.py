"""Thin, stable test API over the triage domain area."""

from datetime import date
from decimal import Decimal

from claimgate.domain.models import Candidate, TriageOutcome
from claimgate.domain.triage import assign_severity as _assign_severity
from claimgate.domain.triage import route_queue as _route_queue
from claimgate.domain.triage import triage_and_route as _triage_and_route


def assign_severity(loss_type: str, loss_amount: Decimal | None = None) -> str:
    return _assign_severity(loss_type, loss_amount)


def route_queue(severity: str) -> str:
    return _route_queue(severity)


def triage_and_route(
    *,
    loss_type: str,
    loss_amount: Decimal | None = None,
    loss_date: date,
    policy_inception_date: date | None = None,
) -> TriageOutcome:
    candidate = Candidate(
        loss_type=loss_type,
        loss_amount=loss_amount,
        loss_date=loss_date,
        policy_inception_date=policy_inception_date,
    )
    return _triage_and_route(candidate)
