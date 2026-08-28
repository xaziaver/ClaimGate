"""The SQLite schema phase 2 writes into: five tables and the triggers that
make PHASE2_DESIGN.md's append-only rules enforceable.

STRICT tables and schema-declared constraints, per ASSUMPTIONS.md's
"Persistence engine" - the point of choosing an engine at all was that
`PHASE2_DESIGN.md`'s Idempotency section requires uniqueness on
`(carrier_code, idempotency_key)` "enforced by a database constraint, not a
check-then-write". That constraint is declared here, not checked in Python.

Two design statements become enforced facts rather than conventions:

- **"Append-only. No update path and no delete path exist in this schema, in
  phase 2, at all."** The `BEFORE UPDATE` and `BEFORE DELETE` triggers on
  `audit_entries` and `payload_records` `RAISE(ABORT)`. A correction has to be
  a compensating entry because the database refuses anything else. `notices`
  carries no such trigger: a notice's state legitimately moves RECEIVED ->
  TRIAGED/PENDED, and it is the audit trail, not the notice row, that is the
  history.
- **"The raw inbound payload is stored once, verbatim, ... and referenced by
  hash."** Each payload record links to its notice, carries its position in that
  notice's arrival sequence, and - since item 5e - carries the content itself.
  `reference` is the hash the design names; `content` is the "verbatim" half of
  the same sentence, stored because a resolution's current view is derived by
  overlaying the sequence field by field and a hash cannot be overlaid. Item 5e
  appends a resolution's own payload record to that sequence; `UNIQUE
  (notice_id, arrival_index)` is what keeps it from acquiring two occupants of
  one position. SQLite treats NULLs as distinct, so the unlinked refusal
  records - which have no notice and no sequence - are exempt from it, which is
  the intended reading.

`payload_records.error_code` is item 5i (ASSUMPTIONS.md, "Item 5i decisions",
ruling 4). A deployment fault is answered before any notice exists, and
`audit_entries.notice_id` is `NOT NULL REFERENCES notices (notice_id)`, so no
audit entry can carry the fault - the receipted payload record is the only thing
left that outlives the request, and it names which fault it was. Nullable
because every other record has no fault to name: it is null on the accepted
path, on the schema-invalid 400 and on the mis-keyed 409 alike. It is metadata
about how the submission was answered and sits beside `carrier_code` and
`received_at`, never inside `content` - the verbatim payload and the hash over
it stay exactly what arrived.

`notices.jurisdiction_marking`, `notices.future_dated_loss` and
`notices.future_dated_loss_reason` are item 5g. They sit on the notice row and
not in a trail of their own because they are the notice's *current* answer,
rewritten whenever the rules run again - unlike `audit_entries` and
`siu_indicator_events`, which record what was observed at a moment and carry the
triggers that make that permanent. `future_dated_loss_reason` is null unless
`future_dated_loss` is `NOT_EVALUATED`, the same convention
`siu_indicator_events.reason_code` follows. All three are null until the first
decision is written: a notice at RECEIVED has had no rule run over it, which is
not the same fact as a rule having run and found nothing.

`notices.pended_at` and `notices.resolved_at` are item 5e decision (a)
(ASSUMPTIONS.md): the two ends of the interval Fla. Stat. 627.70131(8)(b)
defines, which PHASE2_DESIGN.md asks to be recorded "precisely, in UTC, on the
notice and in the audit trail". Whether that interval means anything is a
downstream legal determination and nothing here computes it. Both columns are
written through COALESCE, so each takes a value once and no later write can
replace it; a refused attempt's instant lives on its audit entry alone. Adding
these columns does not upgrade an existing database - CREATE TABLE IF NOT
EXISTS leaves an older file as it found it - which decision (b) accepts.

`carrier_code` is on `audit_entries` because PHASE2_DESIGN.md's "Carrier
reference" section requires it persisted on every audit entry. It is
attribution and nothing else; no query in this package branches on it.

`siu_indicator_events` is item 5f's, and it is a table rather than columns on
`notices` because that is PHASE2_DESIGN.md's "SIU handling" point 1: "physical
separation is the part that's hard to retrofit ... columns on the main record
are a leak risk in every future query and serializer, forever." Nothing on the
notice row reaches it, so no serializer over that row can carry it by accident.
It gets the same `BEFORE UPDATE` / `BEFORE DELETE` refusal the audit trail has,
for the reason ASSUMPTIONS.md's item 5f decision 3 gives: "unevaluated is not
negative" is only auditable if the unevaluated evaluation is written down, and a
trail something can edit afterwards records what was last believed rather than
what was observed. `reason_code` is null unless the value is `NOT_EVALUATED`,
and `threshold_days` is null where the carrier configured none - never zero,
which is a real carrier choice meaning every notice is late
(carrier_configuration.feature) and would record a rule nobody configured.
`UNIQUE (notice_id, ordinal)` keeps one position in a notice's trail to one row,
the way it does for the arrival sequence above.

Adding it does not upgrade an existing database, for the same reason
`pended_at` and `resolved_at` did not: `CREATE TABLE IF NOT EXISTS` leaves an
older file as it found it, and item 5e decision (b) accepts that a schema change
recreates the database.
"""

