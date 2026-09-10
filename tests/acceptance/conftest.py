"""Shared fixtures and step definitions for acceptance tests.

Steps live here when more than one feature file states them in the same words.
The notice-submission steps below arrived here with features/idempotency.feature
(item 5d), which restates features/notice_intake.feature's Background verbatim;
copying them into a second module would be a duplicate block the duplication
gate refuses, and rewording them is not available - both specs are locked.

A module's own step definition overrides one of the same text here (ordinary
pytest fixture precedence, confirmed by test_carrier_configuration_acceptance.py,
which keeps its own carrier-rules steps and its own rules-source vocabulary).
features/resolution.feature (item 5e) uses that override for one phrase and
shares the rest: the blockers assertion and the three idempotency phrases below
moved here when it became the second locked spec to state them word for word.

The reviewer's four phrases and the carrier's late reporting threshold moved here
in item 5f, by the same rule and for the same reason: features/siu_separation.
feature states all five in exactly the words another locked spec already used.
The threshold phrase came from test_carrier_configuration_acceptance.py, which
keeps its own definition of it - that module has its own rules-source vocabulary
and writes to its own context key, which neither submit_notice nor resolve_notice
reads. Written here on the _rules_entry pattern instead, it replaces the value in
place, which is what lets a scenario configure a threshold after the notice has
already arrived.

Item 7f added the carrier's policy source. Every spec that submits a notice now
declares one in its Background - five locked specs say it is unavailable, and
features/policy_match.feature gives it a policy to find - so the source-fault
phrase, the binding fault, and the bindings the submission is made with all live
here, and the recorded-indicator phrase moved here from
test_siu_separation_acceptance.py when policy_match.feature became the second
spec to state it word for word. A source fault is not a deployment fault:
"this deployment is configured correctly" clears the three configuration faults
and leaves an unavailable source unavailable, because the source is another
system and nothing about this deployment's configuration made it so.
"""

from datetime import date, datetime
from typing import Any

import pytest
from pytest_bdd import given, parsers, then, when

from tests.acceptance.support import (
    assert_recorded_indicator,
    parse_compact_blockers,
    parse_instant,
    policy_terms,
    shown_verification,
    verification,
)
from tests.api.coverage import (
    cancelled,
    policy_term,
    reinstated,
    reinstated_retroactively,
    unobtained_term_history,
)
from tests.api.notice_intake import (
    CARRIER_IDENTITY_REFERENCE,
    IN_MEMORY_DATABASE,
    JURISDICTION_REFERENCE,
    NoticeFields,
    NoticeStore,
    submit_notice,
)
from tests.api.policy_match import PolicySources
from tests.api.resolution import resolve_notice

DEFAULT_TODAY = date(2026, 8, 2)
# The reviewer a resolution is attributed to where the scenario identified none
# (item 7g): policy_match.feature's resolution rows are about the re-search and
# name no reviewer, and the endpoint answers a body without one 400, which is
# resolution.feature's own subject and not theirs. The same identity every
# locked Background gives; "absent" there is still None, set by its step.
_DEFAULT_REVIEWER = "adjuster-4471"
_SUPPLIED_FIELDS = {
    "policy number": "policy_number",
    "notice type": "notice_type",
    "loss type": "loss_type",
    "property state": "property_state",
    # A reviewer may correct the loss date like any other notice-content field
    # (item 5e decision 1). It joined this map at item 5i, whose third row in
    # resolution.feature Rule 2 supplies one that is not a date at all.
    "loss date": "loss_date",
    # A reviewer may supply the insured name and risk postal code the notice
    # lacked (item 7g decision 7): the pair is the other route to the policy.
    "insured name": "insured_name",
    "risk postal code": "risk_postal_code",
}


@pytest.fixture
def context() -> dict[str, Any]:
    return {
        "today": DEFAULT_TODAY, "fields": {}, "idempotency_key": None,
        "policy_sources": PolicySources(),
    }


@given(parsers.parse('today is "{value}"'))
def set_today(context: dict[str, Any], value: str) -> None:
    context["today"] = date.fromisoformat(value)


