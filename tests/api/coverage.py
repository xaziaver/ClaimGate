"""Thin, stable test API over the coverage verification domain area."""

from dataclasses import replace
from datetime import date

from claimgate.domain.coverage import (
    CANCELLATION,
    REINSTATEMENT,
    PolicyTerm,
    StatusChangeKind,
    TermHistory,
    TermInForceDetermination,
    TermStatusChange,
)
from claimgate.domain.coverage import determine_term_in_force as _determine_term_in_force


def policy_term(effective: date, expiration: date) -> PolicyTerm:
    return PolicyTerm(effective=effective, expiration=expiration)


def cancelled(term: PolicyTerm, effective: date) -> PolicyTerm:
    return _with_change(term, CANCELLATION, effective)


def reinstated(term: PolicyTerm, effective: date) -> PolicyTerm:
    return _with_change(term, REINSTATEMENT, effective)


def reinstated_retroactively(term: PolicyTerm, as_of: date) -> PolicyTerm:
    """A retroactive reinstatement is one dated on the cancellation it rescinds -
    the domain reads the date, not a flag. The spec's phrase carries an as-of
    date, so this checks it names that cancellation rather than quietly
    recording a reinstatement with a lapse under a phrase that promised none."""
    cancellations = [c.effective for c in term.status_changes if c.kind == CANCELLATION]
    if not cancellations or as_of != cancellations[-1]:
        raise ValueError(
            f"retroactive reinstatement as of {as_of} names no cancellation of this term"
        )
    return _with_change(term, REINSTATEMENT, as_of)


def _with_change(term: PolicyTerm, kind: StatusChangeKind, effective: date) -> PolicyTerm:
    change = TermStatusChange(kind=kind, effective=effective)
    return replace(term, status_changes=(*term.status_changes, change))


def term_history(terms: list[PolicyTerm]) -> TermHistory:
    return TermHistory(value="OBTAINED", terms=tuple(terms))


def unobtained_term_history(reason: str) -> TermHistory:
    return TermHistory(value="NOT_OBTAINED", reason=reason)


def determine_term_in_force(history: TermHistory, loss_date: date) -> TermInForceDetermination:
    return _determine_term_in_force(history, loss_date)
