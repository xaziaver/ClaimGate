"""Pure duplicate-claim detection for a candidate FNOL record."""

from collections.abc import Iterable
from datetime import date

from claimgate.domain.models import Candidate, DuplicateMatchResult, ExistingClaim

FOLLOW_ON_NOTICE_TYPE = "FOLLOW_ON_NOTICE_TYPE"
NO_EXISTING_CLAIM_NOTICE_TYPE = "NO_EXISTING_CLAIM_NOTICE_TYPE"

_FOLLOW_ON_NOTICE_TYPES = frozenset({"SUPPLEMENTAL", "REOPENED"})


def find_duplicates(
    candidate: Candidate,
    existing_claims: Iterable[ExistingClaim],
    window_days: int,
) -> DuplicateMatchResult:
    excluded = _resolve_notice_type_exclusion(candidate.notice_type)
    if excluded is not None:
        return excluded

    loss_date = _require_loss_date(candidate)
    matches = [
        claim.claim_id
        for claim in existing_claims
        if _is_candidate_match(candidate, claim, loss_date, window_days)
    ]
    # Evaluation walks existing_claims in whatever order the caller passed -
    # the sort below is what produces the ascending order the spec requires.
    # Do not reorder evaluation to match output "for clarity": a mutation
    # deleting this sort is only caught because the two orders differ
    # (docs/harness-findings.md, "Ordering assertions can pass without a sort
    # existing").
    return DuplicateMatchResult(value="EVALUATED", matches=tuple(sorted(matches)))


def _resolve_notice_type_exclusion(notice_type: str) -> DuplicateMatchResult | None:
    if notice_type in _FOLLOW_ON_NOTICE_TYPES:
        return DuplicateMatchResult(value="NOT_EVALUATED", reason=FOLLOW_ON_NOTICE_TYPE)
    if notice_type == "LOSS_ASSESSMENT":
        return DuplicateMatchResult(value="NOT_EVALUATED", reason=NO_EXISTING_CLAIM_NOTICE_TYPE)
    if notice_type == "INITIAL":
        return None
    # Unreached on the designed path: validation.feature already resolves any
    # other value to NOTICE_TYPE_UNRECOGNIZED, and PHASE2_DESIGN.md's
    # transition table sends a notice with a blocker to PENDED, never
    # TRIAGED - duplicate candidates are data on a TRIAGED notice, so this
    # function never sees one. ValueError, not a third NOT_EVALUATED reason
    # code: this isn't a business outcome to record, it's a caller contract
    # violation, and the enumeration is closed at two.
    raise ValueError(f"find_duplicates: unrecognized notice_type {notice_type!r}")


def _require_loss_date(candidate: Candidate) -> date:
    # Unreached on the designed path, for the reason the notice-type raise
    # above is: duplicate candidates are data on a TRIAGED notice, and an
    # absent loss date is a blocker that pends the notice instead (item 5h).
    # ValueError and not a third NOT_EVALUATED reason - the same ground item 3
    # settled one function over, a caller contract violation rather than a
    # business outcome to record, and this enumeration is closed at two.
    # Checked here and not above the exclusion because the loss date is
    # required only where a comparison is actually run: an excluded notice
    # type needs no date to resolve, and raising on one would refuse an input
    # this function answers without ever reading it.
    if candidate.loss_date is None:
        raise ValueError("find_duplicates: candidate states no loss date")
    return candidate.loss_date


def _is_candidate_match(
    candidate: Candidate, claim: ExistingClaim, loss_date: date, window_days: int
) -> bool:
    same_policy = candidate.policy_number == claim.policy_number
    same_loss_type = candidate.loss_type == claim.loss_type
    within_window = abs((loss_date - claim.loss_date).days) <= window_days
    return same_policy and same_loss_type and within_window
