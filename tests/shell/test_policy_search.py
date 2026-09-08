"""The intake path's policy search (item 7f): what the verification records
beside the decision, how its answer reaches the rules and the SIU evaluation,
what is not searched at all, and what the resolution path re-asserts.

These live under tests/shell/ because code mutation reaches none of the shell
(conftest.py); for shell/policy_match.py, shell/coverage_verifications.py and
the wiring in notice_intake.py and resolution_evaluation.py, they and
features/policy_match.feature are the whole of the protection.
"""

from dataclasses import replace
from datetime import date

import pytest

from claimgate.domain.ruleset import RULESET_VERSION
from claimgate.shell import coverage_verifications
from claimgate.shell.faults import PORT_BINDING_UNRESOLVABLE
from claimgate.shell.notice_intake import get_notice
from claimgate.shell.store import NoticeStore
from tests.api.policy_match import PolicySources, bound_sources
from tests.fixtures.core_system import FixtureAddress
from tests.shell.support import (
    DEFAULT_FIELDS,
    DEFAULT_SUBMITTED_AT,
    PENDING_FIELDS,
    Resolver,
    Submitter,
)

REFERENCE = "POL-31007"
OTHER_REFERENCE = "POL-31008"
INSURED = "Dana Alvarez"
POSTAL_CODE = "34102"
LIVE_QUERY_LABEL = "AAAA/policy:live-query"
# DEFAULT_FIELDS' loss is 2026-06-01: twelve days after the first inception,
# 151 after the second, against VALID_RULES' 30-day threshold.
RECENT_INCEPTION = date(2026, 5, 20)
OLD_INCEPTION = date(2026, 1, 1)
EXPIRATION = date(2027, 1, 1)
_INJURY = replace(DEFAULT_FIELDS, loss_type="injury")
_NO_LOSS_DATE = replace(DEFAULT_FIELDS, loss_date=None)


def holding(
    effective: date = OLD_INCEPTION, *, number: str = DEFAULT_FIELDS.policy_number
) -> PolicySources:
    sources = bound_sources(["AAAA"])
    sources.hold_policy("AAAA", REFERENCE, number, INSURED, POSTAL_CODE)
    sources.add_term(effective, EXPIRATION)
    return sources


def test_a_matched_policy_in_force_triages_and_records_the_verification_with_the_decision(
    store: NoticeStore, submit: Submitter
) -> None:
    response = submit(policy_sources=holding())

    assert (response.status, response.state, response.blockers) == (201, "TRIAGED", ())
    row = _only_verification(store, response.notice_id)
    assert (row.policy_match, row.policy_reference, row.policy_match_reason) == (
        "MATCHED", REFERENCE, None,
    )
    assert (row.term_in_force, row.term_effective, row.term_expiration) == (
        "IN_FORCE", OLD_INCEPTION, EXPIRATION,
    )
    assert (row.term_reason, row.cancellation_effective) == (None, None)
    assert (row.continuous_coverage, row.continuous_coverage_date) == ("DERIVED", OLD_INCEPTION)
    # The live-query shape stamps the binding's clock, which on this path is the
    # submission instant; the row and the events beside it carry the same label.
    assert (row.as_of, row.evaluated_at) == (DEFAULT_SUBMITTED_AT, DEFAULT_SUBMITTED_AT)
    assert (row.binding, row.ruleset_version, row.ordinal) == (LIVE_QUERY_LABEL, RULESET_VERSION, 0)


@pytest.mark.parametrize(
    ("effective", "recent"), [(RECENT_INCEPTION, "TRUE"), (OLD_INCEPTION, "FALSE")]
)
def test_the_recent_inception_indicator_reads_the_date_the_history_yielded(
    store: NoticeStore, submit: Submitter, effective: date, recent: str
) -> None:
    # The first producer of the continuous-coverage date: until this item the
    # indicator was NOT_EVALUATED on every real notice.
    response = submit(policy_sources=holding(effective))

    assert _recent_inception(store, response.notice_id) == (recent, None)


def test_a_number_the_source_does_not_hold_pends_on_policy_not_matched(
    store: NoticeStore, submit: Submitter
) -> None:
    response = submit(policy_sources=holding(number="HO-7654321"))

    assert (response.status, response.state) == (201, "PENDED")
    assert [(b.code, b.field) for b in response.blockers] == [("POLICY_NOT_MATCHED", "")]
    row = _only_verification(store, response.notice_id)
    assert (row.policy_match, row.policy_reference) == ("NOT_MATCHED", None)
    # Nothing about the term or the date is derived from a policy nobody found;
    # both say why instead.
    assert (row.term_in_force, row.term_reason) == ("NOT_EVALUATED", "POLICY_NOT_MATCHED")
    assert (row.continuous_coverage, row.continuous_coverage_reason) == (
        "NOT_EVALUATED", "POLICY_NOT_MATCHED",
    )
    assert store.get_siu_events(_id(response.notice_id)) == ()


