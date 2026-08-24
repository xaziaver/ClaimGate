"""Orchestration for POST /notices and GET /notices/{notice_id}.

PHASE2_DESIGN.md's "Record state model", "HTTP surface" and "Idempotency";
STATUTORY_REGISTER.md for the duties discharged here. RECEIVED is written
durably, with its receipt timestamp, before any domain rule runs - a deliberate
two-write design, because that timestamp starts the Fla. Stat. 627.70131(1)(a)
seven-calendar-day acknowledgment clock and must not depend on whether rule
evaluation succeeds, is correct, or even runs at all. There is no rejected,
invalid, or discarded state (CLAUDE.md): once a submission clears the checks
below it always reaches RECEIVED and then TRIAGED or PENDED in the same
request. The raw payload is persisted in that same RECEIVED write - the receipt
and the payload are one statutory fact, not two, and item 5e's resolution
design appends later payload records to the same per-notice sequence it starts.

**The receipt instant is `submitted_at`, and nothing here reads a clock.** Every
timestamp a submission writes - the notice's receipt, both audit entries, the
payload record - is the instant the caller supplied. Decided 2026-08-24,
ASSUMPTIONS.md "One receipt clock, not two": two clock reads for one statutory
receipt event are invisible while calls are synchronous and wrong the moment a
transport layer or a queue sits between them.

**The whole submission is one transaction** (`store.submission()`): a refusal,
or a receipt with its decision and its idempotency key, commits once.

**Order on the way in** (ASSUMPTIONS.md, "Idempotency: what a repeated key is
compared against"): carrier identity, then the idempotency lookup, then the
loss-date schema check, then receipt. The key is envelope, like the carrier
code - answered before the content it accompanies is judged - so a conflicting
resubmission whose loss date does not parse is a 409, not a 400.

Refusals before the receipt persist differently, each by recorded decision:
- An unrecognized carrier_code (checked first, ahead of every other rule) means
  there is no insurer here for a 627.70131(1)(a) duty to arise to - refused with
  nothing persisted at all ("Item 5c's 400 validates against the identity
  reference, not the rules source").
- A loss date that fails to parse as a date at all is still a received claim
  communication under 627.70131(1)(a) - refused, but its raw payload is kept and
  referenced by hash ("A refused submission is still a received communication").
  Its key, if it carried one, is not remembered against the refusal: a key is
  remembered only by the notice it created, so the corrected resubmission the
  caller sends next is judged on its own.
- A repeated key carrying different content is a 409 - see idempotency.py.

An absent (not merely malformed) loss_date is deliberately not a further case
here: item 5h's presence check does not exist yet, and building it inside this
item would decide that reopening the opposite way from what's ratified. See
_parse_loss_date.

Two further states are reachable only through decisions this item does not
build, and raise rather than invent a status code for them: a carrier the
identity reference recognizes but whose rules entry cannot be resolved (item
5i), and a jurisdiction_timezone this item receives but cannot resolve (item
5g owns deriving and validating it). No scenario reaches either path.

Out of scope here: the resolution endpoint (5e), SIU computation and storage
(5f), jurisdiction-map generalization (5g), and duplicate-candidate detection,
left unsettled rather than assumed.
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
from claimgate.shell.messages import NoticeFields, NoticeView, Submission, SubmitNoticeResponse
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
    try:
        with store.submission():
            return _submit(submission)
    except IdempotencyKeyAlreadyRememberedError:
        with store.submission():
            return replay_after_losing_the_race(submission)


def _submit(submission: Submission) -> SubmitNoticeResponse:
    identity = resolve_carrier_identity(submission.carrier_code, CARRIER_IDENTITY_REFERENCE)
    if identity.value == "REFUSED":
        return SubmitNoticeResponse(status=400)
    remembered = find_remembered_notice(submission)
    if remembered is not None and is_within_key_lifetime(submission, remembered):
        return answer_repeated_key(submission, remembered)
    return _first_submission(submission, expired_key=remembered is not None)


def _first_submission(submission: Submission, *, expired_key: bool) -> SubmitNoticeResponse:
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
) -> SubmitNoticeResponse:
    store = submission.store
    notice_id = str(uuid.uuid4())
    received_at = submission.submitted_at
    store.receive_notice(notice_id, submission.carrier_code, submission.raw_payload, received_at)
    state, blockers, severity, queue = _apply_domain_rules(candidate, today, rules)
    store.record_decision(
        notice_id, state=state, blockers=blockers, severity=severity, queue=queue,
        occurred_at=received_at,
    )
    if submission.idempotency_key is not None:
        store.remember_key(
            submission.carrier_code, submission.idempotency_key, notice_id,
            replacing_expired=expired_key,
        )
    return SubmitNoticeResponse(
        status=201, notice_id=notice_id, state=state, blockers=blockers, severity=severity,
        queue=queue, received_at=received_at,
    )


def get_notice(store: NoticeStore, notice_id: str) -> NoticeView | None:
    record = store.get_notice(notice_id)
    if record is None:
        return None
    return NoticeView(
        notice_id=record.notice_id,
        state=record.state,
        blockers=record.blockers,
        severity=record.severity,
        queue=record.queue,
    )


def _parse_loss_date(raw: str | None) -> date | None:
    """Absent (None) input is item 5h's gap, preserved deliberately: it flows
    through as date.min, unchanged from today's behavior. A present value
    that is not a date at all returns None, the schema-invalid signal."""
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
