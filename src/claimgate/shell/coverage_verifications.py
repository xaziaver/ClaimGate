"""The coverage_verifications table: what the policy search and the two coverage
rules concluded about a notice, one dated row per evaluation, and the view of
it that GET /notices/{id} shows.

PHASE3_DESIGN.md, "Persistence": a second append-only table on
siu_indicator_events' pattern - keyed (notice_id, ordinal), stamped with the
ruleset_version and the evaluated_at instant of the transaction that wrote it,
BEFORE UPDATE / BEFORE DELETE triggers in schema.py - holding what the outcome
needs and never the history the port returned. That is the identification's
value and reason, the matched policy's reference and the identifiers it was
found on (item 7g); the term-in-force value
and reason, the deciding term's effective and expiration dates and the
cancellation that produced the value where one did; the continuous-coverage
value, date and reason; the port's as_of and the binding that answered. Each
row is a dated fact about what was verified when, which is why it is a trail
and not columns on the notice row (item 5f's argument, reapplied), and the
latest row is what the notice shows now.

The module lives beside store.py rather than inside it, as siu_events.py does,
because that module has no room left under the size gate. Unlike siu_events.py
it carries its own record type and reads the store's connection through the
property store.py exposes for exactly this, so records.py and store.py both
stay where they are (item 7f). An ordinary attribute, not a restricted one: the
view is on GET /notices/{id}'s allow-list (serialization.py), and SIU stays
where it is.

The continuous-coverage date and reason are stored although the design's column
list did not name them: policy_match.feature reads the date off the notice, the
SIU event beside it records only the indicator the date fed, and a date shown
absent with no reason would be a not-computed result reported as empty
(CLAUDE.md). Recorded as a judgment in QUEUE.md's 7f implementation paragraph.
"""

import sqlite3
from dataclasses import dataclass
from datetime import date, datetime
from typing import cast

from claimgate.domain.continuous_coverage import (
    ContinuousCoverageDerivation,
    ContinuousCoverageValue,
)
from claimgate.domain.coverage import TermInForceDetermination
from claimgate.domain.policy_match import PolicyMatch, PolicyMatchValue
from claimgate.shell.store import NoticeStore


@dataclass(frozen=True)
class Verification:
    """What the intake path verified about a notice, before the decision
    transaction records it: the three domain results, and the search answer's
    instant and binding (shell/policy_match.py)."""

    match: PolicyMatch
    term: TermInForceDetermination
    coverage: ContinuousCoverageDerivation
    as_of: datetime
    binding: str
    # The found policy's own number, from the search answer, None unless the
    # match is MATCHED (ASSUMPTIONS.md, 7h decision 9). Carried so duplicate
    # detection compares against the policy that was found rather than the
    # number the reporter typed (decision 4); `append` below does not store it
    # and `view_of` does not show it - the row keeps the reference only.
    policy_number: str | None = None


@dataclass(frozen=True)
class CoverageVerification:
    """One stored row. Every value column follows the domain's convention: a
    reason only beside NOT_EVALUATED, a reference only beside MATCHED, a term
    and a cancellation only where one decided the value, a date only beside
    DERIVED. `ordinal` is the row's position in its notice's own trail,
    assigned where it is written; `evaluated_at` is the instant of the
    transaction that wrote it, `as_of` the instant the source's answer reflects
    - the same instant in the live-query shape and not in an extract's."""

    notice_id: str
    ordinal: int
    policy_match: str
    policy_match_reason: str | None
    policy_reference: str | None
    identified_on: str | None
    term_in_force: str
    term_reason: str | None
    term_effective: date | None
    term_expiration: date | None
    cancellation_effective: date | None
    continuous_coverage: str
    continuous_coverage_reason: str | None
    continuous_coverage_date: date | None
    as_of: datetime
    binding: str
    ruleset_version: str
    evaluated_at: datetime


@dataclass(frozen=True)
class CoverageVerificationView:
    """The verification as GET /notices/{id} shows it, named as
    features/policy_match.feature reads it. The trail's own bookkeeping - the
    ordinal, the rule set, the binding, the instant the row was written - stays
    on the row, as the notice's receipt instant stays off NoticeView."""

    policy_match: str
    matched_policy: str | None
    identified_on: str | None
    reason: str | None
    term_in_force: str
    deciding_term_effective: date | None
    deciding_term_expiration: date | None
    continuous_coverage_date: date | None
    continuous_coverage_reason: str | None
    as_of: datetime


def view_of(record: CoverageVerification | None) -> CoverageVerificationView | None:
    """None where the notice has no verification: nothing has been searched, so
    there is nothing to show - a different fact from a search that found nothing,
    which is a MATCHED-or-not value with its reason."""
    if record is None:
        return None
    return CoverageVerificationView(
        policy_match=record.policy_match,
        matched_policy=record.policy_reference,
        identified_on=record.identified_on,
        reason=record.policy_match_reason,
        term_in_force=record.term_in_force,
        deciding_term_effective=record.term_effective,
        deciding_term_expiration=record.term_expiration,
        continuous_coverage_date=record.continuous_coverage_date,
        continuous_coverage_reason=record.continuous_coverage_reason,
        as_of=record.as_of,
    )


