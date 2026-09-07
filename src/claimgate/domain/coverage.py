"""Pure term-in-force determination for an identified policy at a loss date.

Verification, not determination: this answers whether a term of the policy was
in force on the loss date and records which term, and which status change,
decided it. Whether the policy covers the loss is coverage determination, which
is permanently out of scope (ROADMAP.md). The rule reads no configuration and
no clock. The term history arrives as data - from the policy port on the intake
path since item 7f (shell/policy_match.py), and from callers that build it
themselves.

The shapes every caller names are in coverage_types.py and re-exported here, and
the mechanics of a term's in-force periods in term_periods.py; both were split
out in item 7f, when this module had one line of headroom under the size gate
and the deciding-term reading below needed more. No behaviour moved with the
code.

**Which term decides.** IN_FORCE cites the term in force. BOUNDARY_DAY cites the
one term whose boundary the date is, and no term where two share it - a seamless
renewal, a rewrite on the cancellation date - because the date belongs to both
and citing one would be a silent pick (coverage_verification.feature, "A seamless
renewal date is a boundary day"). NOT_IN_FORCE cites the term whose standing
cancellation holds the date, with that cancellation; otherwise the term whose
coverage most recently ended before the date - the expiration or the
cancellation that left it uncovered - and no term where none had run by then.
The BOUNDARY_DAY reading and the no-cancellation reading are item 7f's, asked for
by features/policy_match.feature's term-verdict rows, which cite a single-term
policy's term on its expiration date and after it; coverage_verification.feature
states neither case and every citation it does state is unchanged. Recorded as a
judgment in QUEUE.md's 7f implementation paragraph.
"""

from bisect import bisect_left
from datetime import date

from claimgate.domain.coverage_types import (
    BOUNDARY_DAY,
    CANCELLATION,
    IN_FORCE,
    NOT_EVALUATED,
    NOT_IN_FORCE,
    REINSTATEMENT,
    PolicyTerm,
    PriorCoverage,
    StatusChangeKind,
    TermHistory,
    TermInForceDetermination,
    TermInForceValue,
    TermStatusChange,
)
from claimgate.domain.term_periods import Coverage, coverages_of

__all__ = [
    "BOUNDARY_DAY",
    "CANCELLATION",
    "IN_FORCE",
    "NOT_EVALUATED",
    "NOT_IN_FORCE",
    "REINSTATEMENT",
    "PolicyTerm",
    "PriorCoverage",
    "StatusChangeKind",
    "TermHistory",
    "TermInForceDetermination",
    "TermInForceValue",
    "TermStatusChange",
    "determine_term_in_force",
    "in_force_periods",
]


def determine_term_in_force(history: TermHistory, loss_date: date) -> TermInForceDetermination:
    if history.value == "NOT_OBTAINED":
        return _not_evaluated(history)
    coverages = coverages_of(history)
    bounding = [c.term for c in coverages if c.position(loss_date) == "BOUNDARY"]
    if bounding:
        return TermInForceDetermination(value=BOUNDARY_DAY, term=_only(bounding))
    covering = _covering(coverages, loss_date)
    if covering is not None:
        return TermInForceDetermination(value=IN_FORCE, term=covering.term)
    return _not_in_force(coverages, loss_date)


def in_force_periods(history: TermHistory) -> list[tuple[date, date]]:
    """Every period a term was actually in force, earliest first, for the
    continuous-coverage rule. Terms only, never prior-carrier coverage; a
    malformed history raises exactly as determine_term_in_force does."""
    return sorted(period for coverage in coverages_of(history) for period in coverage.periods)


def _only(terms: list[PolicyTerm]) -> PolicyTerm | None:
    # One term's boundary is that term's; a date two terms share belongs to
    # both, and neither is cited over the other.
    return terms[0] if len(terms) == 1 else None


def _covering(coverages: list[Coverage], loss_date: date) -> Coverage | None:
    # At most one once the history's periods are disjoint (term_periods.py):
    # two terms both strictly inside a period would be two periods sharing a day.
    return next((c for c in coverages if c.position(loss_date) == "COVERED"), None)


def _not_evaluated(history: TermHistory) -> TermInForceDetermination:
    # The source's reason travels with the value. A history not obtained for
    # no stated reason is a caller contract violation, not a value to record:
    # a NOT_EVALUATED with no reason is the unexplained negative the standing
    # rule exists to keep out.
    if history.reason is None:
        raise ValueError("term history not obtained states no reason")
    return TermInForceDetermination(value=NOT_EVALUATED, reason=history.reason)


def _not_in_force(coverages: list[Coverage], loss_date: date) -> TermInForceDetermination:
    # The loss date is strictly inside no period of any term. If it falls
    # within a term's dates after a cancellation that stands, that cancellation
    # ended the coverage and is cited - the latest such one, whose lapse the
    # date is in. Otherwise no term ran on that date, and the one whose
    # coverage most recently ended before it is cited, with no status change.
    standing = _standing_cancellations(coverages, loss_date)
    if not standing:
        return TermInForceDetermination(value=NOT_IN_FORCE, term=_last_ended(coverages, loss_date))
    latest = max(cancelled for cancelled, _ in standing)
    terms = [term for cancelled, term in standing if cancelled == latest]
    if len(terms) > 1:
        # Two terms cancelled the same date both holding the loss date with no
        # day in force shared - a rewrite voided on its own effective date.
        # Malformed like an overlap: nothing picks one term over the other.
        raise ValueError(
            f"term history is inconsistent: {len(terms)} terms cancelled {latest} hold {loss_date}"
        )
    return TermInForceDetermination(
        value=NOT_IN_FORCE, term=terms[0], cancellation_effective=latest
    )


def _last_ended(coverages: list[Coverage], loss_date: date) -> PolicyTerm | None:
    """The term whose coverage most recently ended before the loss date, or None
    where none had run by then. Reached only for a date strictly outside every
    period, so no period ends on it: the split is found by bisection rather than
    by a comparison whose equality case nothing could reach."""
    ended = sorted(
        (end, ordinal, coverage.term)
        for ordinal, coverage in enumerate(coverages)
        for _, end in coverage.periods
    )
    before = bisect_left([end for end, _, _ in ended], loss_date)
    return None if before == 0 else ended[before - 1][2]


def _standing_cancellations(
    coverages: list[Coverage], loss_date: date
) -> list[tuple[date, PolicyTerm]]:
    standing: list[tuple[date, PolicyTerm]] = []
    for coverage in coverages:
        cancelled = coverage.lapse_cancellation(loss_date)
        if cancelled is not None:
            standing.append((cancelled, coverage.term))
    return standing
