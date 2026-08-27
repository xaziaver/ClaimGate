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
The values these fixtures build on live in support.py, not here - see its own
docstring for why that separation is load-bearing rather than tidy.
"""

from collections.abc import Mapping
from datetime import datetime
from typing import Any

import pytest

from claimgate.shell import notice_intake
from claimgate.shell.messages import NoticeFields, ResolutionResponse, SubmitNoticeResponse
from claimgate.shell.notice_intake import submit_notice
from claimgate.shell.resolution import resolve_notice
from claimgate.shell.store import NoticeStore
from tests.shell.support import (
    DEFAULT_FIELDS,
    DEFAULT_RESOLVED_AT,
    DEFAULT_REVIEWER,
    DEFAULT_SUBMITTED_AT,
    IDENTITY_REFERENCE,
    JURISDICTIONS,
    VALID_RULES,
    Resolver,
    RuleEvaluationBugError,
    Submitter,
)


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
        carrier_identity_reference: Mapping[str, Any] = IDENTITY_REFERENCE,
        jurisdiction_reference: Mapping[str, Mapping[str, str]] = JURISDICTIONS,
        carrier_rules_source: dict[str, object] | None = None,
        fields: NoticeFields = DEFAULT_FIELDS,
        idempotency_key: str | None = None,
    ) -> SubmitNoticeResponse:
        source = carrier_rules_source if carrier_rules_source is not None else {"AAAA": VALID_RULES}
        return submit_notice(
            store,
            carrier_code=carrier_code,
            submitted_at=submitted_at,
            carrier_identity_reference=carrier_identity_reference,
            jurisdiction_reference=jurisdiction_reference,
            carrier_rules_source=source,
            fields=fields,
            idempotency_key=idempotency_key,
        )

    return _submit


@pytest.fixture
def resolve(store: NoticeStore) -> Resolver:
    """One resolution against the fixture's store, defaulted the way `submit` is
    so each test states only what it varies."""

    def _resolve(
        notice_id: str,
        actor_id: str | None = DEFAULT_REVIEWER,
        resolved_at: datetime = DEFAULT_RESOLVED_AT,
        jurisdiction_reference: Mapping[str, Mapping[str, str]] = JURISDICTIONS,
        carrier_rules_source: dict[str, object] | None = None,
        supplied: dict[str, Any] | None = None,
    ) -> ResolutionResponse:
        source = carrier_rules_source if carrier_rules_source is not None else {"AAAA": VALID_RULES}
        return resolve_notice(
            store,
            notice_id,
            actor_id=actor_id,
            resolved_at=resolved_at,
            jurisdiction_reference=jurisdiction_reference,
            carrier_rules_source=source,
            supplied=supplied if supplied is not None else {},
        )

    return _resolve


@pytest.fixture
def rule_evaluation_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make apply_domain_rules raise. Patched on notice_intake rather than on
    rules.py, where it now lives, because the name the intake path resolves is
    the one this module imported - patching the definition would leave that
    binding pointing at the original. Patched at module level on purpose: the
    point is that the receipt has already committed by the time anything in
    rule evaluation can go wrong, and only a real raise from inside that step
    proves the transaction boundary is where it is claimed to be."""

    def _raise(*_: object, **__: object) -> None:
        raise RuleEvaluationBugError("rule evaluation is broken")

    monkeypatch.setattr(notice_intake, "apply_domain_rules", _raise)
