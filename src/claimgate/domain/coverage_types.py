"""The shapes the term-in-force and continuous-coverage rules read and answer
with (split out of coverage.py in item 7f, no behaviour change). coverage.py
re-exports every name here, and callers keep importing from it.
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
class PriorCoverage:
    # Coverage on the risk by a prior carrier, as the source records it: a data
    # point for the continuous-coverage rule (item 7b), never a term in force here.
    effective: date
    ending: date


@dataclass(frozen=True)
class TermHistory:
    # The policy source's answer, in the shape every port answer takes
    # (PHASE3_DESIGN.md): reason is set only when the history was not obtained,
    # terms only when it was.
    value: Literal["OBTAINED", "NOT_OBTAINED"]
    terms: tuple[PolicyTerm, ...] = ()
    reason: str | None = None
    # Item 7b, read by the continuous-coverage rule only. history_from is the
    # source's horizon - every term in force on or after it is supplied, earlier
    # ones may be missing; None asserts a complete history.
    history_from: date | None = None
    prior_coverage: PriorCoverage | None = None


@dataclass(frozen=True)
class TermInForceDetermination:
    # term is the deciding term: the one in force for IN_FORCE; for
    # BOUNDARY_DAY the one term whose boundary the date is; for NOT_IN_FORCE
    # the one whose standing cancellation holds the date, or else the one whose
    # coverage most recently ended before it. None where no single term decided
    # - a date two terms share, a loss before any term ran, or NOT_EVALUATED
    # (coverage.py, "Which term decides"). cancellation_effective is set only
    # when a standing cancellation produced the value; reason only for
    # NOT_EVALUATED, and it is the source's reason.
    value: TermInForceValue
    term: PolicyTerm | None = None
    cancellation_effective: date | None = None
    reason: str | None = None
