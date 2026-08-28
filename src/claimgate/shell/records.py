"""The rows phase 2 persists, and the recipe that references a payload.

Separated from store.py so that module stays inside the size gate once the
SQLite plumbing arrived; these are the shapes, store.py is the machinery.

Field sets match PHASE2_DESIGN.md's "Audit log" schema table and the notice and
payload records its Record-state-model and audit-log sections describe. Two
fields are additions this item made rather than found there:

- `AuditEntry.carrier_code`, required by PHASE2_DESIGN.md's "Carrier reference"
  section ("persisted on every notice and every audit entry - for attribution
  only ... never branched on") and absent from the entry-schema table until
  2026-08-24. Attribution only; nothing reads it to decide anything.
- `PayloadRecord.arrival_index`, the position of a payload in its notice's
  arrival sequence. Item 5e appends a resolution's payload record to that same
  sequence, so the order has to be a stored fact now rather than an artefact of
  insertion order later.
- `PayloadRecord.content`, the payload itself. PHASE2_DESIGN.md says the raw
  payload is "stored once, verbatim, immutable, and referenced by hash"; item 5d
  had no reader for the verbatim half and stored only the hash. Item 5e derives
  a notice's current view by overlaying the sequence field by field, which a
  hash cannot answer, so the content is stored from here on.
- `SiuIndicatorObservation` and `SiuIndicatorEvent`, item 5f. The first is what
  one evaluation observed about one indicator - the domain's own result plus the
  threshold that evaluation was given; the second is that observation as the
  append-only trail stores it, with the notice it is about, its position in that
  notice's own order, the rule set that produced it and when. They are two shapes
  rather than one because the ordinal is assigned where the row is written and is
  not something the evaluation knows.
- `NoticeRecord.jurisdiction_marking` and `NoticeRecord.future_dated_loss`, item
  5g. The first is what a notice whose property state selects no jurisdiction
  carries for a person; the second is the loss-date rule's own three-valued
  determination, which needs a home of its own because the place a positive one
  goes - the notice's blockers - is the place that would block, and an
  unsupported jurisdiction must not block. Both are null until a decision is
  written: a notice resting at RECEIVED has had no rule run over it, which is a
  different fact from a rule having run and found nothing.
- `NoticeRecord.pended_at` and `NoticeRecord.resolved_at`, item 5e decision (a):
  the pend instant and the instant of the resolution that released it, the two
  ends of the interval Fla. Stat. 627.70131(8)(b) defines, which
  PHASE2_DESIGN.md asks to be recorded "precisely, in UTC, on the notice and in
  the audit trail". Null until the notice reaches each.
"""

import hashlib
import json
import sqlite3
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from claimgate.domain.models import (
    FutureDatedLossResult,
    SiuIndicatorResult,
    ValidationBlocker,
)


@dataclass(frozen=True)
class NoticeRecord:
    notice_id: str
    carrier_code: str
    state: str
    blockers: tuple[ValidationBlocker, ...]
    severity: str | None
    queue: str | None
    # The statutory acknowledgment clock's start (Fla. Stat. 627.70131(1)(a)),
    # set once at capture and never recomputed - and, since 2026-08-24, the
    # single receipt instant every timestamp in a submission is written from.
    received_at: datetime
    # Rewritten by every decision, unlike the audit trail and the SIU trail
    # beside it: this is what the notice says now, not what was observed when.
    # None on both until the first decision - no rule has run yet.
    jurisdiction_marking: str | None = None
    future_dated_loss: FutureDatedLossResult | None = None
    # Written once each and never rewritten (item 5e decision (a)); a resolution
    # that is refused moves neither, and its own instant lives on its audit entry.
    pended_at: datetime | None = None
    resolved_at: datetime | None = None


@dataclass(frozen=True)
class AuditEntry:
    notice_id: str
    carrier_code: str
    from_state: str | None
    to_state: str
    actor_id: str
    actor_type: str
    occurred_at: datetime
    blockers: tuple[ValidationBlocker, ...]
    outcome: str
    actor_authenticated: bool
    note: str | None = None
    # No agreed value for either exists yet (PHASE2_DESIGN.md); left unset
    # rather than filled with an invented placeholder.
    ruleset_version: str | None = None
    build_sha: str | None = None


@dataclass(frozen=True)
class PayloadRecord:
    reference: str
    # What arrived in this position, verbatim. The sequence is what a notice's
    # current view is read from, so each record holds what arrived in it and
    # nothing more: a resolution's record carries only the fields its reviewer
    # supplied, and a field absent from it keeps whatever an earlier record gave.
    content: dict[str, Any]
    carrier_code: str
    received_at: datetime
    arrival_index: int
    # None for a refused submission - there is no notice to link it to.
    notice_id: str | None = None
    # Which deployment fault this submission was answered with, where it was
    # one (item 5i). None everywhere else, including the 400 and the 409, whose
    # refusals are about what arrived rather than about this deployment.
    error_code: str | None = None


