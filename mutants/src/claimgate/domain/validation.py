"""Pure validation rules for a candidate FNOL record."""

import re
from datetime import date

from claimgate.domain.models import Candidate, ValidationResult

REPORTING_WINDOW_DAYS = 365
POLICY_NUMBER_PATTERN = re.compile(r"^(?:HO|AU|CP|CA|GL)-\d{7}$")


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x_validate__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_validate__mutmut)
def validate(candidate: Candidate, now: date) -> ValidationResult:
    if not _loss_date_in_window(candidate.loss_date, now):
        return ValidationResult(valid=False)
    if not POLICY_NUMBER_PATTERN.match(candidate.policy_number):
        return ValidationResult(valid=False)
    if candidate.loss_type == "injury":
        missing_field = _first_missing_injury_field(candidate)
        if missing_field is not None:
            return ValidationResult(valid=False, missing_field=missing_field)
    return ValidationResult(valid=True)


def x_validate__mutmut_orig(candidate: Candidate, now: date) -> ValidationResult:
    if not _loss_date_in_window(candidate.loss_date, now):
        return ValidationResult(valid=False)
    if not POLICY_NUMBER_PATTERN.match(candidate.policy_number):
        return ValidationResult(valid=False)
    if candidate.loss_type == "injury":
        missing_field = _first_missing_injury_field(candidate)
        if missing_field is not None:
            return ValidationResult(valid=False, missing_field=missing_field)
    return ValidationResult(valid=True)


def x_validate__mutmut_1(candidate: Candidate, now: date) -> ValidationResult:
    if _loss_date_in_window(candidate.loss_date, now):
        return ValidationResult(valid=False)
    if not POLICY_NUMBER_PATTERN.match(candidate.policy_number):
        return ValidationResult(valid=False)
    if candidate.loss_type == "injury":
        missing_field = _first_missing_injury_field(candidate)
        if missing_field is not None:
            return ValidationResult(valid=False, missing_field=missing_field)
    return ValidationResult(valid=True)


def x_validate__mutmut_2(candidate: Candidate, now: date) -> ValidationResult:
    if not _loss_date_in_window(None, now):
        return ValidationResult(valid=False)
    if not POLICY_NUMBER_PATTERN.match(candidate.policy_number):
        return ValidationResult(valid=False)
    if candidate.loss_type == "injury":
        missing_field = _first_missing_injury_field(candidate)
        if missing_field is not None:
            return ValidationResult(valid=False, missing_field=missing_field)
    return ValidationResult(valid=True)


def x_validate__mutmut_3(candidate: Candidate, now: date) -> ValidationResult:
    if not _loss_date_in_window(candidate.loss_date, None):
        return ValidationResult(valid=False)
    if not POLICY_NUMBER_PATTERN.match(candidate.policy_number):
        return ValidationResult(valid=False)
    if candidate.loss_type == "injury":
        missing_field = _first_missing_injury_field(candidate)
        if missing_field is not None:
            return ValidationResult(valid=False, missing_field=missing_field)
    return ValidationResult(valid=True)


def x_validate__mutmut_4(candidate: Candidate, now: date) -> ValidationResult:
    if not _loss_date_in_window(now):
        return ValidationResult(valid=False)
    if not POLICY_NUMBER_PATTERN.match(candidate.policy_number):
        return ValidationResult(valid=False)
    if candidate.loss_type == "injury":
        missing_field = _first_missing_injury_field(candidate)
        if missing_field is not None:
            return ValidationResult(valid=False, missing_field=missing_field)
    return ValidationResult(valid=True)


def x_validate__mutmut_5(candidate: Candidate, now: date) -> ValidationResult:
    if not _loss_date_in_window(candidate.loss_date, ):
        return ValidationResult(valid=False)
    if not POLICY_NUMBER_PATTERN.match(candidate.policy_number):
        return ValidationResult(valid=False)
    if candidate.loss_type == "injury":
        missing_field = _first_missing_injury_field(candidate)
        if missing_field is not None:
            return ValidationResult(valid=False, missing_field=missing_field)
    return ValidationResult(valid=True)


