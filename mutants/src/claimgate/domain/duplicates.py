"""Pure duplicate-claim detection for a candidate FNOL record."""

from collections.abc import Iterable

from claimgate.domain.models import Candidate, ExistingClaim

DUPLICATE_WINDOW_DAYS = 3


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x_find_duplicates__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_find_duplicates__mutmut)
def find_duplicates(candidate: Candidate, existing_claims: Iterable[ExistingClaim]) -> list[str]:
    matches = [
        claim.claim_id for claim in existing_claims if _is_probable_duplicate(candidate, claim)
    ]
    return sorted(matches)


def x_find_duplicates__mutmut_orig(candidate: Candidate, existing_claims: Iterable[ExistingClaim]) -> list[str]:
    matches = [
        claim.claim_id for claim in existing_claims if _is_probable_duplicate(candidate, claim)
    ]
    return sorted(matches)


def x_find_duplicates__mutmut_1(candidate: Candidate, existing_claims: Iterable[ExistingClaim]) -> list[str]:
    matches = None
    return sorted(matches)


def x_find_duplicates__mutmut_2(candidate: Candidate, existing_claims: Iterable[ExistingClaim]) -> list[str]:
    matches = [
        claim.claim_id for claim in existing_claims if _is_probable_duplicate(None, claim)
    ]
    return sorted(matches)


def x_find_duplicates__mutmut_3(candidate: Candidate, existing_claims: Iterable[ExistingClaim]) -> list[str]:
    matches = [
        claim.claim_id for claim in existing_claims if _is_probable_duplicate(candidate, None)
    ]
    return sorted(matches)


def x_find_duplicates__mutmut_4(candidate: Candidate, existing_claims: Iterable[ExistingClaim]) -> list[str]:
    matches = [
        claim.claim_id for claim in existing_claims if _is_probable_duplicate(claim)
    ]
    return sorted(matches)


def x_find_duplicates__mutmut_5(candidate: Candidate, existing_claims: Iterable[ExistingClaim]) -> list[str]:
    matches = [
        claim.claim_id for claim in existing_claims if _is_probable_duplicate(candidate, )
    ]
    return sorted(matches)


def x_find_duplicates__mutmut_6(candidate: Candidate, existing_claims: Iterable[ExistingClaim]) -> list[str]:
    matches = [
        claim.claim_id for claim in existing_claims if _is_probable_duplicate(candidate, claim)
    ]
    return sorted(None)

mutants_x_find_duplicates__mutmut['_mutmut_orig'] = x_find_duplicates__mutmut_orig # type: ignore # mutmut generated
mutants_x_find_duplicates__mutmut['x_find_duplicates__mutmut_1'] = x_find_duplicates__mutmut_1 # type: ignore # mutmut generated
mutants_x_find_duplicates__mutmut['x_find_duplicates__mutmut_2'] = x_find_duplicates__mutmut_2 # type: ignore # mutmut generated
mutants_x_find_duplicates__mutmut['x_find_duplicates__mutmut_3'] = x_find_duplicates__mutmut_3 # type: ignore # mutmut generated
mutants_x_find_duplicates__mutmut['x_find_duplicates__mutmut_4'] = x_find_duplicates__mutmut_4 # type: ignore # mutmut generated
mutants_x_find_duplicates__mutmut['x_find_duplicates__mutmut_5'] = x_find_duplicates__mutmut_5 # type: ignore # mutmut generated
mutants_x_find_duplicates__mutmut['x_find_duplicates__mutmut_6'] = x_find_duplicates__mutmut_6 # type: ignore # mutmut generated
mutants_x__is_probable_duplicate__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__is_probable_duplicate__mutmut)
def _is_probable_duplicate(candidate: Candidate, claim: ExistingClaim) -> bool:
    same_policy = candidate.policy_number == claim.policy_number
    same_loss_type = candidate.loss_type == claim.loss_type
    within_window = abs((candidate.loss_date - claim.loss_date).days) <= DUPLICATE_WINDOW_DAYS
    return same_policy and same_loss_type and within_window


def x__is_probable_duplicate__mutmut_orig(candidate: Candidate, claim: ExistingClaim) -> bool:
    same_policy = candidate.policy_number == claim.policy_number
    same_loss_type = candidate.loss_type == claim.loss_type
    within_window = abs((candidate.loss_date - claim.loss_date).days) <= DUPLICATE_WINDOW_DAYS
    return same_policy and same_loss_type and within_window


def x__is_probable_duplicate__mutmut_1(candidate: Candidate, claim: ExistingClaim) -> bool:
    same_policy = None
    same_loss_type = candidate.loss_type == claim.loss_type
    within_window = abs((candidate.loss_date - claim.loss_date).days) <= DUPLICATE_WINDOW_DAYS
    return same_policy and same_loss_type and within_window


def x__is_probable_duplicate__mutmut_2(candidate: Candidate, claim: ExistingClaim) -> bool:
    same_policy = candidate.policy_number != claim.policy_number
    same_loss_type = candidate.loss_type == claim.loss_type
    within_window = abs((candidate.loss_date - claim.loss_date).days) <= DUPLICATE_WINDOW_DAYS
    return same_policy and same_loss_type and within_window


