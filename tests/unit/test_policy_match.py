"""The policy-match rule: what the search's answer does to the notice, and how
its two blockers join the notice's list.

Every code is asserted against its spelling rather than the module's constant,
so a mutated literal is a failing test and not a renamed one.
"""

from datetime import date

import pytest

from claimgate.domain.continuous_coverage import (
    ContinuousCoverageDerivation,
    carry_onto_candidate,
)
from claimgate.domain.models import Candidate, ValidationBlocker
from claimgate.domain.policy_match import (
    FoundPolicy,
    PolicyMatch,
    match_blockers,
    match_policy,
    unobtained_history,
)
from claimgate.domain.validation import canonical_order

_MISSING_NAME = ValidationBlocker("MISSING_REQUIRED_FIELD", "claimant_name")
_MISSING_DESCRIPTION = ValidationBlocker("MISSING_REQUIRED_FIELD", "incident_description")
_FUTURE = ValidationBlocker("LOSS_DATE_IN_FUTURE", "loss_date")
_INSUFFICIENT = ValidationBlocker(
    "POLICY_IDENTIFIERS_INSUFFICIENT", "policy_number,insured_name,risk_postal_code"
)
_BY_NUMBER = FoundPolicy("POL-88213", "POLICY_NUMBER")
_BY_PAIR = FoundPolicy("POL-88213", "INSURED_NAME_AND_POSTAL_CODE")


def test_exactly_one_reference_is_matched_and_names_it_and_what_found_it() -> None:
    match = match_policy((_BY_NUMBER,), None)

    assert match == PolicyMatch(
        "MATCHED", policy_reference="POL-88213", identified_on="POLICY_NUMBER", reason=None
    )


def test_a_policy_found_on_the_pair_says_so() -> None:
    # 7g decision 5: a mistyped number beside a correct pair is the case the
    # search exists for, and the reviewer should see the number did not match.
    match = match_policy((_BY_PAIR,), None)

    assert match.identified_on == "INSURED_NAME_AND_POSTAL_CODE"
    assert match.policy_reference == "POL-88213"


def test_no_reference_is_not_matched_and_names_nothing() -> None:
    assert match_policy((), None) == PolicyMatch("NOT_MATCHED", policy_reference=None, reason=None)


def test_several_references_are_ambiguous_and_name_none_of_them() -> None:
    match = match_policy((_BY_NUMBER, FoundPolicy("POL-88214", "POLICY_NUMBER")), None)

    assert match == PolicyMatch(
        "AMBIGUOUS", policy_reference=None, identified_on=None, reason=None
    )


def test_a_search_that_was_not_evaluated_carries_the_sources_reason_and_no_reference() -> None:
    match = match_policy((), "SOURCE_TIMEOUT")

    assert match == PolicyMatch("NOT_EVALUATED", policy_reference=None, reason="SOURCE_TIMEOUT")


def test_a_reason_beside_a_reference_is_a_caller_contract_violation() -> None:
    with pytest.raises(
        ValueError, match=r"^a search that was not evaluated cannot have found a policy$"
    ):
        match_policy((_BY_NUMBER,), "SOURCE_UNAVAILABLE")


@pytest.mark.parametrize(
    ("match", "expected"),
    [
        (PolicyMatch("MATCHED", policy_reference="POL-88213"), ()),
        (PolicyMatch("NOT_EVALUATED", reason="SOURCE_UNAVAILABLE"), ()),
        (PolicyMatch("NOT_MATCHED"), (ValidationBlocker("POLICY_NOT_MATCHED", ""),)),
        (PolicyMatch("AMBIGUOUS"), (ValidationBlocker("POLICY_AMBIGUOUS", ""),)),
        (None, ()),
    ],
)
def test_only_the_two_actionable_outcomes_block_and_neither_names_a_field(
    match: PolicyMatch | None, expected: tuple[ValidationBlocker, ...]
) -> None:
    assert match_blockers(match) == expected


@pytest.mark.parametrize(
    ("match", "reason"),
    [
        (PolicyMatch("NOT_MATCHED"), "POLICY_NOT_MATCHED"),
        (PolicyMatch("AMBIGUOUS"), "POLICY_AMBIGUOUS"),
        (PolicyMatch("NOT_EVALUATED", reason="SOURCE_MALFORMED"), "SOURCE_MALFORMED"),
    ],
)
def test_an_unmatched_notices_history_is_not_obtained_for_the_identifications_own_reason(
    match: PolicyMatch, reason: str
) -> None:
    history = unobtained_history(match)

    assert history.value == "NOT_OBTAINED"
    assert history.reason == reason
    assert history.terms == ()


def test_a_matched_policys_history_is_the_sources_to_supply_not_this_rules() -> None:
    with pytest.raises(
        ValueError, match=r"^a matched policy's term history is the source's to supply$"
    ):
        unobtained_history(PolicyMatch("MATCHED", policy_reference="POL-88213"))


def test_the_three_families_sort_arrival_then_identification_then_search() -> None:
    # No locked scenario carries a search blocker beside another family on one
    # row, and the identification blocker never co-occurs with the search's
    # (7g decision 2); this is the only assertion of the order across all
    # three, which is why it is asserted here.
    not_matched = ValidationBlocker("POLICY_NOT_MATCHED", "")
    ambiguous = ValidationBlocker("POLICY_AMBIGUOUS", "")

    assert canonical_order([not_matched, _INSUFFICIENT, _MISSING_NAME, _FUTURE]) == (
        _FUTURE, _MISSING_NAME, _INSUFFICIENT, not_matched,
    )
    assert canonical_order([ambiguous, _INSUFFICIENT, _MISSING_DESCRIPTION, _MISSING_NAME]) == (
        _MISSING_NAME, _MISSING_DESCRIPTION, _INSUFFICIENT, ambiguous,
    )


def test_a_derived_date_is_carried_onto_the_candidate_and_nothing_else_moves() -> None:
    candidate = Candidate(policy_number="HO-4471209", loss_date=date(2026, 6, 1), loss_type="fire")
    derivation = ContinuousCoverageDerivation("DERIVED", continuous_since=date(2026, 1, 15))

    carried = carry_onto_candidate(candidate, derivation)

    assert carried.continuous_coverage_date == date(2026, 1, 15)
    assert carried == Candidate(
        policy_number="HO-4471209", loss_date=date(2026, 6, 1), loss_type="fire",
        continuous_coverage_date=date(2026, 1, 15),
    )


def test_a_derivation_that_was_not_evaluated_leaves_the_candidate_without_a_date() -> None:
    candidate = Candidate(loss_date=date(2026, 6, 1), continuous_coverage_date=date(2020, 1, 1))
    derivation = ContinuousCoverageDerivation("NOT_EVALUATED", reason="SOURCE_UNAVAILABLE")

    assert carry_onto_candidate(candidate, derivation).continuous_coverage_date is None
