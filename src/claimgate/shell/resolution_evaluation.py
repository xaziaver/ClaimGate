"""The resolution's three steps: read, judge, write (split out of resolution.py
in item 7f; restructured into two transactions in item 7g).

**Read, judge, write - two transactions with the evaluation between them**
(PHASE3_DESIGN.md, "Where the calls sit", the resolution path). The read
transaction takes the notice as it stands, every record in its arrival
sequence and its latest coverage verification, under one lock and with no I/O.
The judgement runs outside any transaction: the full validation over the
merged view and, from item 7g, the port calls the re-search needs - none is
made yet, and this is where they go. The write transaction re-reads the notice
and answers 409 if it is no longer PENDED - a second reviewer's resolution can
now commit while the first is being judged, a path the single transaction used
to exclude by holding the lock - and otherwise appends the reviewer's payload
record and writes the decision, the audit entry and the SIU events together.
Gherkin cannot express the race; tests/shell/test_resolution.py's overtaken
test is the guard's specification.

**The view is the arrival sequence overlaid with what this reviewer supplied,
field by field**, an absent field keeping its prior value (decision 1). The
reviewer's record is appended in the write transaction and not before, so a
resolution answered 409 leaves nothing behind, and the view it is judged
against includes what was just supplied exactly as it did when the record was
appended first. The full validation re-runs over that view - the same one
intake runs, through rules.py: decision 2(a)'s one definition of "no blocker" -
on the jurisdiction date of the resolution's own instant (decision 2(b)),
under the jurisdiction the merged view selects, not the one known at receipt
(item 5g; ASSUMPTIONS.md 2026-08-26), and the late-reporting interval counts
from the notice's own receipt (item 5f decision 2). The notice's blockers are
replaced by the whole result, so the 422 body and the record cannot disagree;
one audit entry is written either way, APPLIED or REFUSED, and every instant
written is the one the caller supplied for this call - resolved_at only by
the resolution that moves the notice (ASSUMPTIONS.md, "One receipt clock, not
two"). A release owes an SIU evaluation (item 5f decision 1), written inside
the write transaction from the rules the judgement resolved (decision 6).

**The policy match is re-asserted from the stored verification, not searched
again** (item 7f; ASSUMPTIONS.md, 7f decision 6): the judgement hands the rules
the match the latest verification recorded, so POLICY_NOT_MATCHED and
POLICY_AMBIGUOUS persist through a resolution that corrects an unrelated
field, and its continuous-coverage date travels onto the candidate through
the producer intake uses. No port is called and no verification row is
written: nothing new was verified. Item 7g re-searches on the merged
identifiers, which is what will clear such a pend once a reviewer has
corrected the policy number.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from claimgate.domain.continuous_coverage import carry_onto_candidate
from claimgate.domain.models import Candidate
from claimgate.domain.policy_match import PolicyMatch
from claimgate.shell import coverage_verifications, rules, siu
from claimgate.shell.coverage_verifications import CoverageVerification
from claimgate.shell.messages import (
    Decision,
    Judgement,
    NoticeFields,
    Resolution,
    ResolutionResponse,
)
from claimgate.shell.records import NoticeRecord, PayloadRecord
from claimgate.shell.store import NoticeStore


@dataclass(frozen=True)
class Reading:
    """What the read transaction found - the notice as it stood, its view with
    this resolution's fields overlaid, its latest verification - so the judgement reads nothing."""

    record: NoticeRecord
    view: NoticeFields
    verification: CoverageVerification | None


def evaluate(resolution: Resolution) -> ResolutionResponse:
    """The three answers a notice-shaped question has, in the order their own
    reasons force: an id nobody has is refused before any state is examined,
    only a notice that exists and is not pended reaches the 409, and only a
    pended one is judged - and then judged against the notice it still is."""
    reading = read(resolution)
    if isinstance(reading, ResolutionResponse):
        return reading
    judged = judge(resolution, reading)
    return write(resolution, reading, judged)


def read(resolution: Resolution) -> Reading | ResolutionResponse:
    """The first transaction: three reads under one lock and no I/O, so the
    view, the verification and the state the judgement assumes are one
    consistent picture of the notice."""
    store = resolution.store
    with store.submission():
        record = store.get_notice(resolution.notice_id)
        if record is None:
            return ResolutionResponse(status=404)
        if record.state != "PENDED":
            return conflict(record)
        view = _overlaid(notice_records(store, record.notice_id), resolution.supplied)
        verification = coverage_verifications.latest(store, record.notice_id)
    return Reading(record, view, verification)


