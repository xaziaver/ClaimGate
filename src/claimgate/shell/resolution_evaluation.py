"""The resolution's judgement and its write transaction (split out of
resolution.py in item 7f; restructured into two transactions in item 7g, with
the read transaction in resolution_reading.py).

**Read, judge, write - two transactions with the evaluation between them**
(PHASE3_DESIGN.md, "Where the calls sit", the resolution path). The read is
resolution_reading.py's. The judgement runs outside any transaction: the
policy check over the merged identifiers - the carrier's port, resolved for
this call, is asked again (item 7g) - and the full validation over the merged
view. The write transaction re-reads the notice and answers 409 if it is no
longer PENDED - a second reviewer's resolution can commit while the first is
being judged, a path the single transaction used to exclude by holding the
lock - and otherwise appends the reviewer's payload record and writes the
decision, the verification row, the audit entry and the SIU events together.
Gherkin cannot express the race; tests/shell/test_resolution.py's overtaken
test is the guard's specification.

**The full validation re-runs over the merged view** - the same one intake
runs, through rules.py: decision 2(a)'s one definition of "no blocker" - on
the jurisdiction date of the resolution's own instant (decision 2(b)), under
the jurisdiction the merged view selects, not the one known at receipt (item
5g; ASSUMPTIONS.md 2026-08-26), and the late-reporting interval counts from
the notice's own receipt (item 5f decision 2). The notice's blockers are
replaced by the whole result, so the 422 body and the record cannot disagree;
one audit entry is written either way, APPLIED or REFUSED, and every instant
written is the one the caller supplied for this call - resolved_at only by
the resolution that moves the notice (ASSUMPTIONS.md, "One receipt clock, not
two"). A release owes an SIU evaluation (item 5f decision 1), written inside
the write transaction from the rules the judgement resolved (decision 6).

**The re-search decides afresh only when it answers** (ASSUMPTIONS.md, 7g
decision 6). Correcting a policy number, or supplying the insured name and
risk postal code the notice lacked, is searched through the same check intake
uses (shell/policy_match.py), and an answer - matched, not matched, ambiguous
- replaces the stored match and its blockers. A search that could not answer,
or did not run, leaves the last answer standing: its blocker and its
continuous-coverage date both, so an outage cannot turn a correction into a
triage and the date a release's SIU evaluation reads is one that was
computed. Every search that ran is recorded, so the notice shows the newest
row and says why it could not answer where it could not.
"""

from datetime import date

from claimgate.domain.continuous_coverage import (
    ContinuousCoverageDerivation,
    carry_onto_candidate,
)
from claimgate.domain.models import Candidate
from claimgate.domain.policy_match import PolicyMatch
from claimgate.domain.ruleset import RULESET_VERSION
from claimgate.shell import coverage_verifications, rules, siu
from claimgate.shell.bindings import resolve_policy_port
from claimgate.shell.bundles import Decision, Judgement, Resolution
from claimgate.shell.coverage_verifications import CoverageVerification, Verification
from claimgate.shell.messages import NoticeFields, ResolutionResponse
from claimgate.shell.policy_match import answered, check_policy
from claimgate.shell.ports import PolicyPort
from claimgate.shell.records import NoticeRecord
from claimgate.shell.resolution_reading import Reading, conflict, read


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


def judge(resolution: Resolution, reading: Reading) -> Judgement:
    """The policy check and the whole validation, over the merged view, on the
    jurisdiction date of this resolution's own instant - outside any
    transaction, so no port round trip holds the write lock against intake.
    The candidate, the carrier's rules and the jurisdiction come back with the
    outcome because the SIU evaluation the write may owe has to use these and
    not a second reading of any of them."""
    view, record = reading.view, reading.record
    loss_date = rules.parse_loss_date(view.loss_date).loss_date
    check = check_policy(_port_of(resolution, record), view, loss_date)
    match, derivation = _answer_standing(check.verification, reading.answered)
    candidate = _candidate_of(view, loss_date, derivation)
    carrier_rules = rules.resolve_rules(record.carrier_code, resolution.carrier_rules_source)
    jurisdiction = rules.resolve_jurisdiction(
        view.property_state, resolution.jurisdiction_reference
    )
    decision: Decision = rules.apply_domain_rules(
        candidate, jurisdiction, rules.resolve_today(resolution.resolved_at, jurisdiction),
        carrier_rules, match, check.blockers,
    )
    return Judgement(decision, candidate, carrier_rules, jurisdiction, check.verification)


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


def _port_of(resolution: Resolution, record: NoticeRecord) -> PolicyPort:
    """The carrier's policy port, resolved for this call with the resolution's
    own instant as its clock, so the verification's as_of is the instant the
    reviewer's correction was searched on. An unbound carrier is item 5i's
    deployment fault, answered 500 with nothing written, as the rules and the
    jurisdiction map are."""
    return resolve_policy_port(
        record.carrier_code, resolution.bindings_source, resolution.implementation_registry,
        lambda: resolution.resolved_at,
    )


def _answer_standing(
    fresh: Verification | None, stored: CoverageVerification | None
) -> tuple[PolicyMatch | None, ContinuousCoverageDerivation | None]:
    """7g decision 6 (module docstring): the re-search's own answer where it
    answered, else the last answer standing - match and derivation together -
    and nothing where no search has ever answered over this notice."""
    if answered(fresh):
        return fresh.match, fresh.coverage
    if stored is None:
        return None, None
    return coverage_verifications.match_of(stored), coverage_verifications.derivation_of(stored)


def _candidate_of(
    view: NoticeFields, loss_date: date | None, derivation: ContinuousCoverageDerivation | None
) -> Candidate:
    """The merged view as a candidate, carrying the continuous-coverage date
    the answer standing yielded where there is one. The parse cannot fail
    here and there is no branch for it: every arrival in the sequence cleared
    a schema boundary that answers an unparseable loss date 400, so the merged
    view carries a date or states none (decision (e))."""
    candidate = rules.build_candidate(view, loss_date)
    return candidate if derivation is None else carry_onto_candidate(candidate, derivation)


def _apply(resolution: Resolution, record: NoticeRecord, judged: Judgement) -> bool:
    """The decision onto the notice row, the verification row where a search
    ran, then the attempt's own records; True where the notice moved."""
    decision = judged.decision
    applied = decision.state == "TRIAGED"
    resolution.store.write_notice_decision(
        record.notice_id, state=decision.state, blockers=decision.blockers,
        severity=decision.severity, queue=decision.queue,
        jurisdiction_marking=decision.jurisdiction_marking,
        future_dated_loss=decision.future_dated_loss,
        pended_at=None, resolved_at=resolution.resolved_at if applied else None,
    )
    if judged.verification is not None:
        coverage_verifications.append(
            resolution.store, record.notice_id, judged.verification,
            ruleset_version=RULESET_VERSION, evaluated_at=resolution.resolved_at,
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
