"""The domain rules as the shell runs them, and the translations they need.

Extracted from notice_intake.py in item 5e because the resolution path has to
run the same ones. That is not a convenience: ASSUMPTIONS.md's item 5e decision
2(a) says the full validation runs over a resolution's merged current view
because there must be "one definition of 'no blocker', the same one intake uses
- a second definition for this endpoint would be two meanings of TRIAGED." A
single callable is how that stays true; two copies would let it stop being true
without any gate noticing.

Nothing here reads a clock. `resolve_today` converts a caller-supplied instant,
whichever call supplied it - the submission's for intake, the resolution's own
for a resolution (ASSUMPTIONS.md, "One receipt clock, not two", as extended to
the resolution path).

**Two lookups, one shape** (QUEUE.md item 5a). The carrier's rules come from a
mapping keyed by carrier_code and the jurisdiction from a mapping keyed by the
property's state; each selects an entry and passes its value through, and
nothing here or downstream reads either key to choose behaviour. If the two ever
stop matching structurally, one of them has become a branch wearing a lookup's
name.

Three states raise rather than invent a status code. A carrier the identity
reference recognizes but whose rules entry cannot be resolved is item 5i's, and
that raise is unchanged. The other two are item 5g's raise rebuilt rather than
removed: the parameter that caused it is gone - no reporter supplies a timezone
name any more - and what is left is this deployment's own map, whose entry can
name no timezone at all or name one this system does not recognize. Both are
defects in our own configuration rather than in anything a reporter sent, so
both are item 5i's class of problem rather than this item's ("A carrier this
deployment administers but cannot configure is our defect, not the reporter's").
Marking such a notice jurisdiction_unsupported would answer a misconfiguration
by telling the reporter their state is not supported, which is false. No
scenario reaches any of the three.
"""

from collections.abc import Mapping
from datetime import date, datetime
from typing import Any

from claimgate.domain.carrier_configuration import resolve_carrier_configuration
from claimgate.domain.jurisdiction import (
    JURISDICTION_UNSUPPORTED,
    resolve_jurisdiction_date,
    select_jurisdiction,
)
from claimgate.domain.models import Candidate, CarrierRules, Jurisdiction
from claimgate.domain.triage import triage_and_route
from claimgate.domain.validation import validate
from claimgate.shell.messages import Decision, NoticeFields


def parse_loss_date(raw: str | None) -> date | None:
    """Absent (None) input is item 5h's gap, preserved deliberately: it flows
    through as date.min, unchanged from today's behavior, because building 5h's
    presence check here would decide that reopening the opposite way from what
    is ratified. A present value that is not a date at all returns None, the
    schema-invalid signal."""
    if raw is None:
        return date.min
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


def build_candidate(fields: NoticeFields, loss_date: date) -> Candidate:
    """`property_state` is deliberately not carried across. It selects the
    jurisdiction at this boundary and the domain never sees it - a domain that
    could read which state a notice is from is a domain that could branch on
    it (PHASE2_DESIGN.md, "Jurisdiction axis")."""
    return Candidate(
        policy_number=fields.policy_number,
        loss_date=loss_date,
        loss_type=fields.loss_type,
        notice_type=fields.notice_type,
        claimant_name=fields.claimant_name,
        claimant_contact=fields.claimant_contact,
        incident_description=fields.incident_description,
    )


def resolve_rules(
    carrier_code: str, rules_source: Mapping[str, Mapping[str, Any]]
) -> CarrierRules:
    result = resolve_carrier_configuration(carrier_code, rules_source)
    if result.rules is None:
        raise NotImplementedError(
            "carrier is identity-recognized but its rules entry could not be "
            "resolved - the status code for this is item 5i's to decide, not "
            "built here"
        )
    return result.rules


def resolve_jurisdiction(
    property_state: str | None, jurisdiction_reference: Mapping[str, Mapping[str, str]]
) -> Jurisdiction | None:
    """The jurisdiction the insured property's state selects, or None where this
    deployment has no entry for it. None is not an error: the notice proceeds,
    carrying the marking below for a person. An entry that exists and names no
    timezone is a different fact and escalates - see the module docstring."""
    result = select_jurisdiction(property_state, jurisdiction_reference)
    if result.value == "MALFORMED":
        raise NotImplementedError(
            "this deployment's jurisdiction map holds an entry naming no "
            "timezone - our own misconfiguration, whose status code is item "
            "5i's class of question and is not decided"
        )
    return result.jurisdiction


def marking_for(jurisdiction: Jurisdiction | None) -> str | None:
    return None if jurisdiction is not None else JURISDICTION_UNSUPPORTED


def resolve_today(instant: datetime, jurisdiction: Jurisdiction | None) -> date | None:
    """The jurisdiction's calendar date for a caller-supplied instant, or None
    where no jurisdiction was selected and there is no calendar to ask."""
    if jurisdiction is None:
        return None
    result = resolve_jurisdiction_date(instant, jurisdiction.timezone)
    if result.resolved_date is None:
        raise NotImplementedError(
            "this deployment's jurisdiction map holds a timezone this system "
            "does not recognize - our own misconfiguration, whose status code "
            "is item 5i's class of question and is not decided"
        )
    return result.resolved_date


def apply_domain_rules(
    candidate: Candidate, jurisdiction: Jurisdiction | None, today: date | None,
    rules: CarrierRules,
) -> Decision:
    """One notice's whole decision. The resolution path calls this over a merged
    current view and intake calls it over a submission; both get the same answer
    to "is anything missing" by construction."""
    result = validate(
        candidate,
        today,
        claimant_name_required=rules.claimant_name_required,
        claimant_contact_required=rules.claimant_contact_required,
        recognized_policy_number_prefixes=rules.recognized_policy_number_prefixes,
    )
    marking, determination = marking_for(jurisdiction), result.future_dated_loss
    if result.blockers:
        return Decision("PENDED", result.blockers, None, None, marking, determination)
    outcome = triage_and_route(candidate)
    return Decision("TRIAGED", (), outcome.severity, outcome.queue, marking, determination)
