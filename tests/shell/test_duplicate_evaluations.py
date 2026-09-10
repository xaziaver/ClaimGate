"""The duplicate_evaluations table and the evaluation that fills it (item 7h):
append-only from the database's side, ordered by its own ordinal, read back
column for column; the evaluation's two branches and its one translation; the
transition it belongs to; and the claims binding a submission now needs.
"""

import sqlite3
from dataclasses import replace
from datetime import UTC, date, datetime

import pytest

from claimgate.domain.continuous_coverage import ContinuousCoverageDerivation
from claimgate.domain.coverage import TermInForceDetermination
from claimgate.domain.models import Candidate, ExistingClaim
from claimgate.domain.policy_match import PolicyMatch
from claimgate.shell import duplicate_evaluations
from claimgate.shell.coverage_verifications import Verification
from claimgate.shell.duplicate_evaluations import (
    NOT_EVALUATED,
    OBTAINED,
    DuplicateEvaluation,
    DuplicateEvaluationView,
)
from claimgate.shell.faults import PORT_BINDING_UNRESOLVABLE
from claimgate.shell.notice_intake import get_notice, submit_notice
from claimgate.shell.ports import NOT_OBTAINED, ExistingClaimsAnswer
from claimgate.shell.store import NoticeStore
from tests.api.policy_match import bound_sources, policy_entry
from tests.shell.support import (
    DEFAULT_FIELDS,
    DEFAULT_SUBMITTED_AT,
    IDENTITY_REFERENCE,
    JURISDICTIONS,
    VALID_RULES,
    Submitter,
)

_RECEIVED_AT = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
_AS_OF = datetime(2026, 6, 1, 11, 58, tzinfo=UTC)
_CLAIMS_AS_OF = datetime(2026, 6, 1, 11, 59, tzinfo=UTC)
_BINDING = "AAAA/claims:live-query"
_MATCHED = Verification(
    match=PolicyMatch("MATCHED", policy_reference="POL-88213", identified_on="POLICY_NUMBER"),
    term=TermInForceDetermination("IN_FORCE"),
    coverage=ContinuousCoverageDerivation("DERIVED", continuous_since=date(2026, 1, 15)),
    as_of=_AS_OF,
    binding="AAAA/policy:live-query",
    policy_number="HO-4471209",
)
_UNANSWERED = Verification(
    match=PolicyMatch("NOT_EVALUATED", reason="SOURCE_TIMEOUT"),
    term=TermInForceDetermination("NOT_EVALUATED", reason="SOURCE_TIMEOUT"),
    coverage=ContinuousCoverageDerivation("NOT_EVALUATED", reason="SOURCE_TIMEOUT"),
    as_of=_AS_OF,
    binding="AAAA/policy:live-query",
)
# The notice typed a wrong number; the search found the policy on the pair.
_CANDIDATE = Candidate(
    policy_number="HO-4471290", loss_date=date(2026, 6, 1), loss_type="wind_hail",
    notice_type="INITIAL",
)
_ON_THE_FOUND_POLICY = ExistingClaim("CLM-1001", "HO-4471209", date(2026, 5, 20), "wind_hail")
_OBTAINED_ROW = DuplicateEvaluation(OBTAINED, ("CLM-1001",), None, _CLAIMS_AS_OF, _BINDING)


class _RecordingClaimsPort:
    def __init__(self, answer: ExistingClaimsAnswer) -> None:
        self.answer = answer
        self.asked: list[str] = []

    def existing_claims(self, policy_reference: str) -> ExistingClaimsAnswer:
        self.asked.append(policy_reference)
        return self.answer


def _obtained(*claims: ExistingClaim) -> _RecordingClaimsPort:
    return _RecordingClaimsPort(
        ExistingClaimsAnswer(value="OBTAINED", claims=claims, as_of=_CLAIMS_AS_OF, binding=_BINDING)
    )


# -- the evaluation ------------------------------------------------------------


def test_a_matched_notice_is_compared_against_the_found_policys_claims_by_its_number() -> None:
    # Decision 4: the claims come back for the reference, and the rule
    # compares numbers, so the found number goes onto the candidate - the
    # typed HO-4471290 would read clean against a claim on HO-4471209.
    port = _obtained(_ON_THE_FOUND_POLICY)

    evaluation = duplicate_evaluations.evaluate_duplicates(port, _MATCHED, _CANDIDATE, 60)

    assert port.asked == ["POL-88213"]
    assert evaluation == _OBTAINED_ROW


def test_the_rules_own_refusal_passes_through_with_its_reason() -> None:
    # Decision 3: FOLLOW_ON_NOTICE_TYPE is the domain's word and reaches the
    # row unchanged; the port was still asked, since the rule decides.
    port = _obtained(_ON_THE_FOUND_POLICY)

    evaluation = duplicate_evaluations.evaluate_duplicates(
        port, _MATCHED, replace(_CANDIDATE, notice_type="SUPPLEMENTAL"), 60
    )

    assert evaluation == DuplicateEvaluation(
        NOT_EVALUATED, (), "FOLLOW_ON_NOTICE_TYPE", _CLAIMS_AS_OF, _BINDING
    )


def test_claims_that_could_not_be_read_leave_the_evaluation_not_evaluated_with_that_reason() -> None:
    port = _RecordingClaimsPort(
        ExistingClaimsAnswer(
            value=NOT_OBTAINED, reason="SOURCE_MALFORMED", as_of=_CLAIMS_AS_OF, binding=_BINDING
        )
    )

    evaluation = duplicate_evaluations.evaluate_duplicates(port, _MATCHED, _CANDIDATE, 60)

    assert evaluation == DuplicateEvaluation(
        NOT_EVALUATED, (), "SOURCE_MALFORMED", _CLAIMS_AS_OF, _BINDING
    )