def x_validate__mutmut_6(candidate: Candidate, now: date) -> ValidationResult:
    if not _loss_date_in_window(candidate.loss_date, now):
        return ValidationResult(valid=None)
    if not POLICY_NUMBER_PATTERN.match(candidate.policy_number):
        return ValidationResult(valid=False)
    if candidate.loss_type == "injury":
        missing_field = _first_missing_injury_field(candidate)
        if missing_field is not None:
            return ValidationResult(valid=False, missing_field=missing_field)
    return ValidationResult(valid=True)


def x_validate__mutmut_7(candidate: Candidate, now: date) -> ValidationResult:
    if not _loss_date_in_window(candidate.loss_date, now):
        return ValidationResult(valid=True)
    if not POLICY_NUMBER_PATTERN.match(candidate.policy_number):
        return ValidationResult(valid=False)
    if candidate.loss_type == "injury":
        missing_field = _first_missing_injury_field(candidate)
        if missing_field is not None:
            return ValidationResult(valid=False, missing_field=missing_field)
    return ValidationResult(valid=True)


def x_validate__mutmut_8(candidate: Candidate, now: date) -> ValidationResult:
    if not _loss_date_in_window(candidate.loss_date, now):
        return ValidationResult(valid=False)
    if POLICY_NUMBER_PATTERN.match(candidate.policy_number):
        return ValidationResult(valid=False)
    if candidate.loss_type == "injury":
        missing_field = _first_missing_injury_field(candidate)
        if missing_field is not None:
            return ValidationResult(valid=False, missing_field=missing_field)
    return ValidationResult(valid=True)


def x_validate__mutmut_9(candidate: Candidate, now: date) -> ValidationResult:
    if not _loss_date_in_window(candidate.loss_date, now):
        return ValidationResult(valid=False)
    if not POLICY_NUMBER_PATTERN.match(None):
        return ValidationResult(valid=False)
    if candidate.loss_type == "injury":
        missing_field = _first_missing_injury_field(candidate)
        if missing_field is not None:
            return ValidationResult(valid=False, missing_field=missing_field)
    return ValidationResult(valid=True)


def x_validate__mutmut_10(candidate: Candidate, now: date) -> ValidationResult:
    if not _loss_date_in_window(candidate.loss_date, now):
        return ValidationResult(valid=False)
    if not POLICY_NUMBER_PATTERN.match(candidate.policy_number):
        return ValidationResult(valid=None)
    if candidate.loss_type == "injury":
        missing_field = _first_missing_injury_field(candidate)
        if missing_field is not None:
            return ValidationResult(valid=False, missing_field=missing_field)
    return ValidationResult(valid=True)


def x_validate__mutmut_11(candidate: Candidate, now: date) -> ValidationResult:
    if not _loss_date_in_window(candidate.loss_date, now):
        return ValidationResult(valid=False)
    if not POLICY_NUMBER_PATTERN.match(candidate.policy_number):
        return ValidationResult(valid=True)
    if candidate.loss_type == "injury":
        missing_field = _first_missing_injury_field(candidate)
        if missing_field is not None:
            return ValidationResult(valid=False, missing_field=missing_field)
    return ValidationResult(valid=True)


def x_validate__mutmut_12(candidate: Candidate, now: date) -> ValidationResult:
    if not _loss_date_in_window(candidate.loss_date, now):
        return ValidationResult(valid=False)
    if not POLICY_NUMBER_PATTERN.match(candidate.policy_number):
        return ValidationResult(valid=False)
    if candidate.loss_type != "injury":
        missing_field = _first_missing_injury_field(candidate)
        if missing_field is not None:
            return ValidationResult(valid=False, missing_field=missing_field)
    return ValidationResult(valid=True)


def x_validate__mutmut_13(candidate: Candidate, now: date) -> ValidationResult:
    if not _loss_date_in_window(candidate.loss_date, now):
        return ValidationResult(valid=False)
    if not POLICY_NUMBER_PATTERN.match(candidate.policy_number):
        return ValidationResult(valid=False)
    if candidate.loss_type == "XXinjuryXX":
        missing_field = _first_missing_injury_field(candidate)
        if missing_field is not None:
            return ValidationResult(valid=False, missing_field=missing_field)
    return ValidationResult(valid=True)