def match_of(record: CoverageVerification) -> PolicyMatch:
    """The stored identification as the domain's own result, for the resolution
    path to re-assert unchanged (ASSUMPTIONS.md, 7f decision 6)."""
    return PolicyMatch(
        cast(PolicyMatchValue, record.policy_match),
        policy_reference=record.policy_reference,
        identified_on=record.identified_on,
        reason=record.policy_match_reason,
    )


def derivation_of(record: CoverageVerification) -> ContinuousCoverageDerivation:
    """The stored derivation as the domain's own result, so the resolution path
    carries the date onto its candidate through the same producer intake uses."""
    return ContinuousCoverageDerivation(
        cast(ContinuousCoverageValue, record.continuous_coverage),
        continuous_since=record.continuous_coverage_date,
        reason=record.continuous_coverage_reason,
    )


def append(
    store: NoticeStore, notice_id: str, verification: Verification,
    *, ruleset_version: str, evaluated_at: datetime,
) -> None:
    """One evaluation's row, at the next free position in the notice's own
    order, inside whatever transaction the caller holds - the decision
    transaction, so the row commits with the decision it belongs to."""
    connection = store.connection
    connection.execute(
        "INSERT INTO coverage_verifications"
        " (notice_id, ordinal, policy_match, policy_match_reason, policy_reference,"
        " identified_on, term_in_force, term_reason, term_effective, term_expiration,"
        " cancellation_effective, continuous_coverage, continuous_coverage_reason,"
        " continuous_coverage_date, as_of, binding, ruleset_version, evaluated_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (notice_id, _next_ordinal(connection, notice_id), *_columns(verification),
         verification.as_of.isoformat(), verification.binding, ruleset_version,
         evaluated_at.isoformat()),
    )


def latest(store: NoticeStore, notice_id: str) -> CoverageVerification | None:
    """What the notice shows now: its most recent row, by stored position."""
    row = store.connection.execute(
        "SELECT * FROM coverage_verifications WHERE notice_id = ? ORDER BY ordinal DESC LIMIT 1",
        (notice_id,),
    ).fetchone()
    return None if row is None else _from_row(row)


def for_notice(store: NoticeStore, notice_id: str) -> tuple[CoverageVerification, ...]:
    """One notice's trail in its own order."""
    rows = store.connection.execute(
        "SELECT * FROM coverage_verifications WHERE notice_id = ? ORDER BY ordinal", (notice_id,)
    ).fetchall()
    return tuple(_from_row(row) for row in rows)


def _columns(verification: Verification) -> tuple[str | None, ...]:
    match, term, coverage = verification.match, verification.term, verification.coverage
    deciding = term.term
    return (
        match.value, match.reason, match.policy_reference, match.identified_on,
        term.value, term.reason,
        None if deciding is None else deciding.effective.isoformat(),
        None if deciding is None else deciding.expiration.isoformat(),
        _stamp(term.cancellation_effective),
        coverage.value, coverage.reason, _stamp(coverage.continuous_since),
    )


def _next_ordinal(connection: sqlite3.Connection, notice_id: str) -> int:
    row = connection.execute(
        "SELECT COUNT(*) AS total FROM coverage_verifications WHERE notice_id = ?", (notice_id,)
    ).fetchone()
    return int(row["total"])


def _from_row(row: sqlite3.Row) -> CoverageVerification:
    return CoverageVerification(
        notice_id=row["notice_id"],
        ordinal=row["ordinal"],
        policy_match=row["policy_match"],
        policy_match_reason=row["policy_match_reason"],
        policy_reference=row["policy_reference"],
        identified_on=row["identified_on"],
        term_in_force=row["term_in_force"],
        term_reason=row["term_reason"],
        term_effective=_day(row["term_effective"]),
        term_expiration=_day(row["term_expiration"]),
        cancellation_effective=_day(row["cancellation_effective"]),
        continuous_coverage=row["continuous_coverage"],
        continuous_coverage_reason=row["continuous_coverage_reason"],
        continuous_coverage_date=_day(row["continuous_coverage_date"]),
        as_of=datetime.fromisoformat(row["as_of"]),
        binding=row["binding"],
        ruleset_version=row["ruleset_version"],
        evaluated_at=datetime.fromisoformat(row["evaluated_at"]),
    )


def _stamp(day: date | None) -> str | None:
    return None if day is None else day.isoformat()


def _day(raw: str | None) -> date | None:
    return None if raw is None else date.fromisoformat(raw)
