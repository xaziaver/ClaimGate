"""Unit tests for the idempotency paths no scenario can reach.

features/idempotency.feature proves what a caller observes. These prove what it
leaves behind, and the one path a single-writer synchronous suite cannot stage
at all: the constraint refusing a concurrent identical submission.
"""

import sqlite3
from collections.abc import Callable
from datetime import timedelta

import pytest

from claimgate.shell.idempotency import KEY_LIFETIME
from claimgate.shell.messages import NoticeFields
from claimgate.shell.records import NoticeRecord
from claimgate.shell.store import IdempotencyKeyAlreadyRememberedError, NoticeStore
from tests.shell.conftest import DEFAULT_SUBMITTED_AT, Submitter

_MALFORMED = NoticeFields(
    policy_number="HO-1234567", loss_date="not-a-date", loss_type="wind_hail", notice_type="INITIAL"
)
_DIFFERENT_CONTENT = NoticeFields(
    policy_number="HO-1234567", loss_date="2026-06-01", loss_type="fire", notice_type="INITIAL"
)


def test_a_schema_refusal_remembers_no_key(store: NoticeStore, submit: Submitter) -> None:
    # ASSUMPTIONS.md decision 4, as corrected 2026-08-24: a refused submission
    # writes no key row, so it can block nothing. The spec proves the caller
    # gets a new notice next time; this proves there is no row to leak.
    response = submit(fields=_MALFORMED, idempotency_key="K-1")

    assert response.status == 400
    assert store.find_key("AAAA", "K-1") is None


def test_an_expired_key_row_is_replaced_by_the_notice_that_reuses_it(
    store: NoticeStore, submit: Submitter
) -> None:
    # One row per (carrier_code, idempotency_key), replaced rather than
    # duplicated - which is why the constraint cannot live on the notice table.
    original = submit(idempotency_key="K-2")
    fresh = submit(submitted_at=DEFAULT_SUBMITTED_AT + KEY_LIFETIME, idempotency_key="K-2")

    assert fresh.status == 201
    assert fresh.notice_id != original.notice_id
    remembered = store.find_key("AAAA", "K-2")
    assert remembered is not None
    assert remembered.notice_id == fresh.notice_id
    assert store.count_notices() == 2


def test_a_conflicting_resubmission_keeps_its_content_with_a_reference_of_its_own(
    store: NoticeStore, submit: Submitter
) -> None:
    original = submit(idempotency_key="K-3")

    conflict = submit(fields=_DIFFERENT_CONTENT, idempotency_key="K-3")

    assert conflict.status == 409
    assert conflict.reference is not None
    payloads = store.list_payloads()
    assert [payload.notice_id for payload in payloads] == [original.notice_id, None]
    assert payloads[1].reference == conflict.reference
    assert store.count_notices() == 1


def test_a_replay_one_second_inside_the_window_is_still_a_replay(
    submit: Submitter,
) -> None:
    # The spec's boundary rows sit a minute either side of the mark; these two
    # sit a second either side of it, so the comparison is the half-open one
    # and not merely one with the right shape at minute resolution.
    original = submit(idempotency_key="K-4")
    inside = submit(
        submitted_at=DEFAULT_SUBMITTED_AT + KEY_LIFETIME - timedelta(seconds=1),
        idempotency_key="K-4",
    )
    outside = submit(
        submitted_at=DEFAULT_SUBMITTED_AT + KEY_LIFETIME + timedelta(seconds=1),
        idempotency_key="K-4",
    )

    assert inside.status == 200
    assert inside.notice_id == original.notice_id
    assert outside.status == 201
    assert outside.notice_id != original.notice_id


def test_losing_the_constraint_race_resolves_by_re_reading_the_key(
    store: NoticeStore, submit: Submitter, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Staged, because a single-writer store cannot produce it: the lookup is
    # made to miss a key that is already remembered, which is what a competing
    # writer committing between the two would look like. The INSERT then loses
    # to the constraint, the transaction rolls back whole, and the resolution
    # answers as a replay of the notice that won.
    winner = submit(idempotency_key="K-5")
    monkeypatch.setattr(store, "find_key", _blind_lookup(store))

    resolved = submit(idempotency_key="K-5")

    assert resolved.status == 200
    assert resolved.notice_id == winner.notice_id
    assert resolved.received_at == winner.received_at
    assert store.count_notices() == 1


def test_a_key_that_vanishes_again_is_not_retried_forever(
    store: NoticeStore, submit: Submitter, monkeypatch: pytest.MonkeyPatch
) -> None:
    # If the re-read finds nothing, the winner is gone too and there is no
    # notice to replay. One retry, then the constraint violation stands.
    submit(idempotency_key="K-6")
    monkeypatch.setattr(store, "find_key", _never_finds_it)

    with pytest.raises(IdempotencyKeyAlreadyRememberedError):
        submit(idempotency_key="K-6")


Lookup = Callable[[str, str], NoticeRecord | None]


def _never_finds_it(carrier_code: str, idempotency_key: str) -> NoticeRecord | None:
    return None


def test_the_same_key_for_one_carrier_cannot_be_remembered_twice(
    store: NoticeStore, submit: Submitter
) -> None:
    # PHASE2_DESIGN.md: uniqueness on (carrier_code, idempotency_key)
    # "enforced by a database constraint, not a check-then-write". What proves
    # it is the database refusing is the cause underneath, not the wrapper.
    first = submit(idempotency_key="K-7")
    second = submit(fields=_DIFFERENT_CONTENT)
    assert second.notice_id is not None
    assert store.find_key("AAAA", "K-7") is not None
    assert first.notice_id != second.notice_id

    with pytest.raises(IdempotencyKeyAlreadyRememberedError) as refused, store.submission():
        store.remember_key("AAAA", "K-7", second.notice_id, replacing_expired=False)

    assert isinstance(refused.value.__cause__, sqlite3.IntegrityError)


def test_the_constraint_is_the_pair_so_another_carrier_may_hold_the_same_key(
    store: NoticeStore, submit: Submitter
) -> None:
    # features/idempotency.feature Rule 2 asserts the caller-visible half of
    # this. Here is the row-level half: the same key held twice, once per
    # carrier, with the constraint declining to object.
    remembered = submit(idempotency_key="K-8")
    assert remembered.notice_id is not None

    with store.submission():
        store.remember_key("BBBB", "K-8", remembered.notice_id, replacing_expired=False)

    for carrier in ("AAAA", "BBBB"):
        assert store.find_key(carrier, "K-8") is not None


def _blind_lookup(store: NoticeStore) -> Lookup:
    """A find_key that reports nothing the first time it is asked and the truth
    afterwards - the second call is the resolution path's own re-read."""
    real = store.find_key
    asked: list[str] = []

    def _find(carrier_code: str, idempotency_key: str) -> NoticeRecord | None:
        asked.append(idempotency_key)
        return None if len(asked) == 1 else real(carrier_code, idempotency_key)

    return _find
