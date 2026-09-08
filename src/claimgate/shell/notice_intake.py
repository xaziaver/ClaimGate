"""Orchestration for POST /notices and GET /notices/{notice_id}.

PHASE2_DESIGN.md's "Record state model", "HTTP surface" and "Idempotency";
STATUTORY_REGISTER.md for the duties discharged here. RECEIVED is written
durably, with its receipt timestamp, before any domain rule runs: that timestamp
starts the Fla. Stat. 627.70131(1)(a) acknowledgment clock and must not depend
on whether rule evaluation succeeds, is correct, or runs at all. There is no
rejected, invalid, or discarded state (CLAUDE.md). The raw payload is persisted
in that same write - receipt and payload are one statutory fact - and item 5e
appends later payload records to the sequence it starts.

**The receipt instant is `submitted_at`, and nothing here reads a clock.** The
notice's receipt, both audit entries and the payload record are all the instant
the caller supplied (ASSUMPTIONS.md, "One receipt clock, not two", 2026-08-24):
two clock reads for one statutory receipt event are invisible while calls are
synchronous and wrong the moment a queue sits between them.

**A created notice is two transactions** (corrected 2026-08-25). The receipt -
payload record, notice at RECEIVED, RECEIVED audit entry, and the key row if one
was supplied - commits before any domain rule runs, with the decision following
in a second transaction and rule evaluation between them, inside neither. An
exception there leaves the notice at RECEIVED with its receipt and its key, and
the client's retry replays it rather than duplicating it: PHASE2_DESIGN.md's
two-write receipt exists so that "a bug in rule evaluation must never be able to
erase or delay the fact that a notice was received." A refusal, a conflict and a
replay each stay one transaction.

**The policy search sits between the two, since item 7f** (PHASE3_DESIGN.md,
"Where the calls sit"; shell/policy_match.py): the carrier's policy port,
resolved with the rest of the configuration before the receipt, is asked for the
policy and then its term history, holding no lock, and the domain reads the
answers - the continuous-coverage date onto the candidate, the match beside
validation's blockers. A source fault is a value and not an exception (ports.py),
so it never leaves a notice at RECEIVED; the decision transaction then writes the
decision, the verification row and the SIU events together, so a notice never
rests TRIAGED with half its attributes.

**Four configuration sources cross this boundary and none of them is a
default** (item 5g; the fourth is item 7f's): the carrier identity reference,
the jurisdiction map, the per-carrier rules source and the port bindings with
the registry they select from, all named explicitly by production and tests
alike. A shipped value read from the domain would make the swappability proofs
a test of monkeypatching rather than of the seam.

**The SIU evaluation item 5f owes a transition into TRIAGED runs inside the
decision transaction**, from siu.py, which the resolution path calls too, and
only where this submission's decision was TRIAGED: a pend is an incomplete
intake record and evaluates nothing, and a replay or a refusal never reaches
here. Duplicate-candidate detection stays out of scope, unsettled not assumed.
"""

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from claimgate.domain.continuous_coverage import carry_onto_candidate
from claimgate.domain.models import Candidate, CarrierIdentity
from claimgate.domain.policy_match import PolicyMatch
from claimgate.domain.ruleset import RULESET_VERSION
from claimgate.shell import coverage_verifications, siu
from claimgate.shell.bindings import BindingsSource, ImplementationRegistry
from claimgate.shell.coverage_verifications import Verification
from claimgate.shell.messages import (
    AcceptedNotice,
    Decision,
    NoticeFields,
    NoticeView,
    Submission,
    SubmitNoticeResponse,
)
from claimgate.shell.policy_match import verify_policy
from claimgate.shell.receipt import receive_or_replay
from claimgate.shell.rules import apply_domain_rules
from claimgate.shell.store import NoticeStore


