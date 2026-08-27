"""Pure validation rules for a candidate FNOL record.

`now` is the jurisdiction's calendar date, and is None where the notice's
property state selected no jurisdiction and there is therefore no calendar to
ask (item 5g). A candidate's loss date is None where the reporter stated none
(item 5h). Neither None is "no future loss": each is an input the loss-date
rule cannot proceed without, so the determination records which one was missing
rather than resolving to a negative - see _determine_future_dated_loss. An
absent loss date is additionally a blocker in its own right, which the
determination is deliberately not the carrier of - see _check_loss_date_present.
"""

import re
from collections.abc import Collection
from datetime import date

from claimgate.domain.models import (
    Candidate,
    FutureDatedLossResult,
    ValidationBlocker,
    ValidationResult,
)

POLICY_NUMBER_PATTERN = re.compile(r"^([A-Z]{2})-\d{7}$")
RECOGNIZED_NOTICE_TYPES = frozenset({"INITIAL", "REOPENED", "SUPPLEMENTAL", "LOSS_ASSESSMENT"})
RECOGNIZED_LOSS_TYPES = frozenset(
    {
        "fire",
        "flood",
        "hurricane",
        "injury",
        "liability",
        "lightning",
        "mold",
        "roof_leak",
        "sinkhole",
        "smoke",
        "theft",
        "vandalism",
        "water_damage",
        "wind_hail",
    }
)
# Membership in RECOGNIZED_LOSS_TYPES is enforced by
# test_section_ii_loss_types_are_recognized (tests/unit/test_validation.py),
# the same shape as _HIGH_SEVERITY_LOSS_TYPES <= RECOGNIZED_LOSS_TYPES in
# triage.py - a direct unit-test assertion, not a scenario or a shared
# module (QUEUE.md item 4h).
_SECTION_II_LOSS_TYPES = frozenset({"injury", "liability"})

POLICY_NUMBER_MALFORMED = "POLICY_NUMBER_MALFORMED"
NOTICE_TYPE_UNRECOGNIZED = "NOTICE_TYPE_UNRECOGNIZED"
LOSS_TYPE_UNRECOGNIZED = "LOSS_TYPE_UNRECOGNIZED"
LOSS_DATE_IN_FUTURE = "LOSS_DATE_IN_FUTURE"
MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"

# The first member of the future-dated-loss determination's own closed reason
# enumeration. It shares a spelling with domain/siu.py's code of the same name
# and is not the same code: the two enumerations are scoped to their own
# subjects and grow independently (CLAUDE.md). The 2026-08-26 ratification
# recorded in features/jurisdiction_selection.feature's Rule 3 is what adds it
# to each of them.
NO_JURISDICTION_DATE = "NO_JURISDICTION_DATE"
# The second member of that same closed enumeration, added by the 2026-08-27
# ratification recorded in ASSUMPTIONS.md's "Item 5h, three decisions" and by
# nothing else. It is deliberately not added to domain/siu.py's enumeration -
# see that module for why an absent loss date raises there instead.
NO_LOSS_DATE = "NO_LOSS_DATE"

# Canonical order is a declared property of the code enumeration, not the
# order checks happen to run in below. The check order is deliberately
# different from this so that a mutant deleting the sort in _canonical_order
# is caught by a scenario expecting canonical order rather than passing by
# coincidence. Do not reorder the checks below to match this tuple.
_CANONICAL_CODE_ORDER = (
    POLICY_NUMBER_MALFORMED,
    NOTICE_TYPE_UNRECOGNIZED,
    LOSS_TYPE_UNRECOGNIZED,
    LOSS_DATE_IN_FUTURE,
    MISSING_REQUIRED_FIELD,
)


def validate(
    candidate: Candidate,
    now: date | None,
    *,
    claimant_name_required: bool,
    claimant_contact_required: bool,
    recognized_policy_number_prefixes: Collection[str],
) -> ValidationResult:
    future_dated_loss = _determine_future_dated_loss(candidate, now)
    blockers = (
        _check_loss_date(future_dated_loss)
        + _check_loss_date_present(candidate)
        + _check_claimant_fields(
            candidate,
            claimant_name_required=claimant_name_required,
            claimant_contact_required=claimant_contact_required,
        )
        + _check_notice_type(candidate)
        + _check_loss_type(candidate)
        + _check_policy_number(candidate, recognized_policy_number_prefixes)
    )
    return ValidationResult(
        blockers=tuple(_canonical_order(blockers)), future_dated_loss=future_dated_loss
    )


