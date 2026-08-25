"""SQLite persistence for notices, audit trails, payload records, and keys.

Engine decided 2026-08-24, ASSUMPTIONS.md "Persistence engine": stdlib sqlite3,
STRICT tables, constraints declared in the schema, no ORM. The constraint that
forced the decision - uniqueness on (carrier_code, idempotency_key) "enforced
by a database constraint, not a check-then-write" - lives in schema.py.

**A created notice is two transactions, not one** (corrected 2026-08-25).
`submission()` opens BEGIN IMMEDIATE and commits once; the receipt transaction
carries the payload record, the notice at RECEIVED, its RECEIVED audit entry
and the idempotency key row, and commits *before* any domain rule runs, with
the decision following in a second transaction. PHASE2_DESIGN.md requires that:
the receipt is "a deliberate two-write design" so that "a bug in rule
evaluation must never be able to erase or delay the fact that a notice was
received," and one transaction spanning both writes would roll the receipt back
on any exception rule evaluation raised - the outcome that design forbids. The
one-transaction shape was an advisor instruction that contradicted the design
and was reversed before merge. Refusals and replays stay single-transaction,
and IMMEDIATE still serializes an idempotency lookup with the insert after it.

Owns the actor identity phase 2 writes (audit schema: actor_id "caller-asserted
in phase 2", actor_authenticated false on every entry, no exceptions - nothing
has been verified because phase 2 verifies nothing). It owns no wall clock any
more: every timestamp it writes is the instant the caller supplied for that
call. See ASSUMPTIONS.md, "One receipt clock, not two", as extended to the
resolution path.

The payload table moved to payloads.py in item 5e - the arrival sequence is what
that item extends, and this module had four lines of headroom before it did. The
methods below that name payloads delegate there so callers keep one store.
"""

import sqlite3
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from datetime import datetime
from typing import Any

from claimgate.domain.models import ValidationBlocker
from claimgate.shell import payloads
from claimgate.shell.records import (
    AuditEntry,
    NoticeRecord,
    PayloadRecord,
    audit_entry_from_row,
    dump_blockers,
    notice_from_row,
)
from claimgate.shell.schema import SCHEMA_STATEMENTS

UNVERIFIED_ACTOR_ID = "no verified identity"


class IdempotencyKeyAlreadyRememberedError(Exception):
    """The (carrier_code, idempotency_key) UNIQUE constraint refused a second
    row, so a concurrent identical submission committed first. PHASE2_DESIGN.md
    asks for exactly this - "Concurrent identical requests must resolve by
    constraint violation, not by a race condition" - so it is the mechanism
    working, not a defect. notice_intake.py resolves it by re-reading the key."""