def submit_notice(
    store: NoticeStore,
    *,
    carrier_code: str,
    submitted_at: datetime,
    carrier_identity_reference: Mapping[str, CarrierIdentity],
    jurisdiction_reference: Mapping[str, Mapping[str, str]],
    carrier_rules_source: Mapping[str, Mapping[str, Any]],
    bindings_source: BindingsSource,
    implementation_registry: ImplementationRegistry,
    fields: NoticeFields,
    idempotency_key: str | None = None,
) -> SubmitNoticeResponse:
    submission = Submission(
        store=store, carrier_code=carrier_code, submitted_at=submitted_at,
        carrier_identity_reference=carrier_identity_reference,
        jurisdiction_reference=jurisdiction_reference,
        carrier_rules_source=carrier_rules_source,
        bindings_source=bindings_source, implementation_registry=implementation_registry,
        fields=fields, idempotency_key=idempotency_key,
    )
    received = receive_or_replay(submission)
    if isinstance(received, SubmitNoticeResponse):
        return received
    return _decide(submission, received)


def _decide(submission: Submission, accepted: AcceptedNotice) -> SubmitNoticeResponse:
    """The search, then rule evaluation, both outside every transaction,
    deliberately. If evaluation raises, the exception propagates and the notice
    rests at RECEIVED with its receipt, its one audit entry and its key - so the
    client's retry replays that notice rather than creating a duplicate of it.
    The search cannot raise: a fault is a value on the verification."""
    verification = verify_policy(
        accepted.policy_port, submission.fields, accepted.candidate.loss_date
    )
    candidate, match = _verified(accepted.candidate, verification)
    decision = apply_domain_rules(
        candidate, accepted.jurisdiction, accepted.today, accepted.rules, match
    )
    with submission.store.submission():
        _record(submission, accepted, decision, verification, candidate)
    return SubmitNoticeResponse(
        status=201, notice_id=accepted.notice_id, state=decision.state,
        blockers=decision.blockers, severity=decision.severity, queue=decision.queue,
        received_at=submission.submitted_at,
    )


def _record(
    submission: Submission, accepted: AcceptedNotice, decision: Decision,
    verification: Verification | None, candidate: Candidate,
) -> None:
    """The decision transaction: the decision, the verification row and the
    SIU events together (PHASE3_DESIGN.md, "Where the calls sit"), so a notice
    never rests TRIAGED with half its attributes."""
    submission.store.record_decision(
        accepted.notice_id, state=decision.state, blockers=decision.blockers,
        severity=decision.severity, queue=decision.queue,
        jurisdiction_marking=decision.jurisdiction_marking,
        future_dated_loss=decision.future_dated_loss,
        occurred_at=submission.submitted_at,
    )
    if verification is not None:
        coverage_verifications.append(
            submission.store, accepted.notice_id, verification,
            ruleset_version=RULESET_VERSION, evaluated_at=submission.submitted_at,
        )
    if decision.state == "TRIAGED":
        _record_indicators(submission, accepted, candidate)


def _verified(
    candidate: Candidate, verification: Verification | None
) -> tuple[Candidate, PolicyMatch | None]:
    """What the rules are given once the search has answered: the candidate
    carrying the continuous-coverage date the history yielded, and the match.
    A notice nothing could be searched on keeps its candidate as received and
    hands the rules no match - not a match that found nothing."""
    if verification is None:
        return candidate, None
    return carry_onto_candidate(candidate, verification.coverage), verification.match


def _record_indicators(
    submission: Submission, accepted: AcceptedNotice, candidate: Candidate
) -> None:
    """The intake path's half of item 5f decision 1, inside the decision
    transaction so the events and the transition commit together. Both instants
    are the submission's: on this path the notice was received and triaged in
    one request, so the day the interval is counted from and the instant the
    evaluation happened are the same event rather than a coincidence. The
    candidate is the verified one, so the recent-inception indicator reads the
    date the term history yielded (item 7f)."""
    siu.record_evaluation(
        submission.store,
        accepted.notice_id,
        candidate=candidate,
        rules=accepted.rules,
        received_at=submission.submitted_at,
        jurisdiction=accepted.jurisdiction,
        evaluated_at=submission.submitted_at,
    )


def get_notice(store: NoticeStore, notice_id: str) -> NoticeView | None:
    record = store.get_notice(notice_id)
    if record is None:
        return None
    verification = coverage_verifications.view_of(coverage_verifications.latest(store, notice_id))
    return NoticeView.of(record, verification)
