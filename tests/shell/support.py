"""Values and types the shell-layer tests share.

A plain module, not `conftest.py`, because pytest imports a `conftest.py` in a
directory with no `__init__.py` under its own module name: importing the same
file again as `tests.shell.conftest` produces a second module object, and a
class defined there then has two identities that `except` and `isinstance` tell
apart. Constants survive that; an exception class does not.
"""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from claimgate.domain.carrier_identity import CARRIER_IDENTITY_REFERENCE
from claimgate.domain.jurisdiction import JURISDICTION_REFERENCE
from claimgate.shell.messages import NoticeFields, ResolutionResponse, SubmitNoticeResponse

# The two configuration sources every call names explicitly (item 5g). Bound
# here rather than defaulted inside the shell so a test wanting a different
# deployment hands over a different mapping - which is what the swappability
# tests do - instead of patching a module.
IDENTITY_REFERENCE = CARRIER_IDENTITY_REFERENCE
JURISDICTIONS = JURISDICTION_REFERENCE
VALID_RULES: dict[str, Any] = {
    "claimant_name_required": False,
    "claimant_contact_required": False,
    "recognized_policy_number_prefixes": ["HO"],
    "late_reporting_threshold_days": None,
    "recent_inception_threshold_days": 30,
    "window_days": 60,
}
DEFAULT_SUBMITTED_AT = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
DEFAULT_RESOLVED_AT = datetime(2026, 6, 2, 9, 0, tzinfo=UTC)
# property_state is "FL", which is what makes a jurisdiction date exist for
# these fixtures at all: without a selected jurisdiction there is no calendar,
# the future-dated-loss determination is NOT_EVALUATED and the late reporting
# indicator has no day to count to. Tests that care about that say so with
# fields of their own.
DEFAULT_FIELDS = NoticeFields(
    policy_number="HO-1234567", loss_date="2026-06-01", loss_type="wind_hail",
    notice_type="INITIAL", property_state="FL",
)
# Lands PENDED on MISSING_REQUIRED_FIELD:policy_number and nothing else, so a
# resolution against it has exactly one thing to clear.
PENDING_FIELDS = NoticeFields(
    policy_number="", loss_date="2026-06-01", loss_type="wind_hail",
    notice_type="INITIAL", property_state="FL",
)
DEFAULT_REVIEWER = "adjuster-4471"

Submitter = Callable[..., SubmitNoticeResponse]
Resolver = Callable[..., ResolutionResponse]


class RuleEvaluationBugError(RuntimeError):
    """Stands in for a bug in domain rule evaluation - the failure
    PHASE2_DESIGN.md's two-write receipt exists to survive."""


class AuditWriteError(RuntimeError):
    """Stands in for whatever could go wrong on the last write a resolution
    makes, so the rollback has something to roll back."""


class SiuWriteError(RuntimeError):
    """Raised after the SIU events have been written and before the transaction
    commits, so a test can tell "the events were never written" apart from "the
    events were written and rolled back with the transition they belong to."
    Only the second is what item 5f decision 1 asks for."""
