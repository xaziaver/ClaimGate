"""The duplicate_evaluations table - what duplicate detection concluded about a
notice on its transition into TRIAGED, one dated row per evaluation - the view
of it GET /notices/{id} shows, and the evaluation itself.

PHASE3_DESIGN.md, "Duplicate detection gets its caller", and ASSUMPTIONS.md's
two 7h entries. The third trail on siu_indicator_events' pattern (trails.py):
keyed (notice_id, ordinal), stamped with the ruleset_version and the
evaluated_at of the transaction that wrote it, refused any update or delete.
On coverage_verifications.py's pattern it carries its own record type and reads
the store's connection, so store.py stays where it is.

**Evaluated on the transition into TRIAGED only, on either path** (decision 2):
after the rules have returned the state and outside every transaction, the row
written inside the decision or write transaction beside the verification and
the SIU events, so a notice never rests TRIAGED with half its attributes. A
PENDED notice gets no call and no row; it is compared when it is triaged, on
what it carries then.

**Against the policy the search found** (decisions 4 and 9): the claims port
scopes by the matched reference, and the domain rule compares policy numbers,
so the found policy's own number - carried on the verification, never stored -
is placed on the candidate before find_duplicates runs. Without it a notice
matched on the insured name and postal code would read clean.

**Two words for one fact** (decision 8): the status a row and the view carry is
OBTAINED or NOT_EVALUATED, the locked spec's vocabulary; the domain rule's
EVALUATED is translated to OBTAINED in `_evaluated` below and nowhere else.
The rule's own reasons pass through unchanged (decision 3); where the shell
never asks the rule - the search did not answer, or the claims could not be
read - the reason is the verification's or the claims answer's, and nothing is
added to the enumeration duplicates.feature calls complete.
"""

import json
import sqlite3
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Final

from claimgate.domain.duplicates import find_duplicates
from claimgate.domain.models import Candidate, DuplicateMatchResult
from claimgate.shell.coverage_verifications import Verification
from claimgate.shell.ports import NOT_OBTAINED, ClaimsPort
from claimgate.shell.store import NoticeStore

OBTAINED: Final = "OBTAINED"
NOT_EVALUATED: Final = "NOT_EVALUATED"


@dataclass(frozen=True)
class DuplicateEvaluation:
    """What one transition into TRIAGED concluded, before the transaction
    records it. `candidates` is set only beside OBTAINED and `reason` only
    beside NOT_EVALUATED, the domain's convention; `as_of` and `binding` are
    the claims answer's where the port was asked, else the verification's,
    because the reason then is the search's own."""

    status: str
    candidates: tuple[str, ...]
    reason: str | None
    as_of: datetime
    binding: str


@dataclass(frozen=True)
class DuplicateEvaluationRecord:
    """One stored row. `ordinal` is the row's position in its notice's own
    trail, assigned where it is written; `evaluated_at` is the instant of the
    transaction that wrote it."""

    notice_id: str
    ordinal: int
    status: str
    candidates: tuple[str, ...]
    reason: str | None
    as_of: datetime
    binding: str
    ruleset_version: str
    evaluated_at: datetime


@dataclass(frozen=True)
class DuplicateEvaluationView:
    """The evaluation as GET /notices/{id} shows it, named as
    features/duplicate_evaluation.feature reads it: one structure, so the
    status and its reason cannot be read apart (ASSUMPTIONS.md 2026-08-22)."""

    status: str
    candidates: tuple[str, ...]
    reason: str | None


def evaluate_on_triage(
    state: str, port: ClaimsPort, verification: Verification | None,
    candidate: Candidate, window_days: int,
) -> DuplicateEvaluation | None:
    """The evaluation where the decision is TRIAGED, and None where it is not
    (decision 2). The second condition is a type guard and not a case: an
    unsearchable notice or one with no loss date pends on its own blocker
    (policy_match.py), so a TRIAGED notice always carries a verification."""
    if state != "TRIAGED" or verification is None:
        return None
    return evaluate_duplicates(port, verification, candidate, window_days)


