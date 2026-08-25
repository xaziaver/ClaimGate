"""What crosses the shell's boundary on POST /notices, GET /notices/{id} and
POST /notices/{id}/resolution: the reporter's fields, the responses, the
retrieval view, one submission's and one resolution's bundled inputs, and the
one shape that crosses between the two transactions a created notice takes.

Separated from notice_intake.py so idempotency.py can name these shapes without
importing the orchestration that assembles them - and so notice_intake.py stays
inside the size gate now that a submission has an idempotency key to carry.
"""

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import date, datetime
from typing import Any

from claimgate.domain.models import Candidate, CarrierRules, ValidationBlocker
from claimgate.shell.records import NoticeRecord
from claimgate.shell.store import NoticeStore


@dataclass(frozen=True)
class NoticeFields:
    """The reporter-supplied notice content - everything but the carrier_code
    envelope, the submission instant, the jurisdiction timezone and the
    idempotency key, which are the shell's inputs, not the notice's."""

    policy_number: str = ""
    loss_date: str | None = None
    loss_type: str = ""
    notice_type: str = ""
    claimant_name: str | None = None
    claimant_contact: str | None = None
    incident_description: str | None = None


@dataclass(frozen=True)
class SubmitNoticeResponse:
    status: int
    notice_id: str | None = None
    state: str | None = None
    blockers: tuple[ValidationBlocker, ...] = ()
    severity: str | None = None
    queue: str | None = None
    # Carried on a 201 and on a replay's 200 alike: a replay reports the
    # original notice's receipt timestamp, which has to be readable somewhere
    # to be reported at all (PHASE2_DESIGN.md's Idempotency section).
    received_at: datetime | None = None
    # Carried on the refusals that keep what arrived - the schema-invalid 400
    # and the mis-keyed 409 - so the reporter and the carrier can name the same
    # communication. Never on the unknown-carrier 400, which persists nothing.
    reference: str | None = None


@dataclass(frozen=True)
class NoticeView:
    notice_id: str
    state: str
    blockers: tuple[ValidationBlocker, ...]
    severity: str | None
    queue: str | None

    @classmethod
    def of(cls, record: NoticeRecord) -> "NoticeView":
        """The stored notice as GET /notices/{id} shows it: everything the
        record carries except the receipt timestamp and the carrier, which are
        envelope and attribution rather than the notice."""
        return cls(record.notice_id, record.state, record.blockers, record.severity, record.queue)


@dataclass(frozen=True)
class Submission:
    """One inbound submission's inputs, bundled so the steps that consume them
    read as steps rather than as parameter lists."""

    store: NoticeStore
    carrier_code: str
    submitted_at: datetime
    jurisdiction_timezone: str
    carrier_rules_source: Mapping[str, Mapping[str, Any]]
    fields: NoticeFields
    idempotency_key: str | None

    @property
    def raw_payload(self) -> dict[str, Any]:
        return asdict(self.fields)


@dataclass(frozen=True)
class Resolution:
    """One reviewer's attempt to release a pended notice, bundled the way a
    Submission is. `supplied` carries only the fields that reviewer named -
    keys are NoticeFields field names, and a field absent from it keeps
    whatever an earlier arrival gave it (ASSUMPTIONS.md item 5e decision 1:
    there is no way to blank a field in phase 2, only to replace one).

    There is no actor_type here. The endpoint stamps USER (decision 4): an
    unauthenticated caller asserting SYSTEM would be asserting something
    nothing in phase 2 can check."""

    store: NoticeStore
    notice_id: str
    actor_id: str
    resolved_at: datetime
    jurisdiction_timezone: str
    carrier_rules_source: Mapping[str, Mapping[str, Any]]
    supplied: Mapping[str, Any]
    note: str | None = None


@dataclass(frozen=True)
class ResolutionResponse:
    """One shape for 200 and 422 alike, so a reviewer's client parses one body
    and lets the status distinguish cleared from still-blocked
    (PHASE2_DESIGN.md). The 409 carries the notice's current state, because
    state is read from the body and never inferred from status. The 400 carries
    nothing: the notice is not read at all, so there is nothing to report."""

    status: int
    notice_id: str | None = None
    state: str | None = None
    blockers: tuple[ValidationBlocker, ...] = ()
    severity: str | None = None
    queue: str | None = None


@dataclass(frozen=True)
class AcceptedNotice:
    """A notice whose receipt transaction has committed and whose decision has
    not been made yet. It exists because rule evaluation runs between the two,
    inside neither - see notice_intake.py."""

    notice_id: str
    candidate: Candidate
    today: date
    rules: CarrierRules
