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

**Order on the way in** (ASSUMPTIONS.md, "Idempotency: what a repeated key is
compared against"): carrier identity, the idempotency lookup, the loss-date
schema check, then the configuration this deployment needs, then receipt. The
key is envelope, answered before the content it accompanies is judged, so a
conflicting resubmission whose loss date does not parse is a 409, not a 400.

Refusals before the receipt persist differently. An unrecognized carrier_code
persists nothing at all; the two that keep what arrived share one shape, in
`_receipt_only`; a repeat carrying different content is a 409, in idempotency.py.

The rules this module runs moved to rules.py in item 5e, because decision 2(a)
wants one definition of "no blocker" rather than one per endpoint; the
deployment faults are raised there and answered here (item 5i, faults.py).
**Both are answered before any notice exists**, which is a measured fact about
this order rather than a choice - the carrier's rules and the jurisdiction
resolve above `_create_notice`, so neither fault leaves a notice at RECEIVED nor
remembers the idempotency key, and a reporter's identical retry creates a notice
rather than replaying one no rule ever ran over (idempotency.feature, Rule 6).

**Three configuration sources cross this boundary and none of them is a
default** (item 5g): the carrier identity reference, the jurisdiction map and
the per-carrier rules source, all named explicitly by production and tests
alike. A shipped value read from the domain would make the swappability proofs
a test of monkeypatching rather than of the seam.

**The SIU evaluation item 5f owes a transition into TRIAGED runs inside the
decision transaction**, from siu.py, which the resolution path calls too, and
only where this submission's decision was TRIAGED: a pend is an incomplete
intake record and evaluates nothing, and a replay or a refusal never reaches
here. Duplicate-candidate detection stays out of scope, unsettled not assumed.
"""

import uuid
from collections.abc import Mapping
from datetime import date, datetime
from typing import Any

from claimgate.domain.carrier_identity import resolve_carrier_identity
from claimgate.domain.models import Candidate, CarrierIdentity, CarrierRules, Jurisdiction
from claimgate.shell import siu
from claimgate.shell.faults import DeploymentFaultError
from claimgate.shell.idempotency import (
    answer_repeated_key,
    find_remembered_notice,
    is_within_key_lifetime,
    replay_after_losing_the_race,
)
from claimgate.shell.messages import (
    AcceptedNotice,
    NoticeFields,
    NoticeView,
    Submission,
    SubmitNoticeResponse,
)
from claimgate.shell.rules import (
    apply_domain_rules,
    build_candidate,
    parse_loss_date,
    resolve_jurisdiction,
    resolve_rules,
    resolve_today,
)
from claimgate.shell.store import IdempotencyKeyAlreadyRememberedError, NoticeStore


def submit_notice(
    store: NoticeStore,
    *,
    carrier_code: str,
    submitted_at: datetime,
    carrier_identity_reference: Mapping[str, CarrierIdentity],
    jurisdiction_reference: Mapping[str, Mapping[str, str]],
    carrier_rules_source: Mapping[str, Mapping[str, Any]],
    fields: NoticeFields,
    idempotency_key: str | None = None,
) -> SubmitNoticeResponse:
    submission = Submission(
        store=store, carrier_code=carrier_code, submitted_at=submitted_at,
        carrier_identity_reference=carrier_identity_reference,
        jurisdiction_reference=jurisdiction_reference,
        carrier_rules_source=carrier_rules_source,
        fields=fields, idempotency_key=idempotency_key,
    )
    received = _receive_or_replay(submission)
    if isinstance(received, SubmitNoticeResponse):
        return received
    return _decide(submission, received)


def _receive_or_replay(submission: Submission) -> SubmitNoticeResponse | AcceptedNotice:
    """The receipt transaction. IMMEDIATE takes the write lock before the
    idempotency lookup, so nothing can insert the key between that lookup and
    the insert that follows it. Losing to the constraint anyway rolls this
    transaction back whole and answers as a replay in a fresh one."""
    try:
        with submission.store.submission():
            return _receive(submission)
    except IdempotencyKeyAlreadyRememberedError:
        with submission.store.submission():
            return replay_after_losing_the_race(submission)


def _receive(submission: Submission) -> SubmitNoticeResponse | AcceptedNotice:
    identity = resolve_carrier_identity(
        submission.carrier_code, submission.carrier_identity_reference
    )
    if identity.value == "REFUSED":
        return SubmitNoticeResponse(status=400)
    remembered = find_remembered_notice(submission)
    if remembered is not None and is_within_key_lifetime(submission, remembered):
        return answer_repeated_key(submission, remembered)
    return _first_submission(submission, expired_key=remembered is not None)


def _first_submission(
    submission: Submission, *, expired_key: bool
) -> SubmitNoticeResponse | AcceptedNotice:
    """Whatever the key situation was, this submission is now judged the way a
    first-ever one is: past its window there is no idempotency record left to
    find, and a key with no notice behind it never named anything."""
    parsed = parse_loss_date(submission.fields.loss_date)
    if parsed.value == "UNPARSEABLE":
        return _receipt_only(submission, status=400)
    try:
        rules = resolve_rules(submission.carrier_code, submission.carrier_rules_source)
        jurisdiction = resolve_jurisdiction(
            submission.fields.property_state, submission.jurisdiction_reference
        )
        today = resolve_today(submission.submitted_at, jurisdiction)
    except DeploymentFaultError as fault:
        return _receipt_only(submission, status=500, error=fault.code)
    # ABSENT is deliberately not refused here: it flows through as None and the
    # domain pends the notice on MISSING_REQUIRED_FIELD:loss_date (item 5h).
    candidate = build_candidate(submission.fields, parsed.loss_date)
    return _create_notice(
        submission, candidate, jurisdiction, today, rules, expired_key=expired_key
    )


def _receipt_only(
    submission: Submission, *, status: int, error: str | None = None
) -> SubmitNoticeResponse:
    """What a submission that creates no notice still leaves behind: its payload,
    referenced by its own hash, and nothing else - no key row, because a key
    names a notice from the moment the notice exists, and no audit entry,
    because one cannot exist without a notice at all (item 5i, ruling 4). The
    two refusals that reach here keep it for reasons of their own, in
    notice_intake.feature's Rules 3 and 5."""
    reference = submission.store.refuse_payload(
        submission.carrier_code, submission.raw_payload, submission.submitted_at, error
    )
    return SubmitNoticeResponse(status=status, reference=reference, error=error)


def _create_notice(
    submission: Submission, candidate: Candidate, jurisdiction: Jurisdiction | None,
    today: date | None, rules: CarrierRules, *, expired_key: bool,
) -> AcceptedNotice:
    """Everything the receipt transaction writes: the payload record and the
    notice at RECEIVED with its audit entry, and the key row, which belongs
    here because a key names a notice from the moment the notice exists."""
    store = submission.store
    notice_id = str(uuid.uuid4())
    store.receive_notice(
        notice_id, submission.carrier_code, submission.raw_payload, submission.submitted_at
    )
    if submission.idempotency_key is not None:
        store.remember_key(
            submission.carrier_code, submission.idempotency_key, notice_id,
            replacing_expired=expired_key,
        )
    return AcceptedNotice(
        notice_id=notice_id, candidate=candidate, jurisdiction=jurisdiction,
        today=today, rules=rules,
    )


def _decide(submission: Submission, accepted: AcceptedNotice) -> SubmitNoticeResponse:
    """Rule evaluation runs outside every transaction, deliberately. If it
    raises, the exception propagates and the notice rests at RECEIVED with its
    receipt, its one audit entry and its key - so the client's retry replays
    that notice rather than creating a duplicate of it."""
    decision = apply_domain_rules(
        accepted.candidate, accepted.jurisdiction, accepted.today, accepted.rules
    )
    with submission.store.submission():
        submission.store.record_decision(
            accepted.notice_id, state=decision.state, blockers=decision.blockers,
            severity=decision.severity, queue=decision.queue,
            jurisdiction_marking=decision.jurisdiction_marking,
            future_dated_loss=decision.future_dated_loss,
            occurred_at=submission.submitted_at,
        )
        if decision.state == "TRIAGED":
            _record_indicators(submission, accepted)
    return SubmitNoticeResponse(
        status=201, notice_id=accepted.notice_id, state=decision.state,
        blockers=decision.blockers, severity=decision.severity, queue=decision.queue,
        received_at=submission.submitted_at,
    )


def _record_indicators(submission: Submission, accepted: AcceptedNotice) -> None:
    """The intake path's half of item 5f decision 1, inside the decision
    transaction so the events and the transition commit together. Both instants
    are the submission's: on this path the notice was received and triaged in
    one request, so the day the interval is counted from and the instant the
    evaluation happened are the same event rather than a coincidence."""
    siu.record_evaluation(
        submission.store,
        accepted.notice_id,
        candidate=accepted.candidate,
        rules=accepted.rules,
        received_at=submission.submitted_at,
        jurisdiction=accepted.jurisdiction,
        evaluated_at=submission.submitted_at,
    )


def get_notice(store: NoticeStore, notice_id: str) -> NoticeView | None:
    record = store.get_notice(notice_id)
    return None if record is None else NoticeView.of(record)

