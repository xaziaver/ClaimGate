"""Pure severity assignment and queue routing for a candidate FNOL record."""

from datetime import date
from decimal import Decimal

from claimgate.domain.models import Candidate, SiuFlags, TriageOutcome
from claimgate.domain.siu import compute_siu_flags

THEFT_LOW_SEVERITY_THRESHOLD = Decimal("500.00")
SIU_QUEUE = "siu_review"

_HIGH_SEVERITY_LOSS_TYPES = frozenset({"injury", "fire"})
_SEVERITY_QUEUES = {"low": "fast_track", "standard": "standard", "high": "complex"}


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x_assign_severity__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_assign_severity__mutmut)
def assign_severity(loss_type: str, loss_amount: Decimal | None) -> str:
    if loss_type in _HIGH_SEVERITY_LOSS_TYPES:
        return "high"
    if _is_low_severity_theft(loss_type, loss_amount):
        return "low"
    return "standard"


def x_assign_severity__mutmut_orig(loss_type: str, loss_amount: Decimal | None) -> str:
    if loss_type in _HIGH_SEVERITY_LOSS_TYPES:
        return "high"
    if _is_low_severity_theft(loss_type, loss_amount):
        return "low"
    return "standard"


def x_assign_severity__mutmut_1(loss_type: str, loss_amount: Decimal | None) -> str:
    if loss_type not in _HIGH_SEVERITY_LOSS_TYPES:
        return "high"
    if _is_low_severity_theft(loss_type, loss_amount):
        return "low"
    return "standard"


def x_assign_severity__mutmut_2(loss_type: str, loss_amount: Decimal | None) -> str:
    if loss_type in _HIGH_SEVERITY_LOSS_TYPES:
        return "XXhighXX"
    if _is_low_severity_theft(loss_type, loss_amount):
        return "low"
    return "standard"


def x_assign_severity__mutmut_3(loss_type: str, loss_amount: Decimal | None) -> str:
    if loss_type in _HIGH_SEVERITY_LOSS_TYPES:
        return "HIGH"
    if _is_low_severity_theft(loss_type, loss_amount):
        return "low"
    return "standard"


def x_assign_severity__mutmut_4(loss_type: str, loss_amount: Decimal | None) -> str:
    if loss_type in _HIGH_SEVERITY_LOSS_TYPES:
        return "high"
    if _is_low_severity_theft(None, loss_amount):
        return "low"
    return "standard"


def x_assign_severity__mutmut_5(loss_type: str, loss_amount: Decimal | None) -> str:
    if loss_type in _HIGH_SEVERITY_LOSS_TYPES:
        return "high"
    if _is_low_severity_theft(loss_type, None):
        return "low"
    return "standard"


def x_assign_severity__mutmut_6(loss_type: str, loss_amount: Decimal | None) -> str:
    if loss_type in _HIGH_SEVERITY_LOSS_TYPES:
        return "high"
    if _is_low_severity_theft(loss_amount):
        return "low"
    return "standard"


def x_assign_severity__mutmut_7(loss_type: str, loss_amount: Decimal | None) -> str:
    if loss_type in _HIGH_SEVERITY_LOSS_TYPES:
        return "high"
    if _is_low_severity_theft(loss_type, ):
        return "low"
    return "standard"


def x_assign_severity__mutmut_8(loss_type: str, loss_amount: Decimal | None) -> str:
    if loss_type in _HIGH_SEVERITY_LOSS_TYPES:
        return "high"
    if _is_low_severity_theft(loss_type, loss_amount):
        return "XXlowXX"
    return "standard"


def x_assign_severity__mutmut_9(loss_type: str, loss_amount: Decimal | None) -> str:
    if loss_type in _HIGH_SEVERITY_LOSS_TYPES:
        return "high"
    if _is_low_severity_theft(loss_type, loss_amount):
        return "LOW"
    return "standard"


def x_assign_severity__mutmut_10(loss_type: str, loss_amount: Decimal | None) -> str:
    if loss_type in _HIGH_SEVERITY_LOSS_TYPES:
        return "high"
    if _is_low_severity_theft(loss_type, loss_amount):
        return "low"
    return "XXstandardXX"


def x_assign_severity__mutmut_11(loss_type: str, loss_amount: Decimal | None) -> str:
    if loss_type in _HIGH_SEVERITY_LOSS_TYPES:
        return "high"
    if _is_low_severity_theft(loss_type, loss_amount):
        return "low"
    return "STANDARD"