def serialize_payload(raw_payload: Mapping[str, Any]) -> str:
    """The bytes a payload is both hashed from and stored as, so the stored
    content and the reference over it can never describe different things."""
    return json.dumps(raw_payload, sort_keys=True, default=str)


def payload_reference(raw_payload: Mapping[str, Any]) -> str:
    """The recipe ASSUMPTIONS.md records under "The payload reference recipe":
    SHA-256 over the submitted fields as JSON, sort_keys=True, default=str.
    One recipe, so a reporter and a carrier name the same communication the
    same way - and, since item 5d, so a repeated idempotency key can be judged
    a replay or a conflict by comparing references rather than content."""
    return hashlib.sha256(serialize_payload(raw_payload).encode()).hexdigest()


def dump_blockers(blockers: tuple[ValidationBlocker, ...]) -> str:
    return json.dumps([[blocker.code, blocker.field] for blocker in blockers])


def load_blockers(raw: str) -> tuple[ValidationBlocker, ...]:
    return tuple(ValidationBlocker(code=code, field=field) for code, field in json.loads(raw))


def _instant(raw: str | None) -> datetime | None:
    return None if raw is None else datetime.fromisoformat(raw)


def _future_dated_loss(row: sqlite3.Row) -> FutureDatedLossResult | None:
    """Null means no decision has been written, not a determination of False."""
    value = row["future_dated_loss"]
    if value is None:
        return None
    return FutureDatedLossResult(value=value, reason=row["future_dated_loss_reason"])


def notice_from_row(row: sqlite3.Row) -> NoticeRecord:
    return NoticeRecord(
        notice_id=row["notice_id"],
        carrier_code=row["carrier_code"],
        state=row["state"],
        blockers=load_blockers(row["blockers"]),
        severity=row["severity"],
        queue=row["queue"],
        received_at=datetime.fromisoformat(row["received_at"]),
        jurisdiction_marking=row["jurisdiction_marking"],
        future_dated_loss=_future_dated_loss(row),
        pended_at=_instant(row["pended_at"]),
        resolved_at=_instant(row["resolved_at"]),
    )


def audit_entry_from_row(row: sqlite3.Row) -> AuditEntry:
    return AuditEntry(
        notice_id=row["notice_id"],
        carrier_code=row["carrier_code"],
        from_state=row["from_state"],
        to_state=row["to_state"],
        actor_id=row["actor_id"],
        actor_type=row["actor_type"],
        occurred_at=datetime.fromisoformat(row["occurred_at"]),
        blockers=load_blockers(row["blockers"]),
        outcome=row["outcome"],
        actor_authenticated=bool(row["actor_authenticated"]),
        note=row["note"],
        ruleset_version=row["ruleset_version"],
        build_sha=row["build_sha"],
    )


def payload_from_row(row: sqlite3.Row) -> PayloadRecord:
    return PayloadRecord(
        reference=row["reference"],
        content=json.loads(row["content"]),
        carrier_code=row["carrier_code"],
        received_at=datetime.fromisoformat(row["received_at"]),
        arrival_index=row["arrival_index"],
        notice_id=row["notice_id"],
        error_code=row["error_code"],
    )


@dataclass(frozen=True)
class SiuIndicatorObservation:
    """One indicator's outcome and the number the evaluation applied to reach
    it. The threshold is null where the carrier configured none and never zero:
    a configured zero makes every notice late (carrier_configuration.feature),
    so zero standing in for absent would record a rule nobody configured."""

    indicator: str
    result: SiuIndicatorResult
    threshold_days: int | None


@dataclass(frozen=True)
class SiuIndicatorEvent:
    """One stored row of the SIU trail. `ordinal` is its position in its own
    notice's order, assigned where the row is written; `evaluated_at` is the
    instant of the transaction that triaged the notice, which on the resolution
    path is not the instant the interval was counted from (ASSUMPTIONS.md, item
    5f decisions 2 and 3)."""

    notice_id: str
    ordinal: int
    indicator: str
    value: str
    ruleset_version: str
    evaluated_at: datetime
    reason_code: str | None = None
    threshold_days: int | None = None


def siu_event_from_row(row: sqlite3.Row) -> SiuIndicatorEvent:
    return SiuIndicatorEvent(
        notice_id=row["notice_id"],
        ordinal=row["ordinal"],
        indicator=row["indicator"],
        value=row["value"],
        ruleset_version=row["ruleset_version"],
        evaluated_at=datetime.fromisoformat(row["evaluated_at"]),
        reason_code=row["reason_code"],
        threshold_days=row["threshold_days"],
    )
