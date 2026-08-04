"""Pure SIU fraud-indicator rules for a candidate FNOL record."""

from datetime import date

from claimgate.domain.models import Candidate, SiuFlags

LATE_REPORTING_THRESHOLD_DAYS = 30
RECENT_INCEPTION_THRESHOLD_DAYS = 30


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x_compute_siu_flags__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_compute_siu_flags__mutmut)
def compute_siu_flags(candidate: Candidate, now: date) -> SiuFlags:
    return SiuFlags(
        late_reporting=_is_late_reporting(candidate.loss_date, now),
        recent_policy_inception=_is_recent_inception(candidate),
    )


def x_compute_siu_flags__mutmut_orig(candidate: Candidate, now: date) -> SiuFlags:
    return SiuFlags(
        late_reporting=_is_late_reporting(candidate.loss_date, now),
        recent_policy_inception=_is_recent_inception(candidate),
    )


def x_compute_siu_flags__mutmut_1(candidate: Candidate, now: date) -> SiuFlags:
    return SiuFlags(
        late_reporting=None,
        recent_policy_inception=_is_recent_inception(candidate),
    )


def x_compute_siu_flags__mutmut_2(candidate: Candidate, now: date) -> SiuFlags:
    return SiuFlags(
        late_reporting=_is_late_reporting(candidate.loss_date, now),
        recent_policy_inception=None,
    )


def x_compute_siu_flags__mutmut_3(candidate: Candidate, now: date) -> SiuFlags:
    return SiuFlags(
        recent_policy_inception=_is_recent_inception(candidate),
    )


def x_compute_siu_flags__mutmut_4(candidate: Candidate, now: date) -> SiuFlags:
    return SiuFlags(
        late_reporting=_is_late_reporting(candidate.loss_date, now),
        )


def x_compute_siu_flags__mutmut_5(candidate: Candidate, now: date) -> SiuFlags:
    return SiuFlags(
        late_reporting=_is_late_reporting(None, now),
        recent_policy_inception=_is_recent_inception(candidate),
    )


def x_compute_siu_flags__mutmut_6(candidate: Candidate, now: date) -> SiuFlags:
    return SiuFlags(
        late_reporting=_is_late_reporting(candidate.loss_date, None),
        recent_policy_inception=_is_recent_inception(candidate),
    )


def x_compute_siu_flags__mutmut_7(candidate: Candidate, now: date) -> SiuFlags:
    return SiuFlags(
        late_reporting=_is_late_reporting(now),
        recent_policy_inception=_is_recent_inception(candidate),
    )


def x_compute_siu_flags__mutmut_8(candidate: Candidate, now: date) -> SiuFlags:
    return SiuFlags(
        late_reporting=_is_late_reporting(candidate.loss_date, ),
        recent_policy_inception=_is_recent_inception(candidate),
    )


def x_compute_siu_flags__mutmut_9(candidate: Candidate, now: date) -> SiuFlags:
    return SiuFlags(
        late_reporting=_is_late_reporting(candidate.loss_date, now),
        recent_policy_inception=_is_recent_inception(None),
    )

mutants_x_compute_siu_flags__mutmut['_mutmut_orig'] = x_compute_siu_flags__mutmut_orig # type: ignore # mutmut generated
mutants_x_compute_siu_flags__mutmut['x_compute_siu_flags__mutmut_1'] = x_compute_siu_flags__mutmut_1 # type: ignore # mutmut generated
mutants_x_compute_siu_flags__mutmut['x_compute_siu_flags__mutmut_2'] = x_compute_siu_flags__mutmut_2 # type: ignore # mutmut generated
mutants_x_compute_siu_flags__mutmut['x_compute_siu_flags__mutmut_3'] = x_compute_siu_flags__mutmut_3 # type: ignore # mutmut generated
mutants_x_compute_siu_flags__mutmut['x_compute_siu_flags__mutmut_4'] = x_compute_siu_flags__mutmut_4 # type: ignore # mutmut generated
mutants_x_compute_siu_flags__mutmut['x_compute_siu_flags__mutmut_5'] = x_compute_siu_flags__mutmut_5 # type: ignore # mutmut generated
mutants_x_compute_siu_flags__mutmut['x_compute_siu_flags__mutmut_6'] = x_compute_siu_flags__mutmut_6 # type: ignore # mutmut generated
mutants_x_compute_siu_flags__mutmut['x_compute_siu_flags__mutmut_7'] = x_compute_siu_flags__mutmut_7 # type: ignore # mutmut generated
mutants_x_compute_siu_flags__mutmut['x_compute_siu_flags__mutmut_8'] = x_compute_siu_flags__mutmut_8 # type: ignore # mutmut generated
mutants_x_compute_siu_flags__mutmut['x_compute_siu_flags__mutmut_9'] = x_compute_siu_flags__mutmut_9 # type: ignore # mutmut generated
mutants_x__is_late_reporting__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__is_late_reporting__mutmut)
def _is_late_reporting(loss_date: date, now: date) -> bool:
    return (now - loss_date).days > LATE_REPORTING_THRESHOLD_DAYS


def x__is_late_reporting__mutmut_orig(loss_date: date, now: date) -> bool:
    return (now - loss_date).days > LATE_REPORTING_THRESHOLD_DAYS


def x__is_late_reporting__mutmut_1(loss_date: date, now: date) -> bool:
    return (now + loss_date).days > LATE_REPORTING_THRESHOLD_DAYS


