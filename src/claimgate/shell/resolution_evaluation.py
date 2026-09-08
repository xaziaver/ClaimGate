"""The evaluation inside the resolution transaction (split out of resolution.py, item 7f).

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

**The policy match is re-asserted from the stored verification, not searched
again** (item 7f; ASSUMPTIONS.md, 7f decision 6). _judge reads the notice's
latest coverage verification (coverage_verifications.py) and hands the rules the
match it recorded, so POLICY_NOT_MATCHED and POLICY_AMBIGUOUS persist through a
resolution that corrects an unrelated field, and the continuous-coverage date it
recorded travels onto the candidate through the same producer intake uses, so
the SIU evaluation a release owes reads the date the term history yielded. No
port is called on this path and no verification row is written: nothing new was
verified. Item 7g re-searches on the merged identifiers, which is what will
clear such a pend once a reviewer has corrected the policy number.
"""

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


def evaluate(resolution: Resolution, record: NoticeRecord) -> ResolutionResponse:
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
    verification = coverage_verifications.latest(resolution.store, record.notice_id)
    candidate = _candidate_of(view, verification)
    carrier_rules = rules.resolve_rules(record.carrier_code, resolution.carrier_rules_source)
    jurisdiction = rules.resolve_jurisdiction(
        view.property_state, resolution.jurisdiction_reference
    )
    decision: Decision = rules.apply_domain_rules(
        candidate,
        jurisdiction,
        rules.resolve_today(resolution.resolved_at, jurisdiction),
        carrier_rules,
        _match_of(verification),
    )
    return Judgement(decision, candidate, carrier_rules, jurisdiction)


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
    fields: dict[str, Any] = {}
    for record in notice_records(store, notice_id):
        fields.update(record.content)
    return NoticeFields(**fields)


def notice_records(store: NoticeStore, notice_id: str) -> tuple[PayloadRecord, ...]:
    return store.get_notice_payloads(notice_id)
