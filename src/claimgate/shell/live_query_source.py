"""What a live-query source answers with, and how it becomes the domain's
shapes: the vendor-facing half of the live-query implementation.

A source is anything satisfying PolicySource or ClaimsSource below - the
in-process fixture under tests/fixtures/ here, and for a real integration the
mapping it writes over its own system's API (PHASE3_DESIGN.md: exemplar shapes
are named, vendors never). It answers in a wire shape of plain mappings and
sequences, the way a JSON API does, and this module is the one place that
shape is read. Nothing crosses into a port envelope unparsed: a value of the
wrong type, a missing key, a date that is not a date or a vocabulary word this
module does not know raises here, and live_query_ports.py answers
SOURCE_MALFORMED for it. Any exception at all - the parsers are not careful
about which - because the alternative is a half-read answer.

The wire shape, as this module reads it:

- search: a sequence of candidates, each `{"policy_reference", "policy_number",
  "named_insureds": [...], "matched_by": "policy_number" |
  "insured_name_and_postal_code"}`. The source says how it matched, in its own
  words; the two are mapped onto the domain's arm names.
- term history: `{"terms": [{"effective", "expiration", "status_changes":
  [{"kind": "cancellation" | "reinstatement", "effective"}]}], "prior_coverage":
  {"effective", "ending"} | null}`. Dates are ISO strings. The horizon is not
  the source's to state: the binding carries it (bindings.py) and the port
  stamps it on every history.
- existing claims: a sequence of `{"claim_id", "policy_number", "loss_date",
  "loss_type"}`, one per claim on the policy.

A source that cannot search on the identifier combination it was handed - one
with no insured-name search, given a name and postal code and no number -
raises UnsupportedSearchError, which the port answers IDENTIFIERS_INSUFFICIENT;
an unknown policy reference is the source's own failure and it raises whatever
it raises.
"""

from collections.abc import Mapping, Sequence
from datetime import date
from typing import Final, Protocol

from claimgate.domain.coverage import (
    CANCELLATION,
    REINSTATEMENT,
    PolicyTerm,
    PriorCoverage,
    StatusChangeKind,
    TermHistory,
    TermStatusChange,
)
from claimgate.domain.models import ExistingClaim
from claimgate.domain.policy_identification import INSURED_NAME_AND_POSTAL_CODE, POLICY_NUMBER
from claimgate.shell.ports import OBTAINED, MatchBasis, PolicyCandidate

Record = Mapping[str, object]


class UnsupportedSearchError(Exception):
    """The source cannot search on the identifiers it was handed."""


class MalformedAnswerError(Exception):
    """The source can tell, before any parser sees it, that what it holds is
    not its own shape - an extract file that is not JSON, a policies file that
    is not a list (item 7i). The port answers SOURCE_MALFORMED for it, as it
    does for a shape the parsers reject."""


class PolicySource(Protocol):
    def search(
        self, policy_number: str | None, insured_name: str | None, risk_postal_code: str | None
    ) -> object: ...

    def term_history(self, policy_reference: str) -> object: ...


class ClaimsSource(Protocol):
    def existing_claims(self, policy_reference: str) -> object: ...


_MATCH_BASES: Final[Mapping[str, MatchBasis]] = {
    "policy_number": POLICY_NUMBER,
    "insured_name_and_postal_code": INSURED_NAME_AND_POSTAL_CODE,
}
_STATUS_KINDS: Final[Mapping[str, StatusChangeKind]] = {
    "cancellation": CANCELLATION,
    "reinstatement": REINSTATEMENT,
}


def parse_candidates(raw: object) -> tuple[PolicyCandidate, ...]:
    return tuple(_candidate(record) for record in _records(raw))


def parse_term_history(raw: object, history_from: date | None) -> TermHistory:
    record = _record(raw)
    prior = record["prior_coverage"]
    return TermHistory(
        value=OBTAINED,
        terms=tuple(_term(item) for item in _records(record["terms"])),
        history_from=history_from,
        prior_coverage=None if prior is None else _prior_coverage(_record(prior)),
    )


def parse_claims(raw: object) -> tuple[ExistingClaim, ...]:
    return tuple(_claim(record) for record in _records(raw))


def _candidate(record: Record) -> PolicyCandidate:
    return PolicyCandidate(
        policy_reference=_text(record, "policy_reference"),
        policy_number=_text(record, "policy_number"),
        named_insureds=tuple(_texts(record["named_insureds"])),
        match_basis=_MATCH_BASES[_text(record, "matched_by")],
    )


def _term(record: Record) -> PolicyTerm:
    return PolicyTerm(
        effective=_day(record, "effective"),
        expiration=_day(record, "expiration"),
        status_changes=tuple(_status_change(item) for item in _records(record["status_changes"])),
    )


def _status_change(record: Record) -> TermStatusChange:
    return TermStatusChange(
        kind=_STATUS_KINDS[_text(record, "kind")], effective=_day(record, "effective")
    )


def _prior_coverage(record: Record) -> PriorCoverage:
    return PriorCoverage(effective=_day(record, "effective"), ending=_day(record, "ending"))


def _claim(record: Record) -> ExistingClaim:
    return ExistingClaim(
        claim_id=_text(record, "claim_id"),
        policy_number=_text(record, "policy_number"),
        loss_date=_day(record, "loss_date"),
        loss_type=_text(record, "loss_type"),
    )


def _records(raw: object) -> list[Record]:
    return [_record(item) for item in _sequence(raw)]


def _record(raw: object) -> Record:
    if not isinstance(raw, Mapping):
        raise TypeError(f"expected a record, got {type(raw).__name__}")
    return raw


def _sequence(raw: object) -> Sequence[object]:
    # A string is a Sequence of its characters and would parse as one.
    if isinstance(raw, str | bytes) or not isinstance(raw, Sequence):
        raise TypeError(f"expected a sequence, got {type(raw).__name__}")
    return raw


def _texts(raw: object) -> list[str]:
    return [_string(item) for item in _sequence(raw)]


def _text(record: Record, key: str) -> str:
    return _string(record[key])


def _string(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError(f"expected text, got {type(value).__name__}")
    return value


def _day(record: Record, key: str) -> date:
    return date.fromisoformat(_text(record, key))
