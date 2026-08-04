"""Pure duplicate-claim detection for a candidate FNOL record."""

from collections.abc import Iterable

from claimgate.domain.models import Candidate, ExistingClaim

DUPLICATE_WINDOW_DAYS = 3


def find_duplicates(candidate: Candidate, existing_claims: Iterable[ExistingClaim]) -> list[str]:
    matches = [
        claim.claim_id for claim in existing_claims if _is_probable_duplicate(candidate, claim)
    ]
    return sorted(matches)


def _is_probable_duplicate(candidate: Candidate, claim: ExistingClaim) -> bool:
    same_policy = candidate.policy_number == claim.policy_number
    same_loss_type = candidate.loss_type == claim.loss_type
    within_window = abs((candidate.loss_date - claim.loss_date).days) <= DUPLICATE_WINDOW_DAYS
    return same_policy and same_loss_type and within_window
