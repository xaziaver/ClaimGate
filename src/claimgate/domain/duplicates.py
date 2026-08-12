"""Pure duplicate-claim detection for a candidate FNOL record."""

from collections.abc import Iterable

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

    matches = [
        claim.claim_id
        for claim in existing_claims
        if _is_candidate_match(candidate, claim, window_days)
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


def _is_candidate_match(candidate: Candidate, claim: ExistingClaim, window_days: int) -> bool:
    same_policy = candidate.policy_number == claim.policy_number
    same_loss_type = candidate.loss_type == claim.loss_type
    within_window = abs((candidate.loss_date - claim.loss_date).days) <= window_days
    return same_policy and same_loss_type and within_window
