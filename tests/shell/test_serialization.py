"""The allow-lists, checked against the surfaces they are lists for.

PHASE2_DESIGN.md's "SIU handling" point 2 asks for allow-list serialization and
gives the reason: "a deny-list leaks every field added after it was written."
The list itself is only half of that. The other half is this file, which fails
whenever a message type and its allow-list stop agreeing - so a field added to
one of those types is either named on its surface or kept off it by someone who
decided, rather than by whichever of the two nobody updated.
"""

from dataclasses import fields
from datetime import UTC, datetime

import pytest

from claimgate.domain.models import ValidationBlocker
from claimgate.shell import serialization
from claimgate.shell.messages import NoticeView, ResolutionResponse, SubmitNoticeResponse
from claimgate.shell.records import AuditEntry

_SURFACES = (
    (SubmitNoticeResponse, serialization.SUBMIT_NOTICE_RESPONSE_FIELDS),
    (ResolutionResponse, serialization.RESOLUTION_RESPONSE_FIELDS),
    (NoticeView, serialization.NOTICE_VIEW_FIELDS),
    (AuditEntry, serialization.AUDIT_ENTRY_FIELDS),
)
_BLOCKER = ValidationBlocker(code="MISSING_REQUIRED_FIELD", field="policy_number")
_RECEIVED_AT = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)


@pytest.mark.parametrize(("message_type", "allowed"), _SURFACES)
def test_an_allow_list_names_every_field_of_the_surface_it_is_for(
    message_type: type, allowed: tuple[str, ...]
) -> None:
    assert sorted(allowed) == sorted(field.name for field in fields(message_type))
    assert len(set(allowed)) == len(allowed)


def test_a_serialized_response_carries_the_allow_lists_keys_and_no_others() -> None:
    # The list is not decoration: what comes out is built from it, so a field
    # left off it does not reach the surface even though the message has it.
    body = serialization.serialize_response(
        SubmitNoticeResponse(
            status=201, notice_id="notice-1", state="TRIAGED", received_at=_RECEIVED_AT
        )
    )

    assert tuple(body) == serialization.SUBMIT_NOTICE_RESPONSE_FIELDS
    assert body["received_at"] == _RECEIVED_AT.isoformat()


def test_the_two_response_types_are_serialized_through_their_own_lists() -> None:
    body = serialization.serialize_response(ResolutionResponse(status=422, blockers=(_BLOCKER,)))

    assert tuple(body) == serialization.RESOLUTION_RESPONSE_FIELDS
    assert body["blockers"] == [{"code": _BLOCKER.code, "field": _BLOCKER.field}]


def test_a_serialized_notice_view_and_audit_entry_carry_their_own_lists_keys() -> None:
    view = NoticeView("notice-1", "PENDED", (_BLOCKER,), None, None)
    entry = _entry()

    assert tuple(serialization.serialize_notice_view(view)) == serialization.NOTICE_VIEW_FIELDS
    assert tuple(serialization.serialize_audit_entry(entry)) == serialization.AUDIT_ENTRY_FIELDS
    assert serialization.serialize_audit_entry(entry)["occurred_at"] == _RECEIVED_AT.isoformat()


def _entry() -> AuditEntry:
    return AuditEntry(
        notice_id="notice-1", carrier_code="AAAA", from_state="RECEIVED", to_state="PENDED",
        actor_id="no verified identity", actor_type="SYSTEM", occurred_at=_RECEIVED_AT,
        blockers=(_BLOCKER,), outcome="APPLIED", actor_authenticated=False,
    )
