"""Pure SIU indicator rules for a candidate FNOL record.

Indicators are factual observations only - never a conclusion, never the word
"fraud" as a system-generated value. See PHASE2_DESIGN.md's "SIU handling"
section.
"""

from datetime import date

from claimgate.domain.models import Candidate, SiuIndicatorResult, SiuIndicators

NO_THRESHOLD_CONFIGURED = "NO_THRESHOLD_CONFIGURED"
NO_CONTINUOUS_COVERAGE_DATE = "NO_CONTINUOUS_COVERAGE_DATE"
# Added to this closed enumeration by the 2026-08-26 ratification recorded in
# features/jurisdiction_selection.feature's Rule 3, and by nothing else. It
# shares a spelling with domain/validation.py's code of the same name and is
# not the same code - two enumerations, two subjects, growing independently
# (CLAUDE.md).
NO_JURISDICTION_DATE = "NO_JURISDICTION_DATE"


# An indicator evaluation reached with no loss date raises, and gains no third
# NOT_EVALUATED reason - ratified 2026-08-27 (ASSUMPTIONS.md, "Item 5h, three
# decisions", decision 3), the find_duplicates shape from item 3: an
# unreachable value is a caller contract violation, not a business outcome to
# record. Basis and fragility belong together. It holds *because* evaluation
# runs only on a transition into TRIAGED, on the intake path and the resolution
# path alike, and an absent loss date is now a blocker, so a notice missing one
# pends and never makes that transition. It stops holding the moment anything
# evaluates indicators on a pended notice, and whoever builds that revisits the
# decision then rather than discovering it as a crash.
def compute_siu_indicators(
    candidate: Candidate,
    now: date | None,
    late_reporting_threshold_days: int | None,
    recent_inception_threshold_days: int | None,
) -> SiuIndicators:
    """`now` is the jurisdiction's calendar date, or None where the notice's
    property state selects no jurisdiction. Only late reporting counts an
    interval against it; recent policy inception measures loss date against
    coverage start and needs no today at all. Both count against the loss date,
    which is why an absent one raises here rather than being carried inward."""
    loss_date = candidate.loss_date
    if loss_date is None:
        raise ValueError("compute_siu_indicators: candidate states no loss date")
    return SiuIndicators(
        late_reporting=_evaluate_late_reporting(
            loss_date, now, late_reporting_threshold_days
        ),
        recent_policy_inception=_evaluate_recent_inception(
            loss_date, candidate.continuous_coverage_date, recent_inception_threshold_days
        ),
    )


def _evaluate_late_reporting(
    loss_date: date, now: date | None, threshold_days: int | None
) -> SiuIndicatorResult:
    # Order is deliberate, not incidental, and the same discipline
    # _evaluate_recent_inception states below: when both inputs are absent, the
    # reason code must name the gap that would still block evaluation if the
    # other were closed. A configured threshold cannot help without a date to
    # count to, so NO_JURISDICTION_DATE wins - ratified 2026-08-26,
    # features/jurisdiction_selection.feature's Rule 3. Do not reorder these
    # checks.
    if now is None:
        return SiuIndicatorResult("NOT_EVALUATED", NO_JURISDICTION_DATE)
    if threshold_days is None:
        return SiuIndicatorResult("NOT_EVALUATED", NO_THRESHOLD_CONFIGURED)
    is_late = (now - loss_date).days > threshold_days
    return SiuIndicatorResult("TRUE" if is_late else "FALSE")


def _evaluate_recent_inception(
    loss_date: date, coverage_start: date | None, threshold_days: int | None
) -> SiuIndicatorResult:
    # Order is deliberate, not incidental: when both inputs are absent, the
    # reason code must name the gap that would still block evaluation if the
    # other were closed. A threshold cannot help without a coverage date, so
    # NO_CONTINUOUS_COVERAGE_DATE wins - see ASSUMPTIONS.md's carried-requirements
    # entry. Do not reorder these checks.
    if coverage_start is None:
        return SiuIndicatorResult("NOT_EVALUATED", NO_CONTINUOUS_COVERAGE_DATE)
    if threshold_days is None:
        return SiuIndicatorResult("NOT_EVALUATED", NO_THRESHOLD_CONFIGURED)
    days_since_inception = (loss_date - coverage_start).days
    is_recent = 0 <= days_since_inception <= threshold_days
    return SiuIndicatorResult("TRUE" if is_recent else "FALSE")
