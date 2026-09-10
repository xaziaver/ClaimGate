"""An in-process stand-in for a core system's policy and claims sides, for the
live-query port implementations to query.

This is the source live_query_source.py's protocols describe, answering in its
wire shape from records a test puts in: policies with a reference, a number,
named insureds, a risk address and a term history; claims per reference. It is
also where a test makes the source misbehave - sleep for a while, raise, answer
a shape that is not the wire shape - once, on the next call from either side,
or on every call for as long as the source lives, which is what a scenario
whose Background declares the source unavailable needs across several
submissions (item 7f); where a source with no insured-name search is stood
up; and where the claims side alone is made to fail (item 7h). Lives
under tests/ because no deployment ships it; item 7i's acceptance runs reach it
from tests/api/ as `tests.fixtures.core_system`, the way the shell tests do.

Matching is deliberately plain: a policy number matches on equality, a name
matches any named insured case-insensitively beside an equal postal code, and a
policy matching on both reports the number. What a real system's matching rule
is belongs to that system.
"""

import time
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any

from claimgate.shell.live_query_source import UnsupportedSearchError

# Not the wire shape of any answer: a mapping where a sequence is expected, a
# mapping without the expected keys where a mapping is.
MALFORMED_ANSWER: dict[str, Any] = {"garbage": True}


@dataclass(frozen=True)
class FixtureAddress:
    line: str
    city: str
    state: str
    postal_code: str


def term(
    effective: date, expiration: date, status_changes: Sequence[tuple[str, date]] = ()
) -> dict[str, Any]:
    """One term in the wire shape. status_changes pairs a kind the wire
    vocabulary knows - "cancellation", "reinstatement" - with its date."""
    return {
        "effective": effective.isoformat(),
        "expiration": expiration.isoformat(),
        "status_changes": [
            {"kind": kind, "effective": on.isoformat()} for kind, on in status_changes
        ],
    }


def claim(claim_id: str, policy_number: str, loss_date: date, loss_type: str) -> dict[str, Any]:
    return {
        "claim_id": claim_id,
        "policy_number": policy_number,
        "loss_date": loss_date.isoformat(),
        "loss_type": loss_type,
    }


class InProcessCoreSystem:
    def __init__(self) -> None:
        self._policies: dict[str, dict[str, Any]] = {}
        self._claims: dict[str, list[dict[str, Any]]] = {}
        self._next_call: tuple[str, Any] | None = None
        self._every_call: tuple[str, Any] | None = None
        self._claims_fault: Exception | None = None
        self._name_search = True

    # -- what a test puts in -------------------------------------------------

    def hold_policy(
        self,
        reference: str,
        number: str,
        named_insureds: Sequence[str],
        address: FixtureAddress,
        terms: Sequence[dict[str, Any]],
        prior_coverage: tuple[date, date] | None = None,
    ) -> None:
        prior = None
        if prior_coverage is not None:
            effective, ending = prior_coverage
            prior = {"effective": effective.isoformat(), "ending": ending.isoformat()}
        self._policies[reference] = {
            "policy_number": number,
            "named_insureds": list(named_insureds),
            "address": address,
            "history": {"terms": list(terms), "prior_coverage": prior},
        }
        self._claims.setdefault(reference, [])

    def hold_claim(self, reference: str, record: dict[str, Any]) -> None:
        self._claims.setdefault(reference, []).append(record)

    # -- how a test makes it misbehave, once, on the next call -----------------

    def sleep_on_next_call(self, seconds: float) -> None:
        self._next_call = ("sleep", seconds)

    def raise_on_next_call(self, error: Exception | None = None) -> None:
        self._next_call = ("raise", error if error is not None else RuntimeError("source failure"))

    def answer_malformed_on_next_call(self) -> None:
        self._next_call = ("malformed", None)

    def without_name_search(self) -> None:
        self._name_search = False

    # -- and on every call, for as long as it lives --------------------------

    def sleep_on_every_call(self, seconds: float) -> None:
        self._every_call = ("sleep", seconds)

    def raise_on_every_call(self, error: Exception | None = None) -> None:
        self._every_call = ("raise", error if error is not None else RuntimeError("source failure"))

    def answer_malformed_on_every_call(self) -> None:
        self._every_call = ("malformed", None)

    # -- and on the claims side only, for as long as it lives --------------------

    def raise_on_every_claims_call(self, error: Exception | None = None) -> None:
        """The claims side down while the policy side answers as before (item
        7h, ASSUMPTIONS.md decision 5): a policy the search finds whose claims
        cannot be read, which one fixture standing in for both sources could
        not otherwise show."""
        self._claims_fault = error if error is not None else RuntimeError("claims source failure")

    # -- the source protocols ---------------------------------------------------

    def search(
        self, policy_number: str | None, insured_name: str | None, risk_postal_code: str | None
    ) -> object:
        misbehaviour = self._misbehave()
        if misbehaviour is not None:
            return misbehaviour
        if policy_number is None and not self._name_search:
            raise UnsupportedSearchError("this source searches by policy number only")
        found = []
        for reference, policy in self._policies.items():
            basis = self._match(policy, policy_number, insured_name, risk_postal_code)
            if basis is not None:
                found.append(self._candidate(reference, policy, basis))
        return found

    def term_history(self, policy_reference: str) -> object:
        misbehaviour = self._misbehave()
        if misbehaviour is not None:
            return misbehaviour
        return self._policies[policy_reference]["history"]

    def existing_claims(self, policy_reference: str) -> object:
        misbehaviour = self._misbehave()
        if misbehaviour is not None:
            return misbehaviour
        if self._claims_fault is not None:
            raise self._claims_fault
        return list(self._claims[policy_reference])

    # -- internals -------------------------------------------------------------

    def _misbehave(self) -> object | None:
        pending, self._next_call = self._next_call, None
        if pending is None:
            pending = self._every_call
        if pending is None:
            return None
        kind, argument = pending
        if kind == "sleep":
            time.sleep(argument)
            return None
        if kind == "raise":
            raise argument
        return MALFORMED_ANSWER

    def _match(
        self,
        policy: dict[str, Any],
        policy_number: str | None,
        insured_name: str | None,
        risk_postal_code: str | None,
    ) -> str | None:
        if policy_number is not None and policy["policy_number"] == policy_number:
            return "policy_number"
        if insured_name is None or risk_postal_code is None or not self._name_search:
            return None
        names = {name.casefold() for name in policy["named_insureds"]}
        address: FixtureAddress = policy["address"]
        if insured_name.casefold() in names and address.postal_code == risk_postal_code:
            return "insured_name_and_postal_code"
        return None

    @staticmethod
    def _candidate(reference: str, policy: dict[str, Any], basis: str) -> dict[str, Any]:
        return {
            "policy_reference": reference,
            "policy_number": policy["policy_number"],
            "named_insureds": list(policy["named_insureds"]),
            "matched_by": basis,
        }
