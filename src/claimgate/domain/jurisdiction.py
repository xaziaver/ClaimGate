"""UTC-instant-to-jurisdiction-date resolution.

Converts a caller-supplied timezone-aware UTC instant to the calendar date in
a caller-supplied IANA timezone. Deciding which zone a given notice gets -
risk location, mailing address, or carrier configuration - is item 5c's, not
this one's. See PHASE2_DESIGN.md's "Jurisdiction axis" and ASSUMPTIONS.md's
"Timezone-correct 'now.'"
"""

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from claimgate.domain.models import JurisdictionDateResult

JURISDICTION_TIMEZONE_UNRECOGNIZED = "JURISDICTION_TIMEZONE_UNRECOGNIZED"


def resolve_jurisdiction_date(instant: datetime, timezone_name: str) -> JurisdictionDateResult:
    try:
        zone = ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError):
        return JurisdictionDateResult("REFUSED", reason=JURISDICTION_TIMEZONE_UNRECOGNIZED)
    return JurisdictionDateResult("RESOLVED", resolved_date=instant.astimezone(zone).date())
