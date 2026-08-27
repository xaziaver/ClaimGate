"""Unit tests for what the resolution path guarantees and no scenario reaches.

features/resolution.feature asserts outcomes, records and audit entries; it
names no table, no column and no transaction, and it cannot - a spec that did
would be specifying storage. Code mutation does not reach src/claimgate/shell/
at all (docs/harness-findings.md, mutmut's source_paths), so what is here and in
the acceptance suite is the whole of the protection for this module.

What only these can assert: that a refusal's three writes commit or fail
together, that the two refusals before the transaction write nothing at all,
that a resolution never moves the pend instant, and that resolved_at is set by
an application and by nothing else. That last one was checked against the
acceptance suite before it was written here - stamping resolved_at on refusals
too passes all 21 scenarios, because no scenario can see it.
"""

from datetime import UTC, datetime

import pytest

from claimgate.shell.records import NoticeRecord
from claimgate.shell.resolution import resolve_notice
from claimgate.shell.store import NoticeStore
from tests.shell.support import (
    DEFAULT_RESOLVED_AT,
    DEFAULT_REVIEWER,
    DEFAULT_SUBMITTED_AT,
    JURISDICTIONS,
    PENDING_FIELDS,
    VALID_RULES,
    AuditWriteError,
    Resolver,
    Submitter,
)

_CLEARS_THE_PEND = {"policy_number": "HO-7654321"}
_LEAVES_IT_BLOCKED = {"policy_number": "HO-12"}


def test_a_refused_resolution_keeps_its_payload_its_blockers_and_its_entry(
    store: NoticeStore, submit: Submitter, resolve: Resolver
) -> None:
    notice_id = _pend(submit)

    response = resolve(notice_id, supplied=_LEAVES_IT_BLOCKED)

    assert response.status == 422
    # Decision 3: the release was refused, not the data.
    assert len(store.get_notice_payloads(notice_id)) == 2
    assert _stored(store, notice_id).blockers == response.blockers
    assert store.get_audit_trail(notice_id)[-1].outcome == "REFUSED"


