"""In-memory persistence for notices, their audit trails, and refused payloads.

Phase 2 names no database technology; item 5d's idempotency key is the first
thing in this project that needs a real database constraint, and it isn't
built yet. This store is the minimal thing that makes GET /notices/{id}
retrieve what POST /notices wrote in the same process - not a decision about
production storage.

Owns every wall-clock timestamp and the actor identity phase 2 writes
(PHASE2_DESIGN.md's audit schema: actor_id "caller-asserted in phase 2",
actor_authenticated false on every entry, no exceptions - phase 2 has no
authentication mechanism, so nothing has been verified).
"""

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Any

from claimgate.domain.models import ValidationBlocker

UNVERIFIED_ACTOR_ID = "no verified identity"


@dataclass(frozen=True)
class NoticeRecord:
    notice_id: str
    carrier_code: str
    state: str
    blockers: tuple[ValidationBlocker, ...]
    severity: str | None
    queue: str | None


@dataclass(frozen=True)
class AuditEntry:
    # Field set matches PHASE2_DESIGN.md's "Audit log" schema table.
    notice_id: str
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
    carrier_code: str
    received_at: datetime


class NoticeStore:
    def __init__(self) -> None:
        self.notices: dict[str, NoticeRecord] = {}
        self.audit_entries: dict[str, list[AuditEntry]] = {}
        self.payloads: list[PayloadRecord] = []

    def receive_notice(self, notice_id: str, carrier_code: str) -> None:
        self.notices[notice_id] = NoticeRecord(
            notice_id=notice_id,
            carrier_code=carrier_code,
            state="RECEIVED",
            blockers=(),
            severity=None,
            queue=None,
        )
        self._append_audit_entry(
            notice_id, from_state=None, to_state="RECEIVED", actor_type="EXTERNAL"
        )

    def record_decision(
        self,
        notice_id: str,
        *,
        state: str,
        blockers: tuple[ValidationBlocker, ...],
        severity: str | None,
        queue: str | None,
    ) -> None:
        current = self.notices[notice_id]
        self.notices[notice_id] = replace(
            current, state=state, blockers=blockers, severity=severity, queue=queue
        )
        self._append_audit_entry(
            notice_id, from_state="RECEIVED", to_state=state, actor_type="SYSTEM", blockers=blockers
        )

    def refuse_payload(self, carrier_code: str, raw_payload: Mapping[str, Any]) -> str:
        reference = hashlib.sha256(
            json.dumps(raw_payload, sort_keys=True, default=str).encode()
        ).hexdigest()
        self.payloads.append(
            PayloadRecord(
                reference=reference, carrier_code=carrier_code, received_at=datetime.now(UTC)
            )
        )
        return reference

    def get_notice(self, notice_id: str) -> NoticeRecord | None:
        return self.notices.get(notice_id)

    def get_audit_trail(self, notice_id: str) -> tuple[AuditEntry, ...]:
        return tuple(self.audit_entries.get(notice_id, ()))

    def _append_audit_entry(
        self,
        notice_id: str,
        *,
        from_state: str | None,
        to_state: str,
        actor_type: str,
        blockers: tuple[ValidationBlocker, ...] = (),
    ) -> None:
        entry = AuditEntry(
            notice_id=notice_id,
            from_state=from_state,
            to_state=to_state,
            actor_id=UNVERIFIED_ACTOR_ID,
            actor_type=actor_type,
            occurred_at=datetime.now(UTC),
            blockers=blockers,
            outcome="APPLIED",
            actor_authenticated=False,
        )
        self.audit_entries.setdefault(notice_id, []).append(entry)