# Shared with siu_indicators.feature and triage.feature - both set thresholds
# with this exact step text (triage.feature's end-to-end scenario supplies the
# same thresholds it hands to compute_siu_indicators via the SIU test API).
@given(parsers.parse("the late reporting threshold is {value:d} days"))
def set_late_reporting_threshold(context: dict[str, Any], value: int) -> None:
    context["late_reporting_threshold_days"] = value


@given(parsers.parse("the recent policy inception threshold is {value:d} days"))
def set_recent_inception_threshold(context: dict[str, Any], value: int) -> None:
    context["recent_inception_threshold_days"] = value


# Bare form only (no reason code) - shared by triage.feature and the
# non-NOT_EVALUATED assertions in siu_indicators.feature. The "with reason"
# form stays local to the siu acceptance test file since only that spec
# asserts reason codes.
#
# Both compare case-insensitively, and that is a test of the specification
# rather than a tolerance. The acceptance engine substitutes an upper-case TRUE
# with a lower-case `true` and returns before it tries a sibling swap
# (docs/harness-findings.md, "The boolean substitution is lowercase and
# preemptive"), so an exact comparison kills every TRUE/FALSE mutant in these
# two files without ever asking which value was computed - 25 of them across
# triage.feature and siu_indicators.feature, measured. Folding the case turns
# each one into the TRUE-versus-FALSE question the cell was written to ask.
@then(parsers.parse("the late reporting indicator is {expected:w}"))
def check_late_reporting_indicator(context: dict[str, Any], expected: str) -> None:
    assert context["siu_indicators"].late_reporting.value == expected.upper()


@then(parsers.parse("the recent policy inception indicator is {expected:w}"))
def check_recent_inception_indicator(context: dict[str, Any], expected: str) -> None:
    assert context["siu_indicators"].recent_policy_inception.value == expected.upper()


def _rules_entry(context: dict[str, Any], carrier: str) -> dict[str, Any]:
    return context.setdefault("carrier_rules_source", {}).setdefault(carrier, {})


@given(parsers.re(r'^(?:the carrier )?"(?P<carrier>[^"]+)" requires the claimant name$'))
def set_claimant_name_required(context: dict[str, Any], carrier: str) -> None:
    _rules_entry(context, carrier)["claimant_name_required"] = True


@given(parsers.parse('"{carrier}" does not require the claimant contact'))
def set_claimant_contact_not_required(context: dict[str, Any], carrier: str) -> None:
    _rules_entry(context, carrier)["claimant_contact_required"] = False


@given(parsers.parse('"{carrier}" configures a late reporting threshold of {value:d} days'))
def set_carrier_late_reporting_threshold(
    context: dict[str, Any], carrier: str, value: int
) -> None:
    _rules_entry(context, carrier)["late_reporting_threshold_days"] = value


@given(parsers.parse('"{carrier}" has no late reporting threshold configured'))
def clear_late_reporting_threshold(context: dict[str, Any], carrier: str) -> None:
    _rules_entry(context, carrier).pop("late_reporting_threshold_days", None)


@given(
    parsers.parse('"{carrier}" configures a recent policy inception threshold of {value:d} days')
)
def set_carrier_recent_inception_threshold(
    context: dict[str, Any], carrier: str, value: int
) -> None:
    _rules_entry(context, carrier)["recent_inception_threshold_days"] = value


@given(parsers.parse('"{carrier}" configures a duplicate match window of {value:d} days'))
def set_duplicate_match_window(context: dict[str, Any], carrier: str, value: int) -> None:
    _rules_entry(context, carrier)["window_days"] = value


# The three faults a policy source can show, in the words policy_match.feature
# and five locked Backgrounds use. Each holds for the rest of the scenario: the
# locked specs submit more than once under an unavailable source.
@given(
    parsers.re(
        r'^"(?P<carrier>[^"]+)"\'s policy source (?P<fault>is unavailable'
        r"|does not answer within its budget|answers in a shape that is not its own)$"
    )
)
def set_policy_source_fault(context: dict[str, Any], carrier: str, fault: str) -> None:
    context["policy_sources"].fault(carrier, fault)