mutants_x_assign_severity__mutmut['_mutmut_orig'] = x_assign_severity__mutmut_orig # type: ignore # mutmut generated
mutants_x_assign_severity__mutmut['x_assign_severity__mutmut_1'] = x_assign_severity__mutmut_1 # type: ignore # mutmut generated
mutants_x_assign_severity__mutmut['x_assign_severity__mutmut_2'] = x_assign_severity__mutmut_2 # type: ignore # mutmut generated
mutants_x_assign_severity__mutmut['x_assign_severity__mutmut_3'] = x_assign_severity__mutmut_3 # type: ignore # mutmut generated
mutants_x_assign_severity__mutmut['x_assign_severity__mutmut_4'] = x_assign_severity__mutmut_4 # type: ignore # mutmut generated
mutants_x_assign_severity__mutmut['x_assign_severity__mutmut_5'] = x_assign_severity__mutmut_5 # type: ignore # mutmut generated
mutants_x_assign_severity__mutmut['x_assign_severity__mutmut_6'] = x_assign_severity__mutmut_6 # type: ignore # mutmut generated
mutants_x_assign_severity__mutmut['x_assign_severity__mutmut_7'] = x_assign_severity__mutmut_7 # type: ignore # mutmut generated
mutants_x_assign_severity__mutmut['x_assign_severity__mutmut_8'] = x_assign_severity__mutmut_8 # type: ignore # mutmut generated
mutants_x_assign_severity__mutmut['x_assign_severity__mutmut_9'] = x_assign_severity__mutmut_9 # type: ignore # mutmut generated
mutants_x_assign_severity__mutmut['x_assign_severity__mutmut_10'] = x_assign_severity__mutmut_10 # type: ignore # mutmut generated
mutants_x_assign_severity__mutmut['x_assign_severity__mutmut_11'] = x_assign_severity__mutmut_11 # type: ignore # mutmut generated
mutants_x__is_low_severity_theft__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__is_low_severity_theft__mutmut)
def _is_low_severity_theft(loss_type: str, loss_amount: Decimal | None) -> bool:
    if loss_type != "theft" or loss_amount is None:
        return False
    return loss_amount < THEFT_LOW_SEVERITY_THRESHOLD


def x__is_low_severity_theft__mutmut_orig(loss_type: str, loss_amount: Decimal | None) -> bool:
    if loss_type != "theft" or loss_amount is None:
        return False
    return loss_amount < THEFT_LOW_SEVERITY_THRESHOLD


def x__is_low_severity_theft__mutmut_1(loss_type: str, loss_amount: Decimal | None) -> bool:
    if loss_type != "theft" and loss_amount is None:
        return False
    return loss_amount < THEFT_LOW_SEVERITY_THRESHOLD


def x__is_low_severity_theft__mutmut_2(loss_type: str, loss_amount: Decimal | None) -> bool:
    if loss_type == "theft" or loss_amount is None:
        return False
    return loss_amount < THEFT_LOW_SEVERITY_THRESHOLD


def x__is_low_severity_theft__mutmut_3(loss_type: str, loss_amount: Decimal | None) -> bool:
    if loss_type != "XXtheftXX" or loss_amount is None:
        return False
    return loss_amount < THEFT_LOW_SEVERITY_THRESHOLD


def x__is_low_severity_theft__mutmut_4(loss_type: str, loss_amount: Decimal | None) -> bool:
    if loss_type != "THEFT" or loss_amount is None:
        return False
    return loss_amount < THEFT_LOW_SEVERITY_THRESHOLD


def x__is_low_severity_theft__mutmut_5(loss_type: str, loss_amount: Decimal | None) -> bool:
    if loss_type != "theft" or loss_amount is not None:
        return False
    return loss_amount < THEFT_LOW_SEVERITY_THRESHOLD


def x__is_low_severity_theft__mutmut_6(loss_type: str, loss_amount: Decimal | None) -> bool:
    if loss_type != "theft" or loss_amount is None:
        return True
    return loss_amount < THEFT_LOW_SEVERITY_THRESHOLD