class NoticeStore:
    def __init__(self, database_path: str) -> None:
        # No default path: a store that silently picks its own database is a
        # store that silently picks the wrong one. Tests pass ":memory:".
        self._connection = sqlite3.connect(database_path, isolation_level=None)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        for statement in SCHEMA_STATEMENTS:
            self._connection.execute(statement)

    @contextmanager
    def submission(self) -> Iterator[None]:
        """One submission, one transaction. IMMEDIATE takes the write lock at
        BEGIN, so the read that decides whether this is a replay cannot be
        overtaken by a writer committing after it."""
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            yield
        except BaseException:
            self._connection.execute("ROLLBACK")
            raise
        self._connection.execute("COMMIT")

    def receive_notice(
        self,
        notice_id: str,
        carrier_code: str,
        raw_payload: Mapping[str, Any],
        received_at: datetime,
    ) -> None:
        self._connection.execute(
            "INSERT INTO notices"
            " (notice_id, carrier_code, state, blockers, severity, queue, received_at)"
            " VALUES (?, ?, 'RECEIVED', '[]', NULL, NULL, ?)",
            (notice_id, carrier_code, received_at.isoformat()),
        )
        payloads.append(self._connection, carrier_code, raw_payload, received_at, notice_id)
        self.append_audit_entry(
            notice_id, from_state=None, to_state="RECEIVED", actor_type="EXTERNAL",
            occurred_at=received_at, blockers=(),
        )

    def record_decision(
        self,
        notice_id: str,
        *,
        state: str,
        blockers: tuple[ValidationBlocker, ...],
        severity: str | None,
        queue: str | None,
        occurred_at: datetime,
    ) -> None:
        """Intake's decision transaction. A decision that lands in PENDED stamps
        the pend instant, which is the instant this decision was made and not a
        second clock read (item 5e decision (a))."""
        self.write_notice_decision(
            notice_id, state=state, blockers=blockers, severity=severity, queue=queue,
            pended_at=occurred_at if state == "PENDED" else None, resolved_at=None,
        )
        self.append_audit_entry(
            notice_id, from_state="RECEIVED", to_state=state, actor_type="SYSTEM",
            occurred_at=occurred_at, blockers=blockers,
        )

    def write_notice_decision(
        self, notice_id: str, *, state: str, blockers: tuple[ValidationBlocker, ...],
        severity: str | None, queue: str | None,
        pended_at: datetime | None, resolved_at: datetime | None,
    ) -> None:
        """The notice row every decision writes, intake's and a resolution's
        alike. Both instants go through COALESCE, so each takes a value once and
        no later write can replace it - item 5e decision (a)'s "written once and
        never rewritten", enforced by the statement rather than by call order.
        Passing None leaves whatever is already there."""
        self._connection.execute(
            "UPDATE notices SET state = ?, blockers = ?, severity = ?, queue = ?,"
            " pended_at = COALESCE(pended_at, ?), resolved_at = COALESCE(resolved_at, ?)"
            " WHERE notice_id = ?",
            (state, dump_blockers(blockers), severity, queue,
             _stamp(pended_at), _stamp(resolved_at), notice_id),
        )

    def refuse_payload(
        self, carrier_code: str, raw_payload: Mapping[str, Any], received_at: datetime
    ) -> str:
        return payloads.append(self._connection, carrier_code, raw_payload, received_at, None)

    def append_notice_payload(
        self, notice_id: str, carrier_code: str,
        content: Mapping[str, Any], received_at: datetime,
    ) -> str:
        """A resolution's own immutable record, at the next position in the
        notice's arrival sequence. What it carries is what that reviewer
        supplied and nothing else - the sequence is the notice."""
        return payloads.append(self._connection, carrier_code, content, received_at, notice_id)

    def get_notice(self, notice_id: str) -> NoticeRecord | None:
        row = self._connection.execute(
            "SELECT * FROM notices WHERE notice_id = ?", (notice_id,)
        ).fetchone()
        return None if row is None else notice_from_row(row)

    def get_audit_trail(self, notice_id: str) -> tuple[AuditEntry, ...]:
        rows = self._connection.execute(
            "SELECT * FROM audit_entries WHERE notice_id = ? ORDER BY entry_id", (notice_id,)
        ).fetchall()
        return tuple(audit_entry_from_row(row) for row in rows)

    def find_key(self, carrier_code: str, idempotency_key: str) -> NoticeRecord | None:
        """The notice a remembered key names, or None if this pair has never
        created one. A key is remembered only by the notice it created."""
        row = self._connection.execute(
            "SELECT notices.* FROM idempotency_keys"
            " JOIN notices ON notices.notice_id = idempotency_keys.notice_id"
            " WHERE idempotency_keys.carrier_code = ?"
            " AND idempotency_keys.idempotency_key = ?",
            (carrier_code, idempotency_key),
        ).fetchone()
        return None if row is None else notice_from_row(row)

    def remember_key(
        self, carrier_code: str, idempotency_key: str, notice_id: str, *, replacing_expired: bool
    ) -> None:
        """A plain INSERT, deliberately: the UNIQUE constraint is the mechanism
        that resolves concurrent identical submissions, and an upsert would
        silence it. An expired row is deleted first, so the key ends up held by
        the notice it just created and by no other."""
        if replacing_expired:
            self._connection.execute(
                "DELETE FROM idempotency_keys WHERE carrier_code = ? AND idempotency_key = ?",
                (carrier_code, idempotency_key),
            )
        try:
            self._connection.execute(
                "INSERT INTO idempotency_keys (carrier_code, idempotency_key, notice_id)"
                " VALUES (?, ?, ?)",
                (carrier_code, idempotency_key, notice_id),
            )
        except sqlite3.IntegrityError as violation:
            raise IdempotencyKeyAlreadyRememberedError(carrier_code, idempotency_key) from violation

    def get_notice_payload_reference(self, notice_id: str) -> str:
        return payloads.notice_reference(self._connection, notice_id)

    def get_notice_payloads(self, notice_id: str) -> tuple[PayloadRecord, ...]:
        return payloads.for_notice(self._connection, notice_id)

    def count_notices(self) -> int:
        row = self._connection.execute("SELECT COUNT(*) AS total FROM notices").fetchone()
        return int(row["total"])

    def list_payloads(self) -> tuple[PayloadRecord, ...]:
        return payloads.all_records(self._connection)

    def append_audit_entry(
        self, notice_id: str, *, from_state: str | None, to_state: str, actor_type: str,
        occurred_at: datetime, blockers: tuple[ValidationBlocker, ...],
        actor_id: str = UNVERIFIED_ACTOR_ID, outcome: str = "APPLIED", note: str | None = None,
    ) -> None:
        """Every transition attempt gets one, refused attempts included
        (PHASE2_DESIGN.md's audit log). actor_authenticated is written 0 here and
        nowhere else, for every actor type without exception: phase 2 has no
        authentication mechanism, so nothing has been verified, and a caller
        cannot assert otherwise because this method does not take it."""
        self._connection.execute(
            "INSERT INTO audit_entries"
            " (notice_id, carrier_code, from_state, to_state, actor_id, actor_type,"
            " occurred_at, blockers, outcome, actor_authenticated, note)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)",
            (notice_id, self._carrier_code_of(notice_id), from_state, to_state, actor_id,
             actor_type, occurred_at.isoformat(), dump_blockers(blockers), outcome, note),
        )

    def _carrier_code_of(self, notice_id: str) -> str:
        row = self._connection.execute(
            "SELECT carrier_code FROM notices WHERE notice_id = ?", (notice_id,)
        ).fetchone()
        return str(row["carrier_code"])


def _stamp(instant: datetime | None) -> str | None:
    return None if instant is None else instant.isoformat()