def _canonical_order(blockers: list[ValidationBlocker]) -> list[ValidationBlocker]:
    return sorted(blockers, key=lambda b: (_CANONICAL_CODE_ORDER.index(b.code), b.field))


def _determine_future_dated_loss(
    candidate: Candidate, now: date | None
) -> FutureDatedLossResult:
    """Neither absence is "no future loss": each is an input this rule cannot
    proceed without, so the determination names the one that was missing rather
    than resolving to a negative (CLAUDE.md)."""
    # Order is deliberate, not incidental. The tie-break the SIU indicators use
    # - name the gap that would still block evaluation if the other were closed
    # - is silent here: with neither a loss date nor a jurisdiction, closing
    # either leaves the other. What decides it is that the loss date is this
    # determination's subject and today only the yardstick it is held against,
    # so the missing subject is the more basic absence. NO_LOSS_DATE outranks
    # NO_JURISDICTION_DATE, ratified 2026-08-27 (ASSUMPTIONS.md, "Item 5h,
    # three decisions"). Do not reorder these checks. Until item 5j's row lands
    # in jurisdiction_selection.feature this comment is the ordering's only
    # protection - nothing asserts which reason the both-absent case names, so
    # nothing fails on a reordering: item 4k's shape, and why 5j exists.
    if candidate.loss_date is None:
        return FutureDatedLossResult("NOT_EVALUATED", NO_LOSS_DATE)
    if now is None:
        return FutureDatedLossResult("NOT_EVALUATED", NO_JURISDICTION_DATE)
    return FutureDatedLossResult("TRUE" if candidate.loss_date > now else "FALSE")


def _check_loss_date(future_dated_loss: FutureDatedLossResult) -> list[ValidationBlocker]:
    """The blocker is read off the determination rather than recomputed, so the
    two cannot disagree - and an unevaluated determination raises no blocker,
    which is what keeps an unsupported jurisdiction from blocking a notice."""
    if future_dated_loss.value == "TRUE":
        return [ValidationBlocker(LOSS_DATE_IN_FUTURE, "loss_date")]
    return []


def _check_loss_date_present(candidate: Candidate) -> list[ValidationBlocker]:
    """Independent of the determination, and it has to be. _check_loss_date
    reads its blocker off the determination and a NOT_EVALUATED determination
    raises none - which is what keeps an unsupported jurisdiction from blocking
    a notice - so the presence blocker cannot ride that path and needs its own
    check. An absent loss date is a blocker, not a refusal (ASSUMPTIONS.md, "An
    absent loss date is a domain blocker, not a schema refusal")."""
    if candidate.loss_date is None:
        return [ValidationBlocker(MISSING_REQUIRED_FIELD, "loss_date")]
    return []


def _check_policy_number(
    candidate: Candidate, recognized_policy_number_prefixes: Collection[str]
) -> list[ValidationBlocker]:
    if not candidate.policy_number.strip():
        return [ValidationBlocker(MISSING_REQUIRED_FIELD, "policy_number")]
    match = POLICY_NUMBER_PATTERN.match(candidate.policy_number)
    if not match or match.group(1) not in recognized_policy_number_prefixes:
        return [ValidationBlocker(POLICY_NUMBER_MALFORMED, "policy_number")]
    return []


def _check_loss_type(candidate: Candidate) -> list[ValidationBlocker]:
    if not candidate.loss_type.strip():
        return [ValidationBlocker(MISSING_REQUIRED_FIELD, "loss_type")]
    if candidate.loss_type not in RECOGNIZED_LOSS_TYPES:
        return [ValidationBlocker(LOSS_TYPE_UNRECOGNIZED, "loss_type")]
    return []


def _check_notice_type(candidate: Candidate) -> list[ValidationBlocker]:
    if not candidate.notice_type.strip():
        return [ValidationBlocker(MISSING_REQUIRED_FIELD, "notice_type")]
    if candidate.notice_type not in RECOGNIZED_NOTICE_TYPES:
        return [ValidationBlocker(NOTICE_TYPE_UNRECOGNIZED, "notice_type")]
    return []


def _check_claimant_fields(
    candidate: Candidate,
    *,
    claimant_name_required: bool,
    claimant_contact_required: bool,
) -> list[ValidationBlocker]:
    if candidate.loss_type not in _SECTION_II_LOSS_TYPES:
        return []
    fields = (
        (True, "incident_description", candidate.incident_description),
        (claimant_name_required, "claimant_name", candidate.claimant_name),
        (claimant_contact_required, "claimant_contact", candidate.claimant_contact),
    )
    return [
        ValidationBlocker(MISSING_REQUIRED_FIELD, field_name)
        for required, field_name, value in fields
        if required and not value
    ]
