"""Unit tests for the schema's own guarantees.

Nothing here goes through notice_intake: these assert what schema.py declares
rather than what any caller does with it. No acceptance scenario can reach any
of it - a spec names no table, no column and no constraint - and code mutation
does not reach src/claimgate/shell/ at all, so if these do not assert it,
nothing does.
"""

import sqlite3
from datetime import UTC, datetime

import pytest

from claimgate.shell.store import NoticeStore

_RECEIVED_AT = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
_PAYLOAD = {"policy_number": "HO-1234567"}


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


def _execute(store: NoticeStore, statement: str) -> None:
    """Reaches past the store's own surface on purpose: the point of these
    tests is that the schema refuses writes no method here offers."""
    store._connection.execute(statement)
