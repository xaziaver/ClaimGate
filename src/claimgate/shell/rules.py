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

**Three states raise a typed deployment fault** (item 5i, ratified 2026-08-28):
a carrier the identity reference recognizes but whose rules entry cannot be
resolved, and this deployment's own jurisdiction map holding an entry that names
no timezone at all or names one this system does not recognize. All three are
defects in our own configuration rather than in anything a reporter sent, so
none of them is a 4xx ("A carrier this deployment administers but cannot
configure is our defect, not the reporter's"). Marking such a notice
jurisdiction_unsupported would answer a misconfiguration by telling the reporter
their state is not supported, which is false.

The raise is here and the answer is not, because the answer differs by endpoint
and the fault does not: intake receipts the submission anyway and a resolution
attempt leaves no trace. faults.py carries the codes and the reasoning; the two
endpoints catch and answer. Nothing here knows a status code.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Literal

from claimgate.domain.carrier_configuration import resolve_carrier_configuration
from claimgate.domain.jurisdiction import (
    JURISDICTION_UNSUPPORTED,
    resolve_jurisdiction_date,
    select_jurisdiction,
)
from claimgate.domain.models import Candidate, CarrierRules, Jurisdiction
from claimgate.domain.triage import triage_and_route
from claimgate.domain.validation import validate
from claimgate.shell.faults import (
    CARRIER_RULES_UNRESOLVABLE,
    JURISDICTION_MAP_UNUSABLE,
    DeploymentFaultError,
)
from claimgate.shell.messages import Decision, NoticeFields

LossDateParseValue = Literal["PARSED", "ABSENT", "UNPARSEABLE"]


@dataclass(frozen=True)
class LossDateParse:
    """Same convention as the domain's result types: loss_date is populated only
    when value is PARSED. Three outcomes and not two because one None used to
    carry two different facts (item 5h) - "the reporter stated no date", which
    is a domain blocker the notice is pended on, and "what arrived is not a date
    at all", which is the schema-invalid refusal. Collapsing them made an absent
    date indistinguishable from a malformed one at the only boundary that can
    still tell them apart."""

    value: LossDateParseValue
    loss_date: date | None = None


def parse_loss_date(raw: str | None) -> LossDateParse:
    """ABSENT flows on to the Candidate as None and becomes
    MISSING_REQUIRED_FIELD:loss_date in the domain (ASSUMPTIONS.md, "An absent
    loss date is a domain blocker, not a schema refusal"). UNPARSEABLE never
    reaches a Candidate at all: what each caller does with it is that endpoint's
    decision, not this function's."""
    if raw is None:
        return LossDateParse("ABSENT")
    try:
        return LossDateParse("PARSED", date.fromisoformat(raw))
    except ValueError:
        return LossDateParse("UNPARSEABLE")


def build_candidate(fields: NoticeFields, loss_date: date | None) -> Candidate:
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
    """A carrier this deployment claims to administer whose rules will not load
    is our defect, not the reporter's: the fault says which, and the endpoint
    that catches it decides what is kept."""
    result = resolve_carrier_configuration(carrier_code, rules_source)
    if result.rules is None:
        raise DeploymentFaultError(CARRIER_RULES_UNRESOLVABLE)
    return result.rules


def resolve_jurisdiction(
    property_state: str | None, jurisdiction_reference: Mapping[str, Mapping[str, str]]
) -> Jurisdiction | None:
    """The jurisdiction the insured property's state selects, or None where this
    deployment has no entry for it. None is not an error: the notice proceeds,
    carrying the marking below for a person. An entry that exists and names no
    timezone is a different fact and faults - see the module docstring."""
    result = select_jurisdiction(property_state, jurisdiction_reference)
    if result.value == "MALFORMED":
        raise DeploymentFaultError(JURISDICTION_MAP_UNUSABLE)
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
        raise DeploymentFaultError(JURISDICTION_MAP_UNUSABLE)
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
