"""Acceptance tests binding features/carrier_configuration.feature to the test API."""

from typing import Any

from pytest_bdd import given, parsers, scenarios, then, when

from tests.api.carrier_configuration import resolve_carrier_configuration

scenarios("../../features/carrier_configuration.feature")

# Every field name the specification writes, mapped to the raw rules-source
# key the domain function reads. Business language on one side, the model's
# own vocabulary on the other - the same split validation.feature's
# "claimant name is ... by configuration" steps already draw.
_FIELD_KEYS = {
    "claimant name": "claimant_name_required",
    "claimant contact": "claimant_contact_required",
    "recognized policy-number prefixes": "recognized_policy_number_prefixes",
    "late reporting threshold": "late_reporting_threshold_days",
    "recent policy inception threshold": "recent_inception_threshold_days",
    "duplicate match window": "window_days",
}

_COMPLETE_VALID_ENTRY = {
    "claimant_name_required": True,
    "claimant_contact_required": True,
    "recognized_policy_number_prefixes": ["HO", "DP"],
    "late_reporting_threshold_days": 30,
    "recent_inception_threshold_days": 30,
    "window_days": 60,
}


@given(
    parsers.parse(
        'the carrier rules source recognizes "{carrier}", with a complete and '
        "valid entry for every one of the six values"
    )
)
def set_up_rules_source(context: dict[str, Any], carrier: str) -> None:
    context["rules_source"] = {carrier: dict(_COMPLETE_VALID_ENTRY)}


@given(parsers.re(r'^(?:the carrier )?"(?P<carrier>[^"]+)" requires the claimant name$'))
def set_claimant_name_required(context: dict[str, Any], carrier: str) -> None:
    context["rules_source"][carrier]["claimant_name_required"] = True


@given(parsers.parse('"{carrier}" does not require the claimant contact'))
def set_claimant_contact_not_required(context: dict[str, Any], carrier: str) -> None:
    context["rules_source"][carrier]["claimant_contact_required"] = False


@given(parsers.parse('"{carrier}" recognizes the policy-number prefixes "{prefixes}"'))
def set_recognized_prefixes(context: dict[str, Any], carrier: str, prefixes: str) -> None:
    context["rules_source"][carrier]["recognized_policy_number_prefixes"] = prefixes.split(";")


@given(parsers.parse('"{carrier}" recognizes no policy-number prefixes'))
def set_no_recognized_prefixes(context: dict[str, Any], carrier: str) -> None:
    context["rules_source"][carrier]["recognized_policy_number_prefixes"] = []


@given(parsers.parse('"{carrier}" configures a late reporting threshold of {value:d} days'))
def set_late_reporting_threshold(context: dict[str, Any], carrier: str, value: int) -> None:
    context["rules_source"][carrier]["late_reporting_threshold_days"] = value


@given(parsers.parse('"{carrier}" has no late reporting threshold configured'))
def clear_late_reporting_threshold(context: dict[str, Any], carrier: str) -> None:
    context["rules_source"][carrier].pop("late_reporting_threshold_days", None)


@given(
    parsers.parse(
        '"{carrier}" configures a recent policy inception threshold of {value:d} days'
    )
)
def set_recent_inception_threshold(context: dict[str, Any], carrier: str, value: int) -> None:
    context["rules_source"][carrier]["recent_inception_threshold_days"] = value


@given(parsers.parse('"{carrier}" has no recent policy inception threshold configured'))
def clear_recent_inception_threshold(context: dict[str, Any], carrier: str) -> None:
    context["rules_source"][carrier].pop("recent_inception_threshold_days", None)


@given(parsers.parse('"{carrier}" configures a duplicate match window of {value:d} days'))
def set_duplicate_match_window(context: dict[str, Any], carrier: str, value: int) -> None:
    context["rules_source"][carrier]["window_days"] = value


@given(
    parsers.parse(
        '"{carrier}" configures the duplicate match window as a negative number of days'
    )
)
def set_duplicate_match_window_negative(context: dict[str, Any], carrier: str) -> None:
    context["rules_source"][carrier]["window_days"] = -1


