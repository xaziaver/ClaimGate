"""Which jurisdiction governs a notice, and the date its calendar is on.

Two questions, kept apart. `select_jurisdiction` answers "which statutory
ruleset applies", from the insured risk's property state and nothing else -
never the carrier's domicile and never the reporter's address
(PHASE2_DESIGN.md, "Jurisdiction axis"). `resolve_jurisdiction_date` answers
"what is today there", from a caller-supplied timezone-aware UTC instant.

**The lookup is keyed by jurisdiction code and reads the key for nothing
else.** It selects an entry and passes its value through; no code path here or
downstream branches on which jurisdiction came back. That is the same shape
carrier_configuration.py's lookup has, deliberately - QUEUE.md item 5a makes
structural identity between the two the check that neither has become a branch
wearing a lookup's name.

**An entry that exists and cannot be read is a third outcome, not a miss.** A
jurisdiction this deployment configured whose entry names no timezone is our own
defect; resolving it to UNSUPPORTED would answer that misconfiguration by
telling a reporter their state is not supported, which is false. The shell
escalates it, exactly as it escalates a carrier whose rules entry cannot be
resolved (QUEUE.md item 5i's class of question).

**A property state with no entry is not a refusal.** There is no rejected,
invalid or discarded state (CLAUDE.md), and the Fla. Stat. 627.70131(1)(a)
acknowledgment clock starts at receipt whether or not this deployment knows the
law where the property sits. UNSUPPORTED means the notice proceeds and carries
JURISDICTION_UNSUPPORTED for a person.

**The match is exact** (ASSUMPTIONS.md, "`property_state` is matched exactly,
and a miss is marked rather than normalized", ratified 2026-08-26). Nothing is
upper-cased, trimmed into a match, or mapped from a name to a code: case folding
is the first step of a chain that ends in inferring what the reporter meant, on
the field that selects which state's law applies.
"""

from collections.abc import Mapping
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from claimgate.domain.models import (
    Jurisdiction,
    JurisdictionDateResult,
    JurisdictionSelectionResult,
)

JURISDICTION_TIMEZONE_UNRECOGNIZED = "JURISDICTION_TIMEZONE_UNRECOGNIZED"
# What a notice whose property state selects no jurisdiction carries for a
# person. Lower-case because it is a marking on a record and not a reason code:
# features/jurisdiction_selection.feature spells it this way in both of the
# columns that assert it.
JURISDICTION_UNSUPPORTED = "jurisdiction_unsupported"
TIMEZONE = "timezone"

# The shipped map, with exactly one entry populated - a genuine lookup, not a
# constant dressed up as one. It is passed in at the shell boundary rather than
# read from here by anything under src/, the way CARRIER_IDENTITY_REFERENCE is,
# so a deployment substitutes its own and the swappability tests can hand over a
# different one without patching a module.
#
# Florida is one entry and therefore one timezone, which is wrong for the nine
# and a half panhandle counties on America/Chicago (49 CFR 71.5(f);
# ASSUMPTIONS.md, ratified 2026-08-26). Eastern's date is never behind
# Central's, so both skewed answers are tolerant and no false
# LOSS_DATE_IN_FUTURE is possible. Revisit when a key finer than the state
# exists, not before.
JURISDICTION_REFERENCE: Mapping[str, Mapping[str, str]] = {
    "FL": {TIMEZONE: "America/New_York"},
}


def select_jurisdiction(
    jurisdiction_code: str | None, reference: Mapping[str, Mapping[str, str]]
) -> JurisdictionSelectionResult:
    if jurisdiction_code is None:
        return JurisdictionSelectionResult("UNSUPPORTED")
    entry = reference.get(jurisdiction_code)
    if entry is None:
        return JurisdictionSelectionResult("UNSUPPORTED")
    timezone = entry.get(TIMEZONE)
    if timezone is None:
        return JurisdictionSelectionResult("MALFORMED")
    return JurisdictionSelectionResult("SELECTED", Jurisdiction(timezone=timezone))


def resolve_jurisdiction_date(instant: datetime, timezone_name: str) -> JurisdictionDateResult:
    try:
        zone = ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError):
        return JurisdictionDateResult("REFUSED", reason=JURISDICTION_TIMEZONE_UNRECOGNIZED)
    return JurisdictionDateResult("RESOLVED", resolved_date=instant.astimezone(zone).date())
