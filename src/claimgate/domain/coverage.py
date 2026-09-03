"""Pure term-in-force determination for an identified policy at a loss date.

Verification, not determination: this answers whether a term of the policy was
in force on the loss date and records which term, and which status change,
decided it. Whether the policy covers the loss is coverage determination, which
is permanently out of scope (ROADMAP.md). The rule reads no configuration and
no clock. The term history arrives as data - from the policy port once item 7f
wires it, and until then from callers that build it themselves.
"""

from dataclasses import dataclass
from datetime import date
from typing import Final, Literal

IN_FORCE: Final = "IN_FORCE"
NOT_IN_FORCE: Final = "NOT_IN_FORCE"
BOUNDARY_DAY: Final = "BOUNDARY_DAY"
NOT_EVALUATED: Final = "NOT_EVALUATED"
TermInForceValue = Literal["IN_FORCE", "NOT_IN_FORCE", "BOUNDARY_DAY", "NOT_EVALUATED"]

CANCELLATION: Final = "CANCELLATION"
REINSTATEMENT: Final = "REINSTATEMENT"
StatusChangeKind = Literal["CANCELLATION", "REINSTATEMENT"]


@dataclass(frozen=True)
class TermStatusChange:
    kind: StatusChangeKind
    effective: date


@dataclass(frozen=True)
class PolicyTerm:
    effective: date
    expiration: date
    # In any order; the rule sorts by effective date. A reinstatement dated on
    # the cancellation it follows is retroactive: it rescinds the cancellation
    # and the lapse never existed. One dated later leaves a lapse between the
    # two. That is how a policy administration system records the two kinds of
    # reinstatement - one transaction shape, told apart by its date.
    status_changes: tuple[TermStatusChange, ...] = ()


@dataclass(frozen=True)
class TermHistory:
    # The policy source's answer, in the shape every port answer takes
    # (PHASE3_DESIGN.md): reason is set only when the history was not obtained,
    # terms only when it was.
    value: Literal["OBTAINED", "NOT_OBTAINED"]
    terms: tuple[PolicyTerm, ...] = ()
    reason: str | None = None


@dataclass(frozen=True)
class TermInForceDetermination:
    # term is the deciding term: the one in force for IN_FORCE, the one whose
    # cancellation ended coverage for NOT_IN_FORCE, and None where no term
    # decided - a loss outside every term, a boundary day, or NOT_EVALUATED.
    # cancellation_effective is set only when a cancellation produced the
    # value; reason only for NOT_EVALUATED, and it is the source's reason.
    value: TermInForceValue
    term: PolicyTerm | None = None
    cancellation_effective: date | None = None
    reason: str | None = None


def determine_term_in_force(history: TermHistory, loss_date: date) -> TermInForceDetermination:
    if history.value == "NOT_OBTAINED":
        return _not_evaluated(history)
    coverages = [_coverage_of(term) for term in history.terms]
    if any(coverage.position(loss_date) == "BOUNDARY" for coverage in coverages):
        return TermInForceDetermination(value=BOUNDARY_DAY)
    covering = _covering(coverages, loss_date)
    if covering is not None:
        return TermInForceDetermination(value=IN_FORCE, term=covering.term)
    return _not_in_force(coverages, loss_date)


def _covering(coverages: list["_Coverage"], loss_date: date) -> "_Coverage | None":
    covering = [c for c in coverages if c.position(loss_date) == "COVERED"]
    if len(covering) > 1:
        raise ValueError(f"term history is inconsistent: {len(covering)} terms cover {loss_date}")
    return covering[0] if covering else None


def _not_evaluated(history: TermHistory) -> TermInForceDetermination:
    # The source's reason travels with the value. A history not obtained for
    # no stated reason is a caller contract violation, not a value to record:
    # a NOT_EVALUATED with no reason is the unexplained negative the standing
    # rule exists to keep out.
    if history.reason is None:
        raise ValueError("term history not obtained states no reason")
    return TermInForceDetermination(value=NOT_EVALUATED, reason=history.reason)


def _not_in_force(coverages: list["_Coverage"], loss_date: date) -> TermInForceDetermination:
    # The loss date is strictly inside no period of any term. If it falls
    # within a term's dates after a cancellation that stands, that cancellation
    # ended the coverage and is cited - the latest such one, whose lapse the
    # date is in. Otherwise no term ran on that date and nothing is cited:
    # before the first term, after the last, or in a gap between two.
    standing = _standing_cancellations(coverages, loss_date)
    if not standing:
        return TermInForceDetermination(value=NOT_IN_FORCE)
    latest = max(cancelled for cancelled, _ in standing)
    # Two terms cancelled on the same date that both hold the loss date is an
    # inconsistent history; the first stated is cited, and the value is the
    # same either way.
    term = next(term for cancelled, term in standing if cancelled == latest)
    return TermInForceDetermination(value=NOT_IN_FORCE, term=term, cancellation_effective=latest)


def _standing_cancellations(
    coverages: list["_Coverage"], loss_date: date
) -> list[tuple[date, PolicyTerm]]:
    standing: list[tuple[date, PolicyTerm]] = []
    for coverage in coverages:
        cancelled = coverage.lapse_cancellation(loss_date)
        if cancelled is not None:
            standing.append((cancelled, coverage.term))
    return standing


@dataclass(frozen=True)
class _Coverage:
    """One term as the periods it was actually in force. A period's first and
    last dates are boundaries - coverage incepts and ends at 12:01 a.m., and
    intake holds a date, not an instant - and a date strictly inside one is
    covered. A term's nominal expiration after a mid-term cancellation, and its
    effective date under a cancellation flat from inception, end no period and
    so are not boundaries: nothing turns on the loss time on a date the term
    did not run to, which is the spec's own precedence for a rescinded date."""

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


def _coverage_of(term: PolicyTerm) -> _Coverage:
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
    return _Coverage(term, tuple(p for p in periods if p[0] < p[1]), tuple(cancellations))


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