@given(parsers.parse('the notice is submitted by carrier "{carrier_code}"'))
@when(parsers.parse('the notice is submitted by carrier "{carrier_code}"'))
def set_carrier_code(context: dict[str, Any], carrier_code: str) -> None:
    context["carrier_code"] = carrier_code


@given(parsers.parse('the insured property is in "{value}"'))
def set_property_state(context: dict[str, Any], value: str) -> None:
    """Notice content, not an input: it is reported on the submission like any
    other field and the jurisdiction is selected from it (item 5g). "absent"
    omits it entirely, the convention notice_intake.feature already uses for a
    field that was never supplied - and the one this spec's own Rule 2 row
    varies against a state this deployment has no entry for."""
    context["fields"].pop("property_state", None)
    if value != "absent":
        context["fields"]["property_state"] = value


@given(parsers.parse('the notice is submitted at "{submitted_at}"'))
@when(parsers.parse('the notice is submitted at "{submitted_at}"'))
def set_submitted_at(context: dict[str, Any], submitted_at: str) -> None:
    # Parsed here rather than at submission time so idempotency.feature's
    # "reports its own new receipt timestamp" has an instant to compare
    # against without re-parsing the cell.
    context["submitted_at"] = datetime.fromisoformat(submitted_at.replace("Z", "+00:00"))


@given(parsers.parse('the notice reports a policy number of "{value}"'))
def set_policy_number(context: dict[str, Any], value: str) -> None:
    context["fields"]["policy_number"] = "" if value == "absent" else value


@given(parsers.parse('the notice reports an insured name of "{value}"'))
def set_insured_name(context: dict[str, Any], value: str) -> None:
    # "absent" is None: the field is not on the notice at all, which is also
    # how a notice from before item 7c reads (item 7g).
    context["fields"]["insured_name"] = None if value == "absent" else value


@given(parsers.parse('the notice reports a risk postal code of "{value}"'))
def set_risk_postal_code(context: dict[str, Any], value: str) -> None:
    context["fields"]["risk_postal_code"] = None if value == "absent" else value


@given(parsers.parse('the notice reports a loss date of "{value}"'))
@when(parsers.parse('the notice reports a loss date of "{value}"'))
def set_loss_date(context: dict[str, Any], value: str) -> None:
    """"absent" is None here and deliberately not the empty string, which is the
    one distinction this field's boundary exists to draw: None is read as ABSENT
    and flows on as the domain blocker the notice pends on, while anything that
    is not a date - the empty string included - is UNPARSEABLE, the schema
    refusal that creates no notice at all (item 5h). The other absent
    conventions in this file each pick whichever spelling their own field's
    absent value is; a loss date's is not a date at all, so it is None."""
    context["fields"]["loss_date"] = None if value == "absent" else value


@given(parsers.parse('the notice reports a loss type of "{value}"'))
@when(parsers.parse('the notice reports a loss type of "{value}"'))
def set_loss_type(context: dict[str, Any], value: str) -> None:
    context["fields"]["loss_type"] = value


@given(parsers.parse('the notice reports a notice type of "{value}"'))
def set_notice_type(context: dict[str, Any], value: str) -> None:
    context["fields"]["notice_type"] = value


@given(parsers.parse('the notice is submitted with the idempotency key "{value}"'))
@when(parsers.parse('the notice is submitted with the idempotency key "{value}"'))
def set_idempotency_key(context: dict[str, Any], value: str) -> None:
    # "absent" is the same cell convention notice_intake.feature already uses
    # for a policy number that was never supplied.
    context["idempotency_key"] = None if value == "absent" else value