def judge(resolution: Resolution, reading: Reading) -> Judgement:
    """The whole validation, over the merged view, on the jurisdiction date of
    this resolution's own instant - outside any transaction, so nothing here
    holds the write lock against intake. A blocker the resolution introduces is
    not a new outcome - it is simply among the current blockers the 422
    reports. The candidate, the carrier's rules and the jurisdiction come back
    with the outcome because the SIU evaluation the write may owe has to use
    these and not a second reading of any of them."""
    candidate = _candidate_of(reading.view, reading.verification)
    carrier_rules = rules.resolve_rules(
        reading.record.carrier_code, resolution.carrier_rules_source
    )
    jurisdiction = rules.resolve_jurisdiction(
        reading.view.property_state, resolution.jurisdiction_reference
    )
    decision: Decision = rules.apply_domain_rules(
        candidate,
        jurisdiction,
        rules.resolve_today(resolution.resolved_at, jurisdiction),
        carrier_rules,
        _match_of(reading.verification),
    )
    return Judgement(decision, candidate, carrier_rules, jurisdiction)


def write(resolution: Resolution, reading: Reading, judged: Judgement) -> ResolutionResponse:
    """The second transaction, opened on the notice the judgement was made
    about and refused if it is no longer that notice: a resolution that
    committed while this one was being judged has moved it, and a decision
    made against the earlier state is not applied to the later one. The
    re-read cannot come back empty - nothing in this package deletes a notice
    row - and `or` carries the type rather than a branch nothing can reach."""
    store, record = resolution.store, reading.record
    with store.submission():
        current = store.get_notice(record.notice_id) or record
        if current.state != "PENDED":
            return conflict(current)
        store.append_notice_payload(
            record.notice_id, record.carrier_code, resolution.supplied, resolution.resolved_at
        )
        applied = _apply(resolution, record, judged)
    decision = judged.decision
    return ResolutionResponse(
        status=200 if applied else 422, notice_id=record.notice_id, state=decision.state,
        blockers=decision.blockers, severity=decision.severity, queue=decision.queue,
    )


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


def _apply(resolution: Resolution, record: NoticeRecord, judged: Judgement) -> bool:
    """The decision onto the notice row, then the attempt's own records; True
    where the notice moved."""
    decision = judged.decision
    applied = decision.state == "TRIAGED"
    resolution.store.write_notice_decision(
        record.notice_id, state=decision.state, blockers=decision.blockers,
        severity=decision.severity, queue=decision.queue,
        jurisdiction_marking=decision.jurisdiction_marking,
        future_dated_loss=decision.future_dated_loss,
        pended_at=None, resolved_at=resolution.resolved_at if applied else None,
    )
    _record_attempt(resolution, record, judged, applied=applied)
    return applied


def _record_attempt(
    resolution: Resolution, record: NoticeRecord, judged: Judgement, *, applied: bool
) -> None:
    """One audit entry either way - a refused attempt is an audit event, not a
    non-event - and the SIU evaluation only where the notice actually moved.
    Both writes are inside the write transaction, so a notice that reached
    TRIAGED without its evaluation beside it is not a state this path can
    produce. The interval is counted from the notice's stored receipt instant
    and the events are stamped with this resolution's: the stamp says when the
    evaluation happened, the interval says what was measured."""
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


def _candidate_of(view: NoticeFields, verification: CoverageVerification | None) -> Candidate:
    """The merged view as a candidate, carrying the continuous-coverage date the
    stored verification recorded where there is one. The parse cannot fail here
    and there is no branch for it: every arrival in the sequence cleared a
    schema boundary that answers an unparseable loss date 400, so the merged
    view carries a date or states none (decision (e))."""
    candidate = rules.build_candidate(view, rules.parse_loss_date(view.loss_date).loss_date)
    if verification is None:
        return candidate
    return carry_onto_candidate(candidate, coverage_verifications.derivation_of(verification))


def _match_of(verification: CoverageVerification | None) -> PolicyMatch | None:
    """None for a notice no search has run over - one with nothing searchable
    on it, or from before the search existed - which is not a match that found
    nothing."""
    return None if verification is None else coverage_verifications.match_of(verification)


def merged_view(store: NoticeStore, notice_id: str) -> NoticeFields:
    """What the notice says now: every record for it overlaid in arrival order,
    field by field. Position 0 is the submission it was created from and carries
    every field; each later record carries only what its reviewer supplied, so
    an omitted field keeps whatever an earlier arrival gave it. A refused
    resolution's record is one of them - the release was refused, not the data
    (decision 3), and "422 with the current blockers" only means something if
    the current view includes what was just supplied."""
    return _overlaid(notice_records(store, notice_id), {})


def _overlaid(records: tuple[PayloadRecord, ...], supplied: Mapping[str, Any]) -> NoticeFields:
    """The stored sequence, then what this call supplied on top of it - the
    view a resolution is judged against before its own record exists."""
    fields: dict[str, Any] = {}
    for record in records:
        fields.update(record.content)
    fields.update(supplied)
    return NoticeFields(**fields)


def notice_records(store: NoticeStore, notice_id: str) -> tuple[PayloadRecord, ...]:
    return store.get_notice_payloads(notice_id)
