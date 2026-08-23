"""Thin, stable test API over the jurisdiction-date domain area."""

from datetime import datetime

from claimgate.domain.jurisdiction import resolve_jurisdiction_date as _resolve_jurisdiction_date
from claimgate.domain.models import JurisdictionDateResult


def resolve_jurisdiction_date(*, instant: datetime, timezone_name: str) -> JurisdictionDateResult:
    return _resolve_jurisdiction_date(instant, timezone_name)
