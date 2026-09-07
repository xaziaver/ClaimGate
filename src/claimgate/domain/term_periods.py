"""The periods a policy term was actually in force, from its dates and its
status changes (split out of coverage.py in item 7f, no behaviour change).

Coverage incepts and ends at 12:01 a.m. and intake holds a date, not an instant,
so a period's first and last dates are boundaries and a date strictly inside one
is covered. A cancellation ends a period on its effective date; a reinstatement
opens a new one on its own, unless it is dated on the cancellation it follows,
which rescinds it and the lapse never existed. A term's nominal expiration after
a mid-term cancellation, and its effective date under a cancellation flat from
inception, end no period and so are not boundaries: nothing turns on the loss
time on a date the term did not run to, which is the spec's own precedence for a
rescinded date (coverage_verification.feature). Two terms of one policy in force
on the same day is malformed source data and raises, as does a status change
dated outside its term or a reinstatement of nothing.
"""

from dataclasses import dataclass
from datetime import date
from itertools import combinations
from typing import Literal

from claimgate.domain.coverage_types import (
    CANCELLATION,
    REINSTATEMENT,
    PolicyTerm,
    TermHistory,
    TermStatusChange,
)


@dataclass(frozen=True)
class Coverage:
    """One term as the periods it was actually in force."""

    term: PolicyTerm
    periods: tuple[tuple[date, date], ...]
    cancellations: tuple[date, ...]

    def position(self, loss_date: date) -> Literal["BOUNDARY", "COVERED", "UNCOVERED"]:
        for start, end in self.periods:
            if start <= loss_date <= end:
                return "BOUNDARY" if loss_date in (start, end) else "COVERED"
        return "UNCOVERED"

    def lapse_cancellation(self, loss_date: date) -> date | None:
        """The standing cancellation whose lapse holds the loss date, or None."""
        if not self.term.effective <= loss_date <= self.term.expiration:
            return None
        return max((c for c in self.cancellations if c <= loss_date), default=None)


def coverages_of(history: TermHistory) -> list[Coverage]:
    coverages = [_coverage_of(term) for term in history.terms]
    _require_disjoint(coverages)
    return coverages


def _require_disjoint(coverages: list[Coverage]) -> None:
    # Two terms of one policy in force on the same day is malformed source
    # data, not a history to answer: neither term could be cited over the
    # other. Periods that touch at a date - a seamless renewal, a rewrite
    # effective on the cancellation date - are disjoint; only a day strictly
    # inside both counts.
    periods = [(period, coverage.term) for coverage in coverages for period in coverage.periods]
    for ((start1, end1), term1), ((start2, end2), term2) in combinations(periods, 2):
        if max(start1, start2) < min(end1, end2):
            first, second = sorted((term1.effective, term2.effective))
            raise ValueError(
                f"term history is inconsistent: terms effective {first} and {second}"
                " were both in force on the same day"
            )


def _coverage_of(term: PolicyTerm) -> Coverage:
    if term.expiration <= term.effective:
        raise ValueError(f"term effective {term.effective} expires on or before it takes effect")
    periods: list[tuple[date, date]] = []
    cancellations: list[date] = []
    in_force_from: date | None = term.effective
    for change in _ordered_changes(term):
        in_force_from = _apply_change(change, in_force_from, periods, cancellations)
    if in_force_from is not None:
        periods.append((in_force_from, term.expiration))
    # A period with no days in it - cancelled flat on the effective date - is
    # dropped: it covers nothing and bounds nothing.
    return Coverage(term, tuple(p for p in periods if p[0] < p[1]), tuple(cancellations))


def _ordered_changes(term: PolicyTerm) -> list[TermStatusChange]:
    for change in term.status_changes:
        if not term.effective <= change.effective <= term.expiration:
            raise ValueError(
                f"{change.kind.lower()} effective {change.effective} is dated outside its term"
                f" {term.effective} to {term.expiration}"
            )
    # A cancellation and a reinstatement on the same date read in that order:
    # the reinstatement rescinds the cancellation. The other order would be a
    # reinstatement of nothing, which _apply_change refuses.
    return sorted(term.status_changes, key=lambda c: (c.effective, c.kind == REINSTATEMENT))


def _apply_change(
    change: TermStatusChange,
    in_force_from: date | None,
    periods: list[tuple[date, date]],
    cancellations: list[date],
) -> date | None:
    """The date coverage has run from once this change applies; None while cancelled."""
    if change.kind == CANCELLATION:
        if in_force_from is None:
            raise ValueError(
                f"cancellation effective {change.effective} on a term already cancelled"
            )
        periods.append((in_force_from, change.effective))
        cancellations.append(change.effective)
        return None
    if in_force_from is not None:
        raise ValueError(
            f"reinstatement effective {change.effective} with no cancellation to reinstate"
        )
    if change.effective == cancellations[-1]:
        # Retroactive: the cancellation is rescinded and coverage was continuous.
        cancellations.pop()
        return periods.pop()[0]
    return change.effective
