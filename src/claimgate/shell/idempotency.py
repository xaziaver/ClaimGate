"""The idempotency rules on POST /notices: what a repeated key resolves to, how
long it resolves to anything, and what a repeat carrying different content is.

PHASE2_DESIGN.md's "Idempotency" section is the specification; the two rules it
left undecided were decided 2026-08-24 and are recorded in ASSUMPTIONS.md,
"Idempotency: what a repeated key is compared against":

- **"Different" is a different payload reference.** One recipe (records.py's
  payload_reference), already persisted on every notice, so there is a single
  definition of "the same submission" rather than a second one invented here.
  Equal is a replay (200); unequal is a conflict (409).
- **The 24-hour window is half-open** - within it strictly before the mark,
  past it at the mark. RFC 9111 section 4.2's rule for a stored response, which
  is what every caller's HTTP stack already applies to a TTL.

Both instants compared here are receipt instants, never a clock read: the
notice's stored received_at, and the resubmission's own submitted_at.

Uniqueness itself is not enforced in this module. It is a UNIQUE constraint in
schema.py, per PHASE2_DESIGN.md's "enforced by a database constraint, not a
check-then-write", and losing to it is how a concurrent identical submission
resolves - see replay_after_losing_the_race.
"""

from datetime import timedelta

from claimgate.shell.messages import Submission, SubmitNoticeResponse
from claimgate.shell.records import NoticeRecord, payload_reference
from claimgate.shell.store import IdempotencyKeyAlreadyRememberedError

KEY_LIFETIME = timedelta(hours=24)


def find_remembered_notice(submission: Submission) -> NoticeRecord | None:
    """The notice this submission's key already created, if it has one. A key
    is remembered only by the notice it created, so a submission refused at the
    schema boundary leaves nothing here for its key to find."""
    if submission.idempotency_key is None:
        return None
    return submission.store.find_key(submission.carrier_code, submission.idempotency_key)


def is_within_key_lifetime(submission: Submission, remembered: NoticeRecord) -> bool:
    return submission.submitted_at - remembered.received_at < KEY_LIFETIME


def answer_repeated_key(submission: Submission, remembered: NoticeRecord) -> SubmitNoticeResponse:
    store = submission.store
    resubmitted = payload_reference(submission.raw_payload)
    if resubmitted != store.get_notice_payload_reference(remembered.notice_id):
        # A conflict creates no notice and adds nothing to the original's
        # trail, but the content is kept: this is an administered carrier and
        # a mis-keyed submission may still be a real loss.
        reference = store.refuse_payload(
            submission.carrier_code, submission.raw_payload, submission.submitted_at
        )
        return SubmitNoticeResponse(status=409, reference=reference)
    # 200, not 201: nothing was created. The state is the notice's current one,
    # read now, not the one it was in when the notice was first processed.
    return SubmitNoticeResponse(
        status=200,
        notice_id=remembered.notice_id,
        state=remembered.state,
        blockers=remembered.blockers,
        severity=remembered.severity,
        queue=remembered.queue,
        received_at=remembered.received_at,
    )


def replay_after_losing_the_race(submission: Submission) -> SubmitNoticeResponse:
    """The UNIQUE constraint refused our key row, so a concurrent identical
    submission committed first and ours rolled back whole. Re-read the key and
    answer as a repeat - PHASE2_DESIGN.md's "concurrent identical requests must
    resolve by constraint violation, not by a race condition". Re-raising when
    the key is gone again bounds this to one retry rather than looping."""
    remembered = find_remembered_notice(submission)
    if remembered is None:
        raise IdempotencyKeyAlreadyRememberedError(
            submission.carrier_code, submission.idempotency_key
        )
    return answer_repeated_key(submission, remembered)
