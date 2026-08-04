"""Pure SIU fraud-indicator rules for a candidate FNOL record."""

from datetime import date

from claimgate.domain.models import Candidate, SiuFlags

LATE_REPORTING_THRESHOLD_DAYS = 30
RECENT_INCEPTION_THRESHOLD_DAYS = 30


def compute_siu_flags(candidate: Candidate, now: date) -> SiuFlags:
    return SiuFlags(
        late_reporting=_is_late_reporting(candidate.loss_date, now),
        recent_policy_inception=_is_recent_inception(candidate),
    )


def _is_late_reporting(loss_date: date, now: date) -> bool:
    return (now - loss_date).days > LATE_REPORTING_THRESHOLD_DAYS


def _is_recent_inception(candidate: Candidate) -> bool:
    inception = candidate.policy_inception_date
    if inception is None:
        return False
    days_since_inception = (candidate.loss_date - inception).days
    return 0 <= days_since_inception <= RECENT_INCEPTION_THRESHOLD_DAYS
