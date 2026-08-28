"""Orchestration for POST /notices/{notice_id}/resolution.

PHASE2_DESIGN.md's pending-resolution section is the specification, and
ASSUMPTIONS.md's five item 5e decisions, ratified 2026-08-25, settle what it
left open. There is no HTTP layer anywhere in this project yet; a reviewer's
resolution arrives here as an ordinary call, the way a submission does.

PENDED -> TRIAGED is the only transition this module performs, and it is a USER
transition: releasing a pend is a human judging that what was missing has
actually arrived. There is still no rejected, invalid, or discarded state
(CLAUDE.md) - a resolution that does not clear the pend leaves the notice
exactly where it was, and is answered rather than discarded.

**The order the four refusals run in, and why.** A body this endpoint cannot
read is refused first, before the notice is read at all - an identity nobody
supplied or a loss date that is not a date, both 400 with nothing persisted
(decisions 4 and (e)); a caller who has not said who they are does not get to
learn a notice's state. An id nobody has is 404, refused before any state is
examined (decision (d)): there is no pend to release and nothing for the content
to be the answer to. A notice that exists and is not pended is the 409, which
decision 3 says persists nothing. Last is item 5i's 500, no refusal of anything
the reviewer sent: this deployment could not read its own configuration, so the
whole transaction rolls back and the notice keeps the records and the trail it
had (ruling 1). Nothing asserts the order directly - each rule asserts its own
answer, and reordering them would answer one case with another's status.

**What the transaction does, in order.** The reviewer's payload record is
appended to the notice's arrival sequence first, so the current view it is
judged against includes it; the view is then derived by overlaying every record
for the notice in arrival order, field by field, an absent field keeping its
prior value (decision 1). The full validation re-runs over that view - the same
one intake runs, through rules.py, because decision 2(a) says there is one
definition of "no blocker" rather than one per endpoint - on the jurisdiction
date of the resolution's own instant (decision 2(b)). The notice's blockers are
replaced by that whole result, so the 422 body and the record cannot disagree.
Either way one audit entry is written, from PENDED to TRIAGED, APPLIED or
REFUSED: a refused attempt is itself an audit event, not a non-event.

**The jurisdiction comes from the merged view, not from what was known at
receipt** (item 5g; ASSUMPTIONS.md 2026-08-26). Where the insured property is is
a fact about the risk rather than about the moment the notice arrived, and a
reviewer supplies it like any other field, so a notice pended for an unrelated
blocker while carrying jurisdiction_unsupported becomes judgeable when its
resolution says where the property is. One selection serves both dates this
transaction needs: the future-date re-check runs on this resolution's instant
(decision 2(b)) and the late-reporting interval on the notice's own receipt
(item 5f decision 2), under the one zone the merged view now yields.

**Every instant written here is the one the caller supplied for this call**, and
the notice's receipt instant and pend instant are untouched by any of it
(ASSUMPTIONS.md, "One receipt clock, not two", as extended to the resolution
path). resolved_at is written only by the resolution that moves the notice to
TRIAGED; a refused attempt's instant lives on its audit entry and nowhere else.

**A resolution that releases the notice owes it an SIU evaluation** (item 5f
decision 1), written from siu.py inside this same transaction and only where the
notice actually moved - a refused attempt transitions nothing and evaluates
nothing. The rules that evaluation applies are the ones _judge resolved for this
transaction, carried out of it rather than read a second time (decision 6), and
the interval it measures is counted from the notice's own receipt instant rather
than from this resolution's (decision 2): a pend does not make the reporter late.

Out of scope, deliberately: the two instants above are recorded and nothing
whatever is computed from them, which is PHASE2_DESIGN.md's "record precisely,
compute nothing" - what the Fla. Stat. 627.70131(8)(b) interval means is a
downstream legal determination and no phase-2 code goes near it.
Duplicate-candidate detection is untouched; and there is no
idempotency key on this endpoint - PHASE2_DESIGN.md scopes the header to
POST /notices, so a network retry of a resolution that already succeeded meets a
TRIAGED notice and is answered by the 409 below. No NotImplementedError remains
anywhere in this module: item 5i ratified the answer to every state that had
one.
"""

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from claimgate.shell import rules, siu
from claimgate.shell.faults import DeploymentFaultError
from claimgate.shell.messages import (
    Decision,
    Judgement,
    NoticeFields,
    Resolution,
    ResolutionResponse,
)
from claimgate.shell.records import NoticeRecord, PayloadRecord
from claimgate.shell.store import NoticeStore


def resolve_notice(
    store: NoticeStore,
    notice_id: str,
    *,
    actor_id: str | None,
    resolved_at: datetime,
    jurisdiction_reference: Mapping[str, Mapping[str, str]],
    carrier_rules_source: Mapping[str, Mapping[str, Any]],
    supplied: Mapping[str, Any],
    note: str | None = None,
) -> ResolutionResponse:
    reviewer = _reviewer_of(actor_id, supplied)
    if reviewer is None:
        return ResolutionResponse(status=400)
    resolution = Resolution(
        store=store, notice_id=notice_id, actor_id=reviewer, resolved_at=resolved_at,
        jurisdiction_reference=jurisdiction_reference, carrier_rules_source=carrier_rules_source,
        supplied=supplied, note=note,
    )
    try:
        with store.submission():
            return _answer(resolution)
    except DeploymentFaultError as fault:
        return ResolutionResponse(status=500, error=fault.code)