def x_validate__mutmut_14(candidate: Candidate, now: date) -> ValidationResult:
    if not _loss_date_in_window(candidate.loss_date, now):
        return ValidationResult(valid=False)
    if not POLICY_NUMBER_PATTERN.match(candidate.policy_number):
        return ValidationResult(valid=False)
    if candidate.loss_type == "INJURY":
        missing_field = _first_missing_injury_field(candidate)
        if missing_field is not None:
            return ValidationResult(valid=False, missing_field=missing_field)
    return ValidationResult(valid=True)


def x_validate__mutmut_15(candidate: Candidate, now: date) -> ValidationResult:
    if not _loss_date_in_window(candidate.loss_date, now):
        return ValidationResult(valid=False)
    if not POLICY_NUMBER_PATTERN.match(candidate.policy_number):
        return ValidationResult(valid=False)
    if candidate.loss_type == "injury":
        missing_field = None
        if missing_field is not None:
            return ValidationResult(valid=False, missing_field=missing_field)
    return ValidationResult(valid=True)


def x_validate__mutmut_16(candidate: Candidate, now: date) -> ValidationResult:
    if not _loss_date_in_window(candidate.loss_date, now):
        return ValidationResult(valid=False)
    if not POLICY_NUMBER_PATTERN.match(candidate.policy_number):
        return ValidationResult(valid=False)
    if candidate.loss_type == "injury":
        missing_field = _first_missing_injury_field(None)
        if missing_field is not None:
            return ValidationResult(valid=False, missing_field=missing_field)
    return ValidationResult(valid=True)


def x_validate__mutmut_17(candidate: Candidate, now: date) -> ValidationResult:
    if not _loss_date_in_window(candidate.loss_date, now):
        return ValidationResult(valid=False)
    if not POLICY_NUMBER_PATTERN.match(candidate.policy_number):
        return ValidationResult(valid=False)
    if candidate.loss_type == "injury":
        missing_field = _first_missing_injury_field(candidate)
        if missing_field is None:
            return ValidationResult(valid=False, missing_field=missing_field)
    return ValidationResult(valid=True)


def x_validate__mutmut_18(candidate: Candidate, now: date) -> ValidationResult:
    if not _loss_date_in_window(candidate.loss_date, now):
        return ValidationResult(valid=False)
    if not POLICY_NUMBER_PATTERN.match(candidate.policy_number):
        return ValidationResult(valid=False)
    if candidate.loss_type == "injury":
        missing_field = _first_missing_injury_field(candidate)
        if missing_field is not None:
            return ValidationResult(valid=None, missing_field=missing_field)
    return ValidationResult(valid=True)


def x_validate__mutmut_19(candidate: Candidate, now: date) -> ValidationResult:
    if not _loss_date_in_window(candidate.loss_date, now):
        return ValidationResult(valid=False)
    if not POLICY_NUMBER_PATTERN.match(candidate.policy_number):
        return ValidationResult(valid=False)
    if candidate.loss_type == "injury":
        missing_field = _first_missing_injury_field(candidate)
        if missing_field is not None:
            return ValidationResult(valid=False, missing_field=None)
    return ValidationResult(valid=True)


def x_validate__mutmut_20(candidate: Candidate, now: date) -> ValidationResult:
    if not _loss_date_in_window(candidate.loss_date, now):
        return ValidationResult(valid=False)
    if not POLICY_NUMBER_PATTERN.match(candidate.policy_number):
        return ValidationResult(valid=False)
    if candidate.loss_type == "injury":
        missing_field = _first_missing_injury_field(candidate)
        if missing_field is not None:
            return ValidationResult(missing_field=missing_field)
    return ValidationResult(valid=True)


def x_validate__mutmut_21(candidate: Candidate, now: date) -> ValidationResult:
    if not _loss_date_in_window(candidate.loss_date, now):
        return ValidationResult(valid=False)
    if not POLICY_NUMBER_PATTERN.match(candidate.policy_number):
        return ValidationResult(valid=False)
    if candidate.loss_type == "injury":
        missing_field = _first_missing_injury_field(candidate)
        if missing_field is not None:
            return ValidationResult(valid=False, )
    return ValidationResult(valid=True)


