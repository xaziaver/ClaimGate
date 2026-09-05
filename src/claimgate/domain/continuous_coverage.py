"""Pure continuous-coverage derivation for an identified policy at a loss date.

The date from which coverage on the risk was continuous as of the loss date:
the start of the unbroken run of in-force coverage holding that date, reaching
back into a prior carrier's coverage where the source records one that meets
the run. Ratified semantics: ASSUMPTIONS.md, "Data we do not have at intake",
the 2026-08-14 entry and the continuous-coverage decisions of 2026-09-04. The
rule reads the term history the term-in-force rule reads and, unlike it, the
history's horizon and prior-carrier coverage. No configuration, no clock, and
no caller until item 7f wires the policy port.
"""

from dataclasses import dataclass
from datetime import date
from typing import Final, Literal

from claimgate.domain.coverage import NOT_EVALUATED, TermHistory, in_force_periods

DERIVED: Final = "DERIVED"
ContinuousCoverageValue = Literal["DERIVED", "NOT_EVALUATED"]

# The closed reason enumeration this feature owns (CLAUDE.md: reason-code
# enumerations are closed and scoped to one feature; ASSUMPTIONS.md, the
# 2026-09-04 continuous-coverage decisions, point 4). A history the source did
# not supply carries the source's own reason through instead, as the
# term-in-force rule does.
HISTORY_MAY_PREDATE_SOURCE: Final = "HISTORY_MAY_PREDATE_SOURCE"
NO_COVERAGE_ON_LOSS_DATE: Final = "NO_COVERAGE_ON_LOSS_DATE"
CONTINUOUS_COVERAGE_REASONS: Final = frozenset(
    {HISTORY_MAY_PREDATE_SOURCE, NO_COVERAGE_ON_LOSS_DATE}
)

Run = tuple[date, date]


@dataclass(frozen=True)
class ContinuousCoverageDerivation:
    # continuous_since only for DERIVED; reason only for NOT_EVALUATED - one of
    # this rule's own two, or the source's for a history it could not supply.
    value: ContinuousCoverageValue
    continuous_since: date | None = None
    reason: str | None = None


def derive_continuous_coverage(
    history: TermHistory, loss_date: date
) -> ContinuousCoverageDerivation:
    if history.value == "NOT_OBTAINED":
        return _not_evaluated(_source_reason(history))
    _require_prior_coverage_well_formed(history)
    run = _run_holding(_runs(in_force_periods(history)), loss_date)
    if run is None:
        return _not_evaluated(_uncovered_reason(history, loss_date))
    run_start = run[0]
    if history.history_from is not None and run_start <= history.history_from:
        # The run's own start is on or before the horizon: a seamless earlier
        # term may be missing, and concluding this date would understate
        # continuity. Tested before any prior-carrier extension (point 3).
        return _not_evaluated(HISTORY_MAY_PREDATE_SOURCE)
    return ContinuousCoverageDerivation(
        value=DERIVED, continuous_since=_reaching_back(history, run_start)
    )


def _runs(periods: list[Run]) -> list[Run]:
    """Maximal chains of in-force periods. A period ending on the day the next
    begins - a seamless renewal, a rewrite on the cancellation date - joins its
    run; any uncovered day between two periods starts a new one."""
    runs: list[Run] = []
    for start, end in periods:
        if runs and start == runs[-1][1]:
            runs[-1] = (runs[-1][0], end)
        else:
            runs.append((start, end))
    return runs


def _run_holding(runs: list[Run], loss_date: date) -> Run | None:
    # A boundary day belongs to the run it bounds: a loss on the day a run ended
    # derives that run's start, and on the day one began, that day. Runs are
    # separated by at least one uncovered day, so at most one holds a date.
    return next((run for run in runs if run[0] <= loss_date <= run[1]), None)


def _uncovered_reason(history: TermHistory, loss_date: date) -> str:
    # No supplied coverage holds the loss date. On or before the horizon a term
    # the source cannot see may have covered it; after the horizon the gap is
    # one the source can see.
    if history.history_from is not None and loss_date <= history.history_from:
        return HISTORY_MAY_PREDATE_SOURCE
    return NO_COVERAGE_ON_LOSS_DATE


def _reaching_back(history: TermHistory, run_start: date) -> date:
    # A prior carrier's coverage that reaches the run - ending on or after the
    # day the run began; overlapping days are covered days - carries its own
    # effective date as the risk's continuous-coverage date. It cannot move
    # the date later: one beginning after the run did leaves the run's start.
    prior = history.prior_coverage
    if prior is None or prior.ending < run_start:
        return run_start
    return min(prior.effective, run_start)


def _require_prior_coverage_well_formed(history: TermHistory) -> None:
    # On or before, the term rule's own convention (ASSUMPTIONS.md, the
    # 2026-09-05 continuous-coverage judgments, 5): a zero-day interval covers
    # nothing and is malformed, not a data point.
    prior = history.prior_coverage
    if prior is not None and prior.ending <= prior.effective:
        raise ValueError(
            f"prior coverage effective {prior.effective} ends {prior.ending},"
            " on or before it takes effect"
        )


def _source_reason(history: TermHistory) -> str:
    # As the term-in-force rule: a history not obtained for no stated reason is
    # a caller contract violation, not a value to record.
    if history.reason is None:
        raise ValueError("term history not obtained states no reason")
    return history.reason


def _not_evaluated(reason: str) -> ContinuousCoverageDerivation:
    return ContinuousCoverageDerivation(value=NOT_EVALUATED, reason=reason)
