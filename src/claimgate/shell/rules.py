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

Two states raise rather than invent a status code, and both raises moved here
intact: a carrier the identity reference recognizes but whose rules entry cannot
be resolved (item 5i), and a jurisdiction_timezone this item cannot resolve
(item 5g). No scenario reaches either.
"""

from collections.abc import Mapping
from datetime import date, datetime
from typing import Any

from claimgate.domain.carrier_configuration import resolve_carrier_configuration
from claimgate.domain.jurisdiction import resolve_jurisdiction_date
from claimgate.domain.models import Candidate, CarrierRules, ValidationBlocker
from claimgate.domain.triage import triage_and_route
from claimgate.domain.validation import validate
from claimgate.shell.messages import NoticeFields


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


def resolve_today(instant: datetime, jurisdiction_timezone: str) -> date:
    result = resolve_jurisdiction_date(instant, jurisdiction_timezone)
    if result.resolved_date is None:
        raise NotImplementedError(
            "an unrecognized jurisdiction_timezone reaching item 5c is not "
            "handled here - deriving and validating it is item 5g's job"
        )
    return result.resolved_date


def apply_domain_rules(
    candidate: Candidate, today: date, rules: CarrierRules
) -> tuple[str, tuple[ValidationBlocker, ...], str | None, str | None]:
    """State, blockers, severity and queue for one candidate. The resolution
    path calls this over a merged current view and intake calls it over a
    submission; both get the same answer to "is anything missing" by
    construction."""
    result = validate(
        candidate,
        today,
        claimant_name_required=rules.claimant_name_required,
        claimant_contact_required=rules.claimant_contact_required,
        recognized_policy_number_prefixes=rules.recognized_policy_number_prefixes,
    )
    if result.blockers:
        return "PENDED", result.blockers, None, None
    outcome = triage_and_route(candidate)
    return "TRIAGED", (), outcome.severity, outcome.queue
