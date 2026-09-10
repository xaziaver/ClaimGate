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

**Item 5i put `error` on both response surfaces, and this file is where that was
decided rather than defaulted.** Adding the field to the two response types made
this module's test fail until someone chose, which is the mechanism working. It
is named because both specs assert the caller reads it: one status carries both
deployment faults, so a client that could not read the code from the body would
have no way to tell them apart at all. It carries no SIU detail and cannot -
`faults.py`'s enumeration is closed, two members, both about this deployment's
configuration.

**Item 5g put a notice column on this surface and deliberately kept a second one
off it.** `jurisdiction_marking` is here because a marking nobody can read is not
a marking: the notice is "still received, still triaged, and visible as needing a
person", and this view is the only surface a person reads a notice from in phase
2. The future-dated-loss determination beside it on the record is not here, for
the reason `NoticeRecord.pended_at` and `resolved_at` are not: it is a stored
fact about the notice rather than part of what the view shows. That choice has a
second effect worth naming, because it is the kind that is invisible until it
bites. The determination's reason enumeration contains `NO_JURISDICTION_DATE`,
which is a different code from the SIU reason code of the same spelling
(CLAUDE.md, closed enumerations) - but `features/siu_separation.feature`'s leak
negatives read the whole serialized surface as text and cannot tell two codes of
one spelling apart. Putting the determination on an ordinary surface would make
a legitimate value indistinguishable from the leak those negatives exist to
catch, and the pressure would then be on the negatives to get looser.

**Item 7f put the coverage verification on the notice view, through an
allow-list of its own.** PHASE3_DESIGN.md's "Persistence" makes both phase-3
tables ordinary attributes, and the view names what features/policy_match.feature
reads: the match, the matched reference and the identifiers it was found on
(item 7g), the identification's reason, the
term verdict with the deciding term's dates, the continuous-coverage date with
its reason, and the instant the answer reflects. It is a nested surface with a
list of its own rather than nine more names on the notice's list, so the
mechanism above - a field added to the type fails until someone decides - holds
for the verification's fields exactly as it does for the notice's. Nothing on
it can name an SIU indicator: the SIU event that reads the date is its own
table, and the verification records the date, never the indicator.

**Item 7h put the duplicate evaluation beside it on the same terms**: its own
nested list - status, candidates, reason - as features/duplicate_evaluation.feature
reads it, an ordinary attribute (PHASE3_DESIGN.md, "Persistence"), and the
candidates a list of claim ids the way the blockers are a list of their two names.
"""

from collections.abc import Sequence
from datetime import date
from typing import Any

from claimgate.domain.models import ValidationBlocker
from claimgate.shell.coverage_verifications import CoverageVerificationView
from claimgate.shell.duplicate_evaluations import DuplicateEvaluationView
from claimgate.shell.messages import NoticeView, ResolutionResponse, SubmitNoticeResponse
from claimgate.shell.records import AuditEntry

SUBMIT_NOTICE_RESPONSE_FIELDS = (
    "status", "notice_id", "state", "blockers", "severity", "queue", "received_at", "reference",
    "error",
)
RESOLUTION_RESPONSE_FIELDS = (
    "status", "notice_id", "state", "blockers", "severity", "queue", "error",
)
NOTICE_VIEW_FIELDS = (
    "notice_id", "state", "blockers", "severity", "queue", "jurisdiction_marking",
    "coverage_verification", "duplicate_evaluation",
)
COVERAGE_VERIFICATION_FIELDS = (
    "policy_match", "matched_policy", "identified_on", "reason", "term_in_force",
    "deciding_term_effective", "deciding_term_expiration", "continuous_coverage_date",
    "continuous_coverage_reason", "as_of",
)
DUPLICATE_EVALUATION_FIELDS = ("status", "candidates", "reason")
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


# The nested surfaces, each through a list of its own: a blocker's two names,
# the verification's fields, and the duplicate evaluation's (item 7h).
_NESTED: dict[type, Sequence[str]] = {
    ValidationBlocker: ("code", "field"),
    CoverageVerificationView: COVERAGE_VERIFICATION_FIELDS,
    DuplicateEvaluationView: DUPLICATE_EVALUATION_FIELDS,
}


def _rendered(value: Any) -> Any:
    """Tuples - the blockers, and the evaluation's candidate ids - render as
    lists of their rendered items; dates and instants as ISO text, a datetime
    being a date so one test renders both; the nested surfaces through their
    own lists; everything else is already a string, a number, a bool or None."""
    if isinstance(value, tuple):
        return [_rendered(item) for item in value]
    if isinstance(value, date):
        return value.isoformat()
    nested = _NESTED.get(type(value))
    return value if nested is None else _project(value, nested)

