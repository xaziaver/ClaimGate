"""The siu_indicator_events table: the write-side trail, and the one place it is
written.

PHASE2_DESIGN.md's "SIU handling" point 4 asks for exactly this - "an
append-only `siu_indicator_events` table, recording which indicator fired, under
which `ruleset_version`, and when" - as write-side correctness that is needed
whether or not an auth system exists. Point 1 is why it is its own table and not
columns on `notices`: physical separation is the part that is hard to retrofit,
and a column on the main record is a leak risk in every future query and
serializer. Nothing reachable from a notice row reaches these rows.

One row per indicator per evaluation, `FALSE` and `NOT_EVALUATED` included
(ASSUMPTIONS.md, item 5f decision 3). A trail of positives would make a missing
row mean three different things at once - not evaluated, evaluated and negative,
or never run - and "unevaluated is not negative" is only auditable if the
unevaluated evaluation is written down.

Append-only, and there is no statement here that updates or deletes one: the
`BEFORE UPDATE` and `BEFORE DELETE` triggers in schema.py make that a refusal
from the database rather than a property of this file staying as it is.

The threshold each evaluation applied is stored beside its outcome. That is what
makes a row answerable a year later without anyone reconstructing which carrier
configuration was in force - the rule version and the number it was given, the
two facts together.
"""

import sqlite3
from collections.abc import Sequence
from datetime import datetime

from claimgate.shell.records import SiuIndicatorEvent, SiuIndicatorObservation, siu_event_from_row


def append_all(
    connection: sqlite3.Connection,
    notice_id: str,
    observations: Sequence[SiuIndicatorObservation],
    *,
    ruleset_version: str,
    evaluated_at: datetime,
) -> None:
    """One evaluation's observations, at the next free positions in the notice's
    own order. They are written in one call because they are one evaluation:
    a notice carrying an event for one indicator and not the other is not a
    state any caller should be able to produce."""
    ordinal = _next_ordinal(connection, notice_id)
    for offset, observation in enumerate(observations):
        connection.execute(
            "INSERT INTO siu_indicator_events"
            " (notice_id, ordinal, indicator, value, reason_code, threshold_days,"
            " ruleset_version, evaluated_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (notice_id, ordinal + offset, observation.indicator, observation.result.value,
             observation.result.reason, observation.threshold_days, ruleset_version,
             evaluated_at.isoformat()),
        )


def for_notice(connection: sqlite3.Connection, notice_id: str) -> tuple[SiuIndicatorEvent, ...]:
    """One notice's trail in its own order, read from the stored ordinal rather
    than from insertion order."""
    rows = connection.execute(
        "SELECT * FROM siu_indicator_events WHERE notice_id = ? ORDER BY ordinal",
        (notice_id,),
    ).fetchall()
    return tuple(siu_event_from_row(row) for row in rows)


def all_records(connection: sqlite3.Connection) -> tuple[SiuIndicatorEvent, ...]:
    rows = connection.execute("SELECT * FROM siu_indicator_events ORDER BY event_id").fetchall()
    return tuple(siu_event_from_row(row) for row in rows)


def _next_ordinal(connection: sqlite3.Connection, notice_id: str) -> int:
    row = connection.execute(
        "SELECT COUNT(*) AS total FROM siu_indicator_events WHERE notice_id = ?", (notice_id,)
    ).fetchone()
    return int(row["total"])