def test_a_refusal_that_cannot_write_its_entry_writes_nothing_at_all(
    store: NoticeStore, submit: Submitter, resolve: Resolver, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The payload record, the notice's blockers and the audit entry are one
    # transaction. The entry is written last, so a raise there is the case that
    # can leave the other two standing if the boundary is not where it is
    # claimed to be.
    notice_id = _pend(submit)
    monkeypatch.setattr(NoticeStore, "append_audit_entry", _raising_append)

    with pytest.raises(AuditWriteError):
        resolve(notice_id, supplied=_LEAVES_IT_BLOCKED)

    assert len(store.get_notice_payloads(notice_id)) == 1
    assert len(store.get_audit_trail(notice_id)) == 2
    stored = _stored(store, notice_id)
    assert stored.state == "PENDED"
    assert [b.field for b in stored.blockers] == ["policy_number"]


def test_a_resolution_against_a_notice_that_is_not_pended_persists_nothing(
    store: NoticeStore, submit: Submitter, resolve: Resolver
) -> None:
    triaged = submit()
    assert triaged.notice_id is not None

    response = resolve(triaged.notice_id, supplied=_CLEARS_THE_PEND)

    assert response.status == 409
    # The body carries the notice's current state: state is read from the body,
    # never inferred from status.
    assert response.state == "TRIAGED"
    assert len(store.get_notice_payloads(triaged.notice_id)) == 1
    assert len(store.get_audit_trail(triaged.notice_id)) == 2
    assert _stored(store, triaged.notice_id).resolved_at is None


@pytest.mark.parametrize("actor_id", [None, "", "   "])
def test_a_resolution_with_no_reviewer_behind_it_persists_nothing(
    store: NoticeStore, submit: Submitter, resolve: Resolver, actor_id: str | None
) -> None:
    notice_id = _pend(submit)

    response = resolve(notice_id, actor_id=actor_id, supplied=_CLEARS_THE_PEND)

    assert response.status == 400
    # Nothing about the notice is in the body either: the identity is checked
    # before the notice is read at all.
    assert response.state is None
    assert len(store.get_notice_payloads(notice_id)) == 1
    assert len(store.get_audit_trail(notice_id)) == 2
    assert _stored(store, notice_id).state == "PENDED"


def test_a_resolution_leaves_the_receipt_and_the_pend_instant_where_they_were(
    store: NoticeStore, submit: Submitter, resolve: Resolver
) -> None:
    notice_id = _pend(submit)

    resolve(notice_id, supplied=_CLEARS_THE_PEND)

    stored = _stored(store, notice_id)
    assert stored.received_at == DEFAULT_SUBMITTED_AT
    assert stored.pended_at == DEFAULT_SUBMITTED_AT


def test_only_the_resolution_that_moves_the_notice_stamps_the_resolution_instant(
    store: NoticeStore, submit: Submitter, resolve: Resolver
) -> None:
    # Decision (a): resolved_at is written only by the resolution that moves the
    # notice to TRIAGED. A refused attempt's instant lives on its audit entry.
    notice_id = _pend(submit)
    refused_at = datetime(2026, 6, 2, 8, 0, tzinfo=UTC)

    resolve(notice_id, resolved_at=refused_at, supplied=_LEAVES_IT_BLOCKED)
    assert _stored(store, notice_id).resolved_at is None
    assert store.get_audit_trail(notice_id)[-1].occurred_at == refused_at

    resolve(notice_id, resolved_at=DEFAULT_RESOLVED_AT, supplied=_CLEARS_THE_PEND)
    assert _stored(store, notice_id).resolved_at == DEFAULT_RESOLVED_AT


def test_every_resolution_entry_records_its_reviewer_as_a_user_and_unverified(
    store: NoticeStore, submit: Submitter, resolve: Resolver
) -> None:
    notice_id = _pend(submit)

    resolve(notice_id, supplied=_CLEARS_THE_PEND)

    entry = store.get_audit_trail(notice_id)[-1]
    assert (entry.actor_type, entry.actor_id) == ("USER", DEFAULT_REVIEWER)
    assert entry.actor_authenticated is False
    # from PENDED to TRIAGED on every attempt, applied or refused: the entry
    # records the transition attempted, and outcome records what came of it.
    assert (entry.from_state, entry.to_state) == ("PENDED", "TRIAGED")


def test_a_resolution_naming_a_notice_this_deployment_does_not_have_raises(
    store: NoticeStore
) -> None:
    # No status code exists for it in PHASE2_DESIGN.md's closed table, so
    # inventing one here would be defaulting a rule nobody approved.
    with pytest.raises(NotImplementedError, match="unknown identifier"):
        resolve_notice(
            store,
            "no-such-notice",
            actor_id=DEFAULT_REVIEWER,
            resolved_at=DEFAULT_RESOLVED_AT,
            jurisdiction_reference=JURISDICTIONS,
            carrier_rules_source={"AAAA": VALID_RULES},
            supplied={},
        )


def test_a_resolution_carrying_a_loss_date_that_is_not_a_date_raises(
    submit: Submitter, resolve: Resolver
) -> None:
    # Intake answers this 400 at the schema boundary; no decision extends that
    # row to this endpoint, so it escalates rather than picking one.
    notice_id = _pend(submit)

    with pytest.raises(NotImplementedError, match="not a date at all"):
        resolve(notice_id, supplied={"loss_date": "not-a-date"})


def _pend(submit: Submitter) -> str:
    response = submit(fields=PENDING_FIELDS)
    assert response.notice_id is not None
    assert response.state == "PENDED"
    return response.notice_id


def _stored(store: NoticeStore, notice_id: str) -> NoticeRecord:
    record = store.get_notice(notice_id)
    assert record is not None
    return record


def _raising_append(*_: object, **__: object) -> None:
    raise AuditWriteError("the audit entry could not be written")
