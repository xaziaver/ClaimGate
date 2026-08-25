"""Unit tests for claimgate.shell.notice_intake.

Covers what the acceptance suite deliberately does not reach: the two
scope-wall raises (items 5g, 5i), the deliberately preserved item 5h gap, the
payload record no scenario can name, and the one receipt clock - no scenario
asserts a literal timestamp, for the reason notice_intake.feature's own Rule 2
comment gives.
"""

from dataclasses import asdict

import pytest

from claimgate.shell.messages import NoticeFields
from claimgate.shell.notice_intake import get_notice
from claimgate.shell.records import payload_reference
from claimgate.shell.store import NoticeStore
from tests.shell.support import (
    DEFAULT_FIELDS,
    DEFAULT_SUBMITTED_AT,
    RuleEvaluationBugError,
    Submitter,
)


def test_an_unrecognized_carrier_is_refused_with_nothing_persisted(
    store: NoticeStore, submit: Submitter
) -> None:
    response = submit(carrier_code="ZZZZ")

    assert response.status == 400
    assert response.notice_id is None
    assert response.reference is None
    assert store.count_notices() == 0
    assert store.list_payloads() == ()


def test_an_unparseable_loss_date_is_refused_with_the_payload_kept(
    store: NoticeStore, submit: Submitter
) -> None:
    fields = NoticeFields(
        policy_number="HO-1234567",
        loss_date="not-a-date",
        loss_type="wind_hail",
        notice_type="INITIAL",
    )

    response = submit(fields=fields)

    assert response.status == 400
    assert response.notice_id is None
    assert response.reference is not None
    assert len(store.list_payloads()) == 1
    assert store.count_notices() == 0


def test_a_schema_valid_notice_is_received_then_triaged(
    store: NoticeStore, submit: Submitter
) -> None:
    response = submit()

    assert response.status == 201
    assert response.state == "TRIAGED"
    assert response.notice_id is not None
    view = get_notice(store, response.notice_id)
    assert view is not None
    assert view.state == "TRIAGED"
    trail = store.get_audit_trail(response.notice_id)
    assert [entry.to_state for entry in trail] == ["RECEIVED", "TRIAGED"]
    assert [entry.actor_type for entry in trail] == ["EXTERNAL", "SYSTEM"]


def test_the_accepted_path_persists_the_raw_payload_linked_to_the_notice(
    store: NoticeStore, submit: Submitter
) -> None:
    # Design-mandated (PHASE2_DESIGN.md's audit log section, 627.70131(4)(b)),
    # not scenario-mandated: no acceptance scenario asserts this, since
    # features/notice_intake.feature names no field or table.
    response = submit()

    assert response.notice_id is not None
    payloads = store.list_payloads()
    assert len(payloads) == 1
    assert payloads[0].notice_id == response.notice_id
    assert payloads[0].carrier_code == "AAAA"
    assert payloads[0].arrival_index == 0
    # Item 5e appends resolution payloads after this one, so position 0 has to
    # be the record the notice was created from.
    assert payloads[0].reference == payload_reference(asdict(DEFAULT_FIELDS))


def test_every_timestamp_a_submission_writes_is_the_one_receipt_instant(
    store: NoticeStore, submit: Submitter
) -> None:
    # ASSUMPTIONS.md, "One receipt clock, not two": submitted_at is the receipt
    # instant and datetime.now is not consulted anywhere on this path. Nothing
    # in features/ can assert this - occurred_at was real wall-clock time until
    # this item, and a spec cannot state a literal for that.
    response = submit()

    assert response.notice_id is not None
    assert response.received_at == DEFAULT_SUBMITTED_AT
    record = store.get_notice(response.notice_id)
    assert record is not None
    assert record.received_at == DEFAULT_SUBMITTED_AT
    trail = store.get_audit_trail(response.notice_id)
    assert [entry.occurred_at for entry in trail] == [DEFAULT_SUBMITTED_AT] * 2
    assert store.list_payloads()[0].received_at == DEFAULT_SUBMITTED_AT


def test_every_audit_entry_carries_the_carrier_it_is_attributed_to(
    store: NoticeStore, submit: Submitter
) -> None:
    # PHASE2_DESIGN.md's "Carrier reference": persisted on every notice and
    # every audit entry, for attribution only, never branched on.
    response = submit()

    assert response.notice_id is not None
    trail = store.get_audit_trail(response.notice_id)
    assert [entry.carrier_code for entry in trail] == ["AAAA", "AAAA"]


def test_an_absent_loss_date_flows_through_unchanged_item_5h_is_not_built_here(
    submit: Submitter,
) -> None:
    fields = NoticeFields(
        policy_number="HO-1234567", loss_date=None, loss_type="wind_hail", notice_type="INITIAL"
    )

    response = submit(fields=fields)

    # Item 5h ("An absent loss date is a domain blocker, not a schema
    # refusal") is not built: validate() has no presence check for
    # loss_date, so this reaches TRIAGED carrying date.min as today's date -
    # a known, recorded defect this item deliberately does not fix.
    assert response.status == 201
    assert response.state == "TRIAGED"


def test_a_carrier_recognized_by_identity_but_unresolvable_rules_is_not_handled(
    submit: Submitter,
) -> None:
    with pytest.raises(NotImplementedError):
        submit(carrier_rules_source={})


def test_an_unrecognized_jurisdiction_timezone_is_not_handled(submit: Submitter) -> None:
    with pytest.raises(NotImplementedError):
        submit(jurisdiction_timezone="Not/AZone")


def test_get_notice_returns_none_for_an_unknown_id(store: NoticeStore) -> None:
    assert get_notice(store, "unknown") is None


def test_a_bug_in_rule_evaluation_cannot_erase_the_receipt(
    store: NoticeStore, submit: Submitter, rule_evaluation_raises: None
) -> None:
    # PHASE2_DESIGN.md's whole reason for writing RECEIVED before any rule
    # runs: "a bug in rule evaluation must never be able to erase or delay the
    # fact that a notice was received." The receipt transaction has committed
    # before rule evaluation is reached, so the exception leaves the notice
    # standing rather than rolling it back.
    with pytest.raises(RuleEvaluationBugError):
        submit(idempotency_key="K-9")

    assert store.count_notices() == 1
    payloads = store.list_payloads()
    assert len(payloads) == 1
    notice_id = payloads[0].notice_id
    assert notice_id is not None
    record = store.get_notice(notice_id)
    assert record is not None
    assert record.state == "RECEIVED"
    assert record.received_at == DEFAULT_SUBMITTED_AT
    trail = store.get_audit_trail(notice_id)
    assert [entry.to_state for entry in trail] == ["RECEIVED"]
    # The key was remembered with the receipt, not with the decision, which is
    # what makes the client's retry a replay rather than a second notice.
    remembered = store.find_key("AAAA", "K-9")
    assert remembered is not None
    assert remembered.notice_id == notice_id
