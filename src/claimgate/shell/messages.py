"""What crosses the shell's boundary on POST /notices, GET /notices/{id} and
POST /notices/{id}/resolution: the reporter's fields, the responses, and the
retrieval view - the shapes serialization.py projects through its allow-lists.

Separated from notice_intake.py so idempotency.py can name these shapes without
importing the orchestration that assembles them. The bundled inputs each
endpoint takes and the shapes that cross between a path's transactions are
bundles.py's since item 7h, so both modules have room under the size gate for
what that item adds.
"""

from dataclasses import dataclass
from datetime import datetime

from claimgate.domain.models import ValidationBlocker
from claimgate.shell.coverage_verifications import CoverageVerificationView
from claimgate.shell.duplicate_evaluations import DuplicateEvaluationView
from claimgate.shell.records import NoticeRecord


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
    (ASSUMPTIONS.md, 2026-08-26).

    `insured_name` and the structured risk address - `risk_address`,
    `risk_city`, `risk_postal_code`, with `property_state` staying the
    address's only state component - are item 7c's, the identifiers the policy
    search will take once item 7g wires it (PHASE3_DESIGN.md, "Identifiers").
    They join the hashed field set on the same terms as `property_state`, with
    the same accepted consequence. Since item 7f the sufficiency rule reads all
    three to decide whether the search runs (shell/policy_match.py); the
    insured-name arm stays unreachable until 7g retires the number requirement."""

    policy_number: str = ""
    loss_date: str | None = None
    loss_type: str = ""
    notice_type: str = ""
    property_state: str | None = None
    claimant_name: str | None = None
    claimant_contact: str | None = None
    incident_description: str | None = None
    insured_name: str | None = None
    risk_address: str | None = None
    risk_city: str | None = None
    risk_postal_code: str | None = None


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
    # Item 7f: what the policy search and the coverage rules concluded, as the
    # latest verification row says it (coverage_verifications.py). None where
    # nothing has been searched - a notice at RECEIVED, or one with nothing to
    # search on - which is not the same fact as a search that found nothing.
    coverage_verification: CoverageVerificationView | None
    # Item 7h: what duplicate detection concluded on the notice's transition
    # into TRIAGED, as the latest evaluation row says it
    # (duplicate_evaluations.py). None where the notice has not been triaged,
    # which is not the same fact as a comparison that found no candidate.
    duplicate_evaluation: DuplicateEvaluationView | None

    @classmethod
    def of(
        cls, record: NoticeRecord, verification: CoverageVerificationView | None,
        duplicates: DuplicateEvaluationView | None,
    ) -> "NoticeView":
        """The stored notice as GET /notices/{id} shows it: everything the
        record carries except the receipt timestamp and the carrier, which are
        envelope and attribution rather than the notice, and the pend and
        release instants and the determination, which are stored facts about
        the notice rather than part of what this view shows."""
        return cls(
            record.notice_id, record.state, record.blockers, record.severity, record.queue,
            record.jurisdiction_marking, verification, duplicates,
        )



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
