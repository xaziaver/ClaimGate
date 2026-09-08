"""The resolution's first transaction and the merged view it reads (split out of
resolution_evaluation.py in item 7g, which adds the re-search to the judgement
and left that module no room; the read moved whole, the judgement stayed).

**The read transaction takes the notice as it stands, every record in its
arrival sequence and its verification trail, under one lock and with no I/O**,
so the view, the last answer standing and the state the judgement assumes are
one consistent picture of the notice. It answers the two refusals that need
only the notice: an id nobody has is 404, refused before any state is examined
(decision (d)), and a notice that exists and is not pended is the 409, which
decision 3 says persists nothing. The write transaction answers the same 409
for a notice that was pended when read and has moved since, through the same
function, so the two 409s cannot drift apart.

**The view is the arrival sequence overlaid with what this reviewer supplied,
field by field**, an absent field keeping its prior value (decision 1). The
reviewer's record is appended in the write transaction and not here, so a
resolution answered 409 leaves nothing behind, and the view it is judged
against includes what was just supplied exactly as it did when the record was
appended first. A refused resolution's record is one of the sequence - the
release was refused, not the data (decision 3), and "422 with the current
blockers" only means something if the current view includes what was just
supplied. merged_view is the same overlay over the stored sequence alone: what
the notice says now, for the test API that reads it back.

**The last answer standing** is the newest verification row whose search
answered - matched, not matched or ambiguous - rather than the newest row: a
row that could not answer left the previous answer's blocker in place
(ASSUMPTIONS.md, 7g decision 6), and the judgement needs that answer where its
own re-search cannot answer either. None where nothing has ever answered.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from claimgate.domain.policy_match import NOT_EVALUATED
from claimgate.shell import coverage_verifications
from claimgate.shell.coverage_verifications import CoverageVerification
from claimgate.shell.messages import NoticeFields, Resolution, ResolutionResponse
from claimgate.shell.records import NoticeRecord, PayloadRecord
from claimgate.shell.store import NoticeStore


@dataclass(frozen=True)
class Reading:
    """What the read transaction found - the notice as it stood, its view with
    this resolution's fields overlaid, the last answer standing - so the judgement reads nothing."""

    record: NoticeRecord
    view: NoticeFields
    answered: CoverageVerification | None


def read(resolution: Resolution) -> Reading | ResolutionResponse:
    """The first transaction: three reads under one lock and no I/O."""
    store = resolution.store
    with store.submission():
        record = store.get_notice(resolution.notice_id)
        if record is None:
            return ResolutionResponse(status=404)
        if record.state != "PENDED":
            return conflict(record)
        view = _overlaid(notice_records(store, record.notice_id), resolution.supplied)
        answered = _last_answered(coverage_verifications.for_notice(store, record.notice_id))
    return Reading(record, view, answered)


def conflict(record: NoticeRecord) -> ResolutionResponse:
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


def merged_view(store: NoticeStore, notice_id: str) -> NoticeFields:
    """What the notice says now: every record for it overlaid in arrival order,
    field by field. Position 0 is the submission it was created from and carries
    every field; each later record carries only what its reviewer supplied, so
    an omitted field keeps whatever an earlier arrival gave it."""
    return _overlaid(notice_records(store, notice_id), {})


def _overlaid(records: tuple[PayloadRecord, ...], supplied: Mapping[str, Any]) -> NoticeFields:
    """The stored sequence, then what this call supplied on top of it - the
    view a resolution is judged against before its own record exists."""
    fields: dict[str, Any] = {}
    for record in records:
        fields.update(record.content)
    fields.update(supplied)
    return NoticeFields(**fields)


def _last_answered(trail: tuple[CoverageVerification, ...]) -> CoverageVerification | None:
    return next((row for row in reversed(trail) if row.policy_match != NOT_EVALUATED), None)


def notice_records(store: NoticeStore, notice_id: str) -> tuple[PayloadRecord, ...]:
    return store.get_notice_payloads(notice_id)
