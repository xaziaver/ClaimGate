"""When the SIU evaluation runs, what it is stamped with, and what it counts from.

features/siu_separation.feature proves the same rules through the endpoints. What
is here is what no scenario can reach: that the events and the transition they
belong to are one transaction rather than two writes that happen to follow each
other, and that a rolled-back transition takes its evaluation with it. Code
mutation does not reach src/claimgate/shell/ at all (tests/shell/conftest.py), so
if these do not assert it, nothing does.
"""

from datetime import UTC, datetime
from typing import Any

import pytest

from claimgate.domain.ruleset import RULESET_VERSION
from claimgate.shell import notice_intake, resolution, siu
from claimgate.shell.messages import NoticeFields
from claimgate.shell.store import NoticeStore
from tests.shell.support import (
    DEFAULT_FIELDS,
    DEFAULT_SUBMITTED_AT,
    VALID_RULES,
    Resolver,
    SiuWriteError,
    Submitter,
)

# The receipt is 2026-06-01T12:00Z, which is 08:00 in America/New_York, so every
# interval below is counted from 2026-06-01 unless a test says otherwise.
_RESOLVED_LATER = datetime(2026, 8, 1, 12, 0, tzinfo=UTC)
_LOSS_BEFORE_THE_RECEIPT = "2026-05-01"
_RULES_WITH_A_THRESHOLD: dict[str, Any] = {**VALID_RULES, "late_reporting_threshold_days": 45}
_SOURCE = {"AAAA": _RULES_WITH_A_THRESHOLD}
_PENDING = NoticeFields(
    policy_number="", loss_date=_LOSS_BEFORE_THE_RECEIPT, loss_type="wind_hail",
    notice_type="INITIAL", property_state="FL",
)
_CLEARS_THE_PEND = {"policy_number": "HO-1234567"}
_LEAVES_IT_BLOCKED: dict[str, Any] = {}


def test_a_notice_triaged_at_intake_records_one_event_per_indicator(
    store: NoticeStore, submit: Submitter
) -> None:
    response = submit(carrier_rules_source=_SOURCE)

    events = store.get_siu_events(response.notice_id)
    assert [event.indicator for event in events] == [siu.LATE_REPORTING, siu.RECENT_POLICY_INCEPTION]
    assert {event.evaluated_at for event in events} == {DEFAULT_SUBMITTED_AT}
    assert {event.ruleset_version for event in events} == {RULESET_VERSION}


def test_a_notice_that_pends_at_intake_records_no_evaluation(
    store: NoticeStore, submit: Submitter
) -> None:
    # A pended notice is an incomplete intake record, not a claim, and a
    # resolution that corrects the loss date would change the interval.
    submit(carrier_rules_source=_SOURCE, fields=_PENDING)

    assert store.list_siu_events() == ()


def test_a_refused_resolution_records_no_evaluation(
    store: NoticeStore, submit: Submitter, resolve: Resolver
) -> None:
    notice_id = submit(carrier_rules_source=_SOURCE, fields=_PENDING).notice_id
    assert notice_id is not None

    response = resolve(notice_id, carrier_rules_source=_SOURCE, supplied=_LEAVES_IT_BLOCKED)

    assert response.status == 422
    assert store.list_siu_events() == ()


def test_a_replayed_submission_records_no_second_evaluation(
    store: NoticeStore, submit: Submitter
) -> None:
    # A replay returns the notice that already exists and moves nothing, so
    # there is nothing to evaluate. Only the count betrays an implementation
    # that evaluated per request rather than per transition.
    first = submit(carrier_rules_source=_SOURCE, idempotency_key="K-800")
    second = submit(carrier_rules_source=_SOURCE, idempotency_key="K-800")

    assert second.notice_id == first.notice_id
    assert len(store.list_siu_events()) == 2


