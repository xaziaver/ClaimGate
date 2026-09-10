"""The extract shape's source half: a generated file set on disk, read by
extract_ports.py under the binding's budget.

PHASE3_DESIGN.md, "Swappability proof": the second conforming shape per port,
beside the live-query pair. Where a live source answers at call time, an
extract answers from files written at one instant, and that instant is what
every answer reflects: a policy bound after the extract ran is not in it and
is NOT_FOUND as of then, which is the one user-visible difference between the
shapes (features/policy_match.feature, "the instant the answer reflects").

The file set, one JSON document per file, as this module reads it:

- `manifest.json`: `{"generated_at": "<instant with offset>", "history_from":
  "complete" | "<ISO date>", "searchable_by": ["policy_number",
  "insured_name_and_postal_code"]}`. The instant is stamped on every answer.
  `history_from` is the extract's own statement of how far back its terms go;
  the port stamps the binding's horizon as the protocol requires, and the two
  disagreeing is an open decision (ASSUMPTIONS.md, 7i), not a rule here.
  `searchable_by` says which search arms the extract carries: an extract of
  policy numbers only cannot be searched by name, and a name search over it is
  IDENTIFIERS_INSUFFICIENT rather than a silent NOT_FOUND - the standing rule
  that a result not computed is never reported as a negative.
- `policies.json`: a list of `{"policy_reference", "policy_number",
  "named_insureds": [...], "risk_postal_code"}`, the search's universe.
- `terms.json`: `{"<policy_reference>": <term history>}`, each history in the
  live-query wire shape live_query_source.py already reads.
- `claims.json`: `{"<policy_reference>": [<claim>, ...]}`, likewise.

Matching is the same plain rule the in-process fixture applies: a number
matches on equality, a name matches any named insured case-insensitively
beside an equal postal code, and a policy matching on both reports the
number. A selected record is then parsed by live_query_source.py's parsers,
so the two shapes cross into the domain through one translation.

What raises, and what the guard makes of it (live_query_ports.py `guarded`):
a file that cannot be read raises whatever the reader raises, SOURCE_UNAVAILABLE;
one that is not JSON, or not the document shape named above, raises
MalformedAnswerError, SOURCE_MALFORMED; a reference no file holds raises
LookupError, SOURCE_UNAVAILABLE as for a live source (ASSUMPTIONS.md, 7e
decision 7). The reader is a parameter so a test can make one read slow or
fail; the default reads the file.
"""

import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Final

from claimgate.domain.policy_identification import SearchIdentifiers
from claimgate.shell.bindings import COMPLETE_HISTORY
from claimgate.shell.live_query_source import MalformedAnswerError, UnsupportedSearchError

MANIFEST: Final = "manifest.json"
POLICIES: Final = "policies.json"
TERMS: Final = "terms.json"
CLAIMS: Final = "claims.json"
# The search arms an extract can declare, in the wire vocabulary
# live_query_source.py maps onto the domain's arm names.
BY_POLICY_NUMBER: Final = "policy_number"
BY_INSURED_NAME_AND_POSTAL_CODE: Final = "insured_name_and_postal_code"
SEARCH_ARMS: Final = frozenset({BY_POLICY_NUMBER, BY_INSURED_NAME_AND_POSTAL_CODE})

Record = Mapping[str, Any]
Reader = Callable[[Path], str]


@dataclass(frozen=True)
class ExtractManifest:
    generated_at: datetime
    history_from: date | None
    searchable_by: frozenset[str]


def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


