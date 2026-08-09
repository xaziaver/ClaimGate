"""Thin, stable test API over the SIU indicator domain area."""

from datetime import date

from claimgate.domain.models import Candidate, SiuIndicators
from claimgate.domain.siu import compute_siu_indicators as _compute_siu_indicators


def siu_indicators(
    *,
    now: date,
    loss_date: date,
    late_reporting_threshold_days: int | None,
    recent_inception_threshold_days: int | None,
    policy_inception_date: date | None = None,
) -> SiuIndicators:
    candidate = Candidate(loss_date=loss_date, policy_inception_date=policy_inception_date)
    return _compute_siu_indicators(
        candidate,
        now,
        late_reporting_threshold_days,
        recent_inception_threshold_days,
    )
