"""The coverage_verifications table: append-only from the database's side and
from the package's, ordered by its own ordinal, read back column for column.
"""

import re
import sqlite3
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from claimgate.domain.continuous_coverage import ContinuousCoverageDerivation
from claimgate.domain.coverage import PolicyTerm, TermInForceDetermination
from claimgate.domain.policy_match import PolicyMatch
from claimgate.shell import coverage_verifications
from claimgate.shell import store as store_module
from claimgate.shell.coverage_verifications import Verification
from claimgate.shell.store import NoticeStore

_RECEIVED_AT = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
_AS_OF = datetime(2026, 6, 1, 11, 58, tzinfo=UTC)
_TERM = PolicyTerm(effective=date(2026, 1, 15), expiration=date(2027, 1, 15))
_MATCHED_IN_FORCE = Verification(
    match=PolicyMatch("MATCHED", policy_reference="POL-88213", identified_on="POLICY_NUMBER"),
    term=TermInForceDetermination("IN_FORCE", term=_TERM),
    coverage=ContinuousCoverageDerivation("DERIVED", continuous_since=date(2024, 1, 15)),
    as_of=_AS_OF,
    binding="AAAA/policy:live-query",
)
_CANCELLED = Verification(
    match=PolicyMatch("MATCHED", policy_reference="POL-88213", identified_on="POLICY_NUMBER"),
    term=TermInForceDetermination(
        "NOT_IN_FORCE", term=_TERM, cancellation_effective=date(2026, 3, 1)
    ),
    coverage=ContinuousCoverageDerivation("NOT_EVALUATED", reason="NO_COVERAGE_ON_LOSS_DATE"),
    as_of=_AS_OF,
    binding="AAAA/policy:live-query",
)
_UNAVAILABLE = Verification(
    match=PolicyMatch("NOT_EVALUATED", reason="SOURCE_UNAVAILABLE"),
    term=TermInForceDetermination("NOT_EVALUATED", reason="SOURCE_UNAVAILABLE"),
    coverage=ContinuousCoverageDerivation("NOT_EVALUATED", reason="SOURCE_UNAVAILABLE"),
    as_of=_AS_OF,
    binding="AAAA/policy:live-query",
)
_WRITES_A_VERIFICATION = (
    re.compile(r"UPDATE\s+coverage_verifications", re.IGNORECASE),
    re.compile(r"DELETE\s+FROM\s+coverage_verifications", re.IGNORECASE),
)


def test_a_verification_cannot_be_updated(store: NoticeStore) -> None:
    _seed(store, _MATCHED_IN_FORCE)

    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        store.connection.execute("UPDATE coverage_verifications SET policy_match = 'NOT_MATCHED'")


def test_a_verification_cannot_be_deleted(store: NoticeStore) -> None:
    _seed(store, _MATCHED_IN_FORCE)

    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        store.connection.execute("DELETE FROM coverage_verifications")


def test_no_statement_in_the_shell_updates_or_deletes_a_verification() -> None:
    # The other half of append-only, read from the package rather than trusted,
    # on tests/shell/test_store.py's pattern for the SIU trail.
    for module in sorted(Path(store_module.__file__).parent.glob("*.py")):
        source = re.sub(r"[\"']|\s+", " ", module.read_text())
        for statement in _WRITES_A_VERIFICATION:
            assert statement.search(source) is None, f"{module.name}: {statement.pattern}"


def test_every_column_reads_back_as_it_was_written(store: NoticeStore) -> None:
    notice_id = _seed(store, _CANCELLED)

    row = coverage_verifications.latest(store, notice_id)

    assert row is not None
    assert (row.notice_id, row.ordinal) == (notice_id, 0)
    assert (row.policy_match, row.policy_reference, row.policy_match_reason) == (
        "MATCHED", "POL-88213", None,
    )
    assert row.identified_on == "POLICY_NUMBER"
    assert (row.term_in_force, row.term_effective, row.term_expiration) == (
        "NOT_IN_FORCE", date(2026, 1, 15), date(2027, 1, 15),
    )
    assert (row.term_reason, row.cancellation_effective) == (None, date(2026, 3, 1))
    assert (row.continuous_coverage, row.continuous_coverage_date) == ("NOT_EVALUATED", None)
    assert row.continuous_coverage_reason == "NO_COVERAGE_ON_LOSS_DATE"
    assert (row.as_of, row.evaluated_at) == (_AS_OF, _RECEIVED_AT)
    assert (row.binding, row.ruleset_version) == ("AAAA/policy:live-query", "2026-01-01")


def test_a_not_evaluated_verification_carries_reasons_and_nothing_else(store: NoticeStore) -> None:
    row = coverage_verifications.latest(store, _seed(store, _UNAVAILABLE))

    assert row is not None
    assert (row.policy_match, row.policy_match_reason, row.policy_reference) == (
        "NOT_EVALUATED", "SOURCE_UNAVAILABLE", None,
    )
    assert (row.term_in_force, row.term_reason, row.term_effective, row.term_expiration) == (
        "NOT_EVALUATED", "SOURCE_UNAVAILABLE", None, None,
    )
    assert (row.continuous_coverage_reason, row.continuous_coverage_date) == (
        "SOURCE_UNAVAILABLE", None,
    )


def test_a_notices_rows_continue_its_own_order_and_the_latest_is_the_highest(
    store: NoticeStore,
) -> None:
    notice_id = _seed(store, _UNAVAILABLE)
    with store.submission():
        coverage_verifications.append(
            store, notice_id, _MATCHED_IN_FORCE, ruleset_version="2026-01-02",
            evaluated_at=_RECEIVED_AT,
        )

    trail = coverage_verifications.for_notice(store, notice_id)
    latest = coverage_verifications.latest(store, notice_id)

    assert [row.ordinal for row in trail] == [0, 1]
    assert [row.policy_match for row in trail] == ["NOT_EVALUATED", "MATCHED"]
    assert latest is not None and latest.ordinal == 1


def test_a_notice_with_no_verification_has_none_and_an_empty_trail(store: NoticeStore) -> None:
    notice_id = _receive(store)

    assert coverage_verifications.latest(store, notice_id) is None
    assert coverage_verifications.for_notice(store, notice_id) == ()
    assert coverage_verifications.view_of(None) is None


def test_the_stored_row_becomes_the_domains_own_results_again(store: NoticeStore) -> None:
    # What the resolution path re-asserts: the match and the derivation, as the
    # domain types the rules take, equal to what intake computed.
    row = coverage_verifications.latest(store, _seed(store, _MATCHED_IN_FORCE))

    assert row is not None
    assert coverage_verifications.match_of(row) == _MATCHED_IN_FORCE.match
    assert coverage_verifications.derivation_of(row) == _MATCHED_IN_FORCE.coverage


def _receive(store: NoticeStore, notice_id: str = "notice-1") -> str:
    with store.submission():
        store.receive_notice(notice_id, "AAAA", {"policy_number": "HO-4471209"}, _RECEIVED_AT)
    return notice_id


def _seed(store: NoticeStore, verification: Verification) -> str:
    notice_id = _receive(store)
    with store.submission():
        coverage_verifications.append(
            store, notice_id, verification, ruleset_version="2026-01-01", evaluated_at=_RECEIVED_AT
        )
    return notice_id
