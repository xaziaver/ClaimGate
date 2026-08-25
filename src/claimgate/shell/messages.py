"""What crosses the shell's boundary on POST /notices and GET /notices/{id}:
the reporter's fields, the response, the retrieval view, one submission's
bundled inputs, and the one shape that crosses between the two transactions a
created notice takes.

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
class AcceptedNotice:
    """A notice whose receipt transaction has committed and whose decision has
    not been made yet. It exists because rule evaluation runs between the two,
    inside neither - see notice_intake.py."""

    notice_id: str
    candidate: Candidate
    today: date
    rules: CarrierRules