def _reviewer_of(actor_id: str | None, supplied: Mapping[str, Any]) -> str | None:
    """The reviewer this body names, or None where the endpoint cannot read the
    body at all - which is the same 400 either way, before the notice is read.

    Two halves, both about the body. The reviewer's identity is required and
    caller-asserted (decision 4). A supplied loss date that is not a date at all
    is the same schema-invalid refusal (decision (e), 2026-08-25), checked here
    rather than deeper in: intake answers that input the same way at its own
    boundary, so no merged view can ever carry one and a parse over the merged
    view would sit on an input that cannot reach it."""
    if actor_id is None or not actor_id.strip():
        return None
    if rules.parse_loss_date(supplied.get("loss_date")).value == "UNPARSEABLE":
        return None
    return actor_id


def _answer(resolution: Resolution) -> ResolutionResponse:
    """The three answers a notice-shaped question has, in the order their own
    reasons force: an id nobody has is refused before any state is examined, and
    only a notice that exists and is not pended reaches the 409."""
    record = resolution.store.get_notice(resolution.notice_id)
    if record is None:
        return ResolutionResponse(status=404)
    if record.state != "PENDED":
        return _conflict(record)
    return _evaluate(resolution, record)


def _conflict(record: NoticeRecord) -> ResolutionResponse:
    """409 with the notice's current state in the body. A notice at rest in
    RECEIVED would get this same answer and no row of its own (decision 5), but
    nothing in phase 2 produces that state: both of item 5i's deployment faults
    are answered before a notice exists, so the premise that deferred a scenario
    here was false and no scenario is owed (ASSUMPTIONS.md, item 5i, ruling
    5)."""
    return ResolutionResponse(
        status=409, notice_id=record.notice_id, state=record.state,
        blockers=record.blockers, severity=record.severity, queue=record.queue,
    )


def _evaluate(resolution: Resolution, record: NoticeRecord) -> ResolutionResponse:
    store = resolution.store
    store.append_notice_payload(
        record.notice_id, record.carrier_code, resolution.supplied, resolution.resolved_at
    )
    judged = _judge(resolution, record)
    decision = judged.decision
    applied = decision.state == "TRIAGED"
    store.write_notice_decision(
        record.notice_id, state=decision.state, blockers=decision.blockers,
        severity=decision.severity, queue=decision.queue,
        jurisdiction_marking=decision.jurisdiction_marking,
        future_dated_loss=decision.future_dated_loss,
        pended_at=None, resolved_at=resolution.resolved_at if applied else None,
    )
    _record_attempt(resolution, record, judged, applied=applied)
    return ResolutionResponse(
        status=200 if applied else 422, notice_id=record.notice_id, state=decision.state,
        blockers=decision.blockers, severity=decision.severity, queue=decision.queue,
    )


def _record_attempt(
    resolution: Resolution, record: NoticeRecord, judged: Judgement, *, applied: bool
) -> None:
    """One audit entry either way - a refused attempt is an audit event, not a
    non-event - and the SIU evaluation only where the notice actually moved.
    Both writes are inside this resolution's transaction, so a notice that
    reached TRIAGED without its evaluation beside it is not a state this path
    can produce. The interval is counted from the notice's stored receipt
    instant and the events are stamped with this resolution's: the stamp says
    when the evaluation happened, the interval says what was measured."""
    resolution.store.append_audit_entry(
        record.notice_id, from_state="PENDED", to_state="TRIAGED", actor_type="USER",
        actor_id=resolution.actor_id, occurred_at=resolution.resolved_at,
        blockers=judged.decision.blockers, outcome="APPLIED" if applied else "REFUSED",
        note=resolution.note,
    )
    if applied:
        siu.record_evaluation(
            resolution.store, record.notice_id,
            candidate=judged.candidate, rules=judged.rules,
            received_at=record.received_at,
            jurisdiction=judged.jurisdiction,
            evaluated_at=resolution.resolved_at,
        )


def _judge(resolution: Resolution, record: NoticeRecord) -> Judgement:
    """The whole validation, over the merged view, on the jurisdiction date of
    this resolution's own instant. A blocker the resolution introduces is not a
    new outcome - it is simply among the current blockers the 422 reports. The
    candidate, the carrier's rules and the jurisdiction come back with the
    outcome because the SIU evaluation this transaction may owe has to use these
    and not a second reading of any of them."""
    view = merged_view(resolution.store, record.notice_id)
    # The parse cannot fail here and there is no branch for it: every arrival in
    # the sequence cleared a schema boundary that answers an unparseable loss
    # date 400, so the merged view carries a date or states none (decision (e)).
    candidate = rules.build_candidate(view, rules.parse_loss_date(view.loss_date).loss_date)
    carrier_rules = rules.resolve_rules(record.carrier_code, resolution.carrier_rules_source)
    jurisdiction = rules.resolve_jurisdiction(
        view.property_state, resolution.jurisdiction_reference
    )
    decision: Decision = rules.apply_domain_rules(
        candidate,
        jurisdiction,
        rules.resolve_today(resolution.resolved_at, jurisdiction),
        carrier_rules,
    )
    return Judgement(decision, candidate, carrier_rules, jurisdiction)


def merged_view(store: NoticeStore, notice_id: str) -> NoticeFields:
    """What the notice says now: every record for it overlaid in arrival order,
    field by field. Position 0 is the submission it was created from and carries
    every field; each later record carries only what its reviewer supplied, so
    an omitted field keeps whatever an earlier arrival gave it. A refused
    resolution's record is one of them - the release was refused, not the data
    (decision 3), and "422 with the current blockers" only means something if
    the current view includes what was just supplied."""
    fields: dict[str, Any] = {}
    for record in notice_records(store, notice_id):
        fields.update(record.content)
    return NoticeFields(**fields)


def notice_records(store: NoticeStore, notice_id: str) -> tuple[PayloadRecord, ...]:
    return store.get_notice_payloads(notice_id)


