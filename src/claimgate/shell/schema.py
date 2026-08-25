"""The SQLite schema phase 2 writes into: four tables and the triggers that
make PHASE2_DESIGN.md's audit-log rule enforceable.

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
- **"The raw inbound payload is stored once ... and referenced by hash."** Each
  payload record links to its notice and carries its position in that notice's
  arrival sequence. Item 5e appends a resolution's own payload record to the
  same sequence; `UNIQUE (notice_id, arrival_index)` is what keeps that
  sequence from acquiring two occupants of one position. SQLite treats NULLs as
  distinct, so the unlinked refusal records - which have no notice and no
  sequence - are exempt from it, which is the intended reading.

`carrier_code` is on `audit_entries` because PHASE2_DESIGN.md's "Carrier
reference" section requires it persisted on every audit entry. It is
attribution and nothing else; no query in this package branches on it.
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
        received_at TEXT NOT NULL
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
        carrier_code TEXT NOT NULL,
        received_at TEXT NOT NULL,
        notice_id TEXT REFERENCES notices (notice_id),
        arrival_index INTEGER NOT NULL,
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
)