def test_a_search_that_did_not_answer_is_not_followed_by_a_claims_call() -> None:
    # Decision 9: the evaluation follows the verification beside it; with no
    # found policy there is nothing to ask about, and the search's own
    # reason, instant and binding are what the row carries.
    port = _obtained(_ON_THE_FOUND_POLICY)

    evaluation = duplicate_evaluations.evaluate_duplicates(port, _UNANSWERED, _CANDIDATE, 60)

    assert port.asked == []
    assert evaluation == DuplicateEvaluation(
        NOT_EVALUATED, (), "SOURCE_TIMEOUT", _AS_OF, "AAAA/policy:live-query"
    )


def test_only_a_triaged_decision_is_evaluated() -> None:
    port = _obtained(_ON_THE_FOUND_POLICY)

    pended = duplicate_evaluations.evaluate_on_triage("PENDED", port, _MATCHED, _CANDIDATE, 60)
    triaged = duplicate_evaluations.evaluate_on_triage("TRIAGED", port, _MATCHED, _CANDIDATE, 60)

    assert pended is None
    assert port.asked == ["POL-88213"]
    assert triaged == _OBTAINED_ROW


# -- the table -------------------------------------------------------------------


def test_an_evaluation_cannot_be_updated_or_deleted(store: NoticeStore) -> None:
    _seed(store, _OBTAINED_ROW)

    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        store.connection.execute("UPDATE duplicate_evaluations SET status = 'NOT_EVALUATED'")
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        store.connection.execute("DELETE FROM duplicate_evaluations")


def test_a_notices_trail_is_ordered_and_the_latest_row_is_what_the_view_shows(
    store: NoticeStore,
) -> None:
    _seed(store, _OBTAINED_ROW)
    later = DuplicateEvaluation(NOT_EVALUATED, (), "SOURCE_UNAVAILABLE", _CLAIMS_AS_OF, _BINDING)
    _seed(store, later)

    latest = duplicate_evaluations.latest(store, "notice-1")

    assert latest is not None
    assert (latest.ordinal, latest.status, latest.reason) == (1, NOT_EVALUATED, "SOURCE_UNAVAILABLE")
    assert latest.candidates == ()
    assert (latest.as_of, latest.binding) == (_CLAIMS_AS_OF, _BINDING)
    assert (latest.ruleset_version, latest.evaluated_at) == ("test", _RECEIVED_AT)
    assert duplicate_evaluations.view_of(latest) == DuplicateEvaluationView(
        NOT_EVALUATED, (), "SOURCE_UNAVAILABLE"
    )
    assert duplicate_evaluations.view_of(None) is None


def test_candidates_round_trip_as_an_ordered_tuple(store: NoticeStore) -> None:
    two = replace(_OBTAINED_ROW, candidates=("CLM-1001", "CLM-1002"))
    _seed(store, two)

    latest = duplicate_evaluations.latest(store, "notice-1")

    assert latest is not None
    assert latest.candidates == ("CLM-1001", "CLM-1002")


def test_an_untriaged_notice_shows_no_evaluation(store: NoticeStore, submit: Submitter) -> None:
    # The default sources are unavailable, so the search is NOT_EVALUATED and
    # the notice triages; the evaluation follows with the search's reason.
    # A notice that pends shows none at all - not a clean result.
    triaged = submit()
    pended = submit(fields=replace(DEFAULT_FIELDS, loss_type="injury"))

    shown = get_notice(store, str(triaged.notice_id))
    unshown = get_notice(store, str(pended.notice_id))

    assert shown is not None and unshown is not None
    assert shown.duplicate_evaluation == DuplicateEvaluationView(
        NOT_EVALUATED, (), "SOURCE_UNAVAILABLE"
    )
    assert unshown.duplicate_evaluation is None


def test_a_carrier_with_no_claims_entry_is_the_same_deployment_fault_as_one_with_no_policy_entry(
    store: NoticeStore,
) -> None:
    # Decision 11: both ports resolve at receipt, so a bindings file naming a
    # policy source and no claims source is item 5i's 500 with no notice.
    sources = bound_sources(["AAAA"])

    response = submit_notice(
        store,
        carrier_code="AAAA",
        submitted_at=DEFAULT_SUBMITTED_AT,
        carrier_identity_reference=IDENTITY_REFERENCE,
        jurisdiction_reference=JURISDICTIONS,
        carrier_rules_source={"AAAA": VALID_RULES},
        bindings_source={"AAAA": {"policy": policy_entry("AAAA")}},
        implementation_registry=sources.registry(),
        fields=DEFAULT_FIELDS,
    )

    assert (response.status, response.error, response.notice_id) == (
        500, PORT_BINDING_UNRESOLVABLE, None
    )
    assert store.count_notices() == 0
    assert [(p.notice_id, p.error_code) for p in store.list_payloads()] == [
        (None, PORT_BINDING_UNRESOLVABLE)
    ]


def _seed(store: NoticeStore, evaluation: DuplicateEvaluation) -> None:
    if store.get_notice("notice-1") is None:
        with store.submission():
            store.receive_notice("notice-1", "AAAA", {"policy_number": "HO-4471209"}, _RECEIVED_AT)
    with store.submission():
        duplicate_evaluations.append(
            store, "notice-1", evaluation, ruleset_version="test", evaluated_at=_RECEIVED_AT
        )