def test_a_number_on_two_policies_pends_on_policy_ambiguous(
    store: NoticeStore, submit: Submitter
) -> None:
    sources = holding()
    sources.hold_policy("AAAA", OTHER_REFERENCE, DEFAULT_FIELDS.policy_number, INSURED, POSTAL_CODE)

    response = submit(policy_sources=sources)

    assert response.state == "PENDED"
    assert [(b.code, b.field) for b in response.blockers] == [("POLICY_AMBIGUOUS", "")]
    row = _only_verification(store, response.notice_id)
    assert (row.policy_match, row.policy_reference, row.term_reason) == (
        "AMBIGUOUS", None, "POLICY_AMBIGUOUS",
    )


def test_a_source_fault_triages_with_the_verification_not_evaluated_and_its_reason(
    store: NoticeStore, submit: Submitter
) -> None:
    # The fixture default: every carrier bound, every call failing - the same
    # statement five locked specs make in their Backgrounds.
    response = submit()

    assert (response.status, response.state, response.blockers) == (201, "TRIAGED", ())
    row = _only_verification(store, response.notice_id)
    assert (row.policy_match, row.policy_match_reason) == ("NOT_EVALUATED", "SOURCE_UNAVAILABLE")
    assert (row.term_in_force, row.term_reason) == ("NOT_EVALUATED", "SOURCE_UNAVAILABLE")
    assert (row.continuous_coverage_date, row.continuous_coverage_reason) == (
        None, "SOURCE_UNAVAILABLE",
    )
    # The indicator learns that there is no date, not why (7f decision 5).
    assert _recent_inception(store, response.notice_id) == (
        "NOT_EVALUATED", "NO_CONTINUOUS_COVERAGE_DATE",
    )


def test_a_history_answered_in_a_shape_that_is_not_its_own_leaves_the_match_and_not_the_term(
    store: NoticeStore, submit: Submitter
) -> None:
    # The search succeeds and the second call does not: a term that is not the
    # wire shape parses as SOURCE_MALFORMED on the history alone.
    sources = holding()
    sources.system("AAAA").hold_policy(
        REFERENCE, DEFAULT_FIELDS.policy_number, [INSURED], _address(), [{"garbage": True}]
    )

    response = submit(policy_sources=sources)

    assert response.state == "TRIAGED"
    row = _only_verification(store, response.notice_id)
    assert (row.policy_match, row.policy_reference) == ("MATCHED", REFERENCE)
    assert (row.term_in_force, row.term_reason) == ("NOT_EVALUATED", "SOURCE_MALFORMED")
    assert (row.continuous_coverage, row.continuous_coverage_reason) == (
        "NOT_EVALUATED", "SOURCE_MALFORMED",
    )


def test_the_search_runs_on_a_notice_that_pends_for_another_reason(
    store: NoticeStore, submit: Submitter
) -> None:
    # 7f decision 4: the reviewer clearing the missing field sees the match
    # beside it, and the port call was spent once, at intake.
    response = submit(policy_sources=holding(), fields=_INJURY)

    assert response.state == "PENDED"
    assert [(b.code, b.field) for b in response.blockers] == [
        ("MISSING_REQUIRED_FIELD", "incident_description")
    ]
    row = _only_verification(store, response.notice_id)
    assert (row.policy_match, row.term_in_force) == ("MATCHED", "IN_FORCE")


@pytest.mark.parametrize(
    ("fields", "blocker"),
    [(PENDING_FIELDS, "policy_number"), (_NO_LOSS_DATE, "loss_date")],
    ids=["no policy number", "no loss date"],
)
def test_a_notice_that_cannot_be_verified_is_not_searched_and_pends_on_validation_alone(
    store: NoticeStore, submit: Submitter, fields: object, blocker: str
) -> None:
    # An empty, available source: had the search run, the notice would carry
    # POLICY_NOT_MATCHED beside the missing field and a row saying so. It
    # carries neither (shell/policy_match.py's module docstring).
    response = submit(policy_sources=bound_sources(["AAAA"]), fields=fields)  # type: ignore[arg-type]

    assert response.state == "PENDED"
    assert [(b.code, b.field) for b in response.blockers] == [("MISSING_REQUIRED_FIELD", blocker)]
    assert coverage_verifications.for_notice(store, _id(response.notice_id)) == ()
    view = get_notice(store, _id(response.notice_id))
    assert view is not None and view.coverage_verification is None


