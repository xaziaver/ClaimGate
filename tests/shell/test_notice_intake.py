"""Unit tests for claimgate.shell.notice_intake.

Covers what the acceptance suite deliberately does not reach: the two
scope-wall raises (items 5g, 5i) and the deliberately preserved item 5h gap.
"""

from collections.abc import Mapping
from datetime import UTC, datetime

import pytest

from claimgate.shell.notice_intake import NoticeFields, SubmitNoticeResponse, get_notice, submit_notice
from claimgate.shell.store import NoticeStore

_VALID_RULES: dict[str, object] = {
    "claimant_name_required": False,
    "claimant_contact_required": False,
    "recognized_policy_number_prefixes": ["HO"],
    "late_reporting_threshold_days": None,
    "recent_inception_threshold_days": 30,
    "window_days": 60,
}
_DEFAULT_SUBMITTED_AT = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
_DEFAULT_FIELDS = NoticeFields(
    policy_number="HO-1234567", loss_date="2026-06-01", loss_type="wind_hail", notice_type="INITIAL"
)


def _submit(
    store: NoticeStore,
    *,
    carrier_code: str = "AAAA",
    submitted_at: datetime = _DEFAULT_SUBMITTED_AT,
    jurisdiction_timezone: str = "America/New_York",
    carrier_rules_source: Mapping[str, Mapping[str, object]] | None = None,
    fields: NoticeFields = _DEFAULT_FIELDS,
) -> SubmitNoticeResponse:
    rules_source = (
        carrier_rules_source if carrier_rules_source is not None else {"AAAA": dict(_VALID_RULES)}
    )
    return submit_notice(
        store,
        carrier_code=carrier_code,
        submitted_at=submitted_at,
        jurisdiction_timezone=jurisdiction_timezone,
        carrier_rules_source=rules_source,
        fields=fields,
    )


def test_an_unrecognized_carrier_is_refused_with_nothing_persisted() -> None:
    store = NoticeStore()

    response = _submit(store, carrier_code="ZZZZ")

    assert response.status == 400
    assert response.notice_id is None
    assert response.reference is None
    assert store.notices == {}
    assert store.payloads == []


def test_an_unparseable_loss_date_is_refused_with_the_payload_kept() -> None:
    store = NoticeStore()
    fields = NoticeFields(
        policy_number="HO-1234567",
        loss_date="not-a-date",
        loss_type="wind_hail",
        notice_type="INITIAL",
    )

    response = _submit(store, fields=fields)

    assert response.status == 400
    assert response.notice_id is None
    assert response.reference is not None
    assert len(store.payloads) == 1
    assert store.notices == {}


def test_a_schema_valid_notice_is_received_then_triaged() -> None:
    store = NoticeStore()

    response = _submit(store)

    assert response.status == 201
    assert response.state == "TRIAGED"
    assert response.notice_id is not None
    view = get_notice(store, response.notice_id)
    assert view is not None
    assert view.state == "TRIAGED"
    trail = store.get_audit_trail(response.notice_id)
    assert [entry.to_state for entry in trail] == ["RECEIVED", "TRIAGED"]
    assert [entry.actor_type for entry in trail] == ["EXTERNAL", "SYSTEM"]


def test_an_absent_loss_date_flows_through_unchanged_item_5h_is_not_built_here() -> None:
    store = NoticeStore()
    fields = NoticeFields(
        policy_number="HO-1234567", loss_date=None, loss_type="wind_hail", notice_type="INITIAL"
    )

    response = _submit(store, fields=fields)

    # Item 5h ("An absent loss date is a domain blocker, not a schema
    # refusal") is not built: validate() has no presence check for
    # loss_date, so this reaches TRIAGED carrying date.min as today's date -
    # a known, recorded defect this item deliberately does not fix.
    assert response.status == 201
    assert response.state == "TRIAGED"


def test_a_carrier_recognized_by_identity_but_unresolvable_rules_is_not_handled() -> None:
    store = NoticeStore()

    with pytest.raises(NotImplementedError):
        _submit(store, carrier_rules_source={})


def test_an_unrecognized_jurisdiction_timezone_is_not_handled() -> None:
    store = NoticeStore()

    with pytest.raises(NotImplementedError):
        _submit(store, jurisdiction_timezone="Not/AZone")


def test_get_notice_returns_none_for_an_unknown_id() -> None:
    store = NoticeStore()

    assert get_notice(store, "unknown") is None
