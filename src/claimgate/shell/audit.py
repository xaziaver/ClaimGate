"""The audit_entries table: every transition attempt phase 2 records, and the
one place they are written.

Extracted from store.py in item 5f for the reason payloads.py was extracted from
it in 5e - that module had seven lines of headroom against the size gate and this
item adds both a column to every entry here and a second table beside them. What
moved is unchanged apart from that column.

PHASE2_DESIGN.md's audit log: "Append-only. No update path and no delete path
exist in this schema, in phase 2, at all. Corrections are compensating entries,
never edits to history." The BEFORE UPDATE / BEFORE DELETE triggers in schema.py
make that a refusal from the database rather than a property of this file, and
every transition *attempt* gets an entry, refused ones included.

Owns the actor identity phase 2 writes: actor_authenticated is written 0 here and
nowhere else, for every actor type without exception. Phase 2 has no
authentication mechanism, so nothing has been verified, and a caller cannot
assert otherwise because these functions do not take it.

**Every entry carries the domain rule set's label** (ASSUMPTIONS.md, item 5f's
ruleset-version decision), which has been null since item 5c because no agreed
value existed. Every entry rather than only the SYSTEM ones: the entry that
releases a pend is a USER entry and the full validation ran to produce it, so
actor type does not tell rule-driven entries from the rest, and an entry that
names the code in force when it was written is not a claim that a rule fired.
"""

import sqlite3
from datetime import datetime

from claimgate.domain.models import ValidationBlocker
from claimgate.domain.ruleset import RULESET_VERSION
from claimgate.shell.records import AuditEntry, audit_entry_from_row, dump_blockers

UNVERIFIED_ACTOR_ID = "no verified identity"


def append(
    connection: sqlite3.Connection, notice_id: str, *, from_state: str | None, to_state: str,
    actor_type: str, occurred_at: datetime, blockers: tuple[ValidationBlocker, ...],
    actor_id: str = UNVERIFIED_ACTOR_ID, outcome: str = "APPLIED", note: str | None = None,
) -> None:
    connection.execute(
        "INSERT INTO audit_entries"
        " (notice_id, carrier_code, from_state, to_state, actor_id, actor_type,"
        " occurred_at, blockers, outcome, actor_authenticated, note, ruleset_version)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)",
        (notice_id, _carrier_code_of(connection, notice_id), from_state, to_state, actor_id,
         actor_type, occurred_at.isoformat(), dump_blockers(blockers), outcome, note,
         RULESET_VERSION),
    )


def for_notice(connection: sqlite3.Connection, notice_id: str) -> tuple[AuditEntry, ...]:
    rows = connection.execute(
        "SELECT * FROM audit_entries WHERE notice_id = ? ORDER BY entry_id", (notice_id,)
    ).fetchall()
    return tuple(audit_entry_from_row(row) for row in rows)


def _carrier_code_of(connection: sqlite3.Connection, notice_id: str) -> str:
    row = connection.execute(
        "SELECT carrier_code FROM notices WHERE notice_id = ?", (notice_id,)
    ).fetchone()
    return str(row["carrier_code"])