def x__is_late_reporting__mutmut_2(loss_date: date, now: date) -> bool:
    return (now - loss_date).days >= LATE_REPORTING_THRESHOLD_DAYS

mutants_x__is_late_reporting__mutmut['_mutmut_orig'] = x__is_late_reporting__mutmut_orig # type: ignore # mutmut generated
mutants_x__is_late_reporting__mutmut['x__is_late_reporting__mutmut_1'] = x__is_late_reporting__mutmut_1 # type: ignore # mutmut generated
mutants_x__is_late_reporting__mutmut['x__is_late_reporting__mutmut_2'] = x__is_late_reporting__mutmut_2 # type: ignore # mutmut generated
mutants_x__is_recent_inception__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__is_recent_inception__mutmut)
def _is_recent_inception(candidate: Candidate) -> bool:
    inception = candidate.policy_inception_date
    if inception is None:
        return False
    days_since_inception = (candidate.loss_date - inception).days
    return 0 <= days_since_inception <= RECENT_INCEPTION_THRESHOLD_DAYS


def x__is_recent_inception__mutmut_orig(candidate: Candidate) -> bool:
    inception = candidate.policy_inception_date
    if inception is None:
        return False
    days_since_inception = (candidate.loss_date - inception).days
    return 0 <= days_since_inception <= RECENT_INCEPTION_THRESHOLD_DAYS


def x__is_recent_inception__mutmut_1(candidate: Candidate) -> bool:
    inception = None
    if inception is None:
        return False
    days_since_inception = (candidate.loss_date - inception).days
    return 0 <= days_since_inception <= RECENT_INCEPTION_THRESHOLD_DAYS


def x__is_recent_inception__mutmut_2(candidate: Candidate) -> bool:
    inception = candidate.policy_inception_date
    if inception is not None:
        return False
    days_since_inception = (candidate.loss_date - inception).days
    return 0 <= days_since_inception <= RECENT_INCEPTION_THRESHOLD_DAYS


def x__is_recent_inception__mutmut_3(candidate: Candidate) -> bool:
    inception = candidate.policy_inception_date
    if inception is None:
        return True
    days_since_inception = (candidate.loss_date - inception).days
    return 0 <= days_since_inception <= RECENT_INCEPTION_THRESHOLD_DAYS


def x__is_recent_inception__mutmut_4(candidate: Candidate) -> bool:
    inception = candidate.policy_inception_date
    if inception is None:
        return False
    days_since_inception = None
    return 0 <= days_since_inception <= RECENT_INCEPTION_THRESHOLD_DAYS


def x__is_recent_inception__mutmut_5(candidate: Candidate) -> bool:
    inception = candidate.policy_inception_date
    if inception is None:
        return False
    days_since_inception = (candidate.loss_date + inception).days
    return 0 <= days_since_inception <= RECENT_INCEPTION_THRESHOLD_DAYS


def x__is_recent_inception__mutmut_6(candidate: Candidate) -> bool:
    inception = candidate.policy_inception_date
    if inception is None:
        return False
    days_since_inception = (candidate.loss_date - inception).days
    return 1 <= days_since_inception <= RECENT_INCEPTION_THRESHOLD_DAYS


def x__is_recent_inception__mutmut_7(candidate: Candidate) -> bool:
    inception = candidate.policy_inception_date
    if inception is None:
        return False
    days_since_inception = (candidate.loss_date - inception).days
    return 0 < days_since_inception <= RECENT_INCEPTION_THRESHOLD_DAYS


def x__is_recent_inception__mutmut_8(candidate: Candidate) -> bool:
    inception = candidate.policy_inception_date
    if inception is None:
        return False
    days_since_inception = (candidate.loss_date - inception).days
    return 0 <= days_since_inception < RECENT_INCEPTION_THRESHOLD_DAYS

mutants_x__is_recent_inception__mutmut['_mutmut_orig'] = x__is_recent_inception__mutmut_orig # type: ignore # mutmut generated
mutants_x__is_recent_inception__mutmut['x__is_recent_inception__mutmut_1'] = x__is_recent_inception__mutmut_1 # type: ignore # mutmut generated
mutants_x__is_recent_inception__mutmut['x__is_recent_inception__mutmut_2'] = x__is_recent_inception__mutmut_2 # type: ignore # mutmut generated
mutants_x__is_recent_inception__mutmut['x__is_recent_inception__mutmut_3'] = x__is_recent_inception__mutmut_3 # type: ignore # mutmut generated
mutants_x__is_recent_inception__mutmut['x__is_recent_inception__mutmut_4'] = x__is_recent_inception__mutmut_4 # type: ignore # mutmut generated
mutants_x__is_recent_inception__mutmut['x__is_recent_inception__mutmut_5'] = x__is_recent_inception__mutmut_5 # type: ignore # mutmut generated
mutants_x__is_recent_inception__mutmut['x__is_recent_inception__mutmut_6'] = x__is_recent_inception__mutmut_6 # type: ignore # mutmut generated
mutants_x__is_recent_inception__mutmut['x__is_recent_inception__mutmut_7'] = x__is_recent_inception__mutmut_7 # type: ignore # mutmut generated
mutants_x__is_recent_inception__mutmut['x__is_recent_inception__mutmut_8'] = x__is_recent_inception__mutmut_8 # type: ignore # mutmut generated
