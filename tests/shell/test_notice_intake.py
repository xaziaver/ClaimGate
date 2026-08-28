"""Unit tests for claimgate.shell.notice_intake.

Covers what the acceptance suite deliberately does not reach: the half of item
5i's jurisdiction fault no scenario row can carry - one row states one fault,
and an entry naming an unresolvable timezone is a different input from one
naming none - the error code on the stored payload record, which is a column
and so cannot be spec text, the shell's half of item 5h, the payload record no
scenario can name, the columns item 5g writes, and the one receipt clock, since
no scenario asserts a literal timestamp, for the reason notice_intake.feature's
own Rule 2 comment gives.
"""

from dataclasses import asdict, replace

import pytest

from claimgate.domain import validation
from claimgate.domain.jurisdiction import JURISDICTION_UNSUPPORTED
from claimgate.domain.models import FutureDatedLossResult
from claimgate.shell.faults import CARRIER_RULES_UNRESOLVABLE, JURISDICTION_MAP_UNUSABLE
from claimgate.shell.messages import NoticeFields
from claimgate.shell.notice_intake import get_notice
from claimgate.shell.records import PayloadRecord
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
    assert store.count_notices() == 0
    # No error code: this refusal is about what arrived, not about this
    # deployment, and the column exists to tell those apart (item 5i).
    assert _only_payload(store).error_code is None
    assert response.error is None


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


def test_an_absent_loss_date_pends_the_notice_rather_than_refusing_it(
    submit: Submitter,
) -> None:
    # The inversion of the test that preserved item 5h's gap, and the reason it
    # is a shell test rather than only a scenario: validation.feature proves the
    # blocker, and what is proved here is that the shell carries an absent loss
    # date into the domain at all instead of refusing it at the schema boundary
    # beside an unparseable one (ASSUMPTIONS.md, "An absent loss date is a
    # domain blocker, not a schema refusal"). property_state is stated so the
    # notice has exactly one absence and the pend is attributable to it.
    fields = NoticeFields(
        policy_number="HO-1234567", loss_date=None, loss_type="wind_hail",
        notice_type="INITIAL", property_state="FL",
    )

    response = submit(fields=fields)

    assert response.status == 201
    assert response.state == "PENDED"
    assert [(b.code, b.field) for b in response.blockers] == [
        ("MISSING_REQUIRED_FIELD", "loss_date")
    ]


def test_a_carrier_recognized_by_identity_but_unresolvable_rules_is_receipted_as_our_defect(
    store: NoticeStore, submit: Submitter
) -> None:
    # Item 5i, ruling 1. AAAA is in the identity reference, so this deployment
    # claims to administer it and the 627.70131(1)(a) duty is real; what failed
    # is our own configuration, and a 4xx would tell the reporter their notice
    # was refused for it.
    response = submit(carrier_rules_source={})

    assert response.status == 500
    assert response.error == CARRIER_RULES_UNRESOLVABLE
    assert response.notice_id is None
    assert store.count_notices() == 0
    assert _only_payload(store).error_code == CARRIER_RULES_UNRESOLVABLE


def test_a_jurisdiction_map_holding_an_unrecognized_timezone_is_our_defect_too(
    store: NoticeStore, submit: Submitter
) -> None:
    # One of the two ways this deployment's own map is unusable, and the one no
    # scenario reaches: an entry naming a timezone this system cannot resolve,
    # caught in resolve_today rather than in the selection. Same code as the
    # other half, because a caller's retry answer is the same for both.
    response = submit(jurisdiction_reference={"FL": {"timezone": "Not/AZone"}})

    assert response.status == 500
    assert response.error == JURISDICTION_MAP_UNUSABLE
    assert response.notice_id is None
    assert store.count_notices() == 0
    assert _only_payload(store).error_code == JURISDICTION_MAP_UNUSABLE


def test_a_deployment_fault_remembers_no_key_so_an_identical_retry_creates_a_notice(
    store: NoticeStore, submit: Submitter
) -> None:
    # The shell's half of features/idempotency.feature Rule 6's third row: the
    # fault is answered above _create_notice, so remember_key never runs and the
    # key names nothing. An implementation that remembered a key against the
    # payload reference instead would replay this identical retry.
    faulted = submit(carrier_rules_source={}, idempotency_key="K-600")
    assert faulted.status == 500
    assert store.find_key("AAAA", "K-600") is None

    retried = submit(idempotency_key="K-600")

    assert retried.status == 201
    assert retried.notice_id is not None


def test_a_property_state_with_no_entry_is_marked_and_never_blocked(
    store: NoticeStore, submit: Submitter
) -> None:
    # The acceptance suite proves the outcome through the spec; what is here is
    # that the marking and the determination are actually persisted on the row
    # rather than computed for a response, which no scenario names a table to
    # assert. The same submission under "FL" is the control.
    response = submit(fields=replace(DEFAULT_FIELDS, property_state="GA"))

    assert response.status == 201
    assert response.state == "TRIAGED"
    assert response.blockers == ()
    record = store.get_notice(response.notice_id)
    assert record is not None
    assert record.jurisdiction_marking == JURISDICTION_UNSUPPORTED
    assert record.future_dated_loss == FutureDatedLossResult(
        "NOT_EVALUATED", validation.NO_JURISDICTION_DATE
    )


def test_a_supported_property_state_is_unmarked_and_its_determination_is_made(
    store: NoticeStore, submit: Submitter
) -> None:
    response = submit()

    record = store.get_notice(response.notice_id)
    assert record is not None
    assert record.jurisdiction_marking is None
    assert record.future_dated_loss == FutureDatedLossResult("FALSE")


def test_the_notice_at_rest_in_received_carries_no_determination_at_all(
    store: NoticeStore, submit: Submitter, rule_evaluation_raises: None
) -> None:
    # Null is not FALSE. A notice whose rules never ran has had no determination
    # made about it, which is a different fact from a determination of "not
    # ahead of today" - CLAUDE.md, "A result that was not computed is never
    # reported as a negative."
    with pytest.raises(RuleEvaluationBugError):
        submit()

    record = store.get_notice(store.list_payloads()[0].notice_id)
    assert record is not None
    assert record.state == "RECEIVED"
    assert record.future_dated_loss is None
    assert record.jurisdiction_marking is None


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


def test_a_jurisdiction_map_entry_naming_no_timezone_is_answered_and_marks_nothing(
    store: NoticeStore, submit: Submitter
) -> None:
    # The other half of the same misconfiguration: an entry that exists and
    # names nothing. It is deliberately not degraded to jurisdiction_unsupported
    # (item 5i, ruling 3), which would blame the reporter for our own map - and
    # there is no notice to carry a marking anyway.
    response = submit(jurisdiction_reference={"FL": {}})

    assert response.status == 500
    assert response.error == JURISDICTION_MAP_UNUSABLE
    assert store.count_notices() == 0


def _only_payload(store: NoticeStore) -> PayloadRecord:
    payloads = store.list_payloads()
    assert len(payloads) == 1
    return payloads[0]
