"""What each of phase 2's outward surfaces is allowed to carry.

PHASE2_DESIGN.md's "SIU handling" point 2: "Response serializers are allow-list
based: explicitly named fields only, never a deny-list. A deny-list leaks every
field added after it was written." There is no HTTP layer in this project yet, so
what these render are the message types themselves rather than a wire format;
what matters now is the mechanism, which is the part that would be expensive to
retrofit once several serializers exist.

Each enumeration below names its surface's fields in full.
tests/shell/test_serialization.py compares every one of them against the type it
belongs to, so a field added to that type and not added here does not quietly
appear on the surface and does not quietly vanish from it either - the test fails
until someone decides which of the two it should be. Forcing that decision is
the whole difference from a deny-list, which decides it by default and always in
the direction of the leak.

**Nothing here knows what an SIU indicator is, and that is the point.** The trail
is its own table, reachable from none of the types these functions accept, so
there is no field for an allow-list to have to exclude and no future field on
`notices` that could carry one in by accident.
"""

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from claimgate.shell.messages import NoticeView, ResolutionResponse, SubmitNoticeResponse
from claimgate.shell.records import AuditEntry

SUBMIT_NOTICE_RESPONSE_FIELDS = (
    "status", "notice_id", "state", "blockers", "severity", "queue", "received_at", "reference",
)
RESOLUTION_RESPONSE_FIELDS = ("status", "notice_id", "state", "blockers", "severity", "queue")
NOTICE_VIEW_FIELDS = ("notice_id", "state", "blockers", "severity", "queue")
AUDIT_ENTRY_FIELDS = (
    "notice_id", "carrier_code", "from_state", "to_state", "actor_id", "actor_type",
    "occurred_at", "blockers", "outcome", "actor_authenticated", "note", "ruleset_version",
    "build_sha",
)


def serialize_response(response: SubmitNoticeResponse | ResolutionResponse) -> dict[str, Any]:
    """The two response bodies through their own allow-lists. They are separate
    lists and not one shared list, because the fields they carry differ and a
    list wide enough for both would be a deny-list wearing an allow-list's
    name."""
    if isinstance(response, SubmitNoticeResponse):
        return _project(response, SUBMIT_NOTICE_RESPONSE_FIELDS)
    return _project(response, RESOLUTION_RESPONSE_FIELDS)


def serialize_notice_view(view: NoticeView) -> dict[str, Any]:
    return _project(view, NOTICE_VIEW_FIELDS)


def serialize_audit_entry(entry: AuditEntry) -> dict[str, Any]:
    """PHASE2_DESIGN.md's point 3: SIU indicator detail never appears in a
    standard audit entry, which would otherwise make the audit endpoint the leak
    path. Nothing on AuditEntry carries any, and this list is what keeps that
    true of anything added to it later."""
    return _project(entry, AUDIT_ENTRY_FIELDS)


def _project(message: Any, allowed: Sequence[str]) -> dict[str, Any]:
    return {name: _rendered(getattr(message, name)) for name in allowed}


def _rendered(value: Any) -> Any:
    """Blockers and instants are the only two field types on these surfaces that
    are not already a string, a number, a bool or None."""
    if isinstance(value, tuple):
        return [{"code": blocker.code, "field": blocker.field} for blocker in value]
    if isinstance(value, datetime):
        return value.isoformat()
    return value