def x__is_low_severity_theft__mutmut_7(loss_type: str, loss_amount: Decimal | None) -> bool:
    if loss_type != "theft" or loss_amount is None:
        return False
    return loss_amount <= THEFT_LOW_SEVERITY_THRESHOLD

mutants_x__is_low_severity_theft__mutmut['_mutmut_orig'] = x__is_low_severity_theft__mutmut_orig # type: ignore # mutmut generated
mutants_x__is_low_severity_theft__mutmut['x__is_low_severity_theft__mutmut_1'] = x__is_low_severity_theft__mutmut_1 # type: ignore # mutmut generated
mutants_x__is_low_severity_theft__mutmut['x__is_low_severity_theft__mutmut_2'] = x__is_low_severity_theft__mutmut_2 # type: ignore # mutmut generated
mutants_x__is_low_severity_theft__mutmut['x__is_low_severity_theft__mutmut_3'] = x__is_low_severity_theft__mutmut_3 # type: ignore # mutmut generated
mutants_x__is_low_severity_theft__mutmut['x__is_low_severity_theft__mutmut_4'] = x__is_low_severity_theft__mutmut_4 # type: ignore # mutmut generated
mutants_x__is_low_severity_theft__mutmut['x__is_low_severity_theft__mutmut_5'] = x__is_low_severity_theft__mutmut_5 # type: ignore # mutmut generated
mutants_x__is_low_severity_theft__mutmut['x__is_low_severity_theft__mutmut_6'] = x__is_low_severity_theft__mutmut_6 # type: ignore # mutmut generated
mutants_x__is_low_severity_theft__mutmut['x__is_low_severity_theft__mutmut_7'] = x__is_low_severity_theft__mutmut_7 # type: ignore # mutmut generated
mutants_x_route_queue__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_route_queue__mutmut)
def route_queue(severity: str, siu_flags: SiuFlags) -> str:
    if siu_flags.late_reporting or siu_flags.recent_policy_inception:
        return SIU_QUEUE
    return _SEVERITY_QUEUES[severity]


def x_route_queue__mutmut_orig(severity: str, siu_flags: SiuFlags) -> str:
    if siu_flags.late_reporting or siu_flags.recent_policy_inception:
        return SIU_QUEUE
    return _SEVERITY_QUEUES[severity]


def x_route_queue__mutmut_1(severity: str, siu_flags: SiuFlags) -> str:
    if siu_flags.late_reporting and siu_flags.recent_policy_inception:
        return SIU_QUEUE
    return _SEVERITY_QUEUES[severity]

mutants_x_route_queue__mutmut['_mutmut_orig'] = x_route_queue__mutmut_orig # type: ignore # mutmut generated
mutants_x_route_queue__mutmut['x_route_queue__mutmut_1'] = x_route_queue__mutmut_1 # type: ignore # mutmut generated
mutants_x_triage_and_route__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_triage_and_route__mutmut)
def triage_and_route(candidate: Candidate, now: date) -> TriageOutcome:
    severity = assign_severity(candidate.loss_type, candidate.loss_amount)
    siu_flags = compute_siu_flags(candidate, now)
    queue = route_queue(severity, siu_flags)
    return TriageOutcome(severity=severity, queue=queue)


def x_triage_and_route__mutmut_orig(candidate: Candidate, now: date) -> TriageOutcome:
    severity = assign_severity(candidate.loss_type, candidate.loss_amount)
    siu_flags = compute_siu_flags(candidate, now)
    queue = route_queue(severity, siu_flags)
    return TriageOutcome(severity=severity, queue=queue)


def x_triage_and_route__mutmut_1(candidate: Candidate, now: date) -> TriageOutcome:
    severity = None
    siu_flags = compute_siu_flags(candidate, now)
    queue = route_queue(severity, siu_flags)
    return TriageOutcome(severity=severity, queue=queue)


def x_triage_and_route__mutmut_2(candidate: Candidate, now: date) -> TriageOutcome:
    severity = assign_severity(None, candidate.loss_amount)
    siu_flags = compute_siu_flags(candidate, now)
    queue = route_queue(severity, siu_flags)
    return TriageOutcome(severity=severity, queue=queue)


def x_triage_and_route__mutmut_3(candidate: Candidate, now: date) -> TriageOutcome:
    severity = assign_severity(candidate.loss_type, None)
    siu_flags = compute_siu_flags(candidate, now)
    queue = route_queue(severity, siu_flags)
    return TriageOutcome(severity=severity, queue=queue)


