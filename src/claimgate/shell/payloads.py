"""The payload_records table: the arrival sequence a notice's content is read
from, and the one place it is written.

Extracted from store.py in item 5e rather than grown there. The sequence is what
this item extends - a resolution appends its own record to it, and the notice's
current view is derived by overlaying the sequence field by field - and store.py
had four lines of headroom against the size gate before any of that arrived.

PHASE2_DESIGN.md: "The raw inbound payload is stored once, verbatim, immutable,
and referenced by hash - never copied into audit entries. ... A resolution's
supplemental data gets its own separate immutable payload record with its own
hash, linked to the notice in order." Both halves of that are here: `reference`
is the hash, `content` is the verbatim payload, and the BEFORE UPDATE / BEFORE
DELETE triggers in schema.py are what make "immutable" a refusal rather than a
convention.

Content is serialized with the same recipe the reference is hashed from
(records.serialize_payload), so the stored bytes and the hash over them can
never describe different things.
"""

import sqlite3
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from claimgate.shell.records import (
    PayloadRecord,
    payload_from_row,
    payload_reference,
    serialize_payload,
)


def append(
    connection: sqlite3.Connection,
    carrier_code: str,
    content: Mapping[str, Any],
    received_at: datetime,
    notice_id: str | None,
    error_code: str | None = None,
) -> str:
    """One immutable record at the next free position in its notice's sequence,
    returning the hash that references it. A refused submission has no notice to
    link to and takes position 0 unlinked - SQLite treats NULLs as distinct, so
    UNIQUE (notice_id, arrival_index) does not collide them.

    error_code names the deployment fault a submission was answered with, where
    there was one (item 5i); it is metadata about the answer and never joins
    content, which stays the verbatim payload the reference is hashed from."""
    reference = payload_reference(content)
    connection.execute(
        "INSERT INTO payload_records"
        " (reference, content, carrier_code, received_at, notice_id, arrival_index, error_code)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (reference, serialize_payload(content), carrier_code, received_at.isoformat(),
         notice_id, _next_arrival_index(connection, notice_id), error_code),
    )
    return reference


def for_notice(connection: sqlite3.Connection, notice_id: str) -> tuple[PayloadRecord, ...]:
    """A notice's records in arrival order - the order the current view is
    overlaid in, so it is read from the stored position rather than from
    insertion order."""
    rows = connection.execute(
        "SELECT * FROM payload_records WHERE notice_id = ? ORDER BY arrival_index",
        (notice_id,),
    ).fetchall()
    return tuple(payload_from_row(row) for row in rows)


def all_records(connection: sqlite3.Connection) -> tuple[PayloadRecord, ...]:
    rows = connection.execute("SELECT * FROM payload_records ORDER BY payload_id").fetchall()
    return tuple(payload_from_row(row) for row in rows)


def notice_reference(connection: sqlite3.Connection, notice_id: str) -> str:
    """The reference of the payload the notice was created from - position 0 of
    its arrival sequence, the one a resolution's records append after."""
    row = connection.execute(
        "SELECT reference FROM payload_records WHERE notice_id = ? AND arrival_index = 0",
        (notice_id,),
    ).fetchone()
    return str(row["reference"])


def _next_arrival_index(connection: sqlite3.Connection, notice_id: str | None) -> int:
    if notice_id is None:
        return 0
    row = connection.execute(
        "SELECT COUNT(*) AS total FROM payload_records WHERE notice_id = ?", (notice_id,)
    ).fetchone()
    return int(row["total"])
