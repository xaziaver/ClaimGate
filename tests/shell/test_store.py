"""Unit tests for the schema's own guarantees.

Nothing here goes through notice_intake: these assert what schema.py declares
rather than what any caller does with it. No acceptance scenario can reach any
of it - a spec names no table, no column and no constraint - and code mutation
does not reach src/claimgate/shell/ at all, so if these do not assert it,
nothing does.
"""

import re
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest

from claimgate.domain.models import SiuIndicatorResult
from claimgate.shell import store as store_module
from claimgate.shell.records import SiuIndicatorObservation
from claimgate.shell.store import NoticeStore

_RECEIVED_AT = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
_PAYLOAD = {"policy_number": "HO-1234567"}
_EVALUATED_AT = datetime(2026, 6, 2, 9, 0, tzinfo=UTC)
_LATE_REPORTING_FIRED = SiuIndicatorObservation("late_reporting", SiuIndicatorResult("TRUE"), 45)
_INCEPTION_UNEVALUATED = SiuIndicatorObservation(
    "recent_policy_inception", SiuIndicatorResult("NOT_EVALUATED", "NO_CONTINUOUS_COVERAGE_DATE"),
    None,
)
_WRITES_AN_SIU_EVENT = (
    re.compile(r"UPDATE\s+siu_indicator_events", re.IGNORECASE),
    re.compile(r"DELETE\s+FROM\s+siu_indicator_events", re.IGNORECASE),
)


def _seed_notice(store: NoticeStore, notice_id: str = "notice-1") -> str:
    with store.submission():
        store.receive_notice(notice_id, "AAAA", _PAYLOAD, _RECEIVED_AT)
    return notice_id


def test_an_audit_entry_cannot_be_updated(store: NoticeStore) -> None:
    _seed_notice(store)

    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        _execute(store, "UPDATE audit_entries SET to_state = 'TRIAGED'")


def test_an_audit_entry_cannot_be_deleted(store: NoticeStore) -> None:
    _seed_notice(store)

    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        _execute(store, "DELETE FROM audit_entries")


def test_a_payload_record_cannot_be_updated(store: NoticeStore) -> None:
    _seed_notice(store)

    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        _execute(store, "UPDATE payload_records SET reference = 'rewritten'")


def test_a_payload_record_cannot_be_deleted(store: NoticeStore) -> None:
    _seed_notice(store)

    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        _execute(store, "DELETE FROM payload_records")


def test_a_notice_may_still_move_state_the_audit_trail_is_the_history(store: NoticeStore) -> None:
    # The append-only triggers are on the audit and payload tables only. A
    # notice's own row legitimately moves RECEIVED -> TRIAGED; forbidding that
    # would forbid the state model.
    notice_id = _seed_notice(store)
    with store.submission():
        store.record_decision(
            notice_id, state="TRIAGED", blockers=(), severity="LOW", queue="STANDARD",
            occurred_at=_RECEIVED_AT,
        )

    record = store.get_notice(notice_id)
    assert record is not None
    assert record.state == "TRIAGED"
    assert len(store.get_audit_trail(notice_id)) == 2


def test_a_decision_that_lands_in_pended_stamps_the_pend_instant(store: NoticeStore) -> None:
    notice_id = _seed_notice(store)
    with store.submission():
        store.record_decision(
            notice_id, state="PENDED", blockers=(), severity=None, queue=None,
            occurred_at=_RECEIVED_AT,
        )

    record = store.get_notice(notice_id)
    assert record is not None
    assert record.pended_at == _RECEIVED_AT
    assert record.resolved_at is None


def test_a_decision_that_lands_in_triaged_stamps_neither_instant(store: NoticeStore) -> None:
    notice_id = _seed_notice(store)
    with store.submission():
        store.record_decision(
            notice_id, state="TRIAGED", blockers=(), severity="standard", queue="standard",
            occurred_at=_RECEIVED_AT,
        )

    record = store.get_notice(notice_id)
    assert record is not None
    assert record.pended_at is None
    assert record.resolved_at is None