def x_validate__mutmut_22(candidate: Candidate, now: date) -> ValidationResult:
    if not _loss_date_in_window(candidate.loss_date, now):
        return ValidationResult(valid=False)
    if not POLICY_NUMBER_PATTERN.match(candidate.policy_number):
        return ValidationResult(valid=False)
    if candidate.loss_type == "injury":
        missing_field = _first_missing_injury_field(candidate)
        if missing_field is not None:
            return ValidationResult(valid=True, missing_field=missing_field)
    return ValidationResult(valid=True)


def x_validate__mutmut_23(candidate: Candidate, now: date) -> ValidationResult:
    if not _loss_date_in_window(candidate.loss_date, now):
        return ValidationResult(valid=False)
    if not POLICY_NUMBER_PATTERN.match(candidate.policy_number):
        return ValidationResult(valid=False)
    if candidate.loss_type == "injury":
        missing_field = _first_missing_injury_field(candidate)
        if missing_field is not None:
            return ValidationResult(valid=False, missing_field=missing_field)
    return ValidationResult(valid=None)


def x_validate__mutmut_24(candidate: Candidate, now: date) -> ValidationResult:
    if not _loss_date_in_window(candidate.loss_date, now):
        return ValidationResult(valid=False)
    if not POLICY_NUMBER_PATTERN.match(candidate.policy_number):
        return ValidationResult(valid=False)
    if candidate.loss_type == "injury":
        missing_field = _first_missing_injury_field(candidate)
        if missing_field is not None:
            return ValidationResult(valid=False, missing_field=missing_field)
    return ValidationResult(valid=False)

mutants_x_validate__mutmut['_mutmut_orig'] = x_validate__mutmut_orig # type: ignore # mutmut generated
mutants_x_validate__mutmut['x_validate__mutmut_1'] = x_validate__mutmut_1 # type: ignore # mutmut generated
mutants_x_validate__mutmut['x_validate__mutmut_2'] = x_validate__mutmut_2 # type: ignore # mutmut generated
mutants_x_validate__mutmut['x_validate__mutmut_3'] = x_validate__mutmut_3 # type: ignore # mutmut generated
mutants_x_validate__mutmut['x_validate__mutmut_4'] = x_validate__mutmut_4 # type: ignore # mutmut generated
mutants_x_validate__mutmut['x_validate__mutmut_5'] = x_validate__mutmut_5 # type: ignore # mutmut generated
mutants_x_validate__mutmut['x_validate__mutmut_6'] = x_validate__mutmut_6 # type: ignore # mutmut generated
mutants_x_validate__mutmut['x_validate__mutmut_7'] = x_validate__mutmut_7 # type: ignore # mutmut generated
mutants_x_validate__mutmut['x_validate__mutmut_8'] = x_validate__mutmut_8 # type: ignore # mutmut generated
mutants_x_validate__mutmut['x_validate__mutmut_9'] = x_validate__mutmut_9 # type: ignore # mutmut generated
mutants_x_validate__mutmut['x_validate__mutmut_10'] = x_validate__mutmut_10 # type: ignore # mutmut generated
mutants_x_validate__mutmut['x_validate__mutmut_11'] = x_validate__mutmut_11 # type: ignore # mutmut generated
mutants_x_validate__mutmut['x_validate__mutmut_12'] = x_validate__mutmut_12 # type: ignore # mutmut generated
mutants_x_validate__mutmut['x_validate__mutmut_13'] = x_validate__mutmut_13 # type: ignore # mutmut generated
mutants_x_validate__mutmut['x_validate__mutmut_14'] = x_validate__mutmut_14 # type: ignore # mutmut generated
mutants_x_validate__mutmut['x_validate__mutmut_15'] = x_validate__mutmut_15 # type: ignore # mutmut generated
mutants_x_validate__mutmut['x_validate__mutmut_16'] = x_validate__mutmut_16 # type: ignore # mutmut generated
mutants_x_validate__mutmut['x_validate__mutmut_17'] = x_validate__mutmut_17 # type: ignore # mutmut generated
mutants_x_validate__mutmut['x_validate__mutmut_18'] = x_validate__mutmut_18 # type: ignore # mutmut generated
mutants_x_validate__mutmut['x_validate__mutmut_19'] = x_validate__mutmut_19 # type: ignore # mutmut generated
mutants_x_validate__mutmut['x_validate__mutmut_20'] = x_validate__mutmut_20 # type: ignore # mutmut generated
mutants_x_validate__mutmut['x_validate__mutmut_21'] = x_validate__mutmut_21 # type: ignore # mutmut generated
mutants_x_validate__mutmut['x_validate__mutmut_22'] = x_validate__mutmut_22 # type: ignore # mutmut generated
mutants_x_validate__mutmut['x_validate__mutmut_23'] = x_validate__mutmut_23 # type: ignore # mutmut generated
mutants_x_validate__mutmut['x_validate__mutmut_24'] = x_validate__mutmut_24 # type: ignore # mutmut generated
mutants_x__loss_date_in_window__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__loss_date_in_window__mutmut)
def _loss_date_in_window(loss_date: date, now: date) -> bool:
    if loss_date > now:
        return False
    return (now - loss_date).days <= REPORTING_WINDOW_DAYS