def test_the_interval_is_counted_from_the_receipt_and_the_stamp_is_the_resolution(
    store: NoticeStore, submit: Submitter, resolve: Resolver
) -> None:
    # 2026-05-01 is 31 days before the receipt's jurisdiction date and 92 before
    # the resolution's. Against a 45-day threshold the two clocks disagree, so a
    # single row proves which one was used - and the stamp proves the evaluation
    # still happened at the resolution.
    notice_id = submit(carrier_rules_source=_SOURCE, fields=_PENDING).notice_id
    assert notice_id is not None

    resolve(
        notice_id, resolved_at=_RESOLVED_LATER, carrier_rules_source=_SOURCE,
        supplied=_CLEARS_THE_PEND,
    )

    late_reporting = store.get_siu_events(notice_id)[0]
    assert late_reporting.value == "FALSE"
    assert late_reporting.threshold_days == 45
    assert late_reporting.evaluated_at == _RESOLVED_LATER


def test_every_audit_entry_on_both_paths_carries_the_rule_sets_label(
    store: NoticeStore, submit: Submitter, resolve: Resolver
) -> None:
    notice_id = submit(carrier_rules_source=_SOURCE, fields=_PENDING).notice_id
    assert notice_id is not None
    resolve(notice_id, carrier_rules_source=_SOURCE, supplied=_CLEARS_THE_PEND)
    triaged_at_intake = submit(carrier_rules_source=_SOURCE, fields=DEFAULT_FIELDS).notice_id

    for entries in (store.get_audit_trail(notice_id), store.get_audit_trail(triaged_at_intake)):
        assert entries != ()
        assert {entry.ruleset_version for entry in entries} == {RULESET_VERSION}


def test_an_intake_evaluation_that_fails_takes_the_triage_down_with_it(
    store: NoticeStore, submit: Submitter, siu_write_fails: None
) -> None:
    with pytest.raises(SiuWriteError):
        submit(carrier_rules_source=_SOURCE)

    # The receipt survives - it is its own transaction - but the decision that
    # would have triaged the notice is gone, and so are the events it wrote.
    assert store.count_notices() == 1
    assert store.list_siu_events() == ()
    assert [entry.to_state for entry in store.get_audit_trail(_only_notice(store))] == ["RECEIVED"]


def test_a_resolution_evaluation_that_fails_takes_the_release_down_with_it(
    store: NoticeStore, submit: Submitter, resolve: Resolver, siu_write_fails: None
) -> None:
    notice_id = submit(carrier_rules_source=_SOURCE, fields=_PENDING).notice_id
    assert notice_id is not None

    with pytest.raises(SiuWriteError):
        resolve(notice_id, carrier_rules_source=_SOURCE, supplied=_CLEARS_THE_PEND)

    record = store.get_notice(notice_id)
    assert record is not None
    assert record.state == "PENDED"
    assert record.resolved_at is None
    assert store.list_siu_events() == ()
    assert [entry.to_state for entry in store.get_audit_trail(notice_id)] == ["RECEIVED", "PENDED"]


@pytest.fixture
def siu_write_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """Writes the events and then raises, still inside the transaction. Failing
    before the write would only prove the events were never made; failing after
    it is what tells a rollback apart from never having happened.

    Patched on the siu module itself, unlike conftest.py's rule_evaluation_raises
    - both callers import the module and resolve the name at call time, so one
    patch reaches both paths and neither keeps a binding to the original."""
    original = siu.record_evaluation

    def _write_then_raise(*args: object, **kwargs: object) -> None:
        original(*args, **kwargs)  # type: ignore[arg-type]
        raise SiuWriteError("the SIU trail was written and the transaction then failed")

    monkeypatch.setattr(siu, "record_evaluation", _write_then_raise)
    assert notice_intake.siu is siu and resolution.siu is siu


def _only_notice(store: NoticeStore) -> str:
    payload = store.list_payloads()[0]
    assert payload.notice_id is not None
    return payload.notice_id