def test_an_unbound_carrier_is_receipted_as_our_defect_and_creates_no_notice(
    store: NoticeStore, submit: Submitter
) -> None:
    # Item 5i's pattern, applied to the third configuration lookup: the payload
    # is kept with the fault's code, and nothing else exists - no notice, no
    # key, so an identical retry creates a notice once the binding is fixed.
    response = submit(policy_sources=bound_sources([]), idempotency_key="K-7f")

    assert (response.status, response.error, response.notice_id) == (
        500, PORT_BINDING_UNRESOLVABLE, None,
    )
    assert response.reference is not None
    assert store.count_notices() == 0
    payloads = store.list_payloads()
    assert [(p.notice_id, p.error_code) for p in payloads] == [(None, PORT_BINDING_UNRESOLVABLE)]
    assert store.find_key("AAAA", "K-7f") is None


def test_get_notice_shows_the_latest_verification_and_none_before_any_search(
    store: NoticeStore, submit: Submitter, rule_evaluation_raises: None
) -> None:
    # The receipt survives a failing evaluation with no decision and no
    # verification: the view says nothing was searched, not that nothing was found.
    with pytest.raises(RuntimeError):
        submit(policy_sources=holding())

    notice_id = _id(store.list_payloads()[0].notice_id)
    view = get_notice(store, notice_id)
    assert view is not None
    assert (view.state, view.coverage_verification) == ("RECEIVED", None)


def test_the_view_names_the_verification_as_the_spec_reads_it(
    store: NoticeStore, submit: Submitter
) -> None:
    response = submit(policy_sources=holding(RECENT_INCEPTION))

    view = get_notice(store, _id(response.notice_id))
    assert view is not None and view.coverage_verification is not None
    shown = view.coverage_verification
    assert (shown.policy_match, shown.matched_policy, shown.reason) == ("MATCHED", REFERENCE, None)
    assert (shown.term_in_force, shown.deciding_term_effective, shown.deciding_term_expiration) == (
        "IN_FORCE", RECENT_INCEPTION, EXPIRATION,
    )
    assert (shown.continuous_coverage_date, shown.continuous_coverage_reason) == (
        RECENT_INCEPTION, None,
    )
    assert shown.as_of == DEFAULT_SUBMITTED_AT


def test_correcting_an_unrelated_field_does_not_clear_an_unmatched_policy(
    store: NoticeStore, submit: Submitter, resolve: Resolver
) -> None:
    # 7f decision 6: the resolution path re-asserts the stored match and
    # searches nothing, so only 7g's re-search on the corrected identifiers can
    # clear this pend. No new row: nothing new was verified.
    notice_id = _id(submit(policy_sources=holding(number="HO-7654321")).notice_id)

    response = resolve(notice_id, supplied={"claimant_name": "Ruth Alvarez"})

    assert (response.status, response.state) == (422, "PENDED")
    assert [(b.code, b.field) for b in response.blockers] == [("POLICY_NOT_MATCHED", "")]
    assert len(coverage_verifications.for_notice(store, notice_id)) == 1


def test_a_release_reads_the_stored_coverage_date_for_its_siu_evaluation(
    store: NoticeStore, submit: Submitter, resolve: Resolver
) -> None:
    # The date the intake search yielded travels onto the resolution's
    # candidate through the same producer, so the indicator a release owes is
    # evaluated rather than NOT_EVALUATED for want of a date it already has.
    notice_id = _id(submit(policy_sources=holding(RECENT_INCEPTION), fields=_INJURY).notice_id)

    response = resolve(notice_id, supplied={"incident_description": "Fall on the front steps"})

    assert (response.status, response.state) == (200, "TRIAGED")
    assert _recent_inception(store, notice_id) == ("TRUE", None)
    assert len(coverage_verifications.for_notice(store, notice_id)) == 1


def _only_verification(
    store: NoticeStore, notice_id: str | None
) -> coverage_verifications.CoverageVerification:
    rows = coverage_verifications.for_notice(store, _id(notice_id))
    assert len(rows) == 1
    return rows[0]


def _recent_inception(store: NoticeStore, notice_id: str | None) -> tuple[str, str | None]:
    events = [
        event
        for event in store.get_siu_events(_id(notice_id))
        if event.indicator == "recent_policy_inception"
    ]
    assert len(events) == 1
    return events[0].value, events[0].reason_code


def _id(notice_id: str | None) -> str:
    assert notice_id is not None
    return notice_id


def _address() -> FixtureAddress:
    return FixtureAddress("4140 Bayshore Loop", "North Port", "FL", POSTAL_CODE)
