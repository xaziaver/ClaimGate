"""The allow-lists, checked against the surfaces they are lists for.

PHASE2_DESIGN.md's "SIU handling" point 2 asks for allow-list serialization and
gives the reason: "a deny-list leaks every field added after it was written."
The list itself is only half of that. The other half is this file, which fails
whenever a message type and its allow-list stop agreeing - so a field added to
one of those types is either named on its surface or kept off it by someone who
decided, rather than by whichever of the two nobody updated.
"""

from dataclasses import fields
from datetime import UTC, date, datetime

import pytest

from claimgate.domain.models import ValidationBlocker
from claimgate.shell import serialization
from claimgate.shell.coverage_verifications import CoverageVerificationView
from claimgate.shell.duplicate_evaluations import DuplicateEvaluationView
from claimgate.shell.messages import NoticeView, ResolutionResponse, SubmitNoticeResponse
from claimgate.shell.records import AuditEntry

_SURFACES = (
    (SubmitNoticeResponse, serialization.SUBMIT_NOTICE_RESPONSE_FIELDS),
    (ResolutionResponse, serialization.RESOLUTION_RESPONSE_FIELDS),
    (NoticeView, serialization.NOTICE_VIEW_FIELDS),
    (CoverageVerificationView, serialization.COVERAGE_VERIFICATION_FIELDS),
    (DuplicateEvaluationView, serialization.DUPLICATE_EVALUATION_FIELDS),
    (AuditEntry, serialization.AUDIT_ENTRY_FIELDS),
)
_BLOCKER = ValidationBlocker(code="MISSING_REQUIRED_FIELD", field="policy_number")
_RECEIVED_AT = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
_VERIFICATION = CoverageVerificationView(
    policy_match="MATCHED", matched_policy="POL-88213", reason=None, term_in_force="IN_FORCE",
    identified_on="POLICY_NUMBER",
    deciding_term_effective=date(2026, 1, 15), deciding_term_expiration=date(2027, 1, 15),
    continuous_coverage_date=date(2026, 1, 15), continuous_coverage_reason=None,
    as_of=_RECEIVED_AT,
)
_DUPLICATES = DuplicateEvaluationView(
    status="OBTAINED", candidates=("CLM-1001", "CLM-1002"), reason=None
)


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
    view = NoticeView("notice-1", "PENDED", (_BLOCKER,), None, None, None, None, None)
    entry = _entry()

    assert tuple(serialization.serialize_notice_view(view)) == serialization.NOTICE_VIEW_FIELDS
    assert serialization.serialize_notice_view(view)["coverage_verification"] is None
    assert serialization.serialize_notice_view(view)["duplicate_evaluation"] is None
    assert serialization.serialize_notice_view(view)["blockers"] == [
        {"code": _BLOCKER.code, "field": _BLOCKER.field}
    ]
    assert tuple(serialization.serialize_audit_entry(entry)) == serialization.AUDIT_ENTRY_FIELDS
    assert serialization.serialize_audit_entry(entry)["occurred_at"] == _RECEIVED_AT.isoformat()


def test_the_coverage_verification_is_nested_through_its_own_list_with_dates_as_text() -> None:
    # Item 7f: the nested surface is built from its own allow-list, so a field
    # added to the view and not to the list stays off the wire, and every date
    # on it renders the way an instant does.
    view = NoticeView(
        "notice-1", "TRIAGED", (), "standard", "standard", None, _VERIFICATION, _DUPLICATES
    )

    nested = serialization.serialize_notice_view(view)["coverage_verification"]

    assert tuple(nested) == serialization.COVERAGE_VERIFICATION_FIELDS
    assert nested["deciding_term_effective"] == "2026-01-15"
    assert nested["as_of"] == _RECEIVED_AT.isoformat()
    assert nested["matched_policy"] == "POL-88213"


def test_the_duplicate_evaluation_is_nested_through_its_own_list_with_candidates_as_ids() -> None:
    # Item 7h: the third nested surface, on the verification's terms, and the
    # candidate ids render as a plain list of strings - the tuple rule that
    # renders blockers as their two names does not turn an id into a record.
    view = NoticeView(
        "notice-1", "TRIAGED", (), "standard", "standard", None, _VERIFICATION, _DUPLICATES
    )

    nested = serialization.serialize_notice_view(view)["duplicate_evaluation"]

    assert tuple(nested) == serialization.DUPLICATE_EVALUATION_FIELDS
    assert nested == {"status": "OBTAINED", "candidates": ["CLM-1001", "CLM-1002"], "reason": None}


def _entry() -> AuditEntry:
    return AuditEntry(
        notice_id="notice-1", carrier_code="AAAA", from_state="RECEIVED", to_state="PENDED",
        actor_id="no verified identity", actor_type="SYSTEM", occurred_at=_RECEIVED_AT,
        blockers=(_BLOCKER,), outcome="APPLIED", actor_authenticated=False,
    )
