"""What the orchestration passes to itself: one submission's and one
resolution's bundled inputs, and the three shapes that cross between a path's
transactions - the accepted notice on its way to a decision, the decision, and
the resolution's judgement on its way to the write.

Split out of messages.py in item 7h, structurally and with no behaviour change:
that module keeps the boundary shapes - the reporter's fields, the responses and
the retrieval view, which serialization.py projects - and this one keeps what
never leaves the shell. Neither had room under the size gate for what 7h adds:
the claims port an accepted notice carries, the duplicate evaluation a judgement
carries for the write, and the field the view shows.
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
from claimgate.shell.bindings import BindingsSource, ImplementationRegistry, PortBindings
from claimgate.shell.coverage_verifications import Verification
from claimgate.shell.duplicate_evaluations import DuplicateEvaluation
from claimgate.shell.messages import NoticeFields
from claimgate.shell.store import NoticeStore


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
    # The fourth configuration source (item 7f): which port implementation
    # serves this carrier, resolved by lookup beside the rules and the
    # jurisdiction, and the registry the deployment built for it to select from.
    bindings_source: BindingsSource
    implementation_registry: ImplementationRegistry
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
    # The re-search reaches the policy port through a submission's two sources (item 7g).
    bindings_source: BindingsSource
    implementation_registry: ImplementationRegistry
    note: str | None = None


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
    # What the re-search verified, for the write to record; None where nothing was searched.
    verification: Verification | None
    # What duplicate detection concluded, for the write to record beside the
    # verification (item 7h); None where the decision was not TRIAGED.
    duplicates: DuplicateEvaluation | None


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
    # The carrier's two ports, resolved with the other configuration before
    # the receipt (items 7f and 7h) and called between the two transactions.
    ports: PortBindings
