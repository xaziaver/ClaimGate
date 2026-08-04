"""Thin, stable test API over the SIU fraud-indicator domain area."""

from datetime import date

from claimgate.domain.models import Candidate, SiuFlags
from claimgate.domain.siu import compute_siu_flags as _compute_siu_flags


def siu_flags(
    *,
    now: date,
    loss_date: date,
    policy_inception_date: date | None = None,
) -> SiuFlags:
    candidate = Candidate(loss_date=loss_date, policy_inception_date=policy_inception_date)
    return _compute_siu_flags(candidate, now=now)