def x__loss_date_in_window__mutmut_orig(loss_date: date, now: date) -> bool:
    if loss_date > now:
        return False
    return (now - loss_date).days <= REPORTING_WINDOW_DAYS


def x__loss_date_in_window__mutmut_1(loss_date: date, now: date) -> bool:
    if loss_date >= now:
        return False
    return (now - loss_date).days <= REPORTING_WINDOW_DAYS


def x__loss_date_in_window__mutmut_2(loss_date: date, now: date) -> bool:
    if loss_date > now:
        return True
    return (now - loss_date).days <= REPORTING_WINDOW_DAYS


def x__loss_date_in_window__mutmut_3(loss_date: date, now: date) -> bool:
    if loss_date > now:
        return False
    return (now + loss_date).days <= REPORTING_WINDOW_DAYS


def x__loss_date_in_window__mutmut_4(loss_date: date, now: date) -> bool:
    if loss_date > now:
        return False
    return (now - loss_date).days < REPORTING_WINDOW_DAYS

mutants_x__loss_date_in_window__mutmut['_mutmut_orig'] = x__loss_date_in_window__mutmut_orig # type: ignore # mutmut generated
mutants_x__loss_date_in_window__mutmut['x__loss_date_in_window__mutmut_1'] = x__loss_date_in_window__mutmut_1 # type: ignore # mutmut generated
mutants_x__loss_date_in_window__mutmut['x__loss_date_in_window__mutmut_2'] = x__loss_date_in_window__mutmut_2 # type: ignore # mutmut generated
mutants_x__loss_date_in_window__mutmut['x__loss_date_in_window__mutmut_3'] = x__loss_date_in_window__mutmut_3 # type: ignore # mutmut generated
mutants_x__loss_date_in_window__mutmut['x__loss_date_in_window__mutmut_4'] = x__loss_date_in_window__mutmut_4 # type: ignore # mutmut generated
mutants_x__first_missing_injury_field__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__first_missing_injury_field__mutmut)
def _first_missing_injury_field(candidate: Candidate) -> str | None:
    fields = (
        ("injured_party_name", candidate.injured_party_name),
        ("injured_party_contact", candidate.injured_party_contact),
        ("injury_description", candidate.injury_description),
    )
    for field_name, value in fields:
        if not value:
            return field_name
    return None


def x__first_missing_injury_field__mutmut_orig(candidate: Candidate) -> str | None:
    fields = (
        ("injured_party_name", candidate.injured_party_name),
        ("injured_party_contact", candidate.injured_party_contact),
        ("injury_description", candidate.injury_description),
    )
    for field_name, value in fields:
        if not value:
            return field_name
    return None


def x__first_missing_injury_field__mutmut_1(candidate: Candidate) -> str | None:
    fields = None
    for field_name, value in fields:
        if not value:
            return field_name
    return None