def x__is_probable_duplicate__mutmut_3(candidate: Candidate, claim: ExistingClaim) -> bool:
    same_policy = candidate.policy_number == claim.policy_number
    same_loss_type = None
    within_window = abs((candidate.loss_date - claim.loss_date).days) <= DUPLICATE_WINDOW_DAYS
    return same_policy and same_loss_type and within_window


def x__is_probable_duplicate__mutmut_4(candidate: Candidate, claim: ExistingClaim) -> bool:
    same_policy = candidate.policy_number == claim.policy_number
    same_loss_type = candidate.loss_type != claim.loss_type
    within_window = abs((candidate.loss_date - claim.loss_date).days) <= DUPLICATE_WINDOW_DAYS
    return same_policy and same_loss_type and within_window


def x__is_probable_duplicate__mutmut_5(candidate: Candidate, claim: ExistingClaim) -> bool:
    same_policy = candidate.policy_number == claim.policy_number
    same_loss_type = candidate.loss_type == claim.loss_type
    within_window = None
    return same_policy and same_loss_type and within_window


def x__is_probable_duplicate__mutmut_6(candidate: Candidate, claim: ExistingClaim) -> bool:
    same_policy = candidate.policy_number == claim.policy_number
    same_loss_type = candidate.loss_type == claim.loss_type
    within_window = abs(None) <= DUPLICATE_WINDOW_DAYS
    return same_policy and same_loss_type and within_window


def x__is_probable_duplicate__mutmut_7(candidate: Candidate, claim: ExistingClaim) -> bool:
    same_policy = candidate.policy_number == claim.policy_number
    same_loss_type = candidate.loss_type == claim.loss_type
    within_window = abs((candidate.loss_date + claim.loss_date).days) <= DUPLICATE_WINDOW_DAYS
    return same_policy and same_loss_type and within_window


def x__is_probable_duplicate__mutmut_8(candidate: Candidate, claim: ExistingClaim) -> bool:
    same_policy = candidate.policy_number == claim.policy_number
    same_loss_type = candidate.loss_type == claim.loss_type
    within_window = abs((candidate.loss_date - claim.loss_date).days) < DUPLICATE_WINDOW_DAYS
    return same_policy and same_loss_type and within_window


def x__is_probable_duplicate__mutmut_9(candidate: Candidate, claim: ExistingClaim) -> bool:
    same_policy = candidate.policy_number == claim.policy_number
    same_loss_type = candidate.loss_type == claim.loss_type
    within_window = abs((candidate.loss_date - claim.loss_date).days) <= DUPLICATE_WINDOW_DAYS
    return same_policy and same_loss_type or within_window


def x__is_probable_duplicate__mutmut_10(candidate: Candidate, claim: ExistingClaim) -> bool:
    same_policy = candidate.policy_number == claim.policy_number
    same_loss_type = candidate.loss_type == claim.loss_type
    within_window = abs((candidate.loss_date - claim.loss_date).days) <= DUPLICATE_WINDOW_DAYS
    return same_policy or same_loss_type and within_window

mutants_x__is_probable_duplicate__mutmut['_mutmut_orig'] = x__is_probable_duplicate__mutmut_orig # type: ignore # mutmut generated
mutants_x__is_probable_duplicate__mutmut['x__is_probable_duplicate__mutmut_1'] = x__is_probable_duplicate__mutmut_1 # type: ignore # mutmut generated
mutants_x__is_probable_duplicate__mutmut['x__is_probable_duplicate__mutmut_2'] = x__is_probable_duplicate__mutmut_2 # type: ignore # mutmut generated
mutants_x__is_probable_duplicate__mutmut['x__is_probable_duplicate__mutmut_3'] = x__is_probable_duplicate__mutmut_3 # type: ignore # mutmut generated
mutants_x__is_probable_duplicate__mutmut['x__is_probable_duplicate__mutmut_4'] = x__is_probable_duplicate__mutmut_4 # type: ignore # mutmut generated
mutants_x__is_probable_duplicate__mutmut['x__is_probable_duplicate__mutmut_5'] = x__is_probable_duplicate__mutmut_5 # type: ignore # mutmut generated
mutants_x__is_probable_duplicate__mutmut['x__is_probable_duplicate__mutmut_6'] = x__is_probable_duplicate__mutmut_6 # type: ignore # mutmut generated
mutants_x__is_probable_duplicate__mutmut['x__is_probable_duplicate__mutmut_7'] = x__is_probable_duplicate__mutmut_7 # type: ignore # mutmut generated
mutants_x__is_probable_duplicate__mutmut['x__is_probable_duplicate__mutmut_8'] = x__is_probable_duplicate__mutmut_8 # type: ignore # mutmut generated
mutants_x__is_probable_duplicate__mutmut['x__is_probable_duplicate__mutmut_9'] = x__is_probable_duplicate__mutmut_9 # type: ignore # mutmut generated
mutants_x__is_probable_duplicate__mutmut['x__is_probable_duplicate__mutmut_10'] = x__is_probable_duplicate__mutmut_10 # type: ignore # mutmut generated
