"""The receipt transaction of POST /notices (split out of notice_intake.py, item 7f).

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
"""

import uuid
from datetime import date

from claimgate.domain.carrier_identity import resolve_carrier_identity
from claimgate.domain.models import Candidate, CarrierRules, Jurisdiction
from claimgate.shell.faults import DeploymentFaultError
from claimgate.shell.idempotency import (
    answer_repeated_key,
    find_remembered_notice,
    is_within_key_lifetime,
    replay_after_losing_the_race,
)
from claimgate.shell.messages import AcceptedNotice, Submission, SubmitNoticeResponse
from claimgate.shell.rules import (
    build_candidate,
    parse_loss_date,
    resolve_jurisdiction,
    resolve_rules,
    resolve_today,
)
from claimgate.shell.store import IdempotencyKeyAlreadyRememberedError


def receive_or_replay(submission: Submission) -> SubmitNoticeResponse | AcceptedNotice:
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