def x__first_missing_injury_field__mutmut_2(candidate: Candidate) -> str | None:
    fields = (
        ("XXinjured_party_nameXX", candidate.injured_party_name),
        ("injured_party_contact", candidate.injured_party_contact),
        ("injury_description", candidate.injury_description),
    )
    for field_name, value in fields:
        if not value:
            return field_name
    return None


def x__first_missing_injury_field__mutmut_3(candidate: Candidate) -> str | None:
    fields = (
        ("INJURED_PARTY_NAME", candidate.injured_party_name),
        ("injured_party_contact", candidate.injured_party_contact),
        ("injury_description", candidate.injury_description),
    )
    for field_name, value in fields:
        if not value:
            return field_name
    return None


def x__first_missing_injury_field__mutmut_4(candidate: Candidate) -> str | None:
    fields = (
        ("injured_party_name", candidate.injured_party_name),
        ("XXinjured_party_contactXX", candidate.injured_party_contact),
        ("injury_description", candidate.injury_description),
    )
    for field_name, value in fields:
        if not value:
            return field_name
    return None


def x__first_missing_injury_field__mutmut_5(candidate: Candidate) -> str | None:
    fields = (
        ("injured_party_name", candidate.injured_party_name),
        ("INJURED_PARTY_CONTACT", candidate.injured_party_contact),
        ("injury_description", candidate.injury_description),
    )
    for field_name, value in fields:
        if not value:
            return field_name
    return None


def x__first_missing_injury_field__mutmut_6(candidate: Candidate) -> str | None:
    fields = (
        ("injured_party_name", candidate.injured_party_name),
        ("injured_party_contact", candidate.injured_party_contact),
        ("XXinjury_descriptionXX", candidate.injury_description),
    )
    for field_name, value in fields:
        if not value:
            return field_name
    return None


def x__first_missing_injury_field__mutmut_7(candidate: Candidate) -> str | None:
    fields = (
        ("injured_party_name", candidate.injured_party_name),
        ("injured_party_contact", candidate.injured_party_contact),
        ("INJURY_DESCRIPTION", candidate.injury_description),
    )
    for field_name, value in fields:
        if not value:
            return field_name
    return None


def x__first_missing_injury_field__mutmut_8(candidate: Candidate) -> str | None:
    fields = (
        ("injured_party_name", candidate.injured_party_name),
        ("injured_party_contact", candidate.injured_party_contact),
        ("injury_description", candidate.injury_description),
    )
    for field_name, value in fields:
        if value:
            return field_name
    return None

mutants_x__first_missing_injury_field__mutmut['_mutmut_orig'] = x__first_missing_injury_field__mutmut_orig # type: ignore # mutmut generated
mutants_x__first_missing_injury_field__mutmut['x__first_missing_injury_field__mutmut_1'] = x__first_missing_injury_field__mutmut_1 # type: ignore # mutmut generated
mutants_x__first_missing_injury_field__mutmut['x__first_missing_injury_field__mutmut_2'] = x__first_missing_injury_field__mutmut_2 # type: ignore # mutmut generated
mutants_x__first_missing_injury_field__mutmut['x__first_missing_injury_field__mutmut_3'] = x__first_missing_injury_field__mutmut_3 # type: ignore # mutmut generated
mutants_x__first_missing_injury_field__mutmut['x__first_missing_injury_field__mutmut_4'] = x__first_missing_injury_field__mutmut_4 # type: ignore # mutmut generated
mutants_x__first_missing_injury_field__mutmut['x__first_missing_injury_field__mutmut_5'] = x__first_missing_injury_field__mutmut_5 # type: ignore # mutmut generated
mutants_x__first_missing_injury_field__mutmut['x__first_missing_injury_field__mutmut_6'] = x__first_missing_injury_field__mutmut_6 # type: ignore # mutmut generated
mutants_x__first_missing_injury_field__mutmut['x__first_missing_injury_field__mutmut_7'] = x__first_missing_injury_field__mutmut_7 # type: ignore # mutmut generated
mutants_x__first_missing_injury_field__mutmut['x__first_missing_injury_field__mutmut_8'] = x__first_missing_injury_field__mutmut_8 # type: ignore # mutmut generated