def evaluate_duplicates(
    port: ClaimsPort, verification: Verification, candidate: Candidate, window_days: int
) -> DuplicateEvaluation:
    """Two branches and no more. A TRIAGED notice's match is MATCHED or
    NOT_EVALUATED - NOT_MATCHED and AMBIGUOUS pend (policy_match.feature) -
    and only MATCHED names a reference and a found number, so a verification
    with neither is the search that did not answer, and the claims port is not
    asked: the evaluation carries the search's reason (decisions 3 and 9)."""
    match, found = verification.match, verification.policy_number
    if match.policy_reference is None or found is None:
        return DuplicateEvaluation(
            NOT_EVALUATED, (), match.reason, verification.as_of, verification.binding
        )
    answer = port.existing_claims(match.policy_reference)
    if answer.value == NOT_OBTAINED:
        return DuplicateEvaluation(NOT_EVALUATED, (), answer.reason, answer.as_of, answer.binding)
    result = find_duplicates(replace(candidate, policy_number=found), answer.claims, window_days)
    return DuplicateEvaluation(
        _evaluated(result), result.matches, result.reason, answer.as_of, answer.binding
    )


def _evaluated(result: DuplicateMatchResult) -> str:
    """Decision 8: the domain's EVALUATED is the shell's OBTAINED, translated
    here and nowhere else; the rule's NOT_EVALUATED passes through unchanged."""
    return OBTAINED if result.value == "EVALUATED" else NOT_EVALUATED


def view_of(record: DuplicateEvaluationRecord | None) -> DuplicateEvaluationView | None:
    """None where the notice has no evaluation: it has not been triaged, so
    nothing was compared - a different fact from a comparison that found
    nothing, which is OBTAINED with no candidates."""
    if record is None:
        return None
    return DuplicateEvaluationView(record.status, record.candidates, record.reason)


def append(
    store: NoticeStore, notice_id: str, evaluation: DuplicateEvaluation,
    *, ruleset_version: str, evaluated_at: datetime,
) -> None:
    """One evaluation's row, at the next free position in the notice's own
    order, inside whatever transaction the caller holds - the decision or the
    write transaction, so the row commits with the decision it belongs to."""
    connection = store.connection
    connection.execute(
        "INSERT INTO duplicate_evaluations"
        " (notice_id, ordinal, status, candidates, reason, as_of, binding,"
        " ruleset_version, evaluated_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (notice_id, _next_ordinal(connection, notice_id), evaluation.status,
         json.dumps(list(evaluation.candidates)), evaluation.reason,
         evaluation.as_of.isoformat(), evaluation.binding, ruleset_version,
         evaluated_at.isoformat()),
    )


def latest(store: NoticeStore, notice_id: str) -> DuplicateEvaluationRecord | None:
    """What the notice shows now: its most recent row, by stored position."""
    row = store.connection.execute(
        "SELECT * FROM duplicate_evaluations WHERE notice_id = ? ORDER BY ordinal DESC LIMIT 1",
        (notice_id,),
    ).fetchone()
    return None if row is None else _from_row(row)


def _next_ordinal(connection: sqlite3.Connection, notice_id: str) -> int:
    row = connection.execute(
        "SELECT COUNT(*) AS total FROM duplicate_evaluations WHERE notice_id = ?", (notice_id,)
    ).fetchone()
    return int(row["total"])


def _from_row(row: sqlite3.Row) -> DuplicateEvaluationRecord:
    return DuplicateEvaluationRecord(
        notice_id=row["notice_id"],
        ordinal=row["ordinal"],
        status=row["status"],
        candidates=tuple(json.loads(row["candidates"])),
        reason=row["reason"],
        as_of=datetime.fromisoformat(row["as_of"]),
        binding=row["binding"],
        ruleset_version=row["ruleset_version"],
        evaluated_at=datetime.fromisoformat(row["evaluated_at"]),
    )