@given("the notice is submitted for intake")
@when("the notice is submitted for intake")
def submit(context: dict[str, Any]) -> None:
    store = context.setdefault("store", NoticeStore(IN_MEMORY_DATABASE))
    context["response"] = submit_notice(
        store,
        carrier_code=context["carrier_code"],
        submitted_at=context["submitted_at"],
        carrier_identity_reference=CARRIER_IDENTITY_REFERENCE,
        jurisdiction_reference=jurisdiction_map(context),
        carrier_rules_source=rules_source(context),
        bindings_source=policy_bindings(context),
        implementation_registry=context["policy_sources"].registry(),
        fields=NoticeFields(**context["fields"]),
        idempotency_key=context["idempotency_key"],
    )
    # The notice a later step addresses, kept here because a resolution is a
    # second call against the same notice and the response it leaves behind is
    # its own, not the submission's. A refusal that created nothing leaves None,
    # which no spec that refuses then addresses the notice exists to read.
    context["notice_id"] = context["response"].notice_id


@given("that submission is remembered as the original")
def remember_the_original(context: dict[str, Any]) -> None:
    context["original"] = context["response"]


_CARRIER_RULES_FAULT = "carrier rules"
_JURISDICTION_MAP_FAULT = "jurisdiction map"
_POLICY_BINDING_FAULT = "policy binding"


# The fault phrases are character-identical in notice_intake.feature,
# resolution.feature and idempotency.feature, so each binds one definition here
# (docs/harness-findings.md, "Two locked specs sharing a Background can only
# share step definitions through conftest.py"). They record which fault is in
# force rather than corrupting the configuration in place, because
# idempotency.feature sets one and then clears it mid-scenario, and because
# resolution.feature sets one only after intake has already run cleanly.
@given("this deployment is configured correctly")
@when("this deployment is configured correctly")
def clear_deployment_fault(context: dict[str, Any]) -> None:
    context.pop("deployment_fault", None)


@given("the carrier's rules entry cannot be resolved")
def set_carrier_rules_fault(context: dict[str, Any]) -> None:
    context["deployment_fault"] = _CARRIER_RULES_FAULT


@given("the jurisdiction map entry names no usable timezone")
def set_jurisdiction_map_fault(context: dict[str, Any]) -> None:
    context["deployment_fault"] = _JURISDICTION_MAP_FAULT


# The policy a carrier's source holds and its term, and the two verification
# attributes read back, stated in the same words by features/policy_match.feature
# (item 7f) and features/duplicate_evaluation.feature (item 7h), so they moved
# here from the former's module; the rest of the source's shapes and the
# verification's other attributes stay there, as only that spec states them.
@given(
    parsers.re(
        r'^"(?P<carrier>[^"]+)"\'s policy source (?:also )?holds policy "(?P<reference>[^"]+)"'
        r' numbered "(?P<number>[^"]+)" for "(?P<insured>[^"]+)"'
        r' at postal code "(?P<postal_code>[^"]+)"$'
    )
)
def hold_policy(
    context: dict[str, Any], carrier: str, reference: str, number: str, insured: str,
    postal_code: str,
) -> None:
    context["policy_sources"].hold_policy(carrier, reference, number, insured, postal_code)


@given(parsers.parse('that policy has a term effective "{effective}" and expiring "{expiration}"'))
def add_term(context: dict[str, Any], effective: str, expiration: str) -> None:
    context["policy_sources"].add_term(
        date.fromisoformat(effective), date.fromisoformat(expiration)
    )


@then(parsers.re(r"^the notice's policy match is (?P<value>.*)$"))
def check_policy_match(context: dict[str, Any], value: str) -> None:
    # none is a notice nothing searched - no verification at all, a different
    # fact from NOT_MATCHED (item 7g) - read the way the matched-policy step
    # reads the same word.
    if value == "none":
        assert shown_verification(context) is None
    else:
        assert verification(context).policy_match == value


@then(parsers.re(r"^the policy was identified on (?P<value>.*)$"))
def check_identified_on(context: dict[str, Any], value: str) -> None:
    # The two arm names policy_identification.feature spells, or none where
    # nothing matched; compared exactly, as every code in these files is.
    assert verification(context).identified_on == (None if value == "none" else value)


@given("the carrier's policy source binding cannot be resolved")
def set_policy_binding_fault(context: dict[str, Any]) -> None:
    context["deployment_fault"] = _POLICY_BINDING_FAULT