def x_triage_and_route__mutmut_4(candidate: Candidate, now: date) -> TriageOutcome:
    severity = assign_severity(candidate.loss_amount)
    siu_flags = compute_siu_flags(candidate, now)
    queue = route_queue(severity, siu_flags)
    return TriageOutcome(severity=severity, queue=queue)


def x_triage_and_route__mutmut_5(candidate: Candidate, now: date) -> TriageOutcome:
    severity = assign_severity(candidate.loss_type, )
    siu_flags = compute_siu_flags(candidate, now)
    queue = route_queue(severity, siu_flags)
    return TriageOutcome(severity=severity, queue=queue)


def x_triage_and_route__mutmut_6(candidate: Candidate, now: date) -> TriageOutcome:
    severity = assign_severity(candidate.loss_type, candidate.loss_amount)
    siu_flags = None
    queue = route_queue(severity, siu_flags)
    return TriageOutcome(severity=severity, queue=queue)


def x_triage_and_route__mutmut_7(candidate: Candidate, now: date) -> TriageOutcome:
    severity = assign_severity(candidate.loss_type, candidate.loss_amount)
    siu_flags = compute_siu_flags(None, now)
    queue = route_queue(severity, siu_flags)
    return TriageOutcome(severity=severity, queue=queue)


def x_triage_and_route__mutmut_8(candidate: Candidate, now: date) -> TriageOutcome:
    severity = assign_severity(candidate.loss_type, candidate.loss_amount)
    siu_flags = compute_siu_flags(candidate, None)
    queue = route_queue(severity, siu_flags)
    return TriageOutcome(severity=severity, queue=queue)


def x_triage_and_route__mutmut_9(candidate: Candidate, now: date) -> TriageOutcome:
    severity = assign_severity(candidate.loss_type, candidate.loss_amount)
    siu_flags = compute_siu_flags(now)
    queue = route_queue(severity, siu_flags)
    return TriageOutcome(severity=severity, queue=queue)


def x_triage_and_route__mutmut_10(candidate: Candidate, now: date) -> TriageOutcome:
    severity = assign_severity(candidate.loss_type, candidate.loss_amount)
    siu_flags = compute_siu_flags(candidate, )
    queue = route_queue(severity, siu_flags)
    return TriageOutcome(severity=severity, queue=queue)


def x_triage_and_route__mutmut_11(candidate: Candidate, now: date) -> TriageOutcome:
    severity = assign_severity(candidate.loss_type, candidate.loss_amount)
    siu_flags = compute_siu_flags(candidate, now)
    queue = None
    return TriageOutcome(severity=severity, queue=queue)


def x_triage_and_route__mutmut_12(candidate: Candidate, now: date) -> TriageOutcome:
    severity = assign_severity(candidate.loss_type, candidate.loss_amount)
    siu_flags = compute_siu_flags(candidate, now)
    queue = route_queue(None, siu_flags)
    return TriageOutcome(severity=severity, queue=queue)


def x_triage_and_route__mutmut_13(candidate: Candidate, now: date) -> TriageOutcome:
    severity = assign_severity(candidate.loss_type, candidate.loss_amount)
    siu_flags = compute_siu_flags(candidate, now)
    queue = route_queue(severity, None)
    return TriageOutcome(severity=severity, queue=queue)


def x_triage_and_route__mutmut_14(candidate: Candidate, now: date) -> TriageOutcome:
    severity = assign_severity(candidate.loss_type, candidate.loss_amount)
    siu_flags = compute_siu_flags(candidate, now)
    queue = route_queue(siu_flags)
    return TriageOutcome(severity=severity, queue=queue)


def x_triage_and_route__mutmut_15(candidate: Candidate, now: date) -> TriageOutcome:
    severity = assign_severity(candidate.loss_type, candidate.loss_amount)
    siu_flags = compute_siu_flags(candidate, now)
    queue = route_queue(severity, )
    return TriageOutcome(severity=severity, queue=queue)


def x_triage_and_route__mutmut_16(candidate: Candidate, now: date) -> TriageOutcome:
    severity = assign_severity(candidate.loss_type, candidate.loss_amount)
    siu_flags = compute_siu_flags(candidate, now)
    queue = route_queue(severity, siu_flags)
    return TriageOutcome(severity=None, queue=queue)


