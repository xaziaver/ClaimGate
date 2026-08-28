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

from claimgate.domain.models import (
    Candidate,
    CarrierIdentity,
    CarrierRules,
    FutureDatedLossResult,
    Jurisdiction,
    ValidationBlocker,
)
from claimgate.shell.records import NoticeRecord
from claimgate.shell.store import NoticeStore


@dataclass(frozen=True)
class NoticeFields:
    """The reporter-supplied notice content - everything but the carrier_code
    envelope, the submission instant, the two configuration sources and the
    idempotency key, which are the shell's inputs, not the notice's.

    `property_state` is notice content and not an input (item 5g): where the
    insured risk sits is a fact about the risk, reported like any other, and a
    reviewer can supply it at resolution the way they can any other field. It
    therefore joins the hashed field set, which answers a byte-identical
    resubmission under a key remembered before this item with 409 rather than a
    200 replay - bounded to the 24-hour key lifetime, recorded in QUEUE.md, and
    accepted. `jurisdiction_timezone` left the surface in the same change: two
    sources for one fact need a precedence rule nobody has ratified
    (ASSUMPTIONS.md, 2026-08-26)."""

    policy_number: str = ""
    loss_date: str | None = None
    loss_type: str = ""
    notice_type: str = ""
    property_state: str | None = None
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
    # Carried on the refusals that keep what arrived - the schema-invalid 400,
    # the mis-keyed 409 and item 5i's 500 - so the reporter and the carrier can
    # name the same communication. Never on the unknown-carrier 400, which
    # persists nothing.
    reference: str | None = None
    # Which deployment fault a 500 is answering (faults.py). One status carries
    # both faults and the code is the only thing that tells them apart, so a
    # caller reads it from the body rather than inferring it from the status.
    error: str | None = None


@dataclass(frozen=True)
class NoticeView:
    notice_id: str
    state: str
    blockers: tuple[ValidationBlocker, ...]
    severity: str | None
    queue: str | None
    # The marking is here because it is the whole point of the marking: a
    # notice this deployment cannot yet judge is "still received, still triaged,
    # and visible as needing a person", and this is the only surface a person
    # reads a notice from in phase 2. The future-dated-loss determination beside
    # it on the record deliberately is not - see serialization.py.
    jurisdiction_marking: str | None

    @classmethod
    def of(cls, record: NoticeRecord) -> "NoticeView":
        """The stored notice as GET /notices/{id} shows it: everything the
        record carries except the receipt timestamp and the carrier, which are
        envelope and attribution rather than the notice, and the pend and
        release instants and the determination, which are stored facts about
        the notice rather than part of what this view shows."""
        return cls(
            record.notice_id, record.state, record.blockers, record.severity, record.queue,
            record.jurisdiction_marking,
        )


@dataclass(frozen=True)
class Submission:
    """One inbound submission's inputs, bundled so the steps that consume them
    read as steps rather than as parameter lists."""

    store: NoticeStore
    carrier_code: str
    submitted_at: datetime
    carrier_identity_reference: Mapping[str, CarrierIdentity]
    jurisdiction_reference: Mapping[str, Mapping[str, str]]
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
    jurisdiction_reference: Mapping[str, Mapping[str, str]]
    carrier_rules_source: Mapping[str, Mapping[str, Any]]
    supplied: Mapping[str, Any]
    note: str | None = None


@dataclass(frozen=True)
class ResolutionResponse:
    """One shape for 200 and 422 alike, so a reviewer's client parses one body
    and lets the status distinguish cleared from still-blocked
    (PHASE2_DESIGN.md). The 409 carries the notice's current state, because
    state is read from the body and never inferred from status. The 400 carries
    nothing: the notice is not read at all, so there is nothing to report, and
    the 404 and the 500 carry nothing about the notice for the same reason -
    one was never found and the other was never judged."""

    status: int
    notice_id: str | None = None
    state: str | None = None
    blockers: tuple[ValidationBlocker, ...] = ()
    severity: str | None = None
    queue: str | None = None
    # Which deployment fault a 500 is answering (faults.py), on the same
    # reasoning as the intake response's: one status for both faults, told
    # apart by code and never by status.
    error: str | None = None


@dataclass(frozen=True)
class Decision:
    """What one run of the domain rules concluded about a notice, and the whole
    of what a decision writes to its row. The determination travels with the
    state because the blocker and the determination come from one evaluation of
    the loss-date rule (domain/validation.py) and a row holding one from this
    run and the other from the last would be a record of neither."""

    state: str
    blockers: tuple[ValidationBlocker, ...]
    severity: str | None
    queue: str | None
    jurisdiction_marking: str | None
    future_dated_loss: FutureDatedLossResult


@dataclass(frozen=True)
class Judgement:
    """One transaction's decision, and the three inputs it was produced from.
    The inputs travel with the outcome rather than being recomputed because the
    SIU evaluation the same transaction owes has to apply exactly the rules that
    transaction resolved (ASSUMPTIONS.md, item 5f decision 6) and read its
    interval under exactly the jurisdiction that transaction selected: a second
    lookup of either would be a second reading, and the whole point of the
    decision is that there is one."""

    decision: Decision
    candidate: Candidate
    rules: CarrierRules
    jurisdiction: Jurisdiction | None


@dataclass(frozen=True)
class AcceptedNotice:
    """A notice whose receipt transaction has committed and whose decision has
    not been made yet. It exists because rule evaluation runs between the two,
    inside neither - see notice_intake.py."""

    notice_id: str
    candidate: Candidate
    # None where this notice's property state selected no jurisdiction: there is
    # no calendar to ask what today is, which is a different fact from today
    # being some particular date.
    jurisdiction: Jurisdiction | None
    today: date | None
    rules: CarrierRules
