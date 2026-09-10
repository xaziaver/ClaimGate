"""The evaluation trails: one dated row per evaluation of a notice, keyed
`(notice_id, ordinal)`, stamped with the `ruleset_version` and the
`evaluated_at` of the transaction that wrote it, and refused any update or
delete by trigger.

Split out of schema.py in item 7h, structurally and with no behaviour change:
that module keeps the notice record and its arrival sequence, this one keeps the
tables on `siu_indicator_events`' pattern - item 5f's, item 7f's
`coverage_verifications`, and 7h's `duplicate_evaluations` when it lands - so
each has room under the size gate. schema.py composes `SCHEMA_STATEMENTS` from
both, in the order it always had, so the statements a store executes are the
same statements.

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

`duplicate_evaluations` is item 7h's, the third trail on the same pattern: what
duplicate detection concluded about a notice on its transition into TRIAGED -
the status (`OBTAINED` or `NOT_EVALUATED`, ASSUMPTIONS.md 7h decision 8), the
candidate claim ids as a JSON list, the reason where nothing was compared, the
claims answer's `as_of` and the binding that answered - one row per evaluation,
never the claims the port returned. An ordinary attribute, shown on GET
/notices/{id} through duplicate_evaluations.py's view; `reason` is null unless
the status is `NOT_EVALUATED`, and `candidates` is the empty list there.

`coverage_verifications` is item 7f's (PHASE3_DESIGN.md, "Persistence"), on
`siu_indicator_events`' pattern: `(notice_id, ordinal)`, `ruleset_version`,
`evaluated_at`, the same `BEFORE UPDATE` / `BEFORE DELETE` refusal. It holds
what the policy search and the two coverage rules concluded - the identification
and its reason, the matched reference and the identifiers that found it (item
7g), the term-in-force value and reason with
the deciding term's dates and the cancellation that decided it, the
continuous-coverage value, date and reason, the port's `as_of` and the binding
that answered - and never the history the port returned, which is another
system's data held for no purpose ClaimGate has. Every reason column is null
unless its value is `NOT_EVALUATED`, every reference and date column null unless
its value calls for one. It is an ordinary attribute and reaches GET
/notices/{id} through coverage_verifications.py's view; it is a table and not
columns on `notices` because each row is a dated fact about what was verified
when, and the notice row records only what the notice says now.
"""

TRAIL_TABLES: tuple[str, ...] = (
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
    CREATE TABLE IF NOT EXISTS coverage_verifications (
        verification_id INTEGER PRIMARY KEY,
        notice_id TEXT NOT NULL REFERENCES notices (notice_id),
        ordinal INTEGER NOT NULL,
        policy_match TEXT NOT NULL,
        policy_match_reason TEXT,
        policy_reference TEXT,
        identified_on TEXT,
        term_in_force TEXT NOT NULL,
        term_reason TEXT,
        term_effective TEXT,
        term_expiration TEXT,
        cancellation_effective TEXT,
        continuous_coverage TEXT NOT NULL,
        continuous_coverage_reason TEXT,
        continuous_coverage_date TEXT,
        as_of TEXT NOT NULL,
        binding TEXT NOT NULL,
        ruleset_version TEXT NOT NULL,
        evaluated_at TEXT NOT NULL,
        UNIQUE (notice_id, ordinal)
    ) STRICT
    """,
    """
    CREATE TABLE IF NOT EXISTS duplicate_evaluations (
        evaluation_id INTEGER PRIMARY KEY,
        notice_id TEXT NOT NULL REFERENCES notices (notice_id),
        ordinal INTEGER NOT NULL,
        status TEXT NOT NULL,
        candidates TEXT NOT NULL,
        reason TEXT,
        as_of TEXT NOT NULL,
        binding TEXT NOT NULL,
        ruleset_version TEXT NOT NULL,
        evaluated_at TEXT NOT NULL,
        UNIQUE (notice_id, ordinal)
    ) STRICT
    """,
)

TRAIL_TRIGGERS: tuple[str, ...] = (
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
    """
    CREATE TRIGGER IF NOT EXISTS coverage_verifications_are_append_only_no_update
    BEFORE UPDATE ON coverage_verifications
    BEGIN SELECT RAISE(ABORT, 'coverage verifications are append-only'); END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS coverage_verifications_are_append_only_no_delete
    BEFORE DELETE ON coverage_verifications
    BEGIN SELECT RAISE(ABORT, 'coverage verifications are append-only'); END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS duplicate_evaluations_are_append_only_no_update
    BEFORE UPDATE ON duplicate_evaluations
    BEGIN SELECT RAISE(ABORT, 'duplicate evaluations are append-only'); END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS duplicate_evaluations_are_append_only_no_delete
    BEFORE DELETE ON duplicate_evaluations
    BEGIN SELECT RAISE(ABORT, 'duplicate evaluations are append-only'); END
    """,
)