@dataclass(frozen=True)
class ExtractFileSet:
    directory: Path
    read_text: Reader = read_file

    def manifest(self) -> str:
        return self.read_text(self.directory / MANIFEST)

    def candidates(self, manifest: ExtractManifest, identifiers: SearchIdentifiers) -> list[Record]:
        by_name = BY_INSURED_NAME_AND_POSTAL_CODE in manifest.searchable_by
        if identifiers.policy_number is None and not by_name:
            raise UnsupportedSearchError("this extract carries policy numbers only")
        found = []
        for record in _records(self._load(POLICIES)):
            basis = _basis(record, identifiers, by_name)
            if basis is not None:
                found.append(_candidate(record, basis))
        return found

    def history(self, policy_reference: str) -> object:
        return _entry(self._load(TERMS), policy_reference)

    def claims(self, policy_reference: str) -> object:
        return _entry(self._load(CLAIMS), policy_reference)

    def _load(self, name: str) -> object:
        text = self.read_text(self.directory / name)
        try:
            return json.loads(text)
        except ValueError as malformed:
            raise MalformedAnswerError(f"{name} is not JSON") from malformed


def parse_manifest(raw: object) -> ExtractManifest:
    """The manifest document from its text; anything that is not the shape
    raises, and the port answers SOURCE_MALFORMED with the call instant, there
    being no extract instant to answer with."""
    if not isinstance(raw, str):
        raise TypeError(f"expected the manifest's text, got {type(raw).__name__}")
    record = _mapping(json.loads(raw))
    arms = frozenset(_strings(_field(record, "searchable_by")))
    if not arms or not arms <= SEARCH_ARMS:
        raise ValueError(f"searchable_by names arms this shape does not have: {sorted(arms)}")
    return ExtractManifest(
        generated_at=_instant(_string(_field(record, "generated_at"))),
        history_from=_horizon(_string(_field(record, "history_from"))),
        searchable_by=arms,
    )


def _instant(value: str) -> datetime:
    instant = datetime.fromisoformat(value)
    if instant.tzinfo is None:
        raise ValueError("an extract's instant carries its offset")
    return instant


def _horizon(value: str) -> date | None:
    return None if value == COMPLETE_HISTORY else date.fromisoformat(value)


def _basis(record: Record, identifiers: SearchIdentifiers, by_name: bool) -> str | None:
    if _matches_number(record, identifiers.policy_number):
        return BY_POLICY_NUMBER
    if by_name and _matches_name(record, identifiers):
        return BY_INSURED_NAME_AND_POSTAL_CODE
    return None


def _matches_number(record: Record, policy_number: str | None) -> bool:
    return policy_number is not None and _field(record, "policy_number") == policy_number


def _matches_name(record: Record, identifiers: SearchIdentifiers) -> bool:
    name, postal_code = identifiers.insured_name, identifiers.risk_postal_code
    if name is None or postal_code is None:
        return False
    names = {insured.casefold() for insured in _strings(_field(record, "named_insureds"))}
    return name.casefold() in names and _field(record, "risk_postal_code") == postal_code


def _candidate(record: Record, basis: str) -> Record:
    return {
        "policy_reference": _field(record, "policy_reference"),
        "policy_number": _field(record, "policy_number"),
        "named_insureds": _field(record, "named_insureds"),
        "matched_by": basis,
    }


def _entry(raw: object, policy_reference: str) -> object:
    entries = _mapping(raw)
    if policy_reference not in entries:
        # The extract's own failure, as an unknown reference is a live
        # source's: the reference came from this extract's own search.
        raise LookupError(f"no entry for {policy_reference!r}")
    return entries[policy_reference]


# -- the document shape, checked before any parser sees a record -----------------


def _records(raw: object) -> list[Record]:
    return [_mapping(item) for item in _sequence(raw)]


def _mapping(raw: object) -> Record:
    if not isinstance(raw, Mapping):
        raise MalformedAnswerError(f"expected a record, got {type(raw).__name__}")
    return raw


def _sequence(raw: object) -> Sequence[object]:
    if isinstance(raw, str | bytes) or not isinstance(raw, Sequence):
        raise MalformedAnswerError(f"expected a list, got {type(raw).__name__}")
    return raw


def _strings(raw: object) -> list[str]:
    return [_string(item) for item in _sequence(raw)]


def _string(raw: object) -> str:
    if not isinstance(raw, str):
        raise MalformedAnswerError(f"expected text, got {type(raw).__name__}")
    return raw


def _field(record: Record, key: str) -> object:
    if key not in record:
        raise MalformedAnswerError(f"record has no {key!r}")
    return record[key]
