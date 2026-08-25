"""Orchestration for POST /notices and GET /notices/{notice_id}.

PHASE2_DESIGN.md's "Record state model", "HTTP surface" and "Idempotency";
STATUTORY_REGISTER.md for the duties discharged here. RECEIVED is written
durably, with its receipt timestamp, before any domain rule runs: that
timestamp starts the Fla. Stat. 627.70131(1)(a) acknowledgment clock and must
not depend on whether rule evaluation succeeds, is correct, or runs at all.
There is no rejected, invalid, or discarded state (CLAUDE.md). The raw payload
is persisted in that same write - receipt and payload are one statutory fact,
and item 5e appends later payload records to the sequence it starts.

**The receipt instant is `submitted_at`, and nothing here reads a clock.** The
notice's receipt, both audit entries and the payload record are all the instant
the caller supplied. Decided 2026-08-24, ASSUMPTIONS.md "One receipt clock, not
two": two clock reads for one statutory receipt event are invisible while calls
are synchronous and wrong the moment a queue sits between them.

**A created notice is two transactions** (corrected 2026-08-25). The receipt -
payload record, notice at RECEIVED, RECEIVED audit entry, and the idempotency
key row if one was supplied - commits before any domain rule runs; the decision
is a second transaction. `_apply_domain_rules` sits between them, inside
neither, so an exception there leaves the notice at RECEIVED with its receipt
intact and its key remembered, and the client's retry replays that notice
rather than creating a duplicate. That is what PHASE2_DESIGN.md's two-write
receipt is for: "a bug in rule evaluation must never be able to erase or delay
the fact that a notice was received." A refusal, a conflict and a replay each
stay one transaction.

**Order on the way in** (ASSUMPTIONS.md, "Idempotency: what a repeated key is
compared against"): carrier identity, the idempotency lookup, the loss-date
schema check, receipt. The key is envelope, answered before the content it
accompanies is judged, so a conflicting resubmission whose loss date does not
parse is a 409, not a 400.

Refusals before the receipt persist differently, each by recorded decision. An
unrecognized carrier_code means no insurer for a 627.70131(1)(a) duty to arise
to, so nothing is persisted ("Item 5c's 400 validates against the identity
reference, not the rules source"). A loss date that fails to parse is still a
received communication, so its payload is kept and referenced by hash ("A
refused submission is still a received communication") while its key, if any,
is not remembered against the refusal. A repeat carrying different content is a
409 - see idempotency.py.

Two further states raise rather than invent a status code: a carrier the
identity reference recognizes but whose rules entry cannot be resolved (item
5i), and a jurisdiction_timezone this item cannot resolve (item 5g). No
scenario reaches either. Also out of scope: the resolution endpoint (5e), SIU
(5f), and duplicate-candidate detection, left unsettled rather than assumed.
"""

import uuid
from collections.abc import Mapping
from datetime import date, datetime
from typing import Any

from claimgate.domain.carrier_configuration import resolve_carrier_configuration
from claimgate.domain.carrier_identity import CARRIER_IDENTITY_REFERENCE, resolve_carrier_identity
from claimgate.domain.jurisdiction import resolve_jurisdiction_date
from claimgate.domain.models import Candidate, CarrierRules, ValidationBlocker
from claimgate.domain.triage import triage_and_route
from claimgate.domain.validation import validate
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
from claimgate.shell.store import IdempotencyKeyAlreadyRememberedError, NoticeStore


