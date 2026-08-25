"""Orchestration for POST /notices/{notice_id}/resolution.

PHASE2_DESIGN.md's "Pending resolution and tolling" is the specification, and
ASSUMPTIONS.md's five item 5e decisions, ratified 2026-08-25, settle what it
left open. There is no HTTP layer anywhere in this project yet; a reviewer's
resolution arrives here as an ordinary call, the way a submission does.

PENDED -> TRIAGED is the only transition this module performs, and it is a USER
transition: releasing a pend is a human judging that what was missing has
actually arrived. There is still no rejected, invalid, or discarded state
(CLAUDE.md) - a resolution that does not clear the pend leaves the notice
exactly where it was, and is answered rather than discarded.

**The order the three refusals run in, and why.** The reviewer's identity is
checked first, before the notice is read at all: a caller who has not said who
they are does not get to learn a notice's state, and decision 4 makes that body
schema-invalid - 400, nothing persisted, operational log only. The state check
is second and needs no transaction of its own, because decision 3 says the 409
persists nothing: there is no pend, no request for information, and nothing for
a reviewer's content to be the answer to. Everything after that is one
transaction.

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

**Every instant written here is the one the caller supplied for this call**, and
the notice's receipt instant and pend instant are untouched by any of it
(ASSUMPTIONS.md, "One receipt clock, not two", as extended to the resolution
path). resolved_at is written only by the resolution that moves the notice to
TRIAGED; a refused attempt's instant lives on its audit entry and nowhere else.

Out of scope, deliberately: no tolling is computed and nothing here is named for
it; SIU (5f) and duplicate-candidate detection are untouched; and there is no
idempotency key on this endpoint - PHASE2_DESIGN.md scopes the header to
POST /notices, so a network retry of a resolution that already succeeded meets a
TRIAGED notice and is answered by the 409 below.
"""

from collections.abc import Mapping
from datetime import date, datetime
from typing import Any

from claimgate.domain.models import ValidationBlocker
from claimgate.shell import rules
from claimgate.shell.messages import NoticeFields, Resolution, ResolutionResponse
from claimgate.shell.records import NoticeRecord, PayloadRecord
from claimgate.shell.store import NoticeStore


def resolve_notice(
    store: NoticeStore,
    notice_id: str,
    *,
    actor_id: str | None,
    resolved_at: datetime,
    jurisdiction_timezone: str,
    carrier_rules_source: Mapping[str, Mapping[str, Any]],
    supplied: Mapping[str, Any],
    note: str | None = None,
) -> ResolutionResponse:
    if actor_id is None or not actor_id.strip():
        return ResolutionResponse(status=400)
    resolution = Resolution(
        store=store, notice_id=notice_id, actor_id=actor_id, resolved_at=resolved_at,
        jurisdiction_timezone=jurisdiction_timezone, carrier_rules_source=carrier_rules_source,
        supplied=supplied, note=note,
    )
    with store.submission():
        record = _require_notice(store, notice_id)
        if record.state != "PENDED":
            return _conflict(record)
        return _evaluate(resolution, record)


def _conflict(record: NoticeRecord) -> ResolutionResponse:
    """409 with the notice's current state in the body. A notice at rest in
    RECEIVED gets this same answer and no row of its own (decision 5); its
    scenario is item 5i's, the item that makes that state reachable by a
    specified path."""
    return ResolutionResponse(
        status=409, notice_id=record.notice_id, state=record.state,
        blockers=record.blockers, severity=record.severity, queue=record.queue,
    )


def _evaluate(resolution: Resolution, record: NoticeRecord) -> ResolutionResponse:
    store = resolution.store
    store.append_notice_payload(
        record.notice_id, record.carrier_code, resolution.supplied, resolution.resolved_at
    )
    state, blockers, severity, queue = _judge(resolution, record)
    applied = state == "TRIAGED"
    store.write_notice_decision(
        record.notice_id, state=state, blockers=blockers, severity=severity, queue=queue,
        pended_at=None, resolved_at=resolution.resolved_at if applied else None,
    )
    store.append_audit_entry(
        record.notice_id, from_state="PENDED", to_state="TRIAGED", actor_type="USER",
        actor_id=resolution.actor_id, occurred_at=resolution.resolved_at, blockers=blockers,
        outcome="APPLIED" if applied else "REFUSED", note=resolution.note,
    )
    return ResolutionResponse(
        status=200 if applied else 422, notice_id=record.notice_id, state=state,
        blockers=blockers, severity=severity, queue=queue,
    )


def _judge(
    resolution: Resolution, record: NoticeRecord
) -> tuple[str, tuple[ValidationBlocker, ...], str | None, str | None]:
    """The whole validation, over the merged view, on the jurisdiction date of
    this resolution's own instant. A blocker the resolution introduces is not a
    new outcome - it is simply among the current blockers the 422 reports."""
    view = merged_view(resolution.store, record.notice_id)
    candidate = rules.build_candidate(view, _loss_date_of(view))
    return rules.apply_domain_rules(
        candidate,
        rules.resolve_today(resolution.resolved_at, resolution.jurisdiction_timezone),
        rules.resolve_rules(record.carrier_code, resolution.carrier_rules_source),
    )


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


def _require_notice(store: NoticeStore, notice_id: str) -> NoticeRecord:
    record = store.get_notice(notice_id)
    if record is None:
        raise NotImplementedError(
            "a resolution naming a notice this deployment does not have has no "
            "status code in PHASE2_DESIGN.md's closed table - routing an "
            "unknown identifier belongs to the HTTP layer, which does not exist"
        )
    return record


def _loss_date_of(view: NoticeFields) -> date:
    loss_date = rules.parse_loss_date(view.loss_date)
    if loss_date is None:
        raise NotImplementedError(
            "a resolution carrying a loss date that is not a date at all has no "
            "decided outcome - intake answers it 400 at the schema boundary and "
            "no decision extends that row to this endpoint"
        )
    return loss_date
