"""The notices table: the row a receipt creates and every decision rewrites.

Extracted from store.py in item 5g for the reason payloads.py was extracted in
item 5e and audit.py in item 5f - that module had two lines of headroom against
the size gate and this item adds three columns to this table, two of which every
decision writes. What moved is unchanged apart from those columns.

**This is the one table in the schema a later write is allowed to change**, and
the extraction is a good place to say why. `audit_entries`, `payload_records` and
`siu_indicator_events` carry BEFORE UPDATE / BEFORE DELETE triggers because each
records what was observed at a moment; a notice row records what the notice says
*now*, and its state legitimately moves RECEIVED -> PENDED -> TRIAGED. The
jurisdiction marking and the future-dated-loss determination arriving in item 5g
belong here for exactly that reason: both are re-derived from the merged current
view every time the rules run, so a resolution that supplies a property state
replaces them rather than appending beside them. The trail of what was believed
when is the audit entries and the SIU events, not this row.

Both instants go through COALESCE, so each takes a value once and no later write
can replace it - item 5e decision (a)'s "written once and never rewritten",
enforced by the statement rather than by call order.
"""

import sqlite3
from datetime import datetime

from claimgate.domain.models import FutureDatedLossResult, ValidationBlocker
from claimgate.shell.records import NoticeRecord, dump_blockers, notice_from_row


def receive(
    connection: sqlite3.Connection, notice_id: str, carrier_code: str, received_at: datetime
) -> None:
    """The row as the receipt transaction writes it: no state beyond RECEIVED,
    no blockers, and no decision of any kind, because no rule has run."""
    connection.execute(
        "INSERT INTO notices (notice_id, carrier_code, state, blockers, received_at)"
        " VALUES (?, ?, 'RECEIVED', '[]', ?)",
        (notice_id, carrier_code, received_at.isoformat()),
    )


def write_decision(
    connection: sqlite3.Connection, notice_id: str, *, state: str,
    blockers: tuple[ValidationBlocker, ...], severity: str | None, queue: str | None,
    jurisdiction_marking: str | None, future_dated_loss: FutureDatedLossResult,
    pended_at: datetime | None, resolved_at: datetime | None,
) -> None:
    """Everything one run of the rules concluded, in one statement, so the notice
    cannot hold a state from one evaluation and a determination from another.
    Passing None for either instant leaves whatever is already there."""
    connection.execute(
        "UPDATE notices SET state = ?, blockers = ?, severity = ?, queue = ?,"
        " jurisdiction_marking = ?, future_dated_loss = ?, future_dated_loss_reason = ?,"
        " pended_at = COALESCE(pended_at, ?), resolved_at = COALESCE(resolved_at, ?)"
        " WHERE notice_id = ?",
        (state, dump_blockers(blockers), severity, queue, jurisdiction_marking,
         future_dated_loss.value, future_dated_loss.reason,
         _stamp(pended_at), _stamp(resolved_at), notice_id),
    )


def get(connection: sqlite3.Connection, notice_id: str) -> NoticeRecord | None:
    row = connection.execute(
        "SELECT * FROM notices WHERE notice_id = ?", (notice_id,)
    ).fetchone()
    return None if row is None else notice_from_row(row)


def count(connection: sqlite3.Connection) -> int:
    row = connection.execute("SELECT COUNT(*) AS total FROM notices").fetchone()
    return int(row["total"])


def _stamp(instant: datetime | None) -> str | None:
    return None if instant is None else instant.isoformat()