@given(parsers.parse('"{carrier}"\'s configuration is missing the claimant name'))
def clear_claimant_name_required(context: dict[str, Any], carrier: str) -> None:
    context["rules_source"][carrier].pop("claimant_name_required", None)


@given(parsers.parse('"{carrier}"\'s configuration is missing the claimant contact'))
def clear_claimant_contact_required(context: dict[str, Any], carrier: str) -> None:
    context["rules_source"][carrier].pop("claimant_contact_required", None)


@given(parsers.re(r'^"(?P<carrier>[^"]+)" configures the (?P<field>.*) as (?P<value>.*)$'))
def set_configured_field(context: dict[str, Any], carrier: str, field: str, value: str) -> None:
    if not field:
        return
    entry = context["rules_source"][carrier]
    key = _FIELD_KEYS[field]
    if value == "absent":
        entry.pop(key, None)
    elif value == "neither yes nor no":
        entry[key] = "neither yes nor no"
    elif value == "an empty set":
        entry[key] = []
    elif value == "a negative number of days":
        entry[key] = -1
    else:
        raise ValueError(f"unrecognized configuration value {value!r}")


@when(parsers.parse('the carrier configuration for "{carrier_code}" is loaded'))
def run_load(context: dict[str, Any], carrier_code: str) -> None:
    context["carrier_configuration_result"] = resolve_carrier_configuration(
        carrier_code, context["rules_source"]
    )


@then(parsers.parse('the claimant name is received as "{value}"'))
def check_claimant_name_required(context: dict[str, Any], value: str) -> None:
    assert context["carrier_configuration_result"].rules.claimant_name_required == (
        value == "required"
    )


@then(parsers.parse('the claimant contact is received as "{value}"'))
def check_claimant_contact_required(context: dict[str, Any], value: str) -> None:
    assert context["carrier_configuration_result"].rules.claimant_contact_required == (
        value == "required"
    )


@then(parsers.parse('the recognized policy-number prefixes are received as "{value}"'))
def check_recognized_prefixes(context: dict[str, Any], value: str) -> None:
    rules = context["carrier_configuration_result"].rules
    assert rules.recognized_policy_number_prefixes == frozenset(value.split(";"))


@then(parsers.parse("the late reporting threshold is received as {value:d} days"))
def check_late_reporting_threshold(context: dict[str, Any], value: int) -> None:
    rules = context["carrier_configuration_result"].rules
    assert rules.late_reporting_threshold_days == value


@then('the late reporting threshold is received as "not configured"')
def check_late_reporting_threshold_not_configured(context: dict[str, Any]) -> None:
    rules = context["carrier_configuration_result"].rules
    assert rules.late_reporting_threshold_days is None


@then(parsers.parse("the recent policy inception threshold is received as {value:d} days"))
def check_recent_inception_threshold(context: dict[str, Any], value: int) -> None:
    rules = context["carrier_configuration_result"].rules
    assert rules.recent_inception_threshold_days == value


@then('the recent policy inception threshold is received as "not configured"')
def check_recent_inception_threshold_not_configured(context: dict[str, Any]) -> None:
    rules = context["carrier_configuration_result"].rules
    assert rules.recent_inception_threshold_days is None


@then(parsers.parse("the duplicate match window is received as {value:d} days"))
def check_duplicate_match_window(context: dict[str, Any], value: int) -> None:
    assert context["carrier_configuration_result"].rules.window_days == value


@then(parsers.re(r"^the load is\s*(?P<outcome>.*)$"))
def check_load_outcome(context: dict[str, Any], outcome: str) -> None:
    _assert_outcome(context["carrier_configuration_result"], outcome.strip())


@then(parsers.parse('every rejected value is named in the refusal as "{outcome}"'))
def check_every_rejected_value(context: dict[str, Any], outcome: str) -> None:
    _assert_outcome(context["carrier_configuration_result"], outcome)


def _assert_outcome(result: Any, outcome: str) -> None:
    if not outcome:
        assert result.value == "RESOLVED"
        return
    assert result.value == "REFUSED"
    rendered = ";".join(
        rejection.code if not rejection.field else f"{rejection.code}:{rejection.field}"
        for rejection in result.rejections
    )
    assert rendered == outcome