SCHEMA_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS notices (
        notice_id TEXT PRIMARY KEY,
        carrier_code TEXT NOT NULL,
        state TEXT NOT NULL,
        blockers TEXT NOT NULL,
        severity TEXT,
        queue TEXT,
        received_at TEXT NOT NULL,
        jurisdiction_marking TEXT,
        future_dated_loss TEXT,
        future_dated_loss_reason TEXT,
        pended_at TEXT,
        resolved_at TEXT
    ) STRICT
    """,
    """
    CREATE TABLE IF NOT EXISTS audit_entries (
        entry_id INTEGER PRIMARY KEY,
        notice_id TEXT NOT NULL REFERENCES notices (notice_id),
        carrier_code TEXT NOT NULL,
        from_state TEXT,
        to_state TEXT NOT NULL,
        actor_id TEXT NOT NULL,
        actor_type TEXT NOT NULL,
        occurred_at TEXT NOT NULL,
        blockers TEXT NOT NULL,
        outcome TEXT NOT NULL,
        actor_authenticated INTEGER NOT NULL,
        note TEXT,
        ruleset_version TEXT,
        build_sha TEXT
    ) STRICT
    """,
    """
    CREATE TABLE IF NOT EXISTS payload_records (
        payload_id INTEGER PRIMARY KEY,
        reference TEXT NOT NULL,
        content TEXT NOT NULL,
        carrier_code TEXT NOT NULL,
        received_at TEXT NOT NULL,
        notice_id TEXT REFERENCES notices (notice_id),
        arrival_index INTEGER NOT NULL,
        error_code TEXT,
        UNIQUE (notice_id, arrival_index)
    ) STRICT
    """,
    """
    CREATE TABLE IF NOT EXISTS idempotency_keys (
        carrier_code TEXT NOT NULL,
        idempotency_key TEXT NOT NULL,
        notice_id TEXT NOT NULL REFERENCES notices (notice_id),
        UNIQUE (carrier_code, idempotency_key)
    ) STRICT
    """,
    """
    CREATE TABLE IF NOT EXISTS siu_indicator_events (
        event_id INTEGER PRIMARY KEY,
        notice_id TEXT NOT NULL REFERENCES notices (notice_id),
        ordinal INTEGER NOT NULL,
        indicator TEXT NOT NULL,
        value TEXT NOT NULL,
        reason_code TEXT,
        threshold_days INTEGER,
        ruleset_version TEXT NOT NULL,
        evaluated_at TEXT NOT NULL,
        UNIQUE (notice_id, ordinal)
    ) STRICT
    """,
    """
    CREATE TRIGGER IF NOT EXISTS audit_entries_are_append_only_no_update
    BEFORE UPDATE ON audit_entries
    BEGIN SELECT RAISE(ABORT, 'audit entries are append-only'); END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS audit_entries_are_append_only_no_delete
    BEFORE DELETE ON audit_entries
    BEGIN SELECT RAISE(ABORT, 'audit entries are append-only'); END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS payload_records_are_immutable_no_update
    BEFORE UPDATE ON payload_records
    BEGIN SELECT RAISE(ABORT, 'payload records are immutable'); END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS payload_records_are_immutable_no_delete
    BEFORE DELETE ON payload_records
    BEGIN SELECT RAISE(ABORT, 'payload records are immutable'); END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS siu_indicator_events_are_append_only_no_update
    BEFORE UPDATE ON siu_indicator_events
    BEGIN SELECT RAISE(ABORT, 'SIU indicator events are append-only'); END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS siu_indicator_events_are_append_only_no_delete
    BEFORE DELETE ON siu_indicator_events
    BEGIN SELECT RAISE(ABORT, 'SIU indicator events are append-only'); END
    """,
)