def rules_source(context: dict[str, Any]) -> dict[str, Any]:
    """The per-carrier rules this call is made with. Under the carrier fault the
    administered carrier's own entry is left present but unresolvable - a
    carrier this deployment claims to administer whose rules will not load,
    which is the case notice_intake.feature's Rule 4 sets aside for Rule 5, and
    a different fact from the carrier being absent from the identity
    reference."""
    source = context["carrier_rules_source"]
    if context.get("deployment_fault") != _CARRIER_RULES_FAULT:
        return dict(source)
    carrier = context["carrier_code"]
    return {**source, carrier: {**source[carrier], "window_days": "sixty"}}


def jurisdiction_map(context: dict[str, Any]) -> dict[str, Any]:
    """The jurisdiction map this call is made with. Under the jurisdiction fault
    every entry exists and names no timezone, which is one of the two ways this
    deployment's own map can be unusable; the other - an entry naming a timezone
    this system cannot resolve - reaches the same code and is covered in
    tests/shell/, since one scenario row can only carry one of them."""
    if context.get("deployment_fault") != _JURISDICTION_MAP_FAULT:
        return dict(JURISDICTION_REFERENCE)
    return {code: {} for code in JURISDICTION_REFERENCE}


def policy_bindings(context: dict[str, Any]) -> Any:
    """The port bindings this call is made with (item 7f). Under the binding
    fault the administered carrier has no policy entry at all - a carrier this
    deployment claims to administer and has not bound to any source, which is
    the third row of notice_intake.feature's deployment-fault table."""
    faulted = context.get("deployment_fault") == _POLICY_BINDING_FAULT
    return context["policy_sources"].bindings_source(
        unresolvable_for=context["carrier_code"] if faulted else None
    )


# Stated in the same words by notice_intake.feature and resolution.feature: one
# status carries both faults and the code is the only thing that tells them
# apart, so both files assert it and neither can reword it.
@then(parsers.re(r"^the response names the error (?P<code>.*)$"))
def check_error_code(context: dict[str, Any], code: str) -> None:
    assert context["response"].error == (None if code == "none" else code)


@given(parsers.parse('the reviewer is identified as "{value}"'))
def set_reviewer(context: dict[str, Any], value: str) -> None:
    # "absent" here means no identity in the body at all, which is what makes
    # the body schema-invalid. It is a different absence from a field the
    # reviewer simply did not supply.
    context["reviewer"] = None if value == "absent" else value


@when(parsers.re(r'^the reviewer supplies an? (?P<name>[a-z ]+) of "(?P<value>[^"]*)"$'))
@given(parsers.re(r'^the reviewer supplies an? (?P<name>[a-z ]+) of "(?P<value>[^"]*)"$'))
def supply_field(context: dict[str, Any], name: str, value: str) -> None:
    # "absent" means the field is not in the resolution payload. There is no way
    # to blank a field in phase 2, only to replace one, so it never means
    # cleared - it means this reviewer said nothing about it.
    if name not in _SUPPLIED_FIELDS:
        raise ValueError(f"unrecognized supplied field: {name!r}")
    if value != "absent":
        context.setdefault("supplied", {})[_SUPPLIED_FIELDS[name]] = value


@given(parsers.parse('the reviewer\'s resolution is submitted at "{instant}"'))
@when(parsers.parse('the reviewer\'s resolution is submitted at "{instant}"'))
def submit_resolution(context: dict[str, Any], instant: str) -> None:
    supplied = context.pop("supplied", {})
    context.setdefault("resolutions", []).append(supplied)
    context["response"] = resolve_notice(
        context["store"],
        context.get("named_notice", context["notice_id"]),
        actor_id=context.get("reviewer", _DEFAULT_REVIEWER),
        resolved_at=parse_instant(instant),
        jurisdiction_reference=jurisdiction_map(context),
        carrier_rules_source=rules_source(context),
        bindings_source=policy_bindings(context),
        implementation_registry=context["policy_sources"].registry(),
        supplied=supplied,
    )


