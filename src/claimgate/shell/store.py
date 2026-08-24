"""SQLite persistence for notices, audit trails, payload records, and keys.

Engine decided 2026-08-24, ASSUMPTIONS.md "Persistence engine": stdlib sqlite3,
STRICT tables, constraints declared in the schema, no ORM. The constraint that
forced the decision - uniqueness on (carrier_code, idempotency_key) "enforced
by a database constraint, not a check-then-write" - lives in schema.py.

**One POST /notices is one transaction.** `submission()` opens BEGIN IMMEDIATE
and commits once, so a refusal, or a receipt with its decision and its key,
lands whole or not at all. That turns "the raw payload and the RECEIVED write
are one statutory fact" from a comment describing call order into a guarantee.

*Noted rather than resolved:* PHASE2_DESIGN.md calls the receipt "a deliberate
two-write design" so "a bug in rule evaluation must never be able to erase or
delay the fact that a notice was received." Inside one transaction a raise
between the receipt and the decision rolls the receipt back too. No such path
is reachable today - both raising helpers in notice_intake.py run before the
receipt - and atomicity is the stronger guarantee for the failure that does
exist, a receipt stranded with no decision. Flagged for whoever adds a raise
between those two writes.

Owns the actor identity phase 2 writes (audit schema: actor_id "caller-asserted
in phase 2", actor_authenticated false on every entry, no exceptions - nothing
has been verified because phase 2 verifies nothing). It owns no wall clock any
more: every timestamp in a submission is the receipt instant the caller
supplies. See ASSUMPTIONS.md, "One receipt clock, not two".
"""

import sqlite3
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from datetime import datetime
from typing import Any

from claimgate.domain.models import ValidationBlocker
from claimgate.shell.records import (
    AuditEntry,
    NoticeRecord,
    PayloadRecord,
    audit_entry_from_row,
    dump_blockers,
    notice_from_row,
    payload_from_row,
    payload_reference,
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
        self._insert_payload(carrier_code, raw_payload, received_at, notice_id)
        self._append_audit_entry(
            notice_id, carrier_code, None, "RECEIVED", "EXTERNAL", received_at, ()
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
        self._connection.execute(
            "UPDATE notices SET state = ?, blockers = ?, severity = ?, queue = ?"
            " WHERE notice_id = ?",
            (state, dump_blockers(blockers), severity, queue, notice_id),
        )
        carrier_code = self._carrier_code_of(notice_id)
        self._append_audit_entry(
            notice_id, carrier_code, "RECEIVED", state, "SYSTEM", occurred_at, blockers
        )

    def refuse_payload(
        self, carrier_code: str, raw_payload: Mapping[str, Any], received_at: datetime
    ) -> str:
        self._insert_payload(carrier_code, raw_payload, received_at, None)
        return payload_reference(raw_payload)

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
        """The reference of the payload the notice was created from - position
        0 of its arrival sequence, the one item 5e's resolution records append
        after."""
        row = self._connection.execute(
            "SELECT reference FROM payload_records WHERE notice_id = ? AND arrival_index = 0",
            (notice_id,),
        ).fetchone()
        return str(row["reference"])

    def count_notices(self) -> int:
        row = self._connection.execute("SELECT COUNT(*) AS total FROM notices").fetchone()
        return int(row["total"])

    def list_payloads(self) -> tuple[PayloadRecord, ...]:
        rows = self._connection.execute(
            "SELECT * FROM payload_records ORDER BY payload_id"
        ).fetchall()
        return tuple(payload_from_row(row) for row in rows)

    def _carrier_code_of(self, notice_id: str) -> str:
        row = self._connection.execute(
            "SELECT carrier_code FROM notices WHERE notice_id = ?", (notice_id,)
        ).fetchone()
        return str(row["carrier_code"])

    def _insert_payload(
        self,
        carrier_code: str,
        raw_payload: Mapping[str, Any],
        received_at: datetime,
        notice_id: str | None,
    ) -> None:
        self._connection.execute(
            "INSERT INTO payload_records"
            " (reference, carrier_code, received_at, notice_id, arrival_index)"
            " VALUES (?, ?, ?, ?, ?)",
            (payload_reference(raw_payload), carrier_code, received_at.isoformat(),
             notice_id, self._next_arrival_index(notice_id)),
        )

    def _next_arrival_index(self, notice_id: str | None) -> int:
        if notice_id is None:
            return 0
        row = self._connection.execute(
            "SELECT COUNT(*) AS total FROM payload_records WHERE notice_id = ?", (notice_id,)
        ).fetchone()
        return int(row["total"])

    def _append_audit_entry(
        self,
        notice_id: str,
        carrier_code: str,
        from_state: str | None,
        to_state: str,
        actor_type: str,
        occurred_at: datetime,
        blockers: tuple[ValidationBlocker, ...],
    ) -> None:
        self._connection.execute(
            "INSERT INTO audit_entries"
            " (notice_id, carrier_code, from_state, to_state, actor_id, actor_type,"
            " occurred_at, blockers, outcome, actor_authenticated)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'APPLIED', 0)",
            (notice_id, carrier_code, from_state, to_state, UNVERIFIED_ACTOR_ID,
             actor_type, occurred_at.isoformat(), dump_blockers(blockers)),
        )