def x_triage_and_route__mutmut_17(candidate: Candidate, now: date) -> TriageOutcome:
    severity = assign_severity(candidate.loss_type, candidate.loss_amount)
    siu_flags = compute_siu_flags(candidate, now)
    queue = route_queue(severity, siu_flags)
    return TriageOutcome(severity=severity, queue=None)


def x_triage_and_route__mutmut_18(candidate: Candidate, now: date) -> TriageOutcome:
    severity = assign_severity(candidate.loss_type, candidate.loss_amount)
    siu_flags = compute_siu_flags(candidate, now)
    queue = route_queue(severity, siu_flags)
    return TriageOutcome(queue=queue)


def x_triage_and_route__mutmut_19(candidate: Candidate, now: date) -> TriageOutcome:
    severity = assign_severity(candidate.loss_type, candidate.loss_amount)
    siu_flags = compute_siu_flags(candidate, now)
    queue = route_queue(severity, siu_flags)
    return TriageOutcome(severity=severity, )

mutants_x_triage_and_route__mutmut['_mutmut_orig'] = x_triage_and_route__mutmut_orig # type: ignore # mutmut generated
mutants_x_triage_and_route__mutmut['x_triage_and_route__mutmut_1'] = x_triage_and_route__mutmut_1 # type: ignore # mutmut generated
mutants_x_triage_and_route__mutmut['x_triage_and_route__mutmut_2'] = x_triage_and_route__mutmut_2 # type: ignore # mutmut generated
mutants_x_triage_and_route__mutmut['x_triage_and_route__mutmut_3'] = x_triage_and_route__mutmut_3 # type: ignore # mutmut generated
mutants_x_triage_and_route__mutmut['x_triage_and_route__mutmut_4'] = x_triage_and_route__mutmut_4 # type: ignore # mutmut generated
mutants_x_triage_and_route__mutmut['x_triage_and_route__mutmut_5'] = x_triage_and_route__mutmut_5 # type: ignore # mutmut generated
mutants_x_triage_and_route__mutmut['x_triage_and_route__mutmut_6'] = x_triage_and_route__mutmut_6 # type: ignore # mutmut generated
mutants_x_triage_and_route__mutmut['x_triage_and_route__mutmut_7'] = x_triage_and_route__mutmut_7 # type: ignore # mutmut generated
mutants_x_triage_and_route__mutmut['x_triage_and_route__mutmut_8'] = x_triage_and_route__mutmut_8 # type: ignore # mutmut generated
mutants_x_triage_and_route__mutmut['x_triage_and_route__mutmut_9'] = x_triage_and_route__mutmut_9 # type: ignore # mutmut generated
mutants_x_triage_and_route__mutmut['x_triage_and_route__mutmut_10'] = x_triage_and_route__mutmut_10 # type: ignore # mutmut generated
mutants_x_triage_and_route__mutmut['x_triage_and_route__mutmut_11'] = x_triage_and_route__mutmut_11 # type: ignore # mutmut generated
mutants_x_triage_and_route__mutmut['x_triage_and_route__mutmut_12'] = x_triage_and_route__mutmut_12 # type: ignore # mutmut generated
mutants_x_triage_and_route__mutmut['x_triage_and_route__mutmut_13'] = x_triage_and_route__mutmut_13 # type: ignore # mutmut generated
mutants_x_triage_and_route__mutmut['x_triage_and_route__mutmut_14'] = x_triage_and_route__mutmut_14 # type: ignore # mutmut generated
mutants_x_triage_and_route__mutmut['x_triage_and_route__mutmut_15'] = x_triage_and_route__mutmut_15 # type: ignore # mutmut generated
mutants_x_triage_and_route__mutmut['x_triage_and_route__mutmut_16'] = x_triage_and_route__mutmut_16 # type: ignore # mutmut generated
mutants_x_triage_and_route__mutmut['x_triage_and_route__mutmut_17'] = x_triage_and_route__mutmut_17 # type: ignore # mutmut generated
mutants_x_triage_and_route__mutmut['x_triage_and_route__mutmut_18'] = x_triage_and_route__mutmut_18 # type: ignore # mutmut generated
mutants_x_triage_and_route__mutmut['x_triage_and_route__mutmut_19'] = x_triage_and_route__mutmut_19 # type: ignore # mutmut generated