@given(parsers.re(r"^the response is (?P<value>\d+)$"))
@then(parsers.re(r"^the response is (?P<value>\d+)$"))
def check_response_status(context: dict[str, Any], value: str) -> None:
    assert context["response"].status == int(value)


@then(parsers.re(r"^the response identifies (?P<phrase>.*)$"))
def check_notice_relation(context: dict[str, Any], phrase: str) -> None:
    identified = context["response"].notice_id
    original = context["original"].notice_id
    if phrase == "the original notice":
        assert identified is not None
        assert identified == original
    elif phrase == "a new notice, not the original":
        assert identified is not None
        assert identified != original
    elif phrase == "no notice at all":
        assert identified is None
    else:
        raise ValueError(f"unrecognized notice relation: {phrase!r}")


@given(parsers.re(r"^the notice's state is (?P<value>.*)$"))
@then(parsers.re(r"^the notice's state is (?P<value>.*)$"))
def check_state(context: dict[str, Any], value: str) -> None:
    # A Given too since item 7h: duplicate_evaluation.feature states that a
    # notice pends before its reviewer's correction triages it, the way
    # check_blockers became a Given at 7g.
    assert context["response"].state == value


@given(parsers.re(r"^the notice's blockers are (?P<value>.*)$"))
@then(parsers.re(r"^the notice's blockers are (?P<value>.*)$"))
def check_blockers(context: dict[str, Any], value: str) -> None:
    # A Given too since item 7g: policy_match.feature states what a notice
    # pends on before its reviewer supplies what it lacked.
    actual = [(b.code, b.field) for b in context["response"].blockers]
    assert actual == parse_compact_blockers(value)


# Stated in the same words by features/siu_separation.feature and
# features/policy_match.feature (item 7f), so it moved here from the former's
# module; the reading has been in support.py since item 5g, shared with
# features/jurisdiction_selection.feature, whose module narrows it to the one
# indicator that spec asserts.
@then(
    parsers.re(
        r"^the (?P<indicator>late reporting|recent policy inception) indicator recorded for "
        r"the notice is (?P<phrase>.*)$"
    )
)
def check_recorded_indicator(context: dict[str, Any], indicator: str, phrase: str) -> None:
    assert_recorded_indicator(context, indicator, phrase)


# The term-history steps features/coverage_verification.feature (item 7a) and
# features/continuous_coverage.feature (item 7b) state in the same words: one
# history, read by two rules, each keeping its own When and Then in its own
# module. "the term" in the three status steps is the term most recently
# stated. Every quoted date goes through date.fromisoformat and nothing else -
# the acceptance engine's marker mutation appends "_gauntlet" to a literal, and
# a step that tolerated one, by defaulting or parsing leniently, would let that
# mutant survive.
@given(parsers.parse('a policy term effective "{effective}" and expiring "{expiration}"'))
def add_policy_term(context: dict[str, Any], effective: str, expiration: str) -> None:
    policy_terms(context).append(
        policy_term(date.fromisoformat(effective), date.fromisoformat(expiration))
    )


@given(parsers.parse('the term was cancelled effective "{effective}"'))
def cancel_term(context: dict[str, Any], effective: str) -> None:
    terms = policy_terms(context)
    terms[-1] = cancelled(terms[-1], date.fromisoformat(effective))


@given(parsers.parse('the term was reinstated effective "{effective}"'))
def reinstate_term(context: dict[str, Any], effective: str) -> None:
    terms = policy_terms(context)
    terms[-1] = reinstated(terms[-1], date.fromisoformat(effective))


@given(parsers.parse('the term was reinstated retroactively as of "{as_of}"'))
def reinstate_term_retroactively(context: dict[str, Any], as_of: str) -> None:
    terms = policy_terms(context)
    terms[-1] = reinstated_retroactively(terms[-1], date.fromisoformat(as_of))


@given(parsers.parse('the policy\'s term history could not be obtained, with reason "{reason}"'))
def set_history_unobtained(context: dict[str, Any], reason: str) -> None:
    context["term_history"] = unobtained_term_history(reason)
