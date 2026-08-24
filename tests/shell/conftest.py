"""Shared fixtures for the shell-layer unit tests.

These live under tests/shell/ rather than tests/unit/ because mutmut's
source_paths is scoped to src/claimgate/domain/ while its test selection still
hands it the whole tests/unit/ tree - a shell import inside that sandbox fails
to resolve at collection (docs/harness-findings.md). Code mutation therefore
reaches none of the shell, which is exactly why these tests carry the weight
they do: for src/claimgate/shell/, they and the acceptance suite are the whole
of the protection.

Every store here is ":memory:". The database path is a constructor argument
with no default (ASSUMPTIONS.md, "Persistence engine"), so a test has to say so.
"""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import pytest

from claimgate.shell.notice_intake import NoticeFields, SubmitNoticeResponse, submit_notice
from claimgate.shell.store import NoticeStore

VALID_RULES: dict[str, Any] = {
    "claimant_name_required": False,
    "claimant_contact_required": False,
    "recognized_policy_number_prefixes": ["HO"],
    "late_reporting_threshold_days": None,
    "recent_inception_threshold_days": 30,
    "window_days": 60,
}
DEFAULT_SUBMITTED_AT = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
DEFAULT_FIELDS = NoticeFields(
    policy_number="HO-1234567", loss_date="2026-06-01", loss_type="wind_hail", notice_type="INITIAL"
)

Submitter = Callable[..., SubmitNoticeResponse]


@pytest.fixture
def store() -> NoticeStore:
    return NoticeStore(":memory:")


@pytest.fixture
def submit(store: NoticeStore) -> Submitter:
    """One submission against the fixture's store, with every input defaulted
    to something that reaches TRIAGED, so each test states only what it varies."""

    def _submit(
        carrier_code: str = "AAAA",
        submitted_at: datetime = DEFAULT_SUBMITTED_AT,
        jurisdiction_timezone: str = "America/New_York",
        carrier_rules_source: dict[str, Any] | None = None,
        fields: NoticeFields = DEFAULT_FIELDS,
    ) -> SubmitNoticeResponse:
        source = carrier_rules_source if carrier_rules_source is not None else {"AAAA": VALID_RULES}
        return submit_notice(
            store,
            carrier_code=carrier_code,
            submitted_at=submitted_at,
            jurisdiction_timezone=jurisdiction_timezone,
            carrier_rules_source=source,
            fields=fields,
        )

    return _submit
