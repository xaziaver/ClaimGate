"""Unit tests for claimgate.domain.carrier_configuration."""

from typing import Any

import pytest

from claimgate.domain.carrier_configuration import (
    CARRIER_NOT_CONFIGURED,
    MALFORMED_REQUIRED_CONFIGURATION,
    MISSING_REQUIRED_CONFIGURATION,
    resolve_carrier_configuration,
)

_VALID_ENTRY = {
    "claimant_name_required": True,
    "claimant_contact_required": False,
    "recognized_policy_number_prefixes": ["HO", "DP"],
    "late_reporting_threshold_days": 45,
    "recent_inception_threshold_days": 30,
    "window_days": 60,
}


def test_a_complete_valid_entry_resolves_every_value() -> None:
    result = resolve_carrier_configuration("AAAA", {"AAAA": dict(_VALID_ENTRY)})

    assert result.value == "RESOLVED"
    assert result.rules is not None
    assert result.rules.claimant_name_required is True
    assert result.rules.claimant_contact_required is False
    assert result.rules.recognized_policy_number_prefixes == frozenset({"HO", "DP"})
    assert result.rules.late_reporting_threshold_days == 45
    assert result.rules.recent_inception_threshold_days == 30
    assert result.rules.window_days == 60


def test_a_carrier_with_no_entry_is_refused_as_not_configured() -> None:
    result = resolve_carrier_configuration("ZZZZ", {"AAAA": dict(_VALID_ENTRY)})

    assert result.value == "REFUSED"
    assert result.rules is None
    assert [(r.code, r.field) for r in result.rejections] == [(CARRIER_NOT_CONFIGURED, "")]


@pytest.mark.parametrize(
    "key",
    ["late_reporting_threshold_days", "recent_inception_threshold_days"],
)
def test_either_siu_threshold_may_be_absent(key: str) -> None:
    entry = dict(_VALID_ENTRY)
    del entry[key]

    result = resolve_carrier_configuration("AAAA", {"AAAA": entry})

    assert result.value == "RESOLVED"
    assert result.rules is not None
    assert getattr(result.rules, key) is None


@pytest.mark.parametrize(
    "key",
    ["late_reporting_threshold_days", "recent_inception_threshold_days", "window_days"],
)
def test_a_day_count_of_zero_is_valid(key: str) -> None:
    entry = dict(_VALID_ENTRY)
    entry[key] = 0

    result = resolve_carrier_configuration("AAAA", {"AAAA": entry})

    assert result.value == "RESOLVED"
    assert result.rules is not None
    assert getattr(result.rules, key) == 0


@pytest.mark.parametrize(
    ("key", "field"),
    [
        ("claimant_name_required", "claimant name"),
        ("claimant_contact_required", "claimant contact"),
        ("recognized_policy_number_prefixes", "recognized policy-number prefixes"),
        ("window_days", "duplicate match window"),
    ],
)
def test_a_missing_required_value_is_named_in_the_refusal(key: str, field: str) -> None:
    entry = dict(_VALID_ENTRY)
    del entry[key]

    result = resolve_carrier_configuration("AAAA", {"AAAA": entry})

    assert result.value == "REFUSED"
    assert [(r.code, r.field) for r in result.rejections] == [
        (MISSING_REQUIRED_CONFIGURATION, field)
    ]


@pytest.mark.parametrize(
    ("key", "field", "malformed_value"),
    [
        ("claimant_name_required", "claimant name", "neither yes nor no"),
        ("claimant_contact_required", "claimant contact", "neither yes nor no"),
        ("recognized_policy_number_prefixes", "recognized policy-number prefixes", []),
        ("window_days", "duplicate match window", -1),
        ("late_reporting_threshold_days", "late reporting threshold", -1),
        ("recent_inception_threshold_days", "recent policy inception threshold", -1),
    ],
)
def test_a_malformed_value_is_named_in_the_refusal(
    key: str, field: str, malformed_value: Any
) -> None:
    entry = dict(_VALID_ENTRY)
    entry[key] = malformed_value

    result = resolve_carrier_configuration("AAAA", {"AAAA": entry})

    assert result.value == "REFUSED"
    assert [(r.code, r.field) for r in result.rejections] == [
        (MALFORMED_REQUIRED_CONFIGURATION, field)
    ]


def test_a_boolean_typed_as_an_int_is_not_accidentally_valid() -> None:
    # bool is a subclass of int - 1 must not pass as True by coincidence.
    entry = dict(_VALID_ENTRY)
    entry["claimant_name_required"] = 1

    result = resolve_carrier_configuration("AAAA", {"AAAA": entry})

    assert result.value == "REFUSED"


def test_several_rejections_are_named_together_in_canonical_order() -> None:
    entry = dict(_VALID_ENTRY)
    del entry["claimant_contact_required"]
    entry["recognized_policy_number_prefixes"] = []
    entry["window_days"] = -1

    result = resolve_carrier_configuration("AAAA", {"AAAA": entry})

    assert result.value == "REFUSED"
    assert [(r.code, r.field) for r in result.rejections] == [
        (MALFORMED_REQUIRED_CONFIGURATION, "duplicate match window"),
        (MALFORMED_REQUIRED_CONFIGURATION, "recognized policy-number prefixes"),
        (MISSING_REQUIRED_CONFIGURATION, "claimant contact"),
    ]


def test_missing_values_of_the_same_code_are_named_alphabetically() -> None:
    entry = dict(_VALID_ENTRY)
    del entry["claimant_name_required"]
    del entry["claimant_contact_required"]

    result = resolve_carrier_configuration("AAAA", {"AAAA": entry})

    assert [(r.code, r.field) for r in result.rejections] == [
        (MISSING_REQUIRED_CONFIGURATION, "claimant contact"),
        (MISSING_REQUIRED_CONFIGURATION, "claimant name"),
    ]
