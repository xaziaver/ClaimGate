"""Orchestration for POST /notices and GET /notices/{notice_id}.

PHASE2_DESIGN.md's "Record state model" and "HTTP surface"; STATUTORY_REGISTER.md
for the duties discharged here. RECEIVED is written durably, with its receipt
timestamp, before any domain rule runs - a deliberate two-write design, because
that timestamp starts the Fla. Stat. 627.70131(1)(a) seven-calendar-day
acknowledgment clock and must not depend on whether rule evaluation succeeds, is
correct, or even runs at all. There is no rejected, invalid, or discarded state
(CLAUDE.md): once a submission clears the carrier-identity and loss-date schema
checks below, it always reaches RECEIVED and then TRIAGED or PENDED in the same
request. The raw payload is persisted in that same RECEIVED write
(PHASE2_DESIGN.md's audit log section, "the raw inbound payload is stored once,
verbatim, immutable, and referenced by hash") - the receipt and the payload are
one statutory fact, not two, and item 5e's resolution design appends later
payload records to the same per-notice sequence this write starts.

Two refusals happen before that receipt write, and persist differently, both by
decision recorded in ASSUMPTIONS.md:
- An unrecognized carrier_code (checked first, ahead of every other rule) means
  there is no insurer here for a 627.70131(1)(a) duty to arise to - refused with
  nothing persisted at all ("Item 5c's 400 validates against the identity
  reference, not the rules source").
- A loss date that fails to parse as a date at all is still a received claim
  communication under 627.70131(1)(a) - refused, but its raw payload is kept and
  referenced by hash ("A refused submission is still a received communication").

An absent (not merely malformed) loss_date is deliberately not a third case
here: item 5h's presence check does not exist yet, and building it inside this
item would decide that reopening the opposite way from what's ratified. See
_parse_loss_date.

Two further states are reachable only through decisions this item does not
build, and raise rather than invent a status code for them: a carrier the
identity reference recognizes but whose rules entry cannot be resolved (item
5i), and a jurisdiction_timezone this item receives but cannot resolve (item
5g owns deriving and validating it). No scenario in features/notice_intake.feature
reaches either path.

Out of scope here, per QUEUE.md item 5c's own entry: idempotency (5d), the
resolution endpoint (5e), SIU computation and storage (5f), jurisdiction-map
generalization (5g), and duplicate-candidate detection, left unsettled rather
than assumed.
"""

import uuid
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import date, datetime
from typing import Any

from claimgate.domain.carrier_configuration import resolve_carrier_configuration
from claimgate.domain.carrier_identity import CARRIER_IDENTITY_REFERENCE, resolve_carrier_identity
from claimgate.domain.jurisdiction import resolve_jurisdiction_date
from claimgate.domain.models import Candidate, CarrierRules, ValidationBlocker
from claimgate.domain.triage import triage_and_route
from claimgate.domain.validation import validate
from claimgate.shell.store import NoticeStore


@dataclass(frozen=True)
class NoticeFields:
    """The reporter-supplied notice content - everything but the carrier_code
    envelope, the submission instant, and the jurisdiction timezone, which
    are the shell's inputs, not the notice's."""

    policy_number: str = ""
    loss_date: str | None = None
    loss_type: str = ""
    notice_type: str = ""
    claimant_name: str | None = None
    claimant_contact: str | None = None
    incident_description: str | None = None


@dataclass(frozen=True)
class SubmitNoticeResponse:
    status: int
    notice_id: str | None = None
    state: str | None = None
    blockers: tuple[ValidationBlocker, ...] = ()
    severity: str | None = None
    queue: str | None = None
    # Populated only on the schema-invalid refusal: the persisted payload's
    # hash, so the reporter and the carrier can name the same communication.
    reference: str | None = None


@dataclass(frozen=True)
class NoticeView:
    notice_id: str
    state: str
    blockers: tuple[ValidationBlocker, ...]
    severity: str | None
    queue: str | None


def submit_notice(
    store: NoticeStore,
    *,
    carrier_code: str,
    submitted_at: datetime,
    jurisdiction_timezone: str,
    carrier_rules_source: Mapping[str, Mapping[str, Any]],
    fields: NoticeFields,
) -> SubmitNoticeResponse:
    if resolve_carrier_identity(carrier_code, CARRIER_IDENTITY_REFERENCE).value == "REFUSED":
        return SubmitNoticeResponse(status=400)

    raw_payload = asdict(fields)
    loss_date = _parse_loss_date(fields.loss_date)
    if loss_date is None:
        reference = store.refuse_payload(carrier_code, raw_payload)
        return SubmitNoticeResponse(status=400, reference=reference)

    rules = _resolve_rules(carrier_code, carrier_rules_source)
    today = _resolve_today(submitted_at, jurisdiction_timezone)
    candidate = _build_candidate(fields, loss_date)
    return _create_notice(store, carrier_code, candidate, today, rules, raw_payload)


def _create_notice(
    store: NoticeStore,
    carrier_code: str,
    candidate: Candidate,
    today: date,
    rules: CarrierRules,
    raw_payload: Mapping[str, Any],
) -> SubmitNoticeResponse:
    notice_id = str(uuid.uuid4())
    store.receive_notice(notice_id, carrier_code, raw_payload)
    state, blockers, severity, queue = _apply_domain_rules(candidate, today, rules)
    store.record_decision(
        notice_id, state=state, blockers=blockers, severity=severity, queue=queue
    )
    return SubmitNoticeResponse(
        status=201,
        notice_id=notice_id,
        state=state,
        blockers=blockers,
        severity=severity,
        queue=queue,
    )


def get_notice(store: NoticeStore, notice_id: str) -> NoticeView | None:
    record = store.get_notice(notice_id)
    if record is None:
        return None
    return NoticeView(
        notice_id=record.notice_id,
        state=record.state,
        blockers=record.blockers,
        severity=record.severity,
        queue=record.queue,
    )


def _parse_loss_date(raw: str | None) -> date | None:
    """Absent (None) input is item 5h's gap, preserved deliberately: it flows
    through as date.min, unchanged from today's behavior. A present value
    that is not a date at all returns None, the schema-invalid signal."""
    if raw is None:
        return date.min
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


def _build_candidate(fields: NoticeFields, loss_date: date) -> Candidate:
    return Candidate(
        policy_number=fields.policy_number,
        loss_date=loss_date,
        loss_type=fields.loss_type,
        notice_type=fields.notice_type,
        claimant_name=fields.claimant_name,
        claimant_contact=fields.claimant_contact,
        incident_description=fields.incident_description,
    )


def _resolve_rules(
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


def _resolve_today(submitted_at: datetime, jurisdiction_timezone: str) -> date:
    result = resolve_jurisdiction_date(submitted_at, jurisdiction_timezone)
    if result.resolved_date is None:
        raise NotImplementedError(
            "an unrecognized jurisdiction_timezone reaching item 5c is not "
            "handled here - deriving and validating it is item 5g's job"
        )
    return result.resolved_date


def _apply_domain_rules(
    candidate: Candidate, today: date, rules: CarrierRules
) -> tuple[str, tuple[ValidationBlocker, ...], str | None, str | None]:
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