def submit_notice(
    store: NoticeStore,
    *,
    carrier_code: str,
    submitted_at: datetime,
    jurisdiction_timezone: str,
    carrier_rules_source: Mapping[str, Mapping[str, Any]],
    fields: NoticeFields,
    idempotency_key: str | None = None,
) -> SubmitNoticeResponse:
    submission = Submission(
        store=store, carrier_code=carrier_code, submitted_at=submitted_at,
        jurisdiction_timezone=jurisdiction_timezone, carrier_rules_source=carrier_rules_source,
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
    identity = resolve_carrier_identity(submission.carrier_code, CARRIER_IDENTITY_REFERENCE)
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
    loss_date = _parse_loss_date(submission.fields.loss_date)
    if loss_date is None:
        reference = submission.store.refuse_payload(
            submission.carrier_code, submission.raw_payload, submission.submitted_at
        )
        return SubmitNoticeResponse(status=400, reference=reference)
    rules = _resolve_rules(submission.carrier_code, submission.carrier_rules_source)
    today = _resolve_today(submission.submitted_at, submission.jurisdiction_timezone)
    candidate = _build_candidate(submission.fields, loss_date)
    return _create_notice(submission, candidate, today, rules, expired_key=expired_key)


def _create_notice(
    submission: Submission, candidate: Candidate, today: date, rules: CarrierRules,
    *, expired_key: bool,
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
    return AcceptedNotice(notice_id=notice_id, candidate=candidate, today=today, rules=rules)


def _decide(submission: Submission, accepted: AcceptedNotice) -> SubmitNoticeResponse:
    """Rule evaluation runs outside every transaction, deliberately. If it
    raises, the exception propagates and the notice rests at RECEIVED with its
    receipt, its one audit entry and its key - so the client's retry replays
    that notice rather than creating a duplicate of it."""
    state, blockers, severity, queue = _apply_domain_rules(
        accepted.candidate, accepted.today, accepted.rules
    )
    with submission.store.submission():
        submission.store.record_decision(
            accepted.notice_id, state=state, blockers=blockers, severity=severity, queue=queue,
            occurred_at=submission.submitted_at,
        )
    return SubmitNoticeResponse(
        status=201, notice_id=accepted.notice_id, state=state, blockers=blockers,
        severity=severity, queue=queue, received_at=submission.submitted_at,
    )


def get_notice(store: NoticeStore, notice_id: str) -> NoticeView | None:
    record = store.get_notice(notice_id)
    return None if record is None else NoticeView.of(record)


def _parse_loss_date(raw: str | None) -> date | None:
    """Absent (None) input is item 5h's gap, preserved deliberately: it flows
    through as date.min, unchanged from today's behavior, because building 5h's
    presence check here would decide that reopening the opposite way from what
    is ratified. A present value that is not a date at all returns None, the
    schema-invalid signal."""
    if raw is None:
        return date.min
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


def _build_candidate(fields: NoticeFields, loss_date: date) -> Candidate:
    return Candidate(
        policy_number=fields.policy_number,
        loss_date=loss_date,
        loss_type=fields.loss_type,
        notice_type=fields.notice_type,
        claimant_name=fields.claimant_name,
        claimant_contact=fields.claimant_contact,
        incident_description=fields.incident_description,
    )


def _resolve_rules(
    carrier_code: str, rules_source: Mapping[str, Mapping[str, Any]]
) -> CarrierRules:
    result = resolve_carrier_configuration(carrier_code, rules_source)
    if result.rules is None:
        raise NotImplementedError(
            "carrier is identity-recognized but its rules entry could not be "
            "resolved - the status code for this is item 5i's to decide, not "
            "built here"
        )
    return result.rules


def _resolve_today(submitted_at: datetime, jurisdiction_timezone: str) -> date:
    result = resolve_jurisdiction_date(submitted_at, jurisdiction_timezone)
    if result.resolved_date is None:
        raise NotImplementedError(
            "an unrecognized jurisdiction_timezone reaching item 5c is not "
            "handled here - deriving and validating it is item 5g's job"
        )
    return result.resolved_date


def _apply_domain_rules(
    candidate: Candidate, today: date, rules: CarrierRules
) -> tuple[str, tuple[ValidationBlocker, ...], str | None, str | None]:
    result = validate(
        candidate,
        today,
        claimant_name_required=rules.claimant_name_required,
        claimant_contact_required=rules.claimant_contact_required,
        recognized_policy_number_prefixes=rules.recognized_policy_number_prefixes,
    )
    if result.blockers:
        return "PENDED", result.blockers, None, None
    outcome = triage_and_route(candidate)
    return "TRIAGED", (), outcome.severity, outcome.queue
