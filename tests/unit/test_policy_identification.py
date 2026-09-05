"""Unit tests for claimgate.domain.policy_identification.

The spec's scenarios are repeated here because unit tests call the domain
directly and never read feature files (docs/harness-findings.md, "A green gate
sometimes means nothing was checked"). The rest probes what the spec leaves to
the implementation: None as the shell's spelling of absence, a name or a postal
code beside a policy number without its partner, and the order of arms and of
absent fields.
"""

import pytest

from claimgate.domain.policy_identification import (
    INSURED_NAME_AND_POSTAL_CODE,
    POLICY_IDENTIFIERS_INSUFFICIENT,
    POLICY_NUMBER,
    IdentificationBlocker,
    IdentifierSufficiency,
    SearchIdentifiers,
    evaluate_identifier_sufficiency,
)


def test_a_policy_number_alone_is_searchable_on_the_number_and_carries_only_it() -> None:
    result = evaluate_identifier_sufficiency("HO-4471209", "", "")

    assert result == IdentifierSufficiency(
        "SEARCHABLE", arms=("POLICY_NUMBER",), search=SearchIdentifiers("HO-4471209", None, None)
    )


def test_an_insured_name_with_a_postal_code_is_searchable_without_a_number() -> None:
    result = evaluate_identifier_sufficiency("", "Marisol Quintero", "34287")

    assert result == IdentifierSufficiency(
        "SEARCHABLE",
        arms=("INSURED_NAME_AND_POSTAL_CODE",),
        search=SearchIdentifiers(None, "Marisol Quintero", "34287"),
    )


def test_all_three_identifiers_report_both_arms_number_first() -> None:
    result = evaluate_identifier_sufficiency("HO-4471209", "Marisol Quintero", "34287")

    assert result.value == "SEARCHABLE"
    assert result.arms == (POLICY_NUMBER, INSURED_NAME_AND_POSTAL_CODE)
    assert result.search == SearchIdentifiers("HO-4471209", "Marisol Quintero", "34287")
    assert result.blocker is None


@pytest.mark.parametrize(
    ("insured_name", "risk_postal_code"),
    [("Marisol Quintero", ""), ("", "34287"), ("Marisol Quintero", None), (None, "34287")],
)
def test_a_name_or_a_postal_code_beside_a_number_without_its_partner_is_not_carried(
    insured_name: str | None, risk_postal_code: str | None
) -> None:
    # The pair travels together or not at all: a name without a postal code is
    # not a search input, so the search carries the number and nothing else.
    result = evaluate_identifier_sufficiency("HO-4471209", insured_name, risk_postal_code)

    assert result.arms == ("POLICY_NUMBER",)
    assert result.search == SearchIdentifiers("HO-4471209", None, None)


@pytest.mark.parametrize(
    ("policy_number", "insured_name", "risk_postal_code", "absent"),
    [
        ("", "Marisol Quintero", "", ("policy_number", "risk_postal_code")),
        ("", "", "34287-2210", ("policy_number", "insured_name")),
        ("", "", "", ("policy_number", "insured_name", "risk_postal_code")),
        (None, None, None, ("policy_number", "insured_name", "risk_postal_code")),
        ("   ", "Marisol Quintero", "   ", ("policy_number", "risk_postal_code")),
        (None, "   ", "34287", ("policy_number", "insured_name")),
    ],
)
def test_anything_less_is_insufficient_and_the_blocker_names_every_absent_field_in_order(
    policy_number: str | None,
    insured_name: str | None,
    risk_postal_code: str | None,
    absent: tuple[str, ...],
) -> None:
    result = evaluate_identifier_sufficiency(policy_number, insured_name, risk_postal_code)

    assert result == IdentifierSufficiency(
        "INSUFFICIENT", blocker=IdentificationBlocker("POLICY_IDENTIFIERS_INSUFFICIENT", absent)
    )
    assert result.blocker is not None
    assert result.blocker.code == POLICY_IDENTIFIERS_INSUFFICIENT


def test_identifiers_are_carried_trimmed() -> None:
    result = evaluate_identifier_sufficiency("  HO-4471209 ", " Marisol Quintero  ", " 34287 ")

    assert result.search == SearchIdentifiers("HO-4471209", "Marisol Quintero", "34287")


def test_a_whitespace_only_policy_number_is_absent_beside_a_name_and_postal_code() -> None:
    result = evaluate_identifier_sufficiency("   ", "Marisol Quintero", "34287")

    assert result.arms == (INSURED_NAME_AND_POSTAL_CODE,)
    assert result.search == SearchIdentifiers(None, "Marisol Quintero", "34287")


def test_none_is_absence_the_same_as_the_empty_string() -> None:
    # The shell's optional fields arrive as None; the spec's Givens as "".
    assert evaluate_identifier_sufficiency(None, "Marisol Quintero", "34287") == (
        evaluate_identifier_sufficiency("", "Marisol Quintero", "34287")
    )


@pytest.mark.parametrize("policy_number", ["7Q-000012", "hello", "1"])
def test_a_policy_number_of_any_shape_is_a_search_not_a_pend(policy_number: str) -> None:
    result = evaluate_identifier_sufficiency(policy_number, None, None)

    assert result.value == "SEARCHABLE"
    assert result.search == SearchIdentifiers(policy_number, None, None)


def test_a_nine_digit_postal_code_is_carried_as_given() -> None:
    result = evaluate_identifier_sufficiency(None, "Marisol Quintero", "34287-2210")

    assert result.arms == (INSURED_NAME_AND_POSTAL_CODE,)
    assert result.search == SearchIdentifiers(None, "Marisol Quintero", "34287-2210")


def test_the_vocabulary_is_the_specification_s() -> None:
    assert POLICY_NUMBER == "POLICY_NUMBER"
    assert INSURED_NAME_AND_POSTAL_CODE == "INSURED_NAME_AND_POSTAL_CODE"
    assert POLICY_IDENTIFIERS_INSUFFICIENT == "POLICY_IDENTIFIERS_INSUFFICIENT"
