"""Pure SIU indicator rules for a candidate FNOL record.

Indicators are factual observations only - never a conclusion, never the word
"fraud" as a system-generated value. See PHASE2_DESIGN.md's "SIU handling"
section.
"""

from datetime import date

from claimgate.domain.models import Candidate, SiuIndicatorResult, SiuIndicators

NO_THRESHOLD_CONFIGURED = "NO_THRESHOLD_CONFIGURED"
NO_CONTINUOUS_COVERAGE_DATE = "NO_CONTINUOUS_COVERAGE_DATE"


def compute_siu_indicators(
    candidate: Candidate,
    now: date,
    late_reporting_threshold_days: int | None,
    recent_inception_threshold_days: int | None,
) -> SiuIndicators:
    return SiuIndicators(
        late_reporting=_evaluate_late_reporting(
            candidate.loss_date, now, late_reporting_threshold_days
        ),
        recent_policy_inception=_evaluate_recent_inception(
            candidate, recent_inception_threshold_days
        ),
    )


def _evaluate_late_reporting(
    loss_date: date, now: date, threshold_days: int | None
) -> SiuIndicatorResult:
    if threshold_days is None:
        return SiuIndicatorResult("NOT_EVALUATED", NO_THRESHOLD_CONFIGURED)
    is_late = (now - loss_date).days > threshold_days
    return SiuIndicatorResult("TRUE" if is_late else "FALSE")


def _evaluate_recent_inception(
    candidate: Candidate, threshold_days: int | None
) -> SiuIndicatorResult:
    # Order is deliberate, not incidental: when both inputs are absent, the
    # reason code must name the gap that would still block evaluation if the
    # other were closed. A threshold cannot help without a coverage date, so
    # NO_CONTINUOUS_COVERAGE_DATE wins - see ASSUMPTIONS.md's carried-requirements
    # entry. Do not reorder these checks.
    coverage_start = candidate.continuous_coverage_date
    if coverage_start is None:
        return SiuIndicatorResult("NOT_EVALUATED", NO_CONTINUOUS_COVERAGE_DATE)
    if threshold_days is None:
        return SiuIndicatorResult("NOT_EVALUATED", NO_THRESHOLD_CONFIGURED)
    days_since_inception = (candidate.loss_date - coverage_start).days
    is_recent = 0 <= days_since_inception <= threshold_days
    return SiuIndicatorResult("TRUE" if is_recent else "FALSE")
