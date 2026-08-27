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
audit table moved to audit.py in item 5f, which adds a column to every entry and
a second table beside them, and siu_indicator_events arrived in siu_events.py
rather than here for the same reason. The notices table itself moved to
notices.py in item 5g, which adds three columns to it. What is left here is the
connection, the transaction boundary, and the composition each caller wants; the
methods below that name a table delegate to its module so callers keep one
store.

No statement anywhere in this package updates or deletes an SIU indicator event
(ASSUMPTIONS.md, item 5f decision 3); tests/shell/test_store.py reads the
package looking for one, so the absence is checked rather than asserted here.
"""

import sqlite3
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from datetime import datetime
from typing import Any

from claimgate.domain.models import FutureDatedLossResult, ValidationBlocker
from claimgate.shell import audit, notices, payloads, siu_events
from claimgate.shell.records import (
    AuditEntry,
    NoticeRecord,
    PayloadRecord,
    SiuIndicatorEvent,
    SiuIndicatorObservation,
    notice_from_row,
)
from claimgate.shell.schema import SCHEMA_STATEMENTS


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
        notices.receive(self._connection, notice_id, carrier_code, received_at)
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
        jurisdiction_marking: str | None,
        future_dated_loss: FutureDatedLossResult,
        occurred_at: datetime,
    ) -> None:
        """Intake's decision transaction. A decision that lands in PENDED stamps
        the pend instant, which is the instant this decision was made and not a
        second clock read (item 5e decision (a))."""
        self.write_notice_decision(
            notice_id, state=state, blockers=blockers, severity=severity, queue=queue,
            jurisdiction_marking=jurisdiction_marking, future_dated_loss=future_dated_loss,
            pended_at=occurred_at if state == "PENDED" else None, resolved_at=None,
        )
        self.append_audit_entry(
            notice_id, from_state="RECEIVED", to_state=state, actor_type="SYSTEM",
            occurred_at=occurred_at, blockers=blockers,
        )

    def write_notice_decision(
        self, notice_id: str, *, state: str, blockers: tuple[ValidationBlocker, ...],
        severity: str | None, queue: str | None, jurisdiction_marking: str | None,
        future_dated_loss: FutureDatedLossResult,
        pended_at: datetime | None, resolved_at: datetime | None,
    ) -> None:
        """The notice row every decision writes, intake's and a resolution's
        alike."""
        notices.write_decision(
            self._connection, notice_id, state=state, blockers=blockers, severity=severity,
            queue=queue, jurisdiction_marking=jurisdiction_marking,
            future_dated_loss=future_dated_loss, pended_at=pended_at, resolved_at=resolved_at,
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
        return notices.get(self._connection, notice_id)

    def get_audit_trail(self, notice_id: str) -> tuple[AuditEntry, ...]:
        return audit.for_notice(self._connection, notice_id)

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
        return notices.count(self._connection)

    def list_payloads(self) -> tuple[PayloadRecord, ...]:
        return payloads.all_records(self._connection)

    def append_audit_entry(
        self, notice_id: str, *, from_state: str | None, to_state: str, actor_type: str,
        occurred_at: datetime, blockers: tuple[ValidationBlocker, ...],
        actor_id: str = audit.UNVERIFIED_ACTOR_ID, outcome: str = "APPLIED",
        note: str | None = None,
    ) -> None:
        audit.append(
            self._connection, notice_id, from_state=from_state, to_state=to_state,
            actor_type=actor_type, occurred_at=occurred_at, blockers=blockers,
            actor_id=actor_id, outcome=outcome, note=note,
        )

    def append_siu_events(
        self, notice_id: str, observations: tuple[SiuIndicatorObservation, ...],
        *, ruleset_version: str, evaluated_at: datetime,
    ) -> None:
        siu_events.append_all(
            self._connection, notice_id, observations,
            ruleset_version=ruleset_version, evaluated_at=evaluated_at,
        )

    def get_siu_events(self, notice_id: str) -> tuple[SiuIndicatorEvent, ...]:
        return siu_events.for_notice(self._connection, notice_id)

    def list_siu_events(self) -> tuple[SiuIndicatorEvent, ...]:
        return siu_events.all_records(self._connection)