def test_an_instant_already_stamped_is_never_replaced_by_a_later_write(
    store: NoticeStore,
) -> None:
    # Item 5e decision (a): pended_at is written once and never rewritten. The
    # COALESCE is what enforces it, so a second write naming a different instant
    # has to leave the first one standing.
    notice_id = _seed_notice(store)
    later = datetime(2026, 8, 25, 9, 0, tzinfo=UTC)
    with store.submission():
        store.write_notice_decision(
            notice_id, state="PENDED", blockers=(), severity=None, queue=None,
            pended_at=_RECEIVED_AT, resolved_at=None,
        )
        store.write_notice_decision(
            notice_id, state="PENDED", blockers=(), severity=None, queue=None,
            pended_at=later, resolved_at=None,
        )

    record = store.get_notice(notice_id)
    assert record is not None
    assert record.pended_at == _RECEIVED_AT


def test_a_payload_record_keeps_what_arrived_in_it_verbatim(store: NoticeStore) -> None:
    # PHASE2_DESIGN.md stores the payload "verbatim ... and referenced by hash".
    # The hash alone cannot be overlaid, which is what a notice's current view
    # is derived by doing.
    _seed_notice(store)

    record = store.list_payloads()[0]
    assert record.content == _PAYLOAD
    assert record.arrival_index == 0


def test_an_siu_indicator_event_cannot_be_updated(store: NoticeStore) -> None:
    _seed_events(store)

    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        _execute(store, "UPDATE siu_indicator_events SET value = 'FALSE'")


def test_an_siu_indicator_event_cannot_be_deleted(store: NoticeStore) -> None:
    _seed_events(store)

    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        _execute(store, "DELETE FROM siu_indicator_events")


def test_no_statement_in_the_shell_updates_or_deletes_an_siu_indicator_event() -> None:
    """The triggers above refuse both from the database's side. This asserts the
    other half of ASSUMPTIONS.md's item 5f decision 3 - "no code path for
    either" - by reading the package rather than by trusting that nobody added
    one. Quotes and line breaks are collapsed first, so a statement split across
    adjacent string literals is found the same as one written on a single line.
    """
    for module in sorted(Path(store_module.__file__).parent.glob("*.py")):
        source = re.sub(r"[\"']|\s+", " ", module.read_text())
        for statement in _WRITES_AN_SIU_EVENT:
            assert statement.search(source) is None, f"{module.name}: {statement.pattern}"


def test_a_notices_siu_events_come_back_in_the_order_they_were_written(
    store: NoticeStore,
) -> None:
    # The ordinal is the notice's own arrival order, so a second evaluation
    # continues it rather than restarting - the read is by stored position, not
    # by insertion order.
    notice_id = _seed_events(store)
    with store.submission():
        store.append_siu_events(
            notice_id, (_LATE_REPORTING_FIRED,),
            ruleset_version="2026-01-01", evaluated_at=_EVALUATED_AT,
        )

    events = store.get_siu_events(notice_id)
    assert [event.ordinal for event in events] == [0, 1, 2]
    assert [event.indicator for event in events[:2]] == ["late_reporting", "recent_policy_inception"]
    assert events[2].ruleset_version == "2026-01-01"


def test_an_siu_event_records_no_threshold_rather_than_a_zero_where_none_was_configured(
    store: NoticeStore,
) -> None:
    # A configured zero is a real carrier choice that makes every notice late
    # (carrier_configuration.feature), so an absent threshold has to come back
    # as absent and never as zero.
    _seed_events(store)

    fired, unevaluated = store.list_siu_events()
    assert (fired.value, fired.reason_code, fired.threshold_days) == ("TRUE", None, 45)
    assert unevaluated.value == "NOT_EVALUATED"
    assert unevaluated.reason_code == "NO_CONTINUOUS_COVERAGE_DATE"
    assert unevaluated.threshold_days is None
    assert unevaluated.evaluated_at == _EVALUATED_AT


def _seed_events(store: NoticeStore, notice_id: str = "notice-1") -> str:
    _seed_notice(store, notice_id)
    with store.submission():
        store.append_siu_events(
            notice_id, (_LATE_REPORTING_FIRED, _INCEPTION_UNEVALUATED),
            ruleset_version="2026-08-25", evaluated_at=_EVALUATED_AT,
        )
    return notice_id


def _execute(store: NoticeStore, statement: str) -> None:
    """Reaches past the store's own surface on purpose: the point of these
    tests is that the schema refuses writes no method here offers."""
    store._connection.execute(statement)
