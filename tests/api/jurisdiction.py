"""Thin, stable test API over the jurisdiction domain area.

Two questions with two callables behind them: which jurisdiction a property
state selects, and what the calendar date is there. features/jurisdiction_date.
feature exercises the second in isolation; features/jurisdiction_selection.
feature exercises the first through intake and reads its outcome off the stored
notice, so what it needs from here is the marking's own spelling rather than a
call - taken from the code that defines it, so a step file cannot keep asserting
a name the product no longer uses.
"""

from datetime import datetime

from claimgate.domain.jurisdiction import JURISDICTION_UNSUPPORTED as _UNSUPPORTED
from claimgate.domain.jurisdiction import resolve_jurisdiction_date as _resolve_jurisdiction_date
from claimgate.domain.models import JurisdictionDateResult

JURISDICTION_UNSUPPORTED = _UNSUPPORTED


def resolve_jurisdiction_date(*, instant: datetime, timezone_name: str) -> JurisdictionDateResult:
    return _resolve_jurisdiction_date(instant, timezone_name)
